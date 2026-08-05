#!/usr/bin/env bash
# export-to-pdf.sh — Export an HTML presentation to PDF via Playwright screenshots.
#
# Usage:
#   bash export-to-pdf.sh <presentation.html> [output.pdf]
#
# Requirements:
#   npm install -g playwright
#   npx playwright install chromium
#
# What it does:
#   1. Opens the HTML file in headless Chromium at 1920×1080
#   2. Screenshots each .slide element
#   3. Combines screenshots into a multi-page PDF using ImageMagick (convert)
#      or falls back to printing each image path for manual assembly

set -e

HTML_FILE="${1}"
OUTPUT_PDF="${2:-presentation.pdf}"
TEMP_DIR=".slide-export-tmp"

if [ -z "$HTML_FILE" ]; then
    echo "Usage: $0 <presentation.html> [output.pdf]"
    exit 1
fi

if [ ! -f "$HTML_FILE" ]; then
    echo "ERROR: File not found: $HTML_FILE"
    exit 1
fi

# Check playwright
if ! command -v npx &>/dev/null; then
    echo "ERROR: Node.js/npx not found. Install Node.js first."
    exit 1
fi

mkdir -p "$TEMP_DIR"

echo "[generate-slide] Exporting slides to images..."

# Playwright screenshot script — runs inline via node -e
node - "$HTML_FILE" "$TEMP_DIR" << 'EOF'
const { chromium } = require('playwright');
const path = require('path');

(async () => {
    const htmlPath = process.argv[2];
    const outDir   = process.argv[3];
    const url = `file://${path.resolve(htmlPath)}`;

    const browser = await chromium.launch();
    const page    = await browser.newPage();
    await page.setViewportSize({ width: 1920, height: 1080 });
    await page.goto(url, { waitUntil: 'networkidle' });

    const count = await page.$$eval('.slide', els => els.length);
    console.log(`Found ${count} slides`);

    for (let i = 0; i < count; i++) {
        // Scroll to slide
        await page.evaluate((idx) => {
            document.querySelectorAll('.slide')[idx].scrollIntoView({ behavior: 'instant' });
        }, i);
        await page.waitForTimeout(400); // let animations settle

        const padded = String(i + 1).padStart(3, '0');
        await page.screenshot({ path: `${outDir}/slide-${padded}.png`, fullPage: false });
        process.stdout.write(`  slide ${i + 1}/${count}\r`);
    }

    console.log('\nScreenshots done.');
    await browser.close();
})();
EOF

# Combine into PDF if ImageMagick is available
if command -v convert &>/dev/null; then
    echo "[generate-slide] Combining into PDF..."
    convert "$TEMP_DIR"/slide-*.png "$OUTPUT_PDF"
    echo "[generate-slide] Done: $OUTPUT_PDF"
else
    echo "[generate-slide] ImageMagick not found — slides saved to $TEMP_DIR/"
    echo "Install ImageMagick and run: convert $TEMP_DIR/slide-*.png $OUTPUT_PDF"
fi
