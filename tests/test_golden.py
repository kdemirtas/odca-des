"""Golden fingerprints: every paper that uses odca-des must reproduce its recorded runs exactly.

One directory per paper under tests/golden/, holding that paper's parameter values (config.py),
its scenario definitions (scenarios.py) and fingerprint.json. A change that makes a fingerprint
differ is not neutral: it needs a bug-fix decision and a re-recorded fingerprint (D-2026-09-19-8).
Record with `pytest tests/test_golden.py --write-golden`.
"""

import importlib
import json
import sys
from pathlib import Path

import pytest

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
EXCLUDED_STATS = {"wall_time_s"}  # machine-dependent


def _load_paper(paper_dir: Path):
    """Import one paper's config and scenarios, plus a fresh odca bound to that config.

    Each paper names its modules `config` and `scenarios`, and odca still imports `config`
    (until N2), so all three are dropped from the module cache before each paper loads. Runs
    collected for an earlier paper keep references to the odca objects built for it.
    """
    for name in list(sys.modules):
        if name in ("config", "scenarios") or name == "odca" or name.startswith("odca."):
            del sys.modules[name]
    sys.path.insert(0, str(paper_dir))
    try:
        return importlib.import_module("scenarios")
    finally:
        sys.path.remove(str(paper_dir))


def _cases():
    for paper_dir in sorted(p for p in GOLDEN_DIR.iterdir() if p.is_dir()):
        scenarios = _load_paper(paper_dir)
        for run_id, run in scenarios.golden_runs():
            yield pytest.param(paper_dir, run_id, run, id=f"{paper_dir.name}:{run_id}")


def _fingerprint(stats, counters):
    return {
        "stats": {k: v for k, v in sorted(stats.items()) if k not in EXCLUDED_STATS},
        "counters": dict(sorted(counters.items())),
    }


CASES = list(_cases())


def test_goldens_exist():
    assert CASES, f"no golden runs found under {GOLDEN_DIR}"


@pytest.mark.parametrize("paper_dir,run_id,run", CASES)
def test_golden(paper_dir, run_id, run, request):
    actual = _fingerprint(*run())
    path = paper_dir / "fingerprint.json"
    recorded = json.loads(path.read_text())
    if request.config.getoption("--write-golden"):
        recorded["runs"][run_id] = actual
        path.write_text(json.dumps(recorded, indent=1) + "\n")
        return
    assert actual == recorded["runs"][run_id]
