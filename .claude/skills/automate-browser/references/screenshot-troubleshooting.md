# Screenshot Troubleshooting

## Missing Images in Screenshots

If images don't appear in screenshots, they may be waiting for animation triggers:

1. **Scroll-triggered animations**: Scroll element into view first
   ```bash
   node "$SKILL_DIR/evaluate.js" --script "document.querySelector('.lazy-image').scrollIntoView()"
   # Wait for animation
   node "$SKILL_DIR/evaluate.js" --script "await new Promise(r => setTimeout(r, 1000))"
   node "$SKILL_DIR/screenshot.js" --output ./result.png
   ```

2. **Sequential animation queue**: Wait longer and retry
   ```bash
   # First attempt
   node "$SKILL_DIR/screenshot.js" --url http://localhost:3000 --output ./attempt1.png

   # Wait for animations to complete
   node "$SKILL_DIR/evaluate.js" --script "await new Promise(r => setTimeout(r, 2000))"

   # Retry screenshot
   node "$SKILL_DIR/screenshot.js" --output ./attempt2.png
   ```

3. **Intersection Observer animations**: Trigger by scrolling through page
   ```bash
   node "$SKILL_DIR/evaluate.js" --script "window.scrollTo(0, document.body.scrollHeight)"
   node "$SKILL_DIR/evaluate.js" --script "await new Promise(r => setTimeout(r, 1500))"
   node "$SKILL_DIR/evaluate.js" --script "window.scrollTo(0, 0)"
   node "$SKILL_DIR/screenshot.js" --output ./full-loaded.png --full-page true
   ```
