# Proving Identity, Granting Access

How to prove who's calling and decide what they're allowed to do — OAuth 2.1, JWT, RBAC, and MFA, held to 2025 standards.

## OAuth 2.1 (2025 Standard)

### Key Changes from OAuth 2.0

**Mandatory:**
- PKCE (Proof Key for Code Exchange) on every client
- Redirect URIs that match exactly, character for character
- A state parameter standing guard against CSRF

**Deprecated:**
- The implicit grant flow — it leaks
- Handing over the resource owner's password credentials
- Bearer tokens riding along in query strings

### Authorization Code Flow with PKCE

```typescript
// Step 1: Generate code verifier and challenge
import crypto from 'crypto';

const codeVerifier = crypto.randomBytes(32).toString('base64url');
const codeChallenge = crypto
  .createHash('sha256')
  .update(codeVerifier)
  .digest('base64url');

// Step 2: Redirect to authorization endpoint
const authUrl = new URL('https://auth.example.com/authorize');
authUrl.searchParams.set('client_id', 'your-client-id');
authUrl.searchParams.set('redirect_uri', 'https://app.example.com/callback');
authUrl.searchParams.set('response_type', 'code');
authUrl.searchParams.set('scope', 'openid profile email');
authUrl.searchParams.set('state', crypto.randomBytes(16).toString('hex'));
authUrl.searchParams.set('code_challenge', codeChallenge);
authUrl.searchParams.set('code_challenge_method', 'S256');

// Step 3: Exchange code for token (with code_verifier)
const tokenResponse = await fetch('https://auth.example.com/token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    grant_type: 'authorization_code',
    code: authCode,
    redirect_uri: redirectUri,
    client_id: clientId,
    code_verifier: codeVerifier,
  }),
});
```

## JWT (JSON Web Tokens)

### Structure

```
Header.Payload.Signature
eyJhbGciOi...  .  eyJzdWIiOi...  .  SflKxwRJ...
```

### Best Practices (2025)

1. **Keep lifetimes short** - Access tokens: 15 minutes, Refresh tokens: 7 days
2. **Sign with RS256** - asymmetric keys, not HS256, for anything public-facing
3. **Trust nothing unchecked** - verify signature, issuer, audience, expiration
4. **Carry the bare minimum** - no sensitive data in the claims
5. **Rotate refresh tokens** - hand out a fresh one on every use

### Implementation

```typescript
import jwt from 'jsonwebtoken';

// Generate JWT
const accessToken = jwt.sign(
  {
    sub: user.id,
    email: user.email,
    roles: user.roles,
  },
  process.env.JWT_PRIVATE_KEY,
  {
    algorithm: 'RS256',
    expiresIn: '15m',
    issuer: 'https://api.example.com',
    audience: 'https://app.example.com',
  }
);

// Verify JWT
const decoded = jwt.verify(token, process.env.JWT_PUBLIC_KEY, {
  algorithms: ['RS256'],
  issuer: 'https://api.example.com',
  audience: 'https://app.example.com',
});
```

## Role-Based Access Control (RBAC)

### RBAC Model

```
Users → Roles → Permissions → Resources
```

### Implementation (NestJS Example)

```typescript
// Define roles
export enum Role {
  ADMIN = 'admin',
  EDITOR = 'editor',
  VIEWER = 'viewer',
}

// Role decorator
export const Roles = (...roles: Role[]) => SetMetadata('roles', roles);

// Guard implementation
@Injectable()
export class RolesGuard implements CanActivate {
  constructor(private reflector: Reflector) {}

  canActivate(context: ExecutionContext): boolean {
    const requiredRoles = this.reflector.get<Role[]>('roles', context.getHandler());
    if (!requiredRoles) return true;

    const request = context.switchToHttp().getRequest();
    const user = request.user;

    return requiredRoles.some((role) => user.roles?.includes(role));
  }
}

// Usage
@Post()
@UseGuards(JwtAuthGuard, RolesGuard)
@Roles(Role.ADMIN, Role.EDITOR)
async createPost(@Body() createPostDto: CreatePostDto) {
  return this.postsService.create(createPostDto);
}
```

### RBAC Best Practices

1. **Deny by default** - permissions are granted on purpose, never assumed
2. **Least privilege** - the smallest set of permissions that works
3. **Role hierarchy** - Admin inherits Editor inherits Viewer
4. **Keep roles and permissions separate** - so assignment stays flexible
5. **Audit trail** - log role changes and access

## Multi-Factor Authentication (MFA)

### TOTP (Time-Based One-Time Password)

```typescript
import speakeasy from 'speakeasy';
import QRCode from 'qrcode';

// Generate secret
const secret = speakeasy.generateSecret({
  name: 'MyApp',
  issuer: 'MyCompany',
});

// Generate QR code for user
const qrCode = await QRCode.toDataURL(secret.otpauth_url);

// Verify TOTP token
const verified = speakeasy.totp.verify({
  secret: secret.base32,
  encoding: 'base32',
  token: userToken,
  window: 2, // Allow 2 time steps drift
});
```

### FIDO2/WebAuthn (Passwordless — where 2025 lands)

**Benefits:**
- Phishing slides right off it
- Nothing shared to steal
- Security rooted in hardware
- Smoother for the user (biometrics, security keys)

**Implementation:**
```typescript
// Registration
const publicKeyCredentialCreationOptions = {
  challenge: crypto.randomBytes(32),
  rp: { name: 'MyApp', id: 'example.com' },
  user: {
    id: Buffer.from(user.id),
    name: user.email,
    displayName: user.name,
  },
  pubKeyCredParams: [{ alg: -7, type: 'public-key' }], // ES256
  authenticatorSelection: {
    authenticatorAttachment: 'platform', // 'platform' or 'cross-platform'
    userVerification: 'required',
  },
  timeout: 60000,
  attestation: 'direct',
};

// Use @simplewebauthn/server library
import { verifyRegistrationResponse, verifyAuthenticationResponse } from '@simplewebauthn/server';
```

## Session Management

### Best Practices

1. **Lock down the cookie** - HttpOnly, Secure, SameSite=Strict
2. **Time sessions out** - Idle: 15 minutes, Absolute: 8 hours
3. **Reissue the session ID** - after login and on any privilege bump
4. **Hold state server-side** - Redis once you're distributed
5. **CSRF protection** - SameSite cookies + CSRF tokens

### Implementation

```typescript
import session from 'express-session';
import RedisStore from 'connect-redis';
import { createClient } from 'redis';

const redisClient = createClient();
await redisClient.connect();

app.use(
  session({
    store: new RedisStore({ client: redisClient }),
    secret: process.env.SESSION_SECRET,
    resave: false,
    saveUninitialized: false,
    cookie: {
      secure: true, // HTTPS only
      httpOnly: true, // No JavaScript access
      sameSite: 'strict', // CSRF protection
      maxAge: 1000 * 60 * 15, // 15 minutes
    },
  })
);
```

## Password Security

### Argon2id (the 2025 pick — bcrypt steps aside)

**Why Argon2id:**
- Took first place in the Password Hashing Competition (2015)
- Memory-hard, so GPU and ASIC farms gain little
- CPU and memory cost both tunable
- Blends Argon2i (data-independent) with Argon2d (data-dependent)

```typescript
import argon2 from 'argon2';

// Hash password
const hash = await argon2.hash('password123', {
  type: argon2.argon2id,
  memoryCost: 65536, // 64 MB
  timeCost: 3, // 3 iterations
  parallelism: 4, // 4 threads
});

// Verify password
const valid = await argon2.verify(hash, 'password123');
```

### Password Policy (what NIST advises in 2025)

- **Floor at 12 characters** - 8 no longer cuts it
- **Drop the composition rules** - leave room for passphrases
- **Cross-check against breach dumps** - HaveIBeenPwned API
- **No scheduled rotation** - only force a reset once it's compromised
- **Accept every printable character** - spaces and emojis welcome

## API Key Authentication

### Best Practices

1. **Prefix the key** - `sk_live_`, `pk_test_` make type and environment obvious at a glance
2. **Store only the hash** - keep the SHA-256 digest, never the plaintext
3. **Let users rotate** - rotation should be self-service
4. **Scope it down** - separate keys for read and write
5. **Rate limit per key** - limits attach to the key, not just the user

```typescript
// Generate API key
const apiKey = `sk_${env}_${crypto.randomBytes(24).toString('base64url')}`;

// Store hashed version
const hashedKey = crypto.createHash('sha256').update(apiKey).digest('hex');
await db.apiKeys.create({ userId, hashedKey, scopes: ['read'] });

// Validate API key
const providedHash = crypto.createHash('sha256').update(providedKey).digest('hex');
const keyRecord = await db.apiKeys.findOne({ hashedKey: providedHash });
```

## Authentication Decision Matrix

| Use Case | Recommended Approach |
|----------|---------------------|
| Server-rendered web app | OAuth 2.1 + JWT |
| Native mobile client | OAuth 2.1 + PKCE |
| Browser SPA (single-page app) | OAuth 2.1 Authorization Code + PKCE |
| Machine-to-machine | Client credentials grant + mTLS |
| Outside API consumers | API keys with scopes |
| Locked-down / sensitive | WebAuthn/FIDO2 + MFA |
| Back-office admin | JWT + RBAC + MFA |
| Service-to-service mesh | Service mesh (mTLS) + JWT |

## Security Checklist

- [ ] OAuth 2.1 wired up with PKCE
- [ ] JWT access tokens timing out at 15 minutes
- [ ] Refresh tokens rotating on use
- [ ] RBAC denying by default
- [ ] MFA mandatory on admin accounts
- [ ] Passwords run through Argon2id
- [ ] Session cookies flagged HttpOnly, Secure, SameSite
- [ ] Auth endpoints throttled (10 attempts/15 min)
- [ ] Accounts locking out after repeated failures
- [ ] Password rules: 12+ chars, checked against breaches
- [ ] Login events captured in the audit log

## Resources

- **OAuth 2.1:** https://oauth.net/2.1/
- **JWT Best Practices:** https://datatracker.ietf.org/doc/html/rfc8725
- **WebAuthn:** https://webauthn.guide/
- **NIST Password Guidelines:** https://pages.nist.gov/800-63-3/
- **OWASP Auth Cheat Sheet:** https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html
