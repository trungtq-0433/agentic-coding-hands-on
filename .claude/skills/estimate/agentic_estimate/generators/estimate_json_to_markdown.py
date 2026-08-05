"""Render estimate JSON to markdown report."""

from __future__ import annotations

from agentic_estimate.generators.estimate_render_helpers import (
    all_tasks_from_option,
    get_roles,
    role_display,
    role_md_cells,
    sum_role_md,
    task_total_md,
)

# Option B AI reduction is partial (scope-reduced tasks benefit less from AI)
OPT_B_AI_DISCOUNT = 0.55


def render(data: dict) -> str:
    if data.get("template_tier") == "bidding":
        return _render_bidding(data)
    return _render_quick(data)


def _tbl(headers: list[str], rows: list[list]) -> str:
    lines = [f"| {' | '.join(str(h) for h in headers)} |"]
    lines.append(f"| {' | '.join('---' for _ in headers)} |")
    for row in rows:
        lines.append(f"| {' | '.join(str(c) for c in row)} |")
    return "\n".join(lines)


def _totals(option: dict, roles: list[str]) -> dict:
    tasks = all_tasks_from_option(option)
    role_mds = {r: sum_role_md(tasks, r) for r in roles}
    total_md, dev_md = sum(role_mds.values()), sum(
        task_total_md(t) for t in tasks if t.get("is_dev_task")
    )
    total_sp = sum(t.get("story_points", 0) for t in tasks)
    non_dev_md, ai_pct = total_md - dev_md, option.get("ai_reduction_pct", 20) / 100
    return {
        "role_mds": role_mds,
        "total_md": total_md,
        "total_sp": total_sp,
        "dev_md": dev_md,
        "non_dev_md": non_dev_md,
        "ai_md": round(dev_md * (1 - ai_pct), 2) + non_dev_md,
    }


def _option_b_totals(option: dict, roles: list[str]) -> dict:
    tasks = option.get("tasks", [])
    role_mds = {r: sum_role_md(tasks, r) for r in roles}
    return {
        "role_mds": role_mds,
        "total_md": sum(role_mds.values()),
        "total_sp": sum(t.get("story_points", 0) for t in tasks),
    }


def _header(d: dict) -> str:
    conf = d.get("confidence", {})
    return "\n".join(
        [
            f"# Project Estimate: {d['project_name']}",
            "",
            f"**Generated**: {d['generated_date']}",
            f"**Estimator**: {d.get('estimator', 'Claude AI')}",
            f"**Confidence Level**: {conf.get('level', 'Medium')} (±{conf.get('range_pct', 25)}%)",
            f"**Source Document**: {d.get('source_document', '—')}",
        ]
    )


def _exec_summary(d: dict) -> str:
    opts, cost, currency, roles, names = (
        d.get("options", []),
        d.get("parameters", {}).get("cost_per_md", 40000),
        d.get("parameters", {}).get("currency", "JPY"),
        *get_roles(d),
    )
    headers, role_rows, md_row, buf_row, cost_row = (
        ["Metric"],
        {r: [f"**{role_display(r, names)} MD**"] for r in roles},
        ["**Total MD**"],
        ["**Buffer**"],
        [f"**Cost ({currency})**"],
    )
    for opt in opts:
        name = opt.get("name", opt["id"])
        t = _totals(opt, roles) if opt.get("categories") else _option_b_totals(opt, roles)
        ai_md = (
            t["ai_md"]
            if opt.get("categories")
            else round(
                t["total_md"] * (1 - opt.get("ai_reduction_pct", 20) / 100 * OPT_B_AI_DISCOUNT), 2
            )
        )
        ai_pct = opt.get("ai_reduction_pct", 20) / 100
        headers += [f"{name}", f"{name} + AI"]
        for r in roles:
            factor = (1 - ai_pct) if opt.get("categories") else (1 - ai_pct * OPT_B_AI_DISCOUNT)
            role_rows[r] += [
                str(t["role_mds"].get(r, 0)),
                str(round(t["role_mds"].get(r, 0) * factor, 2)),
            ]
        md_row += [f"**{t['total_md']}**", f"**{ai_md}**"]
        buf_row += ["20% (embedded)", "20%"]
        cost_row += [f"¥{t['total_md'] * cost:,}", f"¥{ai_md * cost:,}"]
    return "## Executive Summary\n\n" + _tbl(
        headers, [role_rows[r] for r in roles] + [md_row, buf_row, cost_row]
    )


def _params(d: dict) -> str:
    p = d.get("parameters", {})
    if not p:
        return ""
    lines = [
        "## Estimation Parameters",
        "",
        "### Formula",
        f"```\n{p.get('formula', 'estimate_days = base × complexity × experience × (1 + buffer)')}\n```",
    ]
    if p.get("project_multipliers"):
        lines += [
            "",
            "### Project-Level Multipliers",
            "",
            _tbl(
                ["Factor", "Value", "Rationale"],
                [
                    [m["name"], f"{m['value']}x", m.get("rationale", "")]
                    for m in p["project_multipliers"]
                ],
            ),
        ]
    if p.get("per_task_factors"):
        lines += [
            "",
            "### Per-Task Complexity Factors",
            "",
            _tbl(
                ["Factor", "Value", "Scope"],
                [[f["name"], f"{f['value']}x", f.get("scope", "")] for f in p["per_task_factors"]],
            ),
        ]
    return "\n".join(lines)


def _option_a(d: dict) -> str:
    opt = next((o for o in d.get("options", []) if o.get("categories")), None)
    if not opt:
        return ""
    roles, names = get_roles(d)
    lines = [
        f"## {opt.get('name', 'Option A')}: {opt.get('subtitle', '')}",
        "",
        "### Detailed Task Estimates",
    ]
    headers = (
        ["ID", "Task"]
        + [role_display(r, names) for r in roles]
        + ["**Total**", "SP", "Orig MD", "Notes"]
    )
    for cat in opt.get("categories", []):
        tasks = cat.get("tasks", [])
        cat_md, cat_sp = sum(task_total_md(t) for t in tasks), sum(
            t.get("story_points", 0) for t in tasks
        )
        lines += ["", f"#### {cat['name']} ({cat_md} MD / {cat_sp} SP)", ""]
        rows = [
            [t["id"], t["name"]]
            + role_md_cells(t, roles)
            + [
                f"**{task_total_md(t)}**",
                f"{t['story_points']} ⚡" if t.get("split_recommended") else str(t["story_points"]),
                t.get("original_md", "—"),
                t.get("notes", ""),
            ]
            for t in tasks
        ]
        lines.append(_tbl(headers, rows))
    lines.append(_option_a_summary(opt, d))
    return "\n".join(lines)


def _option_a_summary(opt: dict, d: dict) -> str:
    roles, names = get_roles(d)
    t, ai_pct = _totals(opt, roles), opt.get("ai_reduction_pct", 20)
    headers = (
        ["Category"]
        + [role_display(r, names) for r in roles]
        + ["Total MD", "SP", "Orig MD", "Delta"]
    )
    rows = []
    for cat in opt.get("categories", []):
        tasks = cat.get("tasks", [])
        md, sp, orig = (
            sum(task_total_md(tk) for tk in tasks),
            sum(tk.get("story_points", 0) for tk in tasks),
            sum(tk.get("original_md", 0) for tk in tasks),
        )
        rows.append(
            [cat["name"]]
            + [sum_role_md(tasks, r) for r in roles]
            + [md, sp, orig or "—", md - orig if orig else "—"]
        )
    rows += [
        ["**Total (no AI)**"]
        + [t["role_mds"].get(r, 0) for r in roles]
        + [f"**{t['total_md']}**", f"**{t['total_sp']}**", "", ""],
        ["**Total (with AI)**"] + ["-"] * len(roles) + [f"**{t['ai_md']}**", "", "", ""],
    ]
    ai_dev = round(t["dev_md"] * (1 - ai_pct / 100), 2)
    return "\n".join(
        [
            "",
            "### Summary by Category",
            "",
            _tbl(headers, rows),
            "",
            "### With vs Without AI",
            "",
            _tbl(
                ["Scope", "Without AI (MD)", "With AI (MD)", "Savings (MD)"],
                [
                    ["Dev tasks", t["dev_md"], ai_dev, f"-{t['dev_md'] - ai_dev}"],
                    ["Non-dev tasks", t["non_dev_md"], t["non_dev_md"], "0"],
                    [
                        "**Total**",
                        f"**{t['total_md']}**",
                        f"**{t['ai_md']}**",
                        f"**-{t['total_md'] - t['ai_md']}**",
                    ],
                ],
            ),
        ]
    )


def _option_b(d: dict) -> str:
    opt = next((o for o in d.get("options", []) if o.get("scope_reductions")), None)
    if not opt:
        return ""
    roles, names = get_roles(d)
    lines = [f"## {opt.get('name', 'Option B')}: {opt.get('subtitle', '')}"]
    if opt.get("scope_reductions"):
        lines += [
            "",
            "### Scope Reductions",
            "",
            _tbl(
                ["Reduction", "Impact"],
                [[r["item"], f"{r['impact_md']} MD"] for r in opt["scope_reductions"]],
            ),
        ]
    tasks = opt.get("tasks", [])
    if tasks:
        headers = (
            ["ID", "Task"]
            + [role_display(r, names) for r in roles]
            + ["**Total B**", "SP", "A MD", "Reason"]
        )
        rows = [
            [t["id"], t["name"]]
            + role_md_cells(t, roles)
            + [
                f"**{task_total_md(t)}**",
                t["story_points"],
                t.get("option_a_md", "—"),
                t.get("reduction_reason", ""),
            ]
            for t in tasks
        ]
        tot_b, tot_sp, tot_a = (
            sum(task_total_md(t) for t in tasks),
            sum(t["story_points"] for t in tasks),
            sum(t.get("option_a_md", 0) for t in tasks),
        )
        rows.append(
            ["", "**TOTAL**"]
            + [sum_role_md(tasks, r) for r in roles]
            + [f"**{tot_b}**", f"**{tot_sp}**", f"**{tot_a}**", ""]
        )
        lines += ["", "### Detailed Task Estimates", "", _tbl(headers, rows)]
        if opt.get("budget_target"):
            cost, budget, ai_md = (
                d.get("parameters", {}).get("cost_per_md", 40000),
                opt["budget_target"],
                round(tot_b * (1 - opt.get("ai_reduction_pct", 20) / 100 * OPT_B_AI_DISCOUNT), 2),
            )
            lines += [
                "",
                "### Cost Analysis",
                "",
                _tbl(
                    ["Scenario", "MD", "Cost", "Within Budget?"],
                    [
                        [
                            "Without AI",
                            tot_b,
                            f"¥{tot_b * cost:,}",
                            "✅" if tot_b * cost <= budget else "❌",
                        ],
                        [
                            f"With AI ({opt.get('ai_reduction_pct', 20)}%)",
                            ai_md,
                            f"¥{ai_md * cost:,}",
                            "✅" if ai_md * cost <= budget else "❌",
                        ],
                    ],
                ),
            ]
    return "\n".join(lines)


def _future(d: dict) -> str:
    phases = d.get("future_phases", [])
    if not phases:
        return ""
    roles, names = get_roles(d)
    headers = (
        ["ID", "Task"]
        + [role_display(r, names) for r in roles]
        + ["**Total**", "SP", "Orig MD", "Notes"]
    )
    lines = ["## Future Phase Reference Estimates"]
    for ph in phases:
        rows = [
            [t["id"], t["name"]]
            + role_md_cells(t, roles)
            + [
                f"**{task_total_md(t)}**",
                t.get("story_points", "—"),
                t.get("original_md", "—"),
                t.get("notes", ""),
            ]
            for t in ph.get("tasks", [])
        ]
        lines += ["", f"### {ph['name']}", "", _tbl(headers, rows)]
    return "\n".join(lines)


def _risks(d: dict) -> str:
    if not d.get("risks"):
        return ""
    lines = [
        "## Risk Assessment",
        "",
        "### Risk Matrix",
        "",
        _tbl(
            ["#", "Risk", "Category", "Probability", "Impact", "Score", "Mitigation"],
            [
                [
                    r["id"],
                    r["description"],
                    r.get("category", ""),
                    r.get("probability", ""),
                    r.get("impact", ""),
                    r.get("score", ""),
                    r.get("mitigation", ""),
                ]
                for r in d["risks"]
            ],
        ),
    ]
    if d.get("tbd_items"):
        lines += [
            "",
            "### TBD Items (⚠)",
            "",
            _tbl(
                ["Item", "Status", "Risk Impact", "Recommendation"],
                [
                    [t["item"], f"⚠ {t['status']}", t["risk_impact"], t["recommendation"]]
                    for t in d["tbd_items"]
                ],
            ),
        ]
    return "\n".join(lines)


def _comparison(d: dict) -> str:
    comp, checks = d.get("comparison", []), d.get("validation_checks", [])
    if not comp and not checks:
        return ""
    lines = ["## Comparison with Original"]
    if comp:
        lines += [
            "",
            _tbl(
                ["Area", "My Estimate", "Original", "Reason"],
                [
                    [c["area"], f"{c['my_md']} MD", f"{c['original_md']} MD", c["reason"]]
                    for c in comp
                ],
            ),
        ]
    if checks:
        status_map = {"pass": "✅", "warning": "⚠", "fail": "❌"}
        lines += [
            "",
            "### Validation Checks",
            "",
            _tbl(
                ["Check", "Result", "Status"],
                [
                    [c["check"], c["result"], status_map.get(c["status"], c["status"])]
                    for c in checks
                ],
            ),
        ]
    return "\n".join(lines)


def _lists(d: dict) -> str:
    lines = []
    for key, title in [
        ("assumptions", "Assumptions"),
        ("recommendations", "Recommendations"),
        ("unresolved_questions", "Unresolved Questions"),
    ]:
        if d.get(key):
            lines += (
                [f"## {title}", ""] + [f"{i}. {item}" for i, item in enumerate(d[key], 1)] + [""]
            )
    return "\n".join(lines)


def _render_bidding(d: dict) -> str:
    return "\n\n---\n\n".join(
        s
        for s in [
            _header(d),
            _exec_summary(d),
            _params(d),
            _option_a(d),
            _option_b(d),
            _future(d),
            _risks(d),
            _comparison(d),
            _lists(d),
        ]
        if s.strip()
    )


def _render_quick(d: dict) -> str:
    opt = d.get("options", [{}])[0] if d.get("options") else {}
    tasks = all_tasks_from_option(opt)
    roles, names = get_roles(d)
    total_sp, total_md = sum(t.get("story_points", 0) for t in tasks), sum(
        task_total_md(t) for t in tasks
    )
    risk_level = d.get("risks", [{}])[0].get("category", "Medium") if d.get("risks") else "Medium"
    lines = [
        _header(d),
        "",
        "## Executive Summary",
        "",
        _tbl(
            ["Metric", "Value"],
            [
                ["Total Story Points", total_sp],
                ["Total Man-Days", total_md],
                ["Buffer", "20%"],
                ["Risk Level", risk_level],
            ],
        ),
    ]
    if tasks:
        hdrs = ["ID", "Requirement"] + [role_display(r, names) for r in roles] + ["**Total**", "SP"]
        rows = [
            [t["id"], t["name"]]
            + role_md_cells(t, roles)
            + [f"**{task_total_md(t)}**", t.get("story_points", "")]
            for t in tasks
        ]
        lines += ["", "## Requirements Breakdown", "", _tbl(hdrs, rows)]
    if d.get("risks"):
        lines += [
            "",
            "## Risk Assessment",
            "",
            _tbl(
                ["Risk", "Category", "Impact", "Mitigation"],
                [
                    [
                        r.get("description", ""),
                        r.get("category", ""),
                        r.get("impact", ""),
                        r.get("mitigation", ""),
                    ]
                    for r in d["risks"]
                ],
            ),
        ]
    return "\n".join(lines + ["", _lists(d)])
