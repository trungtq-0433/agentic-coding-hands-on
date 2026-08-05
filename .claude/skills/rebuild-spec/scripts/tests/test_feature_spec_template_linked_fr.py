"""Snapshot test: feature-spec-template.md BR/SM/ALG/INT blocks contain **Linked FR:** line."""
import re
from pathlib import Path

TEMPLATES_DIR = Path(__file__).resolve().parents[2] / "templates"
TEMPLATE = TEMPLATES_DIR / "technical-spec-template.md"

BLOCK_HEADING_RE = re.compile(r"^### (BR|SM|ALG|INT)-\S+", re.MULTILINE)
LINKED_FR_RE = re.compile(r"^\*\*Linked FR:\*\*", re.MULTILINE)


def _blocks_with_linked_fr(content: str) -> dict[str, bool]:
    """Return {heading: has_linked_fr} for every BR/SM/ALG/INT block."""
    lines = content.splitlines()
    total = len(lines)
    results: dict[str, bool] = {}

    headings: list[tuple[int, str]] = [
        (i, ln) for i, ln in enumerate(lines)
        if BLOCK_HEADING_RE.match(ln)
    ]

    for idx, (line_no, heading) in enumerate(headings):
        end = headings[idx + 1][0] if idx + 1 < len(headings) else total
        block_lines = lines[line_no + 1: end]
        has_it = any(LINKED_FR_RE.match(bl) for bl in block_lines)
        results[heading] = has_it

    return results


class TestFeatureSpecTemplateLinkedFr:
    def _content(self) -> str:
        return TEMPLATE.read_text(encoding="utf-8")

    def test_template_file_exists(self):
        assert TEMPLATE.is_file(), f"template not found: {TEMPLATE}"

    def test_br_block_has_linked_fr(self):
        content = self._content()
        blocks = _blocks_with_linked_fr(content)
        br_blocks = {h: v for h, v in blocks.items() if h.startswith("### BR-")}
        assert br_blocks, "No BR- blocks found in template"
        for heading, has_it in br_blocks.items():
            assert has_it, f"Missing **Linked FR:** in {heading}"

    def test_sm_block_has_linked_fr(self):
        content = self._content()
        blocks = _blocks_with_linked_fr(content)
        sm_blocks = {h: v for h, v in blocks.items() if h.startswith("### SM-")}
        assert sm_blocks, "No SM- blocks found in template"
        for heading, has_it in sm_blocks.items():
            assert has_it, f"Missing **Linked FR:** in {heading}"

    def test_alg_block_has_linked_fr(self):
        content = self._content()
        blocks = _blocks_with_linked_fr(content)
        alg_blocks = {h: v for h, v in blocks.items() if h.startswith("### ALG-")}
        assert alg_blocks, "No ALG- blocks found in template"
        for heading, has_it in alg_blocks.items():
            assert has_it, f"Missing **Linked FR:** in {heading}"

    def test_int_block_has_linked_fr(self):
        content = self._content()
        blocks = _blocks_with_linked_fr(content)
        int_blocks = {h: v for h, v in blocks.items() if h.startswith("### INT-")}
        assert int_blocks, "No INT- blocks found in template"
        for heading, has_it in int_blocks.items():
            assert has_it, f"Missing **Linked FR:** in {heading}"

    def test_all_blocks_have_linked_fr(self):
        """Aggregate check: every BR/SM/ALG/INT block must have **Linked FR:**."""
        content = self._content()
        blocks = _blocks_with_linked_fr(content)
        missing = [h for h, has_it in blocks.items() if not has_it]
        assert missing == [], f"Blocks missing **Linked FR:**: {missing}"
