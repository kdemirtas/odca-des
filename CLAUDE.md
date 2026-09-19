# CLAUDE.md: odca-des

the shared ODCA-DES traffic simulator package (import `odca`), used by every ODCA paper

Read `HANDOVER.md` first, then the top of `STATUS.md`, then `ARCHITECTURE.md` before touching
code. Type `generic`.

## Doc set

    HANDOVER.md        resume pointer, read first
    STATUS.md          session log, current wave; older entries in STATUS_ARCHIVE.md
    PROJECT.md         what and why, phases
    ARCHITECTURE.md    boundaries, contracts, types, invariants, proof; owned by /architect
    DECISIONS.md       dated D- ids: what was decided, the evidence, what it replaced
    CHANGELOG.md       one line per merged PR under its version or vintage
    BACKLOG.md         parked ideas: what, why, trigger
    sources/SOURCES.md reference material catalog

## Rules

- **Structure before code.** A change that adds a module, moves a boundary, or changes a
  contract or core type goes through `/architect` first and cites its `D-` id.
- **Code is the source of truth.** Docs describe what the code does today. A PR that changes
  behavior updates the spec `ARCHITECTURE.md` links in the same PR; a doc that disagrees with the
  code is a defect in the doc unless a `DECISIONS.md` entry says the code is wrong.
- **No history in code.** Comments say what the code does now. Why it changed lives in
  `DECISIONS.md`; when it shipped lives in `CHANGELOG.md`. A date in a comment is a review finding.
- **No switch without a decision.** A new flag, widget or mode names the `D-` id that needs it and
  the date it may be removed. A switch whose branches do the same thing is deleted, not kept.
- **Types, not tuples.** A concept in `ARCHITECTURE.md` Core types is passed as that type. A
  function over 6 parameters is a review finding.
- **Prove neutrality the project's way.** Every PR states which proof from `ARCHITECTURE.md`
  ran and its result; "tests pass" alone is not a proof of neutrality.
- **Numbers travel together.** A change that moves a quoted figure restates it everywhere it is
  quoted in the same PR.
- **Nothing in `odca` imports a paper** (`config`, scripts). A paper's values reach the package as `odca.params` types.
- **A new capability is off by default** and every paper's golden still passes with it off.
- **One bug fix, one place.** The papers' old `code/odca/` copies are frozen; fixes go here.
- **numpy RNG only, never `import random`;** a new RNG stream is spawned last.
- **Units:** cells (7.5 m, `CELL_LENGTH_M`), cells/s, seconds inside `odca`.
- Descriptive snake_case names, no one-letter or cryptic names in anything Kerem reads.
- One name per thing. A concept, column, class or variable keeps the one plain name the domain
  already has, everywhere it appears: the engine's season window is `season_window` in every
  table, type and doc, never a second name such as `movement_window`.
- No em-dashes in anything written here. Colon, comma, parentheses, or split the sentence.

## Environment
uv, Python 3.10+; `uv run pytest`.

## Related
`~/Papers/paper-odca-des` (first user and origin), `~/Papers/CLAUDE.md` (the rule that all ODCA papers use this package).
