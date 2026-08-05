#!/usr/bin/env node
/**
 * Tests for secret-redact.cjs
 * Run: node --test claude/hooks/__tests__/secret-redact.test.cjs
 */

const { describe, it } = require('node:test');
const assert = require('node:assert');

const { redactSecrets, REDACTED } = require('../lib/secret-redact.cjs');

describe('secret-redact.cjs', () => {

  describe('redactSecrets', () => {
    it('passes through plain prose untouched', () => {
      const text = 'The quick brown fox jumps over the lazy dog.';
      assert.strictEqual(redactSecrets(text), text);
    });

    it('handles empty/falsy input', () => {
      assert.strictEqual(redactSecrets(''), '');
      assert.strictEqual(redactSecrets(null), null);
      assert.strictEqual(redactSecrets(undefined), undefined);
    });

    it('redacts an AWS access key ID', () => {
      const out = redactSecrets('key id AKIAIOSFODNN7EXAMPLE please rotate');
      assert(!out.includes('AKIAIOSFODNN7EXAMPLE'));
      assert(out.includes(REDACTED));
    });

    it('redacts an AWS_SECRET_ACCESS_KEY assignment', () => {
      const out = redactSecrets('AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY');
      assert(!out.includes('wJalrXUtnFEMI'));
      assert.match(out, /AWS_SECRET_ACCESS_KEY=\[REDACTED\]/);
    });

    it('redacts an OpenAI-style sk- key', () => {
      const out = redactSecrets('use sk-abcdefghijklmnopqrstuvwxyz1234567890 as the key');
      assert(!out.includes('sk-abcdefghijklmnopqrstuvwxyz1234567890'));
    });

    it('redacts an Anthropic sk-ant- key', () => {
      const out = redactSecrets('token is sk-ant-api03-abcdefghijklmnopqrstuvwxyz1234567890');
      assert(!out.includes('sk-ant-api03-abcdefghijklmnopqrstuvwxyz1234567890'));
    });

    it('redacts a GitHub personal access token', () => {
      const out = redactSecrets('ghp_1234567890abcdefghijklmnopqrstuvwxyz for CI');
      assert(!out.includes('ghp_1234567890abcdefghijklmnopqrstuvwxyz'));
    });

    it('redacts a PEM private key block', () => {
      const pem = [
        '-----BEGIN RSA PRIVATE KEY-----',
        'MIIEowIBAAKCAQEAdummykeycontentdummykeycontent==',
        '-----END RSA PRIVATE KEY-----'
      ].join('\n');
      const out = redactSecrets(`here is my key:\n${pem}\nthanks`);
      assert(!out.includes('MIIEowIBAAKCAQEAdummykeycontentdummykeycontent=='));
      assert(out.includes(REDACTED));
    });

    it('redacts a JWT', () => {
      const jwt = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c';
      const out = redactSecrets(`auth token: ${jwt}`);
      assert(!out.includes(jwt));
    });

    it('redacts an Authorization: Bearer token', () => {
      const out = redactSecrets('Authorization: Bearer abc123.def456-ghi789');
      assert(!out.includes('abc123.def456-ghi789'));
      assert.match(out, /Bearer \[REDACTED\]/i);
    });

    it('redacts credentials embedded in a DB connection string', () => {
      const out = redactSecrets('DATABASE_URL=postgres://admin:sup3rSecret@db.internal:5432/prod');
      assert(!out.includes('sup3rSecret'));
      assert(out.includes('admin')); // username kept, only the password is redacted
    });

    it('redacts a generic .env-style secret assignment', () => {
      const out = redactSecrets('DB_PASSWORD=hunter2\nAPI_TOKEN=zzz999\nSTATUS=ok');
      assert(!out.includes('hunter2'));
      assert(!out.includes('zzz999'));
      assert(out.includes('STATUS=ok')); // non-credential key untouched
    });

    it('does not false-positive on a credential-vocab substring that is not its own segment', () => {
      const out = redactSecrets('BYPASS_HEALTHCHECK=true');
      assert.strictEqual(out, 'BYPASS_HEALTHCHECK=true');
    });

    it('leaves an already-redacted value alone on repeated application', () => {
      const once = redactSecrets('API_KEY=abcdef123456');
      const twice = redactSecrets(once);
      assert.strictEqual(once, twice);
    });
  });

});
