# cobol_mixed fixture (Phase 10, integration corpus)

Mixed-paradigm repo: one genuine SCREEN-SECTION-only `.cbl` file AND one genuine
CICS-BMS-macro-shaped `.bms` file, in the SAME repo — proves the router
(`extract_cobol_screen.py`) dispatches both paradigms in one run and merges them into ONE
screen digest, and that `detect_stack_profile.py` recommends `cobol` with no `--profile` pin
needed (only `cobol.json`'s detection globs match `*.cbl`/`*.bms`).

- `menu_screens.cbl` — the same anonymized inline SCREEN SECTION shape as
  `../cobol_screen_section/inline_screen.cbl` (MENU-SCREEN / ITEM-ENQUIRY-SCREEN). No BMS
  macros, no `EXEC CICS` — routes to `_cobol_screen_section_lib` only.
- `ORDRMAP.bms` — a real fixed-column CICS BMS deck (`DFHMSD`/`DFHMDI`/`DFHMDF`, label col 1,
  macro col ~10, operand col ~17 with a genuine field separator — mirrors the grammar proven
  by `test_cobol_bms.py`). Routes to `_cobol_bms_lib` only.
