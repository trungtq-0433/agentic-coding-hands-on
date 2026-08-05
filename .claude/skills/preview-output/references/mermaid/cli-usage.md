# Mermaid.js CLI Usage

The command-line path for turning Mermaid diagrams into SVG, PNG, or PDF.

## Installation

**Global install:**
```bash
npm install -g @mermaid-js/mermaid-cli
```

**Local install:**
```bash
npm install @mermaid-js/mermaid-cli
./node_modules/.bin/mmdc -h
```

**Run without installing (npx):**
```bash
npx -p @mermaid-js/mermaid-cli mmdc -h
```

**Docker:**
```bash
docker pull ghcr.io/mermaid-js/mermaid-cli/mermaid-cli
```

**Requires:** Node.js ^18.19 || >=20.0

## Basic Commands

**To SVG:**
```bash
mmdc -i input.mmd -o output.svg
```

**To PNG:**
```bash
mmdc -i input.mmd -o output.png
```

**To PDF:**
```bash
mmdc -i input.mmd -o output.pdf
```

The output format follows the extension you give the file.

## CLI Flags

**The core ones:**
- `-i, --input <file>` - Input file (`-` reads stdin)
- `-o, --output <file>` - Where to write the output
- `-t, --theme <name>` - Theme: default, dark, forest, neutral
- `-b, --background <color>` - Background: transparent, white, #hex
- `--cssFile <file>` - Your own CSS for styling
- `--configFile <file>` - A Mermaid config file
- `-h, --help` - List every option

**Everything at once:**
```bash
mmdc -i diagram.mmd -o output.png \
  -t dark \
  -b transparent \
  --cssFile custom.css \
  --configFile mermaid-config.json
```

## Advanced Usage

**Piping from stdin:**
```bash
cat diagram.mmd | mmdc --input - -o output.svg

# Or inline
cat << EOF | mmdc --input - -o output.svg
graph TD
  A[Start] --> B[End]
EOF
```

**Batch Processing:**
```bash
for file in *.mmd; do
  mmdc -i "$file" -o "${file%.mmd}.svg"
done
```

**Markdown files:**
Run it over a markdown file that has diagrams embedded in it:
```bash
mmdc -i README.template.md -o README.md
```

## Docker Workflows

**Basic Docker Usage:**
```bash
docker run --rm \
  -u $(id -u):$(id -g) \
  -v /path/to/diagrams:/data \
  ghcr.io/mermaid-js/mermaid-cli/mermaid-cli \
  -i diagram.mmd -o output.svg
```

**Mount Working Directory:**
```bash
docker run --rm -v $(pwd):/data \
  ghcr.io/mermaid-js/mermaid-cli/mermaid-cli \
  -i /data/input.mmd -o /data/output.png
```

**Podman (with SELinux):**
```bash
podman run --userns keep-id --user ${UID} \
  --rm -v /path/to/diagrams:/data:z \
  ghcr.io/mermaid-js/mermaid-cli/mermaid-cli \
  -i diagram.mmd
```

## Configuration Files

**A Mermaid config (JSON):**
```json
{
  "theme": "dark",
  "look": "handDrawn",
  "fontFamily": "Arial",
  "flowchart": {
    "curve": "basis"
  }
}
```

**Usage:**
```bash
mmdc -i input.mmd --configFile config.json -o output.svg
```

**Custom CSS:**
```css
.node rect {
  fill: #f9f;
  stroke: #333;
}
.edgeLabel {
  background-color: white;
}
```

**Usage:**
```bash
mmdc -i input.mmd --cssFile styles.css -o output.svg
```

## Node.js API

**Programmatic Usage:**
```javascript
import { run } from '@mermaid-js/mermaid-cli';

await run('input.mmd', 'output.svg', {
  theme: 'dark',
  backgroundColor: 'transparent'
});
```

**With Options:**
```javascript
import { run } from '@mermaid-js/mermaid-cli';

await run('diagram.mmd', 'output.png', {
  theme: 'forest',
  backgroundColor: '#ffffff',
  cssFile: 'custom.css',
  configFile: 'config.json'
});
```

## Common Workflows

**Generating docs:**
```bash
# render every diagram under docs/
find docs/ -name "*.mmd" -exec sh -c \
  'mmdc -i "$1" -o "${1%.mmd}.svg"' _ {} \;
```

**Styled output:**
```bash
# dark theme, transparent background
mmdc -i architecture.mmd -o arch.png \
  -t dark \
  -b transparent \
  --cssFile animations.css
```

**In a CI/CD pipeline:**
```yaml
# a GitHub Actions step
- name: Generate Diagrams
  run: |
    npm install -g @mermaid-js/mermaid-cli
    mmdc -i docs/diagram.mmd -o docs/diagram.svg
```

**Keeping accessibility metadata:**
```bash
# accTitle/accDescr carry through
mmdc -i accessible-diagram.mmd -o output.svg
```

## Troubleshooting

**Permissions under Docker:**
Pass `-u $(id -u):$(id -g)` so the container writes as your host user.

**Diagrams that are too big:**
Hand Node.js more memory:
```bash
NODE_OPTIONS="--max-old-space-size=4096" mmdc -i large.mmd -o out.svg
```

**Validation:**
Confirm the syntax parses before you render:
```bash
mmdc -i diagram.mmd -o /dev/null || echo "Invalid syntax"
```
