"""Tests for _credential_scrub_lib.py.

Existing coverage (jaas/password/token/bearer/broker-url) lived only inside
test_extract_service_topology.py; this module adds dedicated coverage plus the
v26.1.0 jobs-pass extension (F6): .service/.timer recognition + systemd
Environment=<KEY>=<value> redaction for abbreviated credential-ish KEY names.

v26.2.x (review C4 + quoted-quote minor): SCRUB (`scrub_line`) and GATE
(`assert_no_secrets`) are now two independent pattern sets — segment-boundary
KEY matching (+`auth` vocab) fixes both the `BYPASS_HEALTHCHECK` false-positive
and the `REDIS_AUTH` false-negative, and the GATE side additionally exempts
placeholder values and bare `Bearer`/`username` prose so clean docs never trip
the hard CRITICAL gate. Quoted `Environment="KEY=VALUE"` redaction now keeps
the closing quote.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import _credential_scrub_lib as scrub_lib  # noqa: E402


class TestIsConfigFile:
    def test_known_config_filenames(self):
        assert scrub_lib.is_config_file("application.yml")
        assert scrub_lib.is_config_file(".env")
        assert scrub_lib.is_config_file(".env.production")

    def test_service_and_timer_units_recognised(self):
        """F6 — .service/.timer unit files must be scannable alongside .env/application.yml."""
        assert scrub_lib.is_config_file("invoice-export.service")
        assert scrub_lib.is_config_file("invoice-export.timer")

    def test_unrelated_filename_not_recognised(self):
        assert not scrub_lib.is_config_file("README.md")
        assert not scrub_lib.is_config_file("invoice_export_job.rb")


class TestScrubLineExisting:
    """Pre-existing patterns must keep working after the F6 addition."""

    def test_scrub_line_removes_sasl_jaas(self):
        line = "sasl.jaas.config = org.apache.kafka.PlainLoginModule required password=\"hunter2\";"
        scrubbed = scrub_lib.scrub_line(line)
        assert "hunter2" not in scrubbed

    def test_scrub_line_removes_password_eq(self):
        line = "db.password=hunter2"
        scrubbed = scrub_lib.scrub_line(line)
        assert "hunter2" not in scrubbed

    def test_scrub_line_removes_bearer_token(self):
        line = "Authorization: Bearer abc123xyz"
        scrubbed = scrub_lib.scrub_line(line)
        assert "abc123xyz" not in scrubbed

    def test_scrub_line_removes_broker_url_creds(self):
        line = "amqp://user:hunter2@broker.internal:5672"
        scrubbed = scrub_lib.scrub_line(line)
        assert "hunter2" not in scrubbed


class TestScrubLineSystemdEnvironment:
    """F6 — Environment=<KEY>=<value> redaction for credential-ish abbreviated KEY names."""

    def test_environment_db_pass_redacted(self):
        line = "Environment=DB_PASS=hunter2"
        scrubbed = scrub_lib.scrub_line(line)
        assert "hunter2" not in scrubbed
        assert "DB_PASS=<redacted>" in scrubbed

    def test_environment_smtp_pwd_redacted(self):
        line = "Environment=SMTP_PWD=s3cr3t"
        scrubbed = scrub_lib.scrub_line(line)
        assert "s3cr3t" not in scrubbed

    def test_environment_api_token_redacted(self):
        line = 'Environment="API_TOKEN=abc123"'
        scrubbed = scrub_lib.scrub_line(line)
        assert "abc123" not in scrubbed

    def test_environment_dsn_redacted(self):
        line = "Environment=STRIPE_DSN=postgres://x"
        scrubbed = scrub_lib.scrub_line(line)
        assert "postgres://x" not in scrubbed

    def test_environment_non_secret_key_untouched(self):
        """A KEY with no credential-ish vocabulary (e.g. NODE_ENV) must NOT be redacted —
        systemd units carry plenty of non-secret config too."""
        line = "Environment=NODE_ENV=production"
        scrubbed = scrub_lib.scrub_line(line)
        assert scrubbed == line

    def test_environment_file_reference_untouched(self):
        """EnvironmentFile=<path> has no inline value — nothing to redact on this line."""
        line = "EnvironmentFile=/etc/myapp/secrets.env"
        scrubbed = scrub_lib.scrub_line(line)
        assert scrubbed == line


class TestScrubLineSegmentBoundary:
    """C4 — segment/word-boundary KEY matching: whole segment must START WITH a
    vocab word, so a substring occurring inside an unrelated segment (BYPASS
    containing "pass", OAUTH containing "auth") must NOT trigger redaction."""

    def test_bypass_healthcheck_not_redacted(self):
        """FP repro: BYPASS_HEALTHCHECK's 'BYPASS' segment must not match 'pass'."""
        line = "Environment=BYPASS_HEALTHCHECK=true"
        assert scrub_lib.scrub_line(line) == line

    def test_oauth_enabled_not_redacted(self):
        """OAUTH_ENABLED's 'OAUTH' segment must not match 'auth'."""
        line = "Environment=OAUTH_ENABLED=true"
        assert scrub_lib.scrub_line(line) == line

    def test_redis_auth_is_redacted(self):
        """FN repro: REDIS_AUTH's 'AUTH' segment must match the new 'auth' vocab word."""
        line = "Environment=REDIS_AUTH=mypassword123"
        scrubbed = scrub_lib.scrub_line(line)
        assert "mypassword123" not in scrubbed
        assert "REDIS_AUTH=<redacted>" in scrubbed

    def test_db_password_full_word_still_redacted(self):
        """Full-word PASSWORD (prefix-matches 'pass') must still redact."""
        line = "Environment=DB_PASSWORD=x"
        scrubbed = scrub_lib.scrub_line(line)
        assert "=x" not in scrubbed
        assert "<redacted>" in scrubbed


class TestScrubLineQuotedQuote:
    """Minor — quoted Environment="KEY=VALUE" redaction must not swallow the
    closing quote."""

    def test_quoted_environment_keeps_closing_quote(self):
        line = 'Environment="DB_PASSWORD=x"'
        scrubbed = scrub_lib.scrub_line(line)
        assert "x" not in scrubbed.replace("<redacted>", "")
        assert scrubbed.endswith('<redacted>"')

    def test_quoted_environment_api_token_keeps_closing_quote(self):
        line = 'Environment="API_TOKEN=abc123"'
        scrubbed = scrub_lib.scrub_line(line)
        assert "abc123" not in scrubbed
        assert scrubbed.endswith('<redacted>"')


class TestAssertNoSecrets:
    def test_detects_leaked_environment_secret(self):
        digest = "some doc text\nEnvironment=DB_PASS=hunter2\nmore text"
        warnings = scrub_lib.assert_no_secrets(digest)
        assert warnings

    def test_clean_text_has_no_warnings(self):
        digest = "This job runs nightly and exports invoices to CSV."
        assert scrub_lib.assert_no_secrets(digest) == []

    def test_bearer_placeholder_prose_not_flagged(self):
        """t6 FP repro: bare 'Bearer <token>' prose must never trip the gate."""
        digest = (
            "Calls the partner API using **Authorization**: Bearer "
            "<service-account-token> header, obtained via the internal token broker."
        )
        assert scrub_lib.assert_no_secrets(digest) == []

    def test_username_prose_not_flagged(self):
        """t6 FP repro: 'username: svc-bot' prose must never trip the gate."""
        digest = "Runs under service account username: svc-inventory-bot."
        assert scrub_lib.assert_no_secrets(digest) == []

    def test_t6_job_list_full_repro_clean(self):
        """Full t6 attack repro doc (Bearer + username prose) → zero warnings."""
        digest = (
            "# Job List\n\n"
            "## JOB001_SyncInventory\n\n"
            "**Source**: `src/jobs/sync.rb:22`\n"
            "**BL Ref**: BL001\n\n"
            "Calls the partner API using **Authorization**: Bearer "
            "<service-account-token> header,\n"
            "obtained via the internal token broker. Runs under service account "
            "username: svc-inventory-bot.\n\n"
            "Runs hourly.\n"
        )
        assert scrub_lib.assert_no_secrets(digest) == []

    def test_bypass_healthcheck_env_not_flagged(self):
        """FP repro: BYPASS_HEALTHCHECK must not trip the gate."""
        digest = "Environment=BYPASS_HEALTHCHECK=true"
        assert scrub_lib.assert_no_secrets(digest) == []

    def test_oauth_enabled_env_not_flagged(self):
        digest = "Environment=OAUTH_ENABLED=true"
        assert scrub_lib.assert_no_secrets(digest) == []

    def test_redis_auth_env_is_flagged(self):
        """FN repro: REDIS_AUTH=<real value> must be a CRITICAL gate hit."""
        digest = "Environment=REDIS_AUTH=mypassword123"
        assert scrub_lib.assert_no_secrets(digest) != []

    def test_basic_auth_env_is_flagged(self):
        digest = "Environment=BASIC_AUTH=Zm9vOmJhcg=="
        assert scrub_lib.assert_no_secrets(digest) != []

    def test_placeholder_value_not_flagged(self):
        """Templated `password=<...>` must pass — only literal values are leaks."""
        digest = "password=<...>"
        assert scrub_lib.assert_no_secrets(digest) == []

    def test_redacted_placeholder_not_flagged(self):
        digest = "token=<redacted>"
        assert scrub_lib.assert_no_secrets(digest) == []

    def test_password_eq_still_flagged(self):
        digest = "password=hunter2"
        assert scrub_lib.assert_no_secrets(digest) != []

    def test_broker_url_creds_still_flagged(self):
        digest = "amqp://user:hunter2@broker.internal:5672"
        assert scrub_lib.assert_no_secrets(digest) != []

    def test_sasl_jaas_config_still_flagged(self):
        digest = "sasl.jaas.config=org.apache.kafka.PlainLoginModule required password=hunter2;"
        assert scrub_lib.assert_no_secrets(digest) != []

    def test_api_key_literal_still_flagged(self):
        """validate_job_list.py's own regression case must keep failing."""
        digest = "api_key=sk_live_ABC123DEF456"
        assert scrub_lib.assert_no_secrets(digest) != []
