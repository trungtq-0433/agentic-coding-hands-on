# Research — Add Authentication

## Authentication Strategy

Chose Passport.js over Auth0 and NextAuth because the project is self-hosted and
requires full control over session storage. Auth0 adds vendor lock-in; NextAuth
is Next.js-specific.

## PKCE Flow

OAuth 2.0 PKCE should be used for all public clients to prevent authorization
code interception. The code verifier must be at least 43 characters.

## Session Storage

Sessions stored server-side in Redis with a 24-hour TTL. JWT tokens are
stateless but cannot be revoked without a denylist — Redis approach preferred
for security compliance.
