# Backend Testing Strategies

A working reference for how to test backend systems — frameworks, layering, and the quality gates worth enforcing (2025).

## Test Pyramid (70-20-10 Rule)

```
        /\
       /E2E\     10% - End-to-End Tests
      /------\
     /Integr.\ 20% - Integration Tests
    /----------\
   /   Unit     \ 70% - Unit Tests
  /--------------\
```

**Why it leans this way:**
- Unit tests: pennies to run, and they point straight at the broken function
- Integration tests: confirm the parts really do speak to one another
- E2E tests: the slow, expensive ones — but they prove the full user journey survives

## Unit Testing

### Frameworks by Language

**TypeScript/JavaScript:**
- **Vitest** - runs 50% faster than Jest in CI/CD, speaks ESM out of the box
- **Jest** - seasoned, with a deep ecosystem and snapshot testing

**Python:**
- **Pytest** - what the field defaults to, with fixtures and parametrization
- **Unittest** - bundled into the standard library

**Go:**
- **testing** - ships with Go, made for table-driven tests
- **testify** - assertions and mocking

### Best Practices

```typescript
// Good: Test single responsibility
describe('ProductService', () => {
  describe('createProduct', () => {
    it('should create product with valid data', async () => {
      const productData = { sku: 'WIDGET-001', priceInCents: 1999 };
      const product = await productService.createProduct(productData);

      expect(product).toMatchObject(productData);
      expect(product.id).toBeDefined();
    });

    it('should throw error with duplicate SKU', async () => {
      const productData = { sku: 'EXISTING-SKU', priceInCents: 500 };

      await expect(productService.createProduct(productData))
        .rejects.toThrow('SKU already exists');
    });

    it('should reject negative price', async () => {
      const productData = { sku: 'WIDGET-002', priceInCents: -1 };

      await expect(productService.createProduct(productData))
        .rejects.toThrow('Price must be non-negative');
    });
  });
});
```

### Mocking

```typescript
// Mock external dependencies
jest.mock('./inventoryService');

it('should reserve stock after order is placed', async () => {
  const inventoryService = require('./inventoryService');
  inventoryService.reserveStock = jest.fn();

  await orderService.placeOrder({ productId: 'WIDGET-001', quantity: 2 });

  expect(inventoryService.reserveStock).toHaveBeenCalledWith('WIDGET-001', 2);
});
```

## Integration Testing

### API Integration Tests

```typescript
import request from 'supertest';
import { app } from '../app';

describe('POST /api/products', () => {
  beforeAll(async () => {
    await db.connect(); // Real database connection (test DB)
  });

  afterAll(async () => {
    await db.disconnect();
  });

  beforeEach(async () => {
    await db.products.deleteMany({}); // Clean state
  });

  it('should create product and return 201', async () => {
    const response = await request(app)
      .post('/api/products')
      .send({ sku: 'GADGET-X1', priceInCents: 4999 })
      .expect(201);

    expect(response.body).toMatchObject({
      sku: 'GADGET-X1',
      priceInCents: 4999,
    });

    // Verify database persistence
    const saved = await db.products.findOne({ sku: 'GADGET-X1' });
    expect(saved).toBeDefined();
  });

  it('should return 400 for negative price', async () => {
    await request(app)
      .post('/api/products')
      .send({ sku: 'BAD-PRICE', priceInCents: -50 })
      .expect(400)
      .expect((res) => {
        expect(res.body.error).toBe('Price must be non-negative');
      });
  });
});
```

### Testing Against a Real Database via TestContainers

```typescript
import { GenericContainer } from 'testcontainers';

let container;
let db;

beforeAll(async () => {
  // Spin up real PostgreSQL in Docker
  container = await new GenericContainer('postgres:15')
    .withEnvironment({ POSTGRES_PASSWORD: 'test' })
    .withExposedPorts(5432)
    .start();

  const port = container.getMappedPort(5432);
  db = await createConnection({
    host: 'localhost',
    port,
    database: 'test',
    password: 'test',
  });
}, 60000);

afterAll(async () => {
  await container.stop();
});
```

## Contract Testing (Microservices)

### Pact (Consumer-Driven Contracts)

```typescript
// Consumer test
import { Pact } from '@pact-foundation/pact';

const provider = new Pact({
  consumer: 'OrderService',
  provider: 'InventoryService',
});

describe('Inventory Service Contract', () => {
  beforeAll(() => provider.setup());
  afterEach(() => provider.verify());
  afterAll(() => provider.finalize());

  it('should check stock availability', async () => {
    await provider.addInteraction({
      state: 'product WIDGET-001 has stock',
      uponReceiving: 'a request to check stock',
      withRequest: {
        method: 'GET',
        path: '/inventory/WIDGET-001',
        headers: { 'Accept': 'application/json' },
      },
      willRespondWith: {
        status: 200,
        body: { sku: 'WIDGET-001', available: 42 },
      },
    });

    const response = await inventoryClient.checkStock('WIDGET-001');
    expect(response.available).toBeGreaterThan(0);
  });
});
```

## Load Testing

### Tools Comparison

**k6** (Current, Easy on Developers)
```javascript
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 }, // Ramp up to 100 users
    { duration: '5m', target: 100 }, // Stay at 100 users
    { duration: '2m', target: 0 },   // Ramp down to 0 users
  ],
  thresholds: {
    http_req_duration: ['p(95)<500'], // 95% requests under 500ms
  },
};

export default function () {
  const res = http.get('https://api.example.com/users');
  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });
  sleep(1);
}
```

**Gatling** (JVM-based, for elaborate scenarios)
**JMeter** (GUI-driven, the old guard)

### Performance Thresholds

- **Response time:** p95 < 500ms, p99 < 1s
- **Throughput:** 1000+ req/sec (set the target off your SLA)
- **Error rate:** < 1%
- **Concurrent users:** push it to 2x the peak you expect

## E2E Testing

### Playwright (Current, Runs Across Browsers)

```typescript
import { test, expect } from '@playwright/test';

test('customer can add item to cart and checkout', async ({ page }) => {
  // Navigate to product page
  await page.goto('https://shop.example.com/products/WIDGET-001');

  // Add item to cart
  await page.click('button[data-action="add-to-cart"]');

  // Proceed to checkout
  await page.click('a[href="/cart"]');
  await page.click('button[data-action="checkout"]');

  // Verify redirect to confirmation page
  await expect(page).toHaveURL('/orders/confirmation');
  await expect(page.locator('h1')).toContainText('Order placed');

  // Verify order was persisted
  const response = await page.waitForResponse('/api/orders');
  expect(response.status()).toBe(201);
});
```

## Database Migration Testing

**Never wave this through:** 83% migrations fail without proper testing

```typescript
describe('Database Migrations', () => {
  it('should migrate products from v1 to v2 without data loss', async () => {
    // Insert test data in v1 schema
    await db.query(`
      INSERT INTO products (id, sku, price_in_cents)
      VALUES (1, 'GADGET-X1', 4999)
    `);

    // Run migration
    await runMigration('v2-add-stock-count.sql');

    // Verify v2 schema — existing rows get the default stock count
    const result = await db.query('SELECT * FROM products WHERE id = 1');
    expect(result.rows[0]).toMatchObject({
      id: 1,
      sku: 'GADGET-X1',
      price_in_cents: 4999,
      stock_count: expect.any(Number),
    });
  });

  it('should rollback migration successfully', async () => {
    await runMigration('v2-add-stock-count.sql');
    await rollbackMigration('v2-add-stock-count.sql');

    // Verify v1 schema restored — new column gone
    const columns = await db.query(`
      SELECT column_name FROM information_schema.columns
      WHERE table_name = 'products'
    `);
    expect(columns.rows.map(r => r.column_name)).not.toContain('stock_count');
  });
});
```

## Security Testing

### SAST (Reading the Source for Holes Before It Runs)

```bash
# SonarQube for code quality + security
sonar-scanner \
  -Dsonar.projectKey=my-backend \
  -Dsonar.sources=src \
  -Dsonar.host.url=http://localhost:9000

# Semgrep for security patterns
semgrep --config auto src/
```

### DAST (Probing the App While It's Live)

```bash
# OWASP ZAP for runtime security scanning
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t https://api.example.com \
  -r zap-report.html
```

### Dependency Scanning (Checking What You Pulled In — SCA)

```bash
# npm audit for Node.js
npm audit fix

# Snyk for multi-language
snyk test
snyk monitor  # Continuous monitoring
```

## Code Coverage

### Numbers to Hit (SonarQube Standards)

- **Overall coverage:** 80%+
- **Critical paths:** 100% (authentication, payment, data integrity)
- **New code:** 90%+

### Implementation

```bash
# Vitest with coverage
vitest run --coverage

# Jest with coverage
jest --coverage --coverageThreshold='{"global":{"branches":80,"functions":80,"lines":80}}'
```

## CI/CD Testing Pipeline

```yaml
# GitHub Actions example
name: Test Pipeline

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Unit Tests
        run: npm run test:unit

      - name: Integration Tests
        run: npm run test:integration

      - name: E2E Tests
        run: npm run test:e2e

      - name: Load Tests
        run: k6 run load-test.js

      - name: Security Scan
        run: npm audit && snyk test

      - name: Coverage Report
        run: npm run test:coverage

      - name: Upload to Codecov
        uses: codecov/codecov-action@v3
```

## Testing Best Practices

1. **Arrange-Act-Assert (AAA) Pattern** — set up, do the thing, then check
2. **Lean toward one assertion per test** (where it's practical)
3. **Let the name describe the behavior** - `should throw error when email is invalid`
4. **Lean on the edges** - empty inputs, boundary values, null/undefined
5. **Begin from a clean, known state** - wipe the database between runs
6. **Keep the clock short** - Unit tests < 10ms, Integration < 100ms
7. **Strip out the randomness** - chase down flaky tests; drop sleep() and wait on waitFor()
8. **Independent of order** - no test may lean on another having gone first

## Testing Checklist

- [ ] Unit tests reach 70% of the codebase
- [ ] Every API endpoint has integration coverage
- [ ] Contracts pinned down between microservices
- [ ] Load tests wired up (k6/Gatling)
- [ ] E2E coverage on the flows that matter most
- [ ] Migrations exercised by their own tests
- [ ] Security scans baked into CI/CD (SAST, DAST, SCA)
- [ ] Coverage reports generated without anyone asking
- [ ] Every PR triggers the suite
- [ ] No flaky tests left standing

## Resources

- **Vitest:** https://vitest.dev/
- **Playwright:** https://playwright.dev/
- **k6:** https://k6.io/docs/
- **Pact:** https://docs.pact.io/
- **TestContainers:** https://testcontainers.com/
