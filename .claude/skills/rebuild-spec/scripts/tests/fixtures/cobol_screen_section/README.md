# cobol_screen_section fixture (Phase 10, integration corpus)

Pipeline-level (detect → extract → generate → validate) round-trip fixture — distinct from
`../cobol_real_sample/` which backs Phase 02/03's per-lib unit tests.

- `inline_screen.cbl` — the SAME anonymized SCREEN SECTION content as
  `../cobol_real_sample/inline_screen.cbl` (two inline `01` records: MENU-SCREEN,
  ITEM-ENQUIRY-SCREEN; PERFORM chain across two SECTIONs). Reused verbatim per the plan's
  real-over-synthetic fixture philosophy — see that file's own docstring for provenance.
- `stock_crud.cbl` — the SAME real AcuCOBOL STOCK shape used by Phase 05's
  `test_extract_cobol_data.py` (indexed/DYNAMIC access, full C/R/U/D verb set against dataset
  `STOCK`). Added here so this one fixture repo drives BOTH `extract_cobol_screen.py` (screens)
  AND `extract_cobol_data.py` (CRUD/db-objects) end to end in a single pipeline run, per the
  phase's Success Criteria ("a COBOL repo that previously produced NO screens now produces
  cited screen-list/flow + CRUD/db-objects").

Neither file contains BMS macros or EXEC SQL — this fixture only exercises the SCREEN SECTION
paradigm + flat-file CRUD, not CICS BMS (see `../cobol_mixed/` for the mixed-paradigm case).
