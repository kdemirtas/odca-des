# odca-des

Discrete-event traffic simulation on object-driven cellular automata (ODCA-DES): capacity-1 SimPy cells, Newell car-following, logistic lane changing, HDV and AV behaviour.
Shared by the ODCA papers under `~/Papers/`; each paper's golden fingerprint is a test here. MIT licensed.

## Layout

    HANDOVER.md        resume pointer, read this first
    STATUS.md          dated log
    PROJECT.md         spec
    ARCHITECTURE.md    shape of the work, proof strategy
    CLAUDE.md          working rules
    docs/              longer reference docs the spec links
    sources/           reference material, catalogued in `sources/SOURCES.md`

## How to use and test

    uv sync --group dev                 # venv with pytest
    uv run pytest                       # every paper's golden fingerprint, exact (about 6 min)
    uv run pytest --write-golden        # re-record, only under a bug-fix or refactor decision
    # in a paper: odca-des = { path = "../../odca-des", editable = true } under [tool.uv.sources]
