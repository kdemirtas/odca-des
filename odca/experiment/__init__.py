"""Experiment kit: run a scenario, write one JSON per run, aggregate runs into CSVs.

D-2026-09-19-33.
"""

from odca.experiment.records import RunRecord, numpy_default, read_runs, run_once, write_run
from odca.experiment.tables import aggregate, write_aggregate_csv, write_per_seed_csv

__all__ = ["RunRecord", "numpy_default", "read_runs", "run_once", "write_run", "aggregate",
           "write_aggregate_csv", "write_per_seed_csv"]
