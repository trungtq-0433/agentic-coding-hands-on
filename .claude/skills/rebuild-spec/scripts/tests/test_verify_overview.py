"""Tests for extensions/scripts/verify_overview.py (OV.3 token-leak gate).

Tests that the scan() function properly:
- Ignores snake_case tokens inside fenced code blocks
- Ignores snake_case tokens inside Markdown link targets and bare URLs
- Still flags snake_case tokens in plain prose
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
REBUILD_SPEC_ROOT = SCRIPTS_DIR.parent
EXTENSIONS_SCRIPTS = REBUILD_SPEC_ROOT / "extensions" / "scripts"
sys.path.insert(0, str(EXTENSIONS_SCRIPTS))
sys.path.insert(0, str(SCRIPTS_DIR))

from verify_overview import scan  # noqa: E402


class TestCodeBlockExclusion:
    def test_snake_case_in_fenced_code_block_ignored(self):
        """Regression: snake_case inside ``` block is NOT flagged."""
        text = """\
# System Overview

Here is an example:

```python
def user_profile():
    user_id = get_user()
    return fetch_data(user_id)
```

The above code is technical.
"""
        findings = scan(text)
        # No findings should report tokens from inside the fenced block
        assert not any(f[2] in ("user_profile", "user_id", "fetch_data") for f in findings)

    def test_snake_case_outside_code_block_flagged(self):
        """Regression guard: snake_case in prose (not in code block) is still flagged."""
        text = """\
# System Overview

Our user_profile system handles authentication.

```python
# code here is safe
internal_var = 1
```
"""
        findings = scan(text)
        # user_profile in prose should be flagged, internal_var in code should not
        assert any(f[2] == "user_profile" for f in findings)
        assert not any(f[2] == "internal_var" for f in findings)

    def test_tilde_fence_also_excludes(self):
        """Regression guard: ~~~ fence also excludes content."""
        text = """\
# Overview

~~~python
snake_case_in_fence = True
~~~

But snake_case_in_prose appears here.
"""
        findings = scan(text)
        assert not any(f[2] == "snake_case_in_fence" for f in findings)
        assert any(f[2] == "snake_case_in_prose" for f in findings)


class TestLinkTargetExclusion:
    def test_snake_case_in_link_target_ignored(self):
        """Regression: snake_case inside link target ](url/path/with_snake) is ignored."""
        text = """\
# Overview

For more details, see [the user guide](https://h.local/docs/user_profile_guide).
"""
        findings = scan(text)
        # user_profile should NOT be flagged because it's inside a link target
        assert not any(f[2] == "user_profile" for f in findings)

    def test_relative_link_target_excluded(self):
        """Regression: snake_case in relative link like ](../user_guide) is ignored."""
        text = """\
# Overview

See [our docs](../system_design/api_reference).
"""
        findings = scan(text)
        # Tokens inside link targets are stripped
        assert not any(f[2] in ("system_design", "api_reference") for f in findings)

    def test_snake_case_in_link_text_still_flagged(self):
        """Regression guard: snake_case in link text [user_profile] IS flagged."""
        text = """\
# Overview

For details see [user_profile](https://example.com).
"""
        findings = scan(text)
        # user_profile in link TEXT (not target) should be flagged
        assert any(f[2] == "user_profile" for f in findings)


class TestBareUrlExclusion:
    def test_snake_case_in_bare_url_ignored(self):
        """Regression: snake_case in bare URL is NOT flagged."""
        text = """\
# Overview

Visit https://api.example.com/v1/user_profile for details.
"""
        findings = scan(text)
        # user_profile inside the URL should not be flagged
        assert not any(f[2] == "user_profile" for f in findings)

    def test_http_url_excluded(self):
        """Regression guard: http (not just https) URLs are excluded."""
        text = """\
# Overview

Check http://system.local/get_user_data for the API.
"""
        findings = scan(text)
        # get_user_data inside URL should be ignored
        assert not any(f[2] == "get_user_data" for f in findings)

    def test_snake_case_outside_url_still_flagged(self):
        """Regression guard: snake_case outside URLs is still flagged."""
        text = """\
# Overview

The user_profile service is available at https://api.example.com/profile.
"""
        findings = scan(text)
        # user_profile outside the URL should be flagged
        assert any(f[2] == "user_profile" for f in findings)


class TestPlainProseDetection:
    def test_snake_case_in_prose_flagged(self):
        """Regression guard: snake_case in plain text IS flagged."""
        text = """\
# System Overview

The order_processing system handles all transactions.
"""
        findings = scan(text)
        assert any(f[2] == "order_processing" for f in findings)

    def test_multiple_snake_case_all_flagged(self):
        """Regression guard: multiple snake_case tokens in prose are all flagged."""
        text = """\
# System Overview

The user_profile and order_history modules work together in the backend_api layer.
"""
        findings = scan(text)
        tokens = {f[2] for f in findings}
        assert "user_profile" in tokens
        assert "order_history" in tokens
        assert "backend_api" in tokens

    def test_file_line_citation_flagged(self):
        """Regression guard: file:line citations in prose are flagged."""
        text = """\
# System Overview

See the auth implementation in src/auth/handler.py:42 for details.
"""
        findings = scan(text)
        assert any("handler.py:42" in str(f[2]) for f in findings)

    def test_entity_code_flagged(self):
        """Regression guard: entity ID codes like F001, SCR123 are flagged."""
        text = """\
# System Overview

Feature F001 and screen SCR042 are the core components.
"""
        findings = scan(text)
        tokens = {f[2] for f in findings}
        assert "F001" in tokens
        assert "SCR042" in tokens

    def test_clean_prose_returns_no_findings(self):
        """Regression guard: clean business English returns no findings."""
        text = """\
# System Overview

The Authentication Service manages all user sign-in and session operations.
It integrates with the Customer Portal to provide seamless access control.
"""
        findings = scan(text)
        assert len(findings) == 0


class TestEdgeCases:
    def test_mixed_code_and_prose(self):
        """Regression guard: code blocks are skipped but surrounding prose is checked."""
        text = """\
# Overview

The user_auth module handles login:

```python
def authenticate(user_id):
    return verify_token(user_id)
```

The internal_cache is used to speed lookups.
"""
        findings = scan(text)
        tokens = {f[2] for f in findings}
        # user_auth and internal_cache in prose should be flagged
        assert "user_auth" in tokens
        assert "internal_cache" in tokens
        # authenticate, verify_token in code should not
        assert "authenticate" not in tokens
        assert "verify_token" not in tokens

    def test_nested_fences_toggle_state(self):
        """Regression guard: fence state toggles (not nested)."""
        text = """\
# Overview

```
first_fence content
```

between_fences text

```
second_fence content
```
"""
        findings = scan(text)
        # between_fences should be flagged (not in fence)
        assert any(f[2] == "between_fences" for f in findings)
        # fence content should not be flagged
        assert not any(f[2] in ("first_fence", "second_fence") for f in findings)

    def test_url_and_code_together(self):
        """Regression guard: combination of URL exclusion and code exclusion."""
        text = """\
# Overview

Visit https://api.local/get_user_data and see the code:

```python
def process_user_data(user_id):
    return db.fetch(user_id)
```

The auth_service handles this flow.
"""
        findings = scan(text)
        tokens = {f[2] for f in findings}
        # In URLs and code: excluded
        assert "get_user_data" not in tokens
        assert "process_user_data" not in tokens
        assert "fetch" not in tokens
        # In prose: flagged
        assert "auth_service" in tokens
