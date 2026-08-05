"""YouTube transcript enrichment via yt-dlp (auto-subs, no download, no API key).

Discovery still comes from the channel RSS feed; this only *appends* a bounded
transcript to an item's summary when yt-dlp is present. Returns "" on any
failure (never raises) so a missing/age-gated transcript silently leaves the
RSS description untouched.

Transcript text is creator/auto-generated *untrusted data* — quoted into the
summary only, never executed. yt-dlp gets a fixed argv (no shell); the URL comes
from the kit's RSS discovery, not user free-text.
"""

import glob
import os
import re
import subprocess
import tempfile

_TIMEOUT = 25


def _vtt_to_text(vtt):
    """Strip WEBVTT header, cue timestamps/indices, inline tags; dedup lines."""
    out = []
    for raw in vtt.splitlines():
        line = raw.strip()
        if not line or line == "WEBVTT" or line.startswith(("Kind:", "Language:", "NOTE")):
            continue
        if "-->" in line:  # timestamp cue line
            continue
        if re.fullmatch(r"\d+", line):  # cue index
            continue
        line = re.sub(r"<[^>]+>", "", line)  # inline timing/styling tags
        line = line.strip()
        if not line or (out and out[-1] == line):
            continue
        out.append(line)
    return " ".join(out).strip()


def transcript(video_url, max_chars=2000, lang="en"):
    """Auto-subtitle transcript for a YouTube URL as plain text (≤ max_chars).

    Writes subs to a temp dir (yt-dlp cannot stream subs to stdout reliably),
    reads the first .vtt, converts to text. "" on any failure.
    """
    if not video_url:
        return ""
    try:
        with tempfile.TemporaryDirectory() as td:
            out_tmpl = os.path.join(td, "sub")
            subprocess.run(
                ["yt-dlp", "--skip-download", "--write-auto-subs", "--write-subs",
                 "--sub-langs", f"{lang}.*,{lang}", "--sub-format", "vtt",
                 "--output", out_tmpl, "--quiet", "--no-warnings", video_url],
                capture_output=True, text=True, timeout=_TIMEOUT)
            vtts = sorted(glob.glob(os.path.join(td, "*.vtt")))
            if not vtts:
                return ""
            with open(vtts[0], encoding="utf-8", errors="ignore") as fh:
                text = _vtt_to_text(fh.read())
            return text[:max_chars]
    except Exception:
        return ""
