# Backend Security

A working reference for hardening backends: where the OWASP Top 10 hurts, how to shut each door, and the standards worth committing to in 2025.

## OWASP Top 10 (2025 RC1)

### New Entries (2025)
- **Supply Chain Failures** - dependencies you didn't write, packages someone tampered with
- **Mishandling of Exceptional Conditions** - error paths that hand the attacker a map of your system

### Top Vulnerabilities & Mitigation

#### 1. Broken Access Control
**Risk:** A user reaches data or actions that aren't theirs (28% of vulnerabilities)

**Mitigation:**
- Stand up RBAC so each role maps to a defined permission set
- Start from a closed door: deny by default, allow on purpose
- Keep a record every time an access check is refused
- Settle authorization on the backend — the client never gets a vote
- Lean on JWT, and check its claims before trusting them

```typescript
// Good: Server-side authorization check
@UseGuards(JwtAuthGuard, RolesGuard)
@Roles('admin')
async deleteUser(@Param('id') id: string) {
  // Verify user can access this resource
  return this.usersService.delete(id);
}
```

#### 2. Cryptographic Failures
**Risk:** Sensitive data leaks; the encryption protecting it was never strong enough

**Mitigation:**
- Hash passwords with Argon2id — it takes over from bcrypt as of 2025
- Wrap data in transit with TLS 1.3
- Lock sensitive data at rest behind AES-256
- Reach for crypto.randomBytes() when minting tokens — Math.random() is not a secret generator
- A password should never sit in storage as plain text

```python
# Good: Argon2id password hashing
from argon2 import PasswordHasher

ph = PasswordHasher()
hash = ph.hash("password123")  # Auto-salted, memory-hard
ph.verify(hash, "password123")  # Verify password
```

#### 3. Injection Attacks
**Risk:** SQL injection, NoSQL injection, command injection (6x increase 2020-2024)

**Mitigation (98% vulnerability reduction):**
- Bind your values: parameterized queries ALWAYS — no exceptions
- Hold input up against an allow-list before accepting it
- Escape the characters that carry special meaning
- Drive your ORM the right way; keep hand-rolled raw queries off the table

```typescript
// Bad: Vulnerable to SQL injection
const query = `SELECT * FROM users WHERE email = '${email}'`;

// Good: Parameterized query
const query = 'SELECT * FROM users WHERE email = $1';
const result = await db.query(query, [email]);
```

#### 4. Insecure Design
**Risk:** The architecture itself is the hole — controls that were never designed in

**Mitigation:**
- Walk the threat model while the design is still on the whiteboard
- Write security requirements alongside the feature ones, from day one
- Grant only the privilege a task actually needs, nothing spare
- Layer your defenses — depth, never a single wall

#### 5. Security Misconfiguration
**Risk:** Shipped defaults, chatty error messages, features left switched on that nobody uses

**Mitigation:**
- Delete the accounts that shipped by default
- Switch directory listing off
- Send the security headers — CSP, HSTS, X-Frame-Options
- Whittle the attack surface down
- Put the configuration under a recurring audit

```typescript
// Security headers middleware
app.use(helmet({
  contentSecurityPolicy: {
    directives: {
      defaultSrc: ["'self'"],
      scriptSrc: ["'self'", "'unsafe-inline'"],
    },
  },
  hsts: {
    maxAge: 31536000,
    includeSubDomains: true,
  },
}));
```

#### 6. Vulnerable Components
**Risk:** Stale dependencies carrying known, published holes

**Mitigation:**
- Refresh dependencies on a steady cadence (npm audit, pip-audit)
- Hand the chasing off to Dependabot/Renovate
- Keep an eye on the CVE databases
- Bolt software composition analysis (SCA) onto your CI/CD
- Confirm the lock file hasn't been tampered with

```bash
# Check for vulnerabilities
npm audit fix
pip-audit --fix
```

#### 7. Authentication Failures
**Risk:** Guessable passwords, hijacked sessions, credential-stuffing runs

**Mitigation:**
- MFA on every admin account, no exceptions
- Throttle the login endpoint (10 attempts/minute)
- Demand strong passwords (12+ chars, complexity)
- Expire the session (15 mins idle, 8 hours absolute)
- Go passwordless with FIDO2/WebAuthn

#### 8. Software & Data Integrity Failures
**Risk:** A poisoned CI/CD pipeline, updates that nobody signed

**Mitigation:**
- Sign your releases
- Check that packages arrive intact (lock files)
- Harden the CI/CD pipeline with immutable builds
- Match the checksum before trusting the artifact

#### 9. Logging & Monitoring Failures
**Risk:** A breach runs for weeks because nothing was watching the trail

**Mitigation:**
- Write a log line for every login, win or fail
- Record the access checks that get refused
- Funnel logs to one place (ELK Stack, Splunk)
- Raise an alert when the pattern looks wrong
- Set rotation and retention rules for the logs

#### 10. Server-Side Request Forgery (SSRF)
**Risk:** Your server gets tricked into knocking on internal doors for the attacker

**Mitigation:**
- Check and clean every URL before fetching it
- Keep an allow-list of the remote resources you'll reach
- Carve the network into segments
- Shut off protocols you don't need (file://, gopher://)

## Input Validation (Prevents 70%+ Vulnerabilities)

### Validation Strategies

**1. Check the Type**
```typescript
// Use class-validator with NestJS
class CreateUserDto {
  @IsEmail()
  email: string;

  @IsString()
  @MinLength(12)
  @Matches(/^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)/)
  password: string;

  @IsInt()
  @Min(18)
  age: number;
}
```

**2. Scrub the Input**
```typescript
import DOMPurify from 'isomorphic-dompurify';

// Sanitize HTML input
const clean = DOMPurify.sanitize(userInput);
```

**3. Allow-lists (Better than Deny-lists)**
```typescript
// Good: Allow-list approach
const allowedFields = ['name', 'email', 'age'];
const sanitized = Object.keys(input)
  .filter(key => allowedFields.includes(key))
  .reduce((obj, key) => ({ ...obj, [key]: input[key] }), {});
```

## Rate Limiting

### Token Bucket Algorithm (the common workhorse)

```typescript
import rateLimit from 'express-rate-limit';

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // 100 requests per window
  standardHeaders: true,
  legacyHeaders: false,
  message: 'Too many requests, please try again later',
});

app.use('/api/', limiter);
```

### API-Specific Limits

- **Login & auth:** 10 attempts/15 min
- **Open public APIs:** 100 requests/15 min
- **Signed-in APIs:** 1000 requests/15 min
- **Admin routes:** 50 requests/15 min

## Security Headers

```typescript
// Essential security headers (2025)
{
  'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
  'Content-Security-Policy': "default-src 'self'",
  'X-Frame-Options': 'DENY',
  'X-Content-Type-Options': 'nosniff',
  'Referrer-Policy': 'strict-origin-when-cross-origin',
  'Permissions-Policy': 'geolocation=(), microphone=()',
}
```

## Secrets Management

### Best Practices

1. **Keep secrets out of the repo** - that's what gitignored .env files are for
2. **One environment, one secret set** - never share across environments
3. **Rotate on a clock** - cycle secrets every 90 days
4. **Encryption at rest** - hold secrets encrypted inside secret managers
5. **Least privilege** - each secret carries only the permissions it needs

### Tools

- **HashiCorp Vault** - runs across clouds, mints secrets on demand
- **AWS Secrets Manager** - fully managed, rotates on its own
- **Azure Key Vault** - wired into the Azure stack
- **Pulumi ESC** - one orchestration layer for all your secrets (2025 trend)

```typescript
// Good: Secrets from environment
const dbPassword = process.env.DB_PASSWORD;
if (!dbPassword) throw new Error('DB_PASSWORD not set');
```

## API Security Checklist

- [ ] HTTPS/TLS 1.3 and nothing older
- [ ] OAuth 2.1 + JWT carrying the authentication
- [ ] Every endpoint rate-limited
- [ ] Every input validated
- [ ] Parameterized queries holding off SQL injection
- [ ] Security headers in place
- [ ] CORS scoped tight — never `*` in production
- [ ] API versioning wired up
- [ ] Errors stay quiet about the system internals
- [ ] Login events landing in the log
- [ ] MFA covering the admin accounts
- [ ] Security audit on the calendar (quarterly)

## Common Security Pitfalls

1. **Validating only in the browser** - the server is the one place validation counts
2. **Minting tokens with Math.random()** - use crypto.randomBytes()
3. **Still hashing with bcrypt** - Argon2id is the 2025 standard
4. **Taking user input at its word** - validate and sanitize everything
5. **A loose CORS policy** - never `*` in production
6. **Thin logging** - capture every authentication/authorization event
7. **No rate limiting** - put it on every public endpoint

## Resources

- **OWASP Top 10 (2025):** https://owasp.org/www-project-top-ten/
- **OWASP Cheat Sheets:** https://cheatsheetseries.owasp.org/
- **CWE Top 25:** https://cwe.mitre.org/top25/
- **NIST Guidelines:** https://www.nist.gov/cybersecurity
