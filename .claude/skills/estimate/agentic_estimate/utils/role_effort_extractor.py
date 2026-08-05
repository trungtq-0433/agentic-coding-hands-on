"""Extract per-role effort from WBS Excel files with various formats.

Handles multi-level headers, merged cells, and different role naming conventions.
Outputs per-task per-role effort suitable for historical entry creation.
"""

import logging
import re
from dataclasses import dataclass, field

import pandas as pd

from agentic_estimate.utils.historical_data_loader import classify_task_type, get_task_type_aliases

logger = logging.getLogger(__name__)

ROLE_PATTERNS: dict[str, list[str]] = {
    "be": ["backend", "be ", "server-side", "server side", "code logic"],
    "fe": ["frontend", "fe ", "client-side", "client side", "ui/ux fe"],
    "qa_manual": [
        "qa",
        "test",
        "quality",
        "qc",
        "gui test",
        "responsive test",
    ],
    "design": ["design", "ui/ux", "ux ", "wireframe", "specification"],
    "infra": ["infra", "devops", "server construction", "environment"],
    "pm": ["pm ", "project manage"],
    "brse": ["brse", "bridge"],
}

EFFORT_SUBLABELS = [
    "code",
    "implement",
    "fixbug",
    "fix bug",
    "review",
    "ut",
    "unit test",
    "ui",
    "responsive",
    "logic",
    "tcs",
    "test case",
    "create",
    "execute",
    "smoke",
    "inspection",
    "gui",
    "regression",
]

SKIP_SUBLABELS = ["number of", "#", "qty", "quantity"]

SKIP_ROW_PATTERNS = re.compile(r"^\s*(total|sum|合計|subtotal|grand total|tổng)\b", re.IGNORECASE)


@dataclass
class TaskEffort:
    task_id: str
    task_name: str
    total_md: float
    effort: dict[str, float] = field(default_factory=dict)
    task_type: str = ""
    priority: str = ""


@dataclass
class ExtractionResult:
    tasks: list[TaskEffort] = field(default_factory=list)
    aggregated: dict[str, dict[str, float]] = field(default_factory=dict)
    category_totals: dict[str, float] = field(default_factory=dict)
    sheet_name: str = ""
    warnings: list[str] = field(default_factory=list)
    header_row: int = -1
    data_start: int = -1


def _detect_header_layout(
    df: pd.DataFrame, header_scan_rows: int = 15
) -> tuple[dict[str, list[int]], int, int]:
    """Detect role columns handling multi-row headers.

    Returns (role_cols, role_header_row, data_start_row).
    Multi-row headers: role label at row N, sub-column labels at row N+1.
    """
    num_cols = len(df.columns)
    scan_end = min(header_scan_rows, len(df))

    role_hits: list[tuple[int, int, str]] = []
    for row_idx in range(scan_end):
        for col_idx in range(num_cols):
            cell = str(df.iloc[row_idx, col_idx]).lower().strip()
            if not cell or cell == "nan":
                continue
            matched = _match_role(cell)
            if matched:
                role_hits.append((row_idx, col_idx, matched))

    if not role_hits:
        return {}, 0, 0

    row_roles: dict[int, set[str]] = {}
    for r, c, role in role_hits:
        row_roles.setdefault(r, set()).add(role)

    best_row = 0
    best_score = -1
    for row, roles_set in row_roles.items():
        score = len(roles_set) * 10
        positions = sorted(
            [(c, role) for r, c, role in role_hits if r == row],
            key=lambda x: x[0],
        )
        for i, (col, _role) in enumerate(positions):
            rend = positions[i + 1][0] if i + 1 < len(positions) else min(col + 15, num_cols)
            for sub_row in range(row + 1, min(row + 3, scan_end)):
                for c in range(col, rend):
                    cell = str(df.iloc[sub_row, c]).lower().strip()
                    if cell and cell != "nan" and _is_effort_sublabel(cell):
                        score += 1
        if score > best_score:
            best_score = score
            best_row = row

    row_role_list = sorted(
        [(c, role) for r, c, role in role_hits if r == best_row],
        key=lambda x: x[0],
    )

    role_cols: dict[str, list[int]] = {}
    for i, (col, role) in enumerate(row_role_list):
        range_end = (
            row_role_list[i + 1][0] if i + 1 < len(row_role_list) else min(col + 15, num_cols)
        )

        sub_cols: list[int] = []
        for sub_row in range(best_row + 1, min(best_row + 3, scan_end)):
            for c in range(col, range_end):
                cell = str(df.iloc[sub_row, c]).lower().strip()
                if not cell or cell == "nan":
                    continue
                if any(skip in cell for skip in SKIP_SUBLABELS):
                    continue
                if _is_effort_sublabel(cell):
                    sub_cols.append(c)
            if sub_cols:
                break

        if not sub_cols:
            sub_cols = [col]

        role_cols.setdefault(role, []).extend(sub_cols)

    for role in role_cols:
        role_cols[role] = sorted(set(role_cols[role]))

    all_cols = [c for cols in role_cols.values() for c in cols]
    data_start = _find_data_start_after(df, best_row, all_cols)

    verified: dict[str, list[int]] = {}
    for role, cols in role_cols.items():
        good = []
        for c in cols:
            num_count = sum(
                1
                for dr in range(data_start, min(data_start + 10, len(df)))
                if _safe_float(df.iloc[dr, c]) > 0
            )
            if num_count >= 2:
                good.append(c)
        if good:
            verified[role] = good

    final = verified if verified else role_cols
    return final, best_row, data_start


def _find_data_start_after(df: pd.DataFrame, header_row: int, effort_cols: list[int]) -> int:
    """Find first data row after the role header row."""
    if not effort_cols:
        return header_row + 2
    for row_idx in range(header_row + 1, min(header_row + 5, len(df))):
        numeric_count = sum(1 for c in effort_cols[:6] if _safe_float(df.iloc[row_idx, c]) > 0)
        if numeric_count >= 2:
            return row_idx
    return header_row + 2


_SHORT_ROLE_RE = re.compile(r"\b(FE|BE|QA|PM)\b", re.IGNORECASE)
_SHORT_ROLE_MAP = {"fe": "fe", "be": "be", "qa": "qa_manual", "pm": "pm"}


def _match_role(text: str) -> str | None:
    for role, patterns in ROLE_PATTERNS.items():
        for p in patterns:
            if p in text:
                return role
    m = _SHORT_ROLE_RE.search(text)
    if m:
        return _SHORT_ROLE_MAP.get(m.group(1).lower())
    return None


def _is_effort_sublabel(text: str) -> bool:
    return any(s in text for s in EFFORT_SUBLABELS)


def _find_task_name_col(df: pd.DataFrame, data_start: int) -> int | None:
    """Heuristic: find the column most likely containing task names.

    Collects all keyword-matched columns then picks the one with the
    richest text data (longer, more varied strings in data rows).
    """
    name_keywords = [
        "task",
        "function",
        "feature",
        "screen",
        "use case",
        "category",
        "screen・feature",
        "ユースケース",
        "タイトル",
        "機能",
        "画面",
    ]
    candidates: list[int] = []
    for row_idx in range(min(data_start, 15)):
        for col_idx in range(min(15, len(df.columns))):
            cell = str(df.iloc[row_idx, col_idx]).lower().strip()
            if any(kw in cell for kw in name_keywords):
                if col_idx not in candidates:
                    candidates.append(col_idx)

    if candidates:
        return _pick_richest_text_col(df, candidates, data_start)

    for col_idx in range(min(10, len(df.columns))):
        str_count = 0
        for row_idx in range(data_start, min(data_start + 10, len(df))):
            val = str(df.iloc[row_idx, col_idx]).strip()
            if val and val != "nan" and len(val) > 3 and not _is_numeric(val):
                str_count += 1
        if str_count >= 3:
            return col_idx
    return None


def _pick_richest_text_col(df: pd.DataFrame, candidates: list[int], data_start: int) -> int:
    """Among candidate columns, pick the one with name-like text.

    Prefers columns with short-to-moderate strings (3-50 chars) over
    description columns with very long text.
    """
    best_col = candidates[0]
    best_score = 0
    for col in candidates:
        score = 0
        for row_idx in range(data_start, min(data_start + 15, len(df))):
            val = str(df.iloc[row_idx, col]).strip()
            if val and val != "nan" and not _is_numeric(val):
                if 3 <= len(val) <= 60:
                    score += 10
                elif len(val) > 60:
                    score += 1
        if score > best_score:
            best_score = score
            best_col = col
    return best_col


def _find_task_id_col(df: pd.DataFrame, data_start: int) -> int | None:
    """Find column with short IDs like A-1, 1, 2, etc."""
    id_pattern = re.compile(r"^[A-Z]-\d+$|^[A-Z]-\w+$|^\d{1,4}$")
    for col_idx in range(min(10, len(df.columns))):
        match_count = 0
        for row_idx in range(data_start, min(data_start + 15, len(df))):
            val = str(df.iloc[row_idx, col_idx]).strip()
            if id_pattern.match(val):
                match_count += 1
        if match_count >= 3:
            return col_idx
    return None


def _find_total_col(df: pd.DataFrame, role_cols: dict, data_start: int) -> int | None:
    """Find a total column: rightmost numeric column not in role_cols."""
    all_role_col_set = {c for cols in role_cols.values() for c in cols}
    for col_idx in range(len(df.columns) - 1, -1, -1):
        if col_idx in all_role_col_set:
            continue
        numeric_count = 0
        for row_idx in range(data_start, min(data_start + 15, len(df))):
            try:
                float(df.iloc[row_idx, col_idx])
                numeric_count += 1
            except (ValueError, TypeError):
                continue
        if numeric_count >= 5:
            return col_idx
    return None


def _is_numeric(val) -> bool:
    try:
        float(val)
        return True
    except (ValueError, TypeError):
        return False


def _safe_float(val) -> float:
    try:
        v = float(val)
        return v if v == v else 0.0
    except (ValueError, TypeError):
        return 0.0


def extract_role_effort(
    excel_path: str,
    sheet_name: str | None = None,
    header_scan_rows: int = 15,
) -> ExtractionResult:
    """Extract per-task per-role effort from an Excel WBS file.

    Args:
        excel_path: Path to Excel file
        sheet_name: Specific sheet to parse (auto-detect if None)
        header_scan_rows: Number of rows to scan for headers
    """
    result = ExtractionResult()
    xls = pd.ExcelFile(excel_path)

    target_sheet = sheet_name or _pick_wbs_sheet(xls)
    if not target_sheet:
        result.warnings.append("No WBS sheet detected")
        return result

    result.sheet_name = target_sheet
    df = pd.read_excel(xls, sheet_name=target_sheet, header=None)

    role_cols, header_row, data_start = _detect_header_layout(df, header_scan_rows)
    if not role_cols:
        result.warnings.append(f"No role columns detected in '{target_sheet}'")
        return result

    result.header_row = header_row
    result.data_start = data_start
    name_col = _find_task_name_col(df, data_start)
    id_col = _find_task_id_col(df, data_start)
    total_col = _find_total_col(df, role_cols, data_start)

    result.warnings.append(
        f"Detected: sheet='{target_sheet}', roles={list(role_cols.keys())}, "
        f"header_row={header_row}, data_start=row {data_start}, "
        f"name_col={name_col}, id_col={id_col}, total_col={total_col}"
    )
    for role, cols in role_cols.items():
        result.warnings.append(f"  {role}: cols {cols}")

    aliases = get_task_type_aliases()

    for row_idx in range(data_start, len(df)):
        task_name = str(df.iloc[row_idx, name_col]).strip() if name_col is not None else ""
        task_id = str(df.iloc[row_idx, id_col]).strip() if id_col is not None else ""

        if not task_name or task_name == "nan":
            if not task_id or task_id == "nan":
                continue
            task_name = task_id

        if SKIP_ROW_PATTERNS.match(task_name):
            continue

        effort: dict[str, float] = {}
        for role, cols in role_cols.items():
            role_sum = sum(_safe_float(df.iloc[row_idx, c]) for c in cols)
            if role_sum > 0:
                effort[role] = round(role_sum, 2)

        if not effort:
            continue

        total_md = _safe_float(df.iloc[row_idx, total_col]) if total_col is not None else 0.0
        if total_md <= 0:
            total_md = round(sum(effort.values()), 2)

        task_type = classify_task_type(task_name, aliases) or "unclassified"

        result.tasks.append(
            TaskEffort(
                task_id=task_id if task_id != "nan" else "",
                task_name=task_name,
                total_md=total_md,
                effort=effort,
                task_type=task_type,
            )
        )

    _aggregate_by_category(result)
    return result


def _pick_wbs_sheet(xls: pd.ExcelFile) -> str | None:
    """Pick the sheet most likely to be a WBS with per-role effort."""
    strong = ["all team", "wbs"]
    weak = ["effort", "estimate", "breakdown", "detail"]
    for name in xls.sheet_names:
        if any(kw in name.lower() for kw in strong):
            return name
    for name in xls.sheet_names:
        if any(kw in name.lower() for kw in weak):
            return name
    for name in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=name, header=None, nrows=15)
            if len(df) < 5:
                continue
            roles, _, _ = _detect_header_layout(df, 15)
            if len(roles) >= 2:
                return name
        except Exception as e:
            logger.debug("Skipping sheet '%s': %s", name, e)
            continue
    return xls.sheet_names[0] if xls.sheet_names else None


def _aggregate_by_category(result: ExtractionResult):
    """Aggregate task effort by KB category."""
    agg: dict[str, dict[str, float]] = {}
    totals: dict[str, float] = {}

    for task in result.tasks:
        cat = task.task_type
        agg.setdefault(cat, {})
        totals[cat] = totals.get(cat, 0) + task.total_md
        for role, md in task.effort.items():
            agg[cat][role] = agg[cat].get(role, 0) + round(md, 2)

    for cat in agg:
        for role in agg[cat]:
            agg[cat][role] = round(agg[cat][role], 1)
    for cat in totals:
        totals[cat] = round(totals[cat], 1)

    result.aggregated = agg
    result.category_totals = totals
