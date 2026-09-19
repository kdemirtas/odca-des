# odca-des: status
> Read `PROJECT.md` first (the spec). This file = where things stand and what to do next. Entries
> older than the current wave are in `STATUS_ARCHIVE.md`. Last updated **2026-09-19**.
> **Current wave:** extraction and refactor, since 2026-09-19

## TL;DR
Shared ODCA simulator, extracted from paper-odca-des 2026-09-19. Bugs fixed, lane-change rate
rule in, refactor design settled; next is the refactor N2 to N8 (ranked list in `HANDOVER.md`).

## Current numbers
Goldens: paper_odca_des 24 quick runs (S1-S4 and bottleneck, seeds 1-3), re-recorded 2026-09-19
after the bug fixes and the lane-change rate rule; `uv run pytest` 25/25 passed.

## 2026-09-19: extraction, bug fixes, lane-change rate, refactor design
- **Created** from paper-odca-des `code/odca/` with its history (git filter-repo); paper-odca-des
  depends on it editable. First move byte-identical: golden 24/24 exact from both sides.
- **Bug fixes** (Kerem: fix every bug, paper is the spec), each a decision: exit lane any lane at
  the segment end (D-2026-09-19-11); one position-change point `_on_cell_change` at arrival, lock unchanged
  (D-2026-09-19-12); lane-change safety rejects occupied or locked cells (D-2026-09-19-13); summary window by exit time
  (D-2026-09-19-14); per-cell delay (D-2026-09-19-15); one exit path, missed off-ramps retargeted and counted, lateral
  race fixed (D-2026-09-19-17); lane changes counted on grant, cooldown for DLC only (D-2026-09-19-18); AVs act at the
  controller rate, initial vehicles follow the AV share (D-2026-09-19-19); measurement fixes, SimPy event
  count, all speed evaluations, lane changes per km over distance driven, space-mean speed (D-2026-09-19-20).
  Golden re-recorded after each; every run moved. S1 seed 1 now reports about 2.25M SimPy events
  (the old counter summed about 57k), so the paper's event and scalability claims need restating.
- **Lane-change rate** (D-2026-09-19-22, Kerem chose "MLC per distance, DLC per second"): q = 1-(1-p)^x, x =
  cells driven / 5.2 (MLC) or seconds (DLC); `odca/models/lane_changing/rate.py`. Where half the
  vehicles have attempted the MLC: 0.60 in every case (was 0.85 for AVs, 0.60 free-flow HDVs).
  Golden, seed 1 old -> new: S1 lane changes 231 -> 235, delay 30.8 -> 29.1 s; S4 delay 9.08 ->
  10.4 s; bottleneck 0% AV delay 69 -> 74.5 s. Write-up `docs/lane-change-rate.md`, including the
  finding that DLC fires at p = 0.047/s with no speed advantage (for paper-lc-logistic).
- **Refactor design** (`/architect`): one config per class with `ConfigMixin`, schemas in
  `odca/params.py`, omegaconf only at the run boundary (D-2026-09-19-23; a DictConfig read measured about 250
  times slower than a dataclass slot); Driver split from Vehicle with the two-way link contract
  Kerem agreed (D-2026-09-19-24). `docs/config-and-driver-design.md`. BACKLOG B5 (segment controllers, a model
  feature), B6 (own event loop instead of SimPy, v2).
- Assumptions open: A-2026-09-19-1 to -7 (`ASSUMPTIONS.md`).
- ⏳ Gate WARN: `params` (long inits), closed by N4.

## How to run
`uv run pytest` (add `-n 12` for parallel; `--write-golden` re-records, only under a decision)
