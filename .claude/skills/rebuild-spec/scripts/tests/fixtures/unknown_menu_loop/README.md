# unknown_menu_loop fixture (Phase 10, integration corpus, Track D)

A small, genuinely unrecognized-stack repo (plain C + a shell helper) — no existing
stack-profile's `detection.globs` matches `*.c` or `*.sh` (cobol/delphi/oracle/web-js-ts all
glob on their own language's file extensions or manifest files), so
`detect_stack_profile.py` returns an empty match at the root and falls through to the
Tier-0/1/2 content-sniff fallback (`_content_sniff_lib.sniff_ui`, Phase 07/08).

- `menu.c` — a C CLI menu loop (`scanf` + `printf`-based option list + `switch` dispatch),
  the same Tier-2 shape (stdin-read AND menu-loop AND no GUI-toolkit import) proven by
  `test_content_sniff.py::TestTier2MenuLoop`.
- `login.sh` — a companion shell-menu helper carrying a planted fake secret flag, reusing
  the exact generic-secret-scrub shape proven by
  `test_content_sniff.py::TestGenericSecretScrub` — this phase's Security Consideration
  ("plant one fake secret line ... assert it's scrubbed before reaching any citation").

Note: this README is prose, not source under test, but `sniff_ui` walks every file under
root regardless of extension — keep wording here free of the sniff-signal keyword table
(see `_content_sniff_signals_lib.SIGNAL_FAMILIES`) so it doesn't add noise signals of its
own to the fixture's expected verdict.
