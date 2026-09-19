"""Configuration schemas for every configurable odca class, and the mixin that loads them.

Each schema is a frozen dataclass with slots: fast to read inside the simulation and
impossible to change by accident. omegaconf is used only where a config enters a run
(`ConfigMixin.validate_config`): it checks types and unknown keys, then hands back the
dataclass (D-2026-09-19-23). Parameter values belong to the papers; the defaults here are
generic settings only. Units: cells, cells/s, seconds.
"""

from __future__ import annotations

import logging
from dataclasses import MISSING, dataclass, field, fields, is_dataclass
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, get_args, get_origin, get_type_hints

from omegaconf import DictConfig, ListConfig, OmegaConf
from omegaconf.errors import MissingMandatoryValue

CELL_LENGTH_M = 7.5  # metres per cell

PACKAGE_CONFIGS = Path(__file__).parent / "configs"  # the published defaults, `odca://<file>`
_PACKAGE_PREFIX = "odca://"
_BASE_KEY = "_base_"  # in a mapping: the file it starts from; its other keys override

_FROZEN = dict(frozen=True, slots=True)
# keyword-only for the config families, so a subclass can add required fields
_FROZEN_FAMILY = dict(frozen=True, slots=True, kw_only=True)


@dataclass(**_FROZEN)
class VehicleConfig:
    """The physical vehicle: top speed and footprint."""

    v_max: float               # maximum speed (cells/s)
    standstill_spacing: float  # jam spacing d (cells)


class ConfigFamily:
    """Base of a config family whose members are chosen by name in the `model` field.

    A YAML or mapping value for a field typed as the family base says which member it is
    (`model: logistic`); `validate` builds that member. Members register with `family_member`.
    """

    members: ClassVar[Dict[str, type]]

    def __init_subclass__(cls, **kwargs):
        """Give each family base (a direct subclass) its own member table.

        Args:
            **kwargs: passed on to `object.__init_subclass__`.
        """
        super().__init_subclass__(**kwargs)
        if ConfigFamily in cls.__bases__:
            cls.members = {}


def family_member(name: str):
    """Register a dataclass as the family member called `name` (its `model` value).

    Args:
        name: the value of `model` that selects this member in YAML.
    """
    def register(cls):
        """Add `cls` to its family's member table under `name`."""
        cls.members[name] = cls
        return cls
    return register


@dataclass(**_FROZEN_FAMILY)
class BaseLaneChangeConfig(ConfigFamily):
    """What every lane-change model has: gap acceptance and the DLC refractory period."""

    model: str                 # which member: "logistic"
    safety_gap_front: float    # min front gap (cells)
    safety_gap_rear: float     # min rear gap (cells)
    dlc_cooldown: float        # refractory time after a lane change (s)
    dlc_enabled: bool = True


@family_member("logistic")
@dataclass(**_FROZEN_FAMILY)
class LogisticLaneChangeConfig(BaseLaneChangeConfig):
    """Logistic MLC and DLC curves, probability per 5.2 cells and per second (D-2026-09-19-22)."""

    model: str = "logistic"

    mlc_k: float               # MLC steepness
    mlc_r0: float              # MLC midpoint (remaining-distance ratio)
    dlc_k: float               # DLC steepness
    dlc_v0: float              # DLC speed-advantage midpoint (cells/s)


@dataclass(**_FROZEN_FAMILY)
class DriverConfig:
    """What every driver has: reaction time, perception range, random slowdown, lane changing."""

    tau: float                 # reaction time; the cell is released tau after leaving it (s)
    action_interval: float     # time between decisions (s)
    slowdown_prob: float       # chance of a random slowdown per decision
    slowdown_delta: float      # speed lost in a slowdown (cells/s)
    look_ahead: int            # cells scanned forward
    look_behind: int           # cells scanned backward
    lane_change: BaseLaneChangeConfig


@dataclass(**_FROZEN_FAMILY)
class HumanDriverConfig(DriverConfig):
    """A human driver population: tau, action_interval and slowdown_prob are means."""

    tau_std: float = 0.0
    action_interval_std: float = 0.0
    slowdown_prob_std: float = 0.0


@dataclass(**_FROZEN_FAMILY)
class AutonomousDriverConfig(DriverConfig):
    """An autonomous driver: every value is exact."""


@dataclass(**_FROZEN)
class ControllerConfig:
    """The central controller that makes the autonomous drivers' decisions."""

    dt: float = 0.1            # decision interval (s)


@dataclass(**_FROZEN)
class OriginConfig:
    """Where vehicles enter: a lane (1 = rightmost) and a cell; an on-ramp if the cell is > 0."""

    lane: int
    cell: int = 0


@dataclass(**_FROZEN)
class DestinationConfig:
    """Where vehicles leave: at the downstream edge of cell `cell - 1`, from `lane`.

    `lane` None means any lane (the segment end of a lane drop, for example). A destination
    before the segment end (`cell` < num_cells) is an off-ramp.
    """

    cell: int
    lane: Optional[int] = None


@dataclass(**_FROZEN)
class NetworkConfig:
    """Freeway geometry and its named origins and destinations (D-2026-09-19-26)."""

    num_lanes: int
    num_cells: int
    speed_limit: float             # cells/s
    origins: Dict[str, OriginConfig]
    destinations: Dict[str, DestinationConfig]

    @property
    def onramp_cells(self) -> List[int]:
        """Cells where an on-ramp joins, upstream first."""
        return sorted({o.cell for o in self.origins.values() if o.cell > 0})

    @property
    def offramp_cells(self) -> List[int]:
        """Cells where an off-ramp leaves, upstream first."""
        return sorted({d.cell for d in self.destinations.values() if d.cell < self.num_cells})

    @classmethod
    def corridor(cls, num_lanes: int, num_cells: int, speed_limit: float) -> "NetworkConfig":
        """A segment without ramps: origin `mainline_lane_<n>` at cell 0 of every lane,
        destinations `end_lane_<n>` (the end of lane n) and `end` (the end, any lane).

        Args:
            num_lanes: lanes, 1 the rightmost.
            num_cells: cells per lane.
            speed_limit: cells/s.
        """
        lanes = range(1, num_lanes + 1)
        destinations = {f"end_lane_{n}": DestinationConfig(num_cells, n) for n in lanes}
        destinations["end"] = DestinationConfig(num_cells)
        return cls(num_lanes=num_lanes, num_cells=num_cells, speed_limit=speed_limit,
                   origins={f"mainline_lane_{n}": OriginConfig(n) for n in lanes},
                   destinations=destinations)


@dataclass(**_FROZEN)
class IncidentConfig:
    """Cells blocked or slowed for a while, then put back as they were (D-2026-09-19-28).

    The cells are `first_cell`..`last_cell` of `lane` (None: every lane), or, when `place`
    names an origin or destination, that place's endpoint cells (throttling only).
    """

    start: float                       # s
    duration: float                    # s
    lane: Optional[int] = None
    first_cell: int = 0
    last_cell: int = -1                # -1: the last cell of the lane
    place: Optional[str] = None
    speed_limit: Optional[float] = None  # cells/s; None blocks the cells


@dataclass(**_FROZEN)
class SimConfig:
    """One run: network, demand, vehicle types, mix, duration and seed."""

    network: NetworkConfig
    # veh/h per (origin, destination) pair, by name (D-2026-09-19-26):
    # origins mainline_lane_<n>, onramp_<k>; destinations offramp_<k>, end_lane_<n>, end
    demand: Dict[str, Dict[str, float]]
    hdv_vehicle: VehicleConfig
    hdv_driver: HumanDriverConfig
    av_vehicle: VehicleConfig
    av_driver: AutonomousDriverConfig
    controller: ControllerConfig = field(default_factory=ControllerConfig)
    incidents: List[IncidentConfig] = field(default_factory=list)
    av_penetration: float = 0.0
    sim_duration: float = 3600.0   # s
    warmup: float = 300.0          # s before statistics are collected
    seed: int = 42
    log_level: int = logging.INFO


def validate(schema: type, cfg: Any) -> Any:
    """Check `cfg` against `schema` and return it as a `schema` instance.

    YAML files may name other files for a nested config (`network: network_s1.yaml`, relative
    to the naming file, or `odca://hdv_driver.yaml` for the package defaults), or start from
    one and override some keys (`hdv_driver: {_base_: odca://hdv_driver.yaml, tau: 1.2}`).

    Args:
        schema: a dataclass from this module.
        cfg: an instance of it, a mapping, a DictConfig, or a YAML path (`odca://` allowed).

    Returns:
        The frozen dataclass, with values converted to the declared types.

    Raises:
        omegaconf.errors.ValidationError: a value has the wrong type.
        omegaconf.errors.ConfigKeyError: a key the schema does not declare.
        omegaconf.errors.MissingMandatoryValue: a required value is absent.
    """
    if isinstance(cfg, schema):
        return OmegaConf.to_object(_writable(OmegaConf.structured(cfg)))
    base_dir = Path.cwd()
    if isinstance(cfg, (str, Path)):
        cfg, base_dir = _load(str(cfg), base_dir)
    if isinstance(cfg, (DictConfig, ListConfig)):
        cfg = OmegaConf.to_container(cfg, resolve=True)
    return _build(schema, cfg, base_dir)


def _load(ref: str, base_dir: Path):
    """Read the YAML file `ref` names.

    Args:
        ref: a path relative to `base_dir`, absolute, or `odca://<file>` for the package defaults.
        base_dir: the directory of the file that names `ref`.

    Returns:
        (plain data, the directory later references inside it are relative to).
    """
    if ref.startswith(_PACKAGE_PREFIX):
        path = PACKAGE_CONFIGS / ref[len(_PACKAGE_PREFIX):]
    else:
        path = base_dir / ref
    return OmegaConf.to_container(OmegaConf.load(path), resolve=True), path.parent


def _build(tp: Any, value: Any, base_dir: Path) -> Any:
    """Build `value` as type `tp`, innermost configs first.

    omegaconf checks the plain values of each config (types, unknown keys, missing values);
    nested configs are built by this function and passed to the dataclass directly. A string
    where a config, list or table belongs names a YAML file; a mapping typed as a
    `ConfigFamily` base becomes
    the member its `model` names.

    Args:
        tp: the declared type of `value` (a schema dataclass, List[...], Optional[...]).
        value: plain data from YAML or a mapping, or an already built config.
        base_dir: the directory file references in `value` are relative to.

    Returns:
        The value with every config mapping turned into its frozen dataclass.

    Raises:
        ValueError: a family mapping names no model, or one the family does not have.
        omegaconf.errors.MissingMandatoryValue: a required value is absent.
    """
    if isinstance(value, str) and (_holds_config(tp) or get_origin(tp) in (list, dict)):
        value, base_dir = _load(value, base_dir)
    elif isinstance(value, dict) and _BASE_KEY in value:
        overrides = {k: v for k, v in value.items() if k != _BASE_KEY}
        start, base_dir = _load(value[_BASE_KEY], base_dir)
        value = OmegaConf.to_container(OmegaConf.merge(start, overrides))
    if get_origin(tp) is not None:  # Optional[X], List[X]
        args = [a for a in get_args(tp) if a is not type(None)]
        if isinstance(value, list) and get_origin(tp) is list:
            return [_build(args[0], item, base_dir) for item in value]
        if isinstance(value, dict) and get_origin(tp) is dict:
            return {key: _build(args[1], item, base_dir) for key, item in value.items()}
        return _build(args[0], value, base_dir) if len(args) == 1 else value
    if not (isinstance(tp, type) and is_dataclass(tp) and isinstance(value, dict)):
        return value
    if issubclass(tp, ConfigFamily):
        name = value.get("model")
        if name not in tp.members:
            raise ValueError(f"{tp.__name__}: model {name!r} is not one of {sorted(tp.members)}")
        tp = tp.members[name]
    hints = get_type_hints(tp)
    value = {k: _build(hints[k], v, base_dir) if k in hints else v for k, v in value.items()}
    nested = {k: v for k, v in value.items() if k in hints and _holds_config(hints[k])}
    plain = OmegaConf.merge(_writable(OmegaConf.structured(tp)),
                            {k: v for k, v in value.items() if k not in nested})
    plain = OmegaConf.to_container(plain)
    kwargs = {}
    for f in fields(tp):
        if f.name in nested:
            kwargs[f.name] = nested[f.name]
        elif not _holds_config(hints[f.name]):
            kwargs[f.name] = plain[f.name]
        elif f.default is MISSING and f.default_factory is MISSING:
            kwargs[f.name] = "???"
        if kwargs.get(f.name) == "???":
            raise MissingMandatoryValue(f"{tp.__name__}.{f.name} is required")
    return tp(**kwargs)


def _holds_config(tp: Any) -> bool:
    """Whether a field of type `tp` holds a config (or a list of them).

    Args:
        tp: a field's declared type.
    """
    if get_origin(tp) is not None:
        return any(_holds_config(a) for a in get_args(tp) if a is not type(None))
    return isinstance(tp, type) and is_dataclass(tp)


def _writable(node):
    """`node` with its read-only flags cleared (see `_make_writable`).

    Args:
        node: a structured config built from a frozen dataclass.
    """
    _make_writable(node)  # frozen dataclasses give read-only nodes, which cannot be merged into
    return node


def _make_writable(node) -> None:
    """Clear the read-only flag on a config node and every node below it.

    Args:
        node: a DictConfig or ListConfig.
    """
    node._set_flag("readonly", None)
    keys = node.keys() if isinstance(node, DictConfig) else range(len(node))
    for key in keys:
        child = node._get_node(key)
        if isinstance(child, (DictConfig, ListConfig)):
            _make_writable(child)


class ConfigMixin:
    """One config per class: the class names its schema, `__init__` takes one `cfg`.

    Runtime objects (the SimPy environment, RNG streams, cells) are separate arguments,
    never part of the config.
    """

    Config: ClassVar[type]
    cfg: Any

    @classmethod
    def validate_config(cls, cfg: Any) -> Any:
        """Return `cfg` checked against `cls.Config` (see `validate`).

        Args:
            cfg: an instance of the schema, a mapping, a DictConfig or a YAML path.
        """
        return validate(cls.Config, cfg)

    @classmethod
    def from_config(cls, cfg: Any, *runtime, **runtime_kw):
        """Build the class from a config in any form `validate` accepts.

        Args:
            cfg: the config, in any form `validate` accepts.
            *runtime: runtime objects passed on to `__init__` after the config.
            **runtime_kw: runtime objects passed on by name.
        """
        return cls(cls.validate_config(cfg), *runtime, **runtime_kw)

    def save_config(self) -> str:
        """The resolved config as YAML."""
        if not is_dataclass(self.cfg):
            raise TypeError(f"{type(self).__name__}.cfg is not a config dataclass")
        return OmegaConf.to_yaml(OmegaConf.structured(self.cfg))
