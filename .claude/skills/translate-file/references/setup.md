# Setup: Dependencies for translate-file

## Required Tools

### pandoc

Required for all input formats. Installed automatically by `install.sh`:

```bash
cd .claude/skills && ./install.sh --with-sudo   # Linux/macOS
```

Manual install:
```bash
sudo apt install pandoc          # Ubuntu/Debian
brew install pandoc              # macOS
winget install JohnMacFarlane.Pandoc  # Windows
```

### Calibre (ebook-convert)

Required for:
- **DOCX and EPUB input** (no fallback)
- **Output file generation** — the skill always rebuilds the original file type (PDF→PDF, DOCX→DOCX)

**PDF input** has fallback converters when calibre is absent (pdftohtml → PyMuPDF), but output will only be `.md` and `.html` — no DOCX/PDF output.

**With sudo** (easiest):
```bash
sudo apt install calibre         # Ubuntu/Debian
brew install --cask calibre      # macOS
winget install Calibre.Calibre   # Windows
```

**Without sudo** (isolated install for Linux):
```bash
# Step 1: get the missing xcb library calibre needs
apt-get download libxcb-cursor0
dpkg-deb -x libxcb-cursor0_*.deb ~/calibre-libs/

# Step 2: install calibre to user home
curl -L https://download.calibre-ebook.com/linux-installer.sh | \
  sh /dev/stdin install_dir=~/calibre-bin isolated=y

# Step 3: verify (the skill auto-detects ~/calibre-bin/calibre/ebook-convert)
QT_QPA_PLATFORM=offscreen ~/calibre-bin/calibre/ebook-convert --version
```

The skill automatically sets `QT_QPA_PLATFORM=offscreen` and adds `~/calibre-libs` to `LD_LIBRARY_PATH` — no extra configuration needed after install.

**Calibre is required for all input formats — there is no fallback.** Output must always match the input file type (PDF→PDF, DOCX→DOCX, EPUB→EPUB).

---

## Auto-Install Steps (no sudo required)

Run these if `pandoc` or `ebook-convert` is missing. Do not ask the user — just proceed and report the result.

### Check availability

```bash
which pandoc 2>/dev/null || echo "PANDOC_MISSING"
which ebook-convert 2>/dev/null \
  || ls ~/calibre-bin/calibre/ebook-convert 2>/dev/null \
  || echo "CALIBRE_MISSING"
```

### Auto-install pandoc

```bash
mkdir -p ~/.local/bin
curl -L https://github.com/jgm/pandoc/releases/download/3.6.4/pandoc-3.6.4-linux-amd64.tar.gz \
  | tar -xz -C /tmp
cp /tmp/pandoc-3.6.4/bin/pandoc ~/.local/bin/
export PATH="$HOME/.local/bin:$PATH"
pandoc --version | head -1
```

Use the latest release tag from `https://github.com/jgm/pandoc/releases/latest` if 3.6.4 is outdated.

### Auto-install calibre (Linux)

Calibre requires `libxcb-cursor.so.0` which is a GUI library. Even though `ebook-convert` is CLI-only, it links against Qt. Install the library locally first:

```bash
# Step 1 — download the missing xcb library without sudo
cd /tmp && apt-get download libxcb-cursor0 2>&1
dpkg-deb -x /tmp/libxcb-cursor0_*.deb ~/calibre-libs/
```

If `apt-get download` fails (no apt, or different distro), skip this step — calibre may still work if the library is installed system-wide.

```bash
# Step 2 — install calibre to user home directory
export LD_LIBRARY_PATH="$HOME/calibre-libs/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
curl -L https://download.calibre-ebook.com/linux-installer.sh \
  | sh /dev/stdin install_dir=~/calibre-bin isolated=y 2>&1 | tail -5
```

```bash
# Step 3 — verify (headless mode, no display needed)
QT_QPA_PLATFORM=offscreen \
LD_LIBRARY_PATH="$HOME/calibre-libs/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH" \
~/calibre-bin/calibre/ebook-convert --version 2>&1 | head -2
```

If the version prints correctly, the skill's `find_calibre_convert()` will auto-detect it on the next run — no further configuration needed. The skill handles `QT_QPA_PLATFORM=offscreen` and `LD_LIBRARY_PATH` automatically.

### macOS / Windows

- macOS: `brew install pandoc && brew install --cask calibre`
- Windows: `winget install JohnMacFarlane.Pandoc && winget install Calibre.Calibre`

No workarounds needed on those platforms.

### If auto-install fails

Tell the user which tool failed and ask them to install it manually with sudo/admin rights, then re-run the skill.
