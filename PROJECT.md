# odca-des: the shared ODCA-DES traffic simulator package (import `odca`), used by every ODCA paper
> **Last updated 2026-10-02.** Read this first; `STATUS.md` says where things stand, `ARCHITECTURE.md`
> says how the code is shaped, `DECISIONS.md` says what was decided and why.

## Overview
The ODCA-DES simulator as one package for all ODCA papers (paper-odca-des:D-2026-09-19-6).

## What "done" means
Every ODCA paper runs on this package, each paper's golden passes, and the package is published with paper-odca-des.

## Design decisions
The founding ones are paper-odca-des:D-2026-09-19-6 to -10; this repo's own are in `DECISIONS.md`.

## Out of scope
Paper-specific scenarios, parameter values and figures (they stay in the papers).



## Phases
1. Extraction (done 2026-09-19). 2. Code-quality refactor (N2 to N8, done 2026-09-19). 3. Other papers switch over. 4. Publication (repo public since 2026-09-22; PyPI is BACKLOG B3).

See `HANDOVER.md`.
