# cobol_real_sample fixtures

Anonymized excerpts derived from a real AcuCOBOL/Micro Focus accounting-system codebase
(the user's target repo), per the plan's Validation Session 1 decision to source Phase 02/03
fixtures from real samples rather than synthetic ones (fidelity to actual SCREEN SECTION shape,
fixed/free-format mix, comment conventions).

Real-world facts this codebase confirmed (informs Phase 02/05/06 scope):
- SCREEN SECTION is commonly built from `COPY <name>.CRT.` statements rather than inline `01`
  records — production screens live in separate copybook files, not inline in the `.CBL`.
- Comment-column noise is real: retired/disabled fields are commented out in place (`*` in the
  indicator column) rather than deleted, sitting right next to live fields.
- File I/O is flat-file/indexed only (`SELECT ... ASSIGN`, `READ ... KEY IS`, `START ... KEY >=`,
  `WITH IGNORE LOCK` / `WITH KEPT LOCK`) — no `EXEC SQL` anywhere in the source. No CICS/BMS
  either (this codebase is AcuCOBOL screen-handling, not mainframe CICS green-screens).
- Personal names (a real author byline) and the real program/company identifiers have been
  stripped or replaced with placeholders; the COBOL syntax shapes (LINE/COLUMN/PIC/VALUE/FROM/
  USING/FOREGROUND-COLOR, REDEFINES, multi-record screens, COPY placement) are preserved as-is.

Files:
- `inline_screen.cbl` — inline SCREEN SECTION, two `01` records (menu + data-entry), comment-noise
  line, PERFORM chain across two paragraphs each ACCEPT/DISPLAY-ing a different screen record.
- `copy_split_screen.cbl` — SCREEN SECTION built entirely from `COPY` statements: one resolvable
  (`STOCKHDR.CRT`, present alongside) and one unresolvable (`LEGACYFOOTER.CRT`, deliberately absent
  — mirrors a real retired copybook still referenced by old code).
- `STOCKHDR.CRT` — the resolvable copybook target, itself carrying comment-noise (a disabled field).
