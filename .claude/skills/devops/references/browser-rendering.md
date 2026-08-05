# Cloudflare Browser Rendering

Driving a headless browser from Cloudflare Workers with Puppeteer/Playwright.

## Setup

**wrangler.toml:**
```toml
name = "browser-worker"
main = "src/index.ts"
compatibility_date = "2024-01-01"

browser = { binding = "MYBROWSER" }
```

## Basic Screenshot Worker

```typescript
import puppeteer from '@cloudflare/puppeteer';

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const browser = await puppeteer.launch(env.MYBROWSER);
    const page = await browser.newPage();

    await page.goto('https://example.com', { waitUntil: 'networkidle2' });
    const screenshot = await page.screenshot({ type: 'png' });

    await browser.close();

    return new Response(screenshot, {
      headers: { 'Content-Type': 'image/png' }
    });
  }
};
```

## Session Reuse (Cost Optimization)

```typescript
// Disconnect instead of close
await browser.disconnect();

// Retrieve and reconnect
const sessions = await puppeteer.sessions(env.MYBROWSER);
const freeSession = sessions.find(s => !s.connectionId);

if (freeSession) {
  const browser = await puppeteer.connect(env.MYBROWSER, freeSession.sessionId);
}
```

## PDF Generation

```typescript
const browser = await puppeteer.launch(env.MYBROWSER);
const page = await browser.newPage();

await page.setContent(`
  <!DOCTYPE html>
  <html>
    <head>
      <style>
        body { font-family: Arial; padding: 50px; }
        h1 { color: #2c3e50; }
      </style>
    </head>
    <body>
      <h1>Certificate</h1>
      <p>Awarded to: <strong>John Doe</strong></p>
    </body>
  </html>
`);

const pdf = await page.pdf({
  format: 'A4',
  printBackground: true,
  margin: { top: '1cm', right: '1cm', bottom: '1cm', left: '1cm' }
});

await browser.close();

return new Response(pdf, {
  headers: { 'Content-Type': 'application/pdf' }
});
```

## Holding a Session Open with Durable Objects

```typescript
export class Browser {
  state: DurableObjectState;
  browser: any;
  lastUsed: number;

  constructor(state: DurableObjectState, env: Env) {
    this.state = state;
    this.lastUsed = Date.now();
  }

  async fetch(request: Request, env: Env) {
    if (!this.browser) {
      this.browser = await puppeteer.launch(env.MYBROWSER);
    }

    this.lastUsed = Date.now();
    await this.state.storage.setAlarm(Date.now() + 10000);

    const page = await this.browser.newPage();
    const url = new URL(request.url).searchParams.get('url');
    await page.goto(url);
    const screenshot = await page.screenshot();
    await page.close();

    return new Response(screenshot, {
      headers: { 'Content-Type': 'image/png' }
    });
  }

  async alarm() {
    if (Date.now() - this.lastUsed > 60000) {
      await this.browser?.close();
      this.browser = null;
    } else {
      await this.state.storage.setAlarm(Date.now() + 10000);
    }
  }
}
```

## AI-Powered Web Scraper

```typescript
import { Ai } from '@cloudflare/ai';

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const browser = await puppeteer.launch(env.MYBROWSER);
    const page = await browser.newPage();
    await page.goto('https://news.ycombinator.com');
    const content = await page.content();
    await browser.close();

    const ai = new Ai(env.AI);
    const response = await ai.run('@cf/meta/llama-3-8b-instruct', {
      messages: [
        {
          role: 'system',
          content: 'Extract top 5 article titles and URLs as JSON'
        },
        { role: 'user', content: content }
      ]
    });

    return Response.json(response);
  }
};
```

## Crawler with Queues

```typescript
export default {
  async queue(batch: MessageBatch<any>, env: Env): Promise<void> {
    const browser = await puppeteer.launch(env.MYBROWSER);

    for (const message of batch.messages) {
      const page = await browser.newPage();
      await page.goto(message.body.url);

      const links = await page.evaluate(() => {
        return Array.from(document.querySelectorAll('a')).map(a => a.href);
      });

      for (const link of links) {
        await env.QUEUE.send({ url: link });
      }

      await page.close();
      message.ack();
    }

    await browser.close();
  }
};
```

## Configuration

### Timeout
```typescript
await page.goto(url, {
  timeout: 60000,  // 60 seconds max
  waitUntil: 'networkidle2'
});

await page.waitForSelector('.content', { timeout: 45000 });
```

### Viewport
```typescript
await page.setViewport({ width: 1920, height: 1080 });
```

### Screenshot Options
```typescript
const screenshot = await page.screenshot({
  type: 'png',       // 'png' | 'jpeg' | 'webp'
  quality: 90,       // JPEG/WebP only
  fullPage: true,    // Full scrollable page
  clip: {            // Crop
    x: 0, y: 0,
    width: 800,
    height: 600
  }
});
```

## Limits & Pricing

### Free Plan
- 10 minutes/day
- 3 concurrent browsers
- 3 new browsers/minute

### Paid Plan
- 10 hours/month included
- 30 concurrent browsers
- 30 new browsers/minute
- $0.09/hour overage
- $2.00/concurrent browser overage

### Cost Optimization
1. Call `disconnect()` rather than `close()`
2. Keep sessions alive with Keep-Alive (10 min max)
3. Share one browser across tabs via browser contexts
4. Stash auth state in KV
5. Wire up Durable Objects cleanup

## Best Practices

### Session Management
- Always `disconnect()` so the session can be reused
- Pool sessions instead of spinning fresh ones
- Keep track of session IDs and their state

### Performance
- Cache content in KV
- Open browser contexts instead of multiple browsers
- Pick the `waitUntil` strategy that fits the page
- Set timeouts you can actually live with

### Error Handling
- Catch timeout errors without crashing
- Confirm a session is free before connecting
- Validate responses before you cache them

### Security
- Validate URLs that come from users
- Put authentication in front of it
- Sanitize anything you scrape out
- Set the right CORS headers

## Troubleshooting

**Timeout Errors:**
```typescript
await page.goto(url, {
  timeout: 60000,
  waitUntil: 'domcontentloaded'  // Faster than networkidle2
});
```

**Memory Issues:**
```typescript
await page.close();  // Close pages
await browser.disconnect();  // Reuse session
```

**Font Rendering:**
Stick to supported fonts (Noto Sans, Roboto, etc.) or pull in your own:
```html
<link href="https://fonts.googleapis.com/css2?family=Poppins" rel="stylesheet">
```

## Key Methods

### Puppeteer
- `puppeteer.launch(binding)` - Spin up a browser
- `puppeteer.connect(binding, sessionId)` - Reconnect to one
- `puppeteer.sessions(binding)` - See what sessions exist
- `browser.newPage()` - Open a page
- `browser.disconnect()` - Detach but keep it alive
- `browser.close()` - Shut it down for good
- `page.goto(url, options)` - Go to a URL
- `page.screenshot(options)` - Grab a screenshot
- `page.pdf(options)` - Render a PDF
- `page.content()` - Pull the HTML
- `page.evaluate(fn)` - Run JS in the page

## Resources

- Docs: https://developers.cloudflare.com/browser-rendering/
- Puppeteer: https://pptr.dev/
- Examples: https://developers.cloudflare.com/workers/examples/
