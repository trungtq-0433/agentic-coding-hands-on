# Backend Code Quality

A working reference for SOLID, the design patterns worth knowing, clean-code habits, and how to refactor toward them (2025).

## SOLID Principles

### Single Responsibility Principle (SRP)

**Concept:** a unit of code should have exactly one reason to change.

**Smell:** one class trying to be database, mailer, reporter, and validator at once.
```typescript
class Invoice {
  persist() { /* ... */ }
  emailToCustomer() { /* ... */ }
  buildPdfReport() { /* ... */ }
  checkLineItems() { /* ... */ }
}
```

**Better:** give each concern its own home.
```typescript
class Invoice {
  constructor(public id: string, public customerId: string, public totalCents: number) {}
}

class InvoiceRepository {
  async save(invoice: Invoice) { /* ... */ }
  async findById(id: string) { /* ... */ }
}

class InvoiceMailer {
  async sendToCustomer(invoice: Invoice) { /* ... */ }
}

class InvoiceValidator {
  validate(invoiceData: unknown) { /* ... */ }
}

class InvoicePdfBuilder {
  buildReport(invoice: Invoice) { /* ... */ }
}
```

### Open/Closed Principle (OCP)

**Concept:** extend behavior without reopening code that already works.

**Smell:** every new export format means another branch in the same method.
```typescript
class ReportExporter {
  export(data: ReportData, format: string) {
    if (format === 'csv') {
      // CSV serialization logic
    } else if (format === 'json') {
      // JSON serialization logic
    }
    // Adding a new format requires touching this class
  }
}
```

**Better (Strategy Pattern):** swap implementations behind a shared interface.
```typescript
interface ExportStrategy {
  export(data: ReportData): Promise<Buffer>;
}

class CsvExporter implements ExportStrategy {
  async export(data: ReportData) {
    // CSV-specific serialization
    return Buffer.from('...');
  }
}

class JsonExporter implements ExportStrategy {
  async export(data: ReportData) {
    // JSON-specific serialization
    return Buffer.from('...');
  }
}

class ReportExporter {
  constructor(private strategy: ExportStrategy) {}

  async export(data: ReportData) {
    return this.strategy.export(data);
  }
}

// Usage
const exporter = new ReportExporter(new CsvExporter());
await exporter.export(reportData);
```

### Liskov Substitution Principle (LSP)

**Concept:** any subtype should drop in for its base type without surprises.

**Smell:** a subclass that breaks the promise of its parent.
```typescript
class Shape {
  area(): number { return 0; }
  resize(factor: number): void { /* scale both dimensions */ }
}

class Circle extends Shape {
  resize(factor: number): void {
    throw new Error('Circle resize not supported');
  }
}

// Violates LSP - Circle breaks Shape contract
```

**Better:** model the shared capability honestly so no subtype has to lie.
```typescript
interface Shape {
  area(): number;
}

class Rectangle implements Shape {
  constructor(private width: number, private height: number) {}
  area() { return this.width * this.height; }
  scale(factor: number) { /* resize both sides */ }
}

class Circle implements Shape {
  constructor(private radius: number) {}
  area() { return Math.PI * this.radius ** 2; }
  expand(delta: number) { /* grow radius */ }
}
```

### Interface Segregation Principle (ISP)

**Concept:** never force a client to depend on methods it has no use for.

**Smell:** one fat interface that forces a read-only client to implement write operations.
```typescript
interface DocumentStore {
  read(id: string): Promise<Document>;
  write(doc: Document): Promise<void>;
  delete(id: string): Promise<void>;
  archive(id: string): Promise<void>;
}

class AuditLogReader implements DocumentStore {
  read(id: string) { /* ... */ }
  write() { throw new Error('Audit log is immutable'); }
  delete() { throw new Error('Audit log is immutable'); }
  archive() { throw new Error('Audit log is immutable'); }
}
```

**Better:** split into small interfaces and compose only what fits.
```typescript
interface Readable {
  read(id: string): Promise<Document>;
}

interface Writable {
  write(doc: Document): Promise<void>;
}

interface Archivable {
  archive(id: string): Promise<void>;
}

class DocumentRepository implements Readable, Writable, Archivable {
  read(id: string) { /* ... */ }
  write(doc: Document) { /* ... */ }
  archive(id: string) { /* ... */ }
}

class AuditLogReader implements Readable {
  read(id: string) { /* ... */ }
}
```

### Dependency Inversion Principle (DIP)

**Concept:** depend on abstractions, not on concrete implementations.

**Smell:** the service hard-wires itself to a concrete notifier, so you can never swap it for tests or a different channel.
```typescript
class SlackNotifier {
  send(message: string) { /* ... */ }
}

class OrderService {
  private notifier = new SlackNotifier(); // Tight coupling

  async completeOrder(orderId: string) {
    // ... fulfillment logic ...
    this.notifier.send(`Order ${orderId} completed`);
  }
}
```

**Better (Dependency Injection):** pass the dependency in so the implementation stays swappable.
```typescript
interface Notifier {
  send(message: string): Promise<void>;
}

class SlackNotifier implements Notifier {
  async send(message: string) { /* ... */ }
}

class EmailNotifier implements Notifier {
  async send(message: string) { /* ... */ }
}

class OrderService {
  constructor(private notifier: Notifier) {} // Injected dependency

  async completeOrder(orderId: string) {
    // ... fulfillment logic ...
    await this.notifier.send(`Order ${orderId} completed`);
  }
}

// Usage
const notifier = new SlackNotifier();
const orderService = new OrderService(notifier);
```

## Design Patterns

### Repository Pattern

**Concept:** put a seam between business logic and however the data actually gets stored.

```typescript
// Domain entity
class Product {
  constructor(
    public id: string,
    public sku: string,
    public priceInCents: number,
  ) {}
}

// Repository interface
interface ProductRepository {
  findById(id: string): Promise<Product | null>;
  findBySku(sku: string): Promise<Product | null>;
  save(product: Product): Promise<void>;
  remove(id: string): Promise<void>;
}

// Implementation
class PostgresProductRepository implements ProductRepository {
  constructor(private db: Database) {}

  async findById(id: string): Promise<Product | null> {
    const row = await this.db.query('SELECT * FROM products WHERE id = $1', [id]);
    return row ? new Product(row.id, row.sku, row.price_in_cents) : null;
  }

  async save(product: Product): Promise<void> {
    await this.db.query(
      'INSERT INTO products (id, sku, price_in_cents) VALUES ($1, $2, $3)',
      [product.id, product.sku, product.priceInCents]
    );
  }

  // Other methods...
}

// Service layer uses repository
class CatalogService {
  constructor(private productRepo: ProductRepository) {}

  async getProduct(id: string) {
    return this.productRepo.findById(id);
  }
}
```

### Factory Pattern

**Concept:** hand back an object without making the caller name the concrete class.

```typescript
interface StorageDriver {
  upload(key: string, data: Buffer): Promise<string>;
}

class S3Driver implements StorageDriver {
  async upload(key: string, data: Buffer) {
    console.log(`Uploaded to S3: ${key}`);
    return `https://s3.example.com/${key}`;
  }
}

class GcsDriver implements StorageDriver {
  async upload(key: string, data: Buffer) {
    console.log(`Uploaded to GCS: ${key}`);
    return `https://storage.googleapis.com/bucket/${key}`;
  }
}

class LocalDriver implements StorageDriver {
  async upload(key: string, data: Buffer) {
    console.log(`Saved locally: ${key}`);
    return `/var/uploads/${key}`;
  }
}

class StorageFactory {
  static create(provider: 's3' | 'gcs' | 'local'): StorageDriver {
    switch (provider) {
      case 's3':
        return new S3Driver();
      case 'gcs':
        return new GcsDriver();
      case 'local':
        return new LocalDriver();
      default:
        throw new Error(`Unknown storage provider: ${provider}`);
    }
  }
}

// Usage
const storage = StorageFactory.create('s3');
await storage.upload('reports/q1.pdf', pdfBuffer);
```

### Decorator Pattern

**Concept:** stack behavior onto an object at runtime instead of subclassing.

```typescript
interface ApiClient {
  fetch(path: string): Promise<Response>;
}

class BaseApiClient implements ApiClient {
  async fetch(path: string) {
    return globalThis.fetch(`https://api.example.com${path}`);
  }
}

class AuthDecorator implements ApiClient {
  constructor(private client: ApiClient, private token: string) {}

  async fetch(path: string) {
    // Injects auth header before delegating
    const res = await globalThis.fetch(`https://api.example.com${path}`, {
      headers: { Authorization: `Bearer ${this.token}` },
    });
    return res;
  }
}

class RetryDecorator implements ApiClient {
  constructor(private client: ApiClient, private attempts = 3) {}

  async fetch(path: string): Promise<Response> {
    for (let i = 0; i < this.attempts; i++) {
      try { return await this.client.fetch(path); } catch (err) {
        if (i === this.attempts - 1) throw err;
      }
    }
    throw new Error('unreachable');
  }
}

// Stack behavior at runtime without subclassing
let client: ApiClient = new BaseApiClient();
client = new AuthDecorator(client, sessionToken);
client = new RetryDecorator(client, 3);

const response = await client.fetch('/orders');
```

### Observer Pattern (Pub/Sub)

**Concept:** let one state change fan out to many listeners without coupling them together.

```typescript
interface EventHandler {
  handle(payload: unknown): void;
}

class EventBus {
  private handlers: Map<string, EventHandler[]> = new Map();

  on(event: string, handler: EventHandler) {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, []);
    }
    this.handlers.get(event)!.push(handler);
  }

  dispatch(event: string, payload: unknown) {
    const handlers = this.handlers.get(event) ?? [];
    handlers.forEach(h => h.handle(payload));
  }
}

// Handlers
class InventoryReserver implements EventHandler {
  handle(payload: unknown) {
    console.log(`Reserving stock for order: ${JSON.stringify(payload)}`);
  }
}

class AuditLogger implements EventHandler {
  handle(payload: unknown) {
    console.log(`Audit trail: ${JSON.stringify(payload)}`);
  }
}

// Usage
const bus = new EventBus();
bus.on('order.placed', new InventoryReserver());
bus.on('order.placed', new AuditLogger());

bus.dispatch('order.placed', { orderId: 'ORD-001', items: 3 });
```

## Clean Code Practices

### Meaningful Names

**Smell:** names that hide what the code does behind single letters and bare numbers.
```typescript
function c(p: number, r: number, t: number) {
  return p * Math.pow(1 + r / 12, t * 12);
}
```

**Better:** the name and the constant tell the whole story.
```typescript
function calculateCompoundInterest(
  principalCents: number,
  annualRateDecimal: number,
  termYears: number,
) {
  const MONTHS_PER_YEAR = 12;
  const monthlyRate = annualRateDecimal / MONTHS_PER_YEAR;
  const periods = termYears * MONTHS_PER_YEAR;
  return principalCents * Math.pow(1 + monthlyRate, periods);
}
```

### Small Functions

**Smell:** one function carrying the entire workflow on its back.
```typescript
async function onboardEmployee(employeeId: string) {
  // 200 lines of code doing everything
  // - validate employee record
  // - provision accounts
  // - assign equipment
  // - enroll in payroll
  // - send welcome email
  // - schedule orientation
}
```

**Better:** each step named, each step its own function.
```typescript
async function onboardEmployee(employeeId: string) {
  const employee = await validateEmployeeRecord(employeeId);
  await provisionSystemAccounts(employee);
  await assignEquipment(employee);
  await enrollInPayroll(employee);
  await sendWelcomeEmail(employee);
  await scheduleOrientation(employee);
}
```

### Avoid Magic Numbers

**Smell:** raw numbers in the logic that nobody can decode six months later.
```typescript
if (cart.items.length > 50) {
  throw new Error('Too many items');
}

setInterval(syncInventory, 300000);
```

**Better:** name the value once and the intent becomes obvious.
```typescript
const MAX_CART_ITEMS = 50;
if (cart.items.length > MAX_CART_ITEMS) {
  throw new Error('Cart item limit reached');
}

const INVENTORY_SYNC_INTERVAL_MS = 5 * 60 * 1000; // every 5 minutes
setInterval(syncInventory, INVENTORY_SYNC_INTERVAL_MS);
```

### Error Handling

**Smell:** swallowing the error, logging nothing useful, returning null and moving on.
```typescript
try {
  const order = await db.findOrder(orderId);
  return order;
} catch (e) {
  console.log(e);
  return null;
}
```

**Better:** make the failure explicit, log with context, and wrap the cause.
```typescript
try {
  const order = await db.findOrder(orderId);
  if (!order) {
    throw new OrderNotFoundError(orderId);
  }
  return order;
} catch (error) {
  logger.error('Failed to fetch order', {
    orderId,
    error: error.message,
    stack: error.stack,
  });
  throw new DatabaseError('Order fetch failed', { cause: error });
}
```

### Don't Repeat Yourself (DRY)

**Smell:** the same price-range guard copied into every route — change one, forget the rest.
```typescript
app.post('/api/products', async (req, res) => {
  if (!req.body.priceInCents || req.body.priceInCents < 0) {
    return res.status(400).json({ error: 'Price must be non-negative' });
  }
  // ...
});

app.put('/api/products/:id', async (req, res) => {
  if (!req.body.priceInCents || req.body.priceInCents < 0) {
    return res.status(400).json({ error: 'Price must be non-negative' });
  }
  // ...
});
```

**Better:** one rule, one place, called from everywhere.
```typescript
function validatePrice(priceInCents: number) {
  if (!priceInCents || priceInCents < 0) {
    throw new ValidationError('Price must be non-negative');
  }
}

app.post('/api/products', async (req, res) => {
  validatePrice(req.body.priceInCents);
  // ...
});

app.put('/api/products/:id', async (req, res) => {
  validatePrice(req.body.priceInCents);
  // ...
});
```

## Code Refactoring Techniques

### Extract Method

**Before:** one function compressing and encrypting inline.
```typescript
function packagePayload(data: Buffer): Buffer {
  // Compress
  const compressed = zlib.gzipSync(data);
  const checksum = crypto.createHash('md5').update(compressed).digest('hex');

  // Encrypt
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv('aes-256-cbc', secretKey, iv);
  const encrypted = Buffer.concat([cipher.update(compressed), cipher.final()]);
  return Buffer.concat([iv, encrypted]);
}
```

**After:** pull each chunk into a named function that reads like its intent.
```typescript
function packagePayload(data: Buffer): Buffer {
  const compressed = compressData(data);
  return encryptData(compressed);
}

function compressData(data: Buffer): Buffer {
  return zlib.gzipSync(data);
}

function encryptData(data: Buffer): Buffer {
  const iv = crypto.randomBytes(16);
  const cipher = crypto.createCipheriv('aes-256-cbc', secretKey, iv);
  const encrypted = Buffer.concat([cipher.update(data), cipher.final()]);
  return Buffer.concat([iv, encrypted]);
}
```

### Swap the Conditional for Polymorphism

**Before:** a growing if/else chain that branches on a subscription tier.
```typescript
function getMonthlyPrice(account: Account) {
  if (account.tier === 'starter') {
    return 9;
  } else if (account.tier === 'growth') {
    return 49;
  } else if (account.tier === 'enterprise') {
    return 299;
  }
}
```

**After:** let each tier own its own answer.
```typescript
interface SubscriptionTier {
  monthlyPriceDollars(): number;
}

class StarterTier implements SubscriptionTier {
  monthlyPriceDollars() {
    return 9;
  }
}

class GrowthTier implements SubscriptionTier {
  monthlyPriceDollars() {
    return 49;
  }
}

class EnterpriseTier implements SubscriptionTier {
  monthlyPriceDollars() {
    return 299;
  }
}
```

## Code Quality Checklist

- [ ] SOLID principles honored
- [ ] Functions stay short (< 20 lines ideal)
- [ ] Variables and functions named for intent
- [ ] No bare numbers — constants instead
- [ ] Errors handled, never swallowed silently
- [ ] DRY — no duplicated logic
- [ ] Comments cover the "why", not the "what"
- [ ] Patterns reached for only where they fit
- [ ] Dependencies injected so tests can substitute them
- [ ] Reads clearly — clarity beats cleverness

## Resources

- **Clean Code (Book):** Robert C. Martin
- **Refactoring (Book):** Martin Fowler
- **Design Patterns:** https://refactoring.guru/design-patterns
- **SOLID Principles:** https://en.wikipedia.org/wiki/SOLID
