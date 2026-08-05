"""Render estimate JSON to self-contained HTML report.

Embeds JSON data directly in the HTML file. Opens in any browser with
no server needed. JavaScript reads embedded data and renders the report.
"""

from __future__ import annotations

import json


def render(data: dict) -> str:
    json_blob = json.dumps(data, ensure_ascii=False, indent=2)
    return _TEMPLATE.replace("/* __ESTIMATE_JSON__ */null", json_blob)


_TEMPLATE = (
    r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Project Estimate</title>
<style>
"""
    + r"""
:root{--bg:#fff;--fg:#1a1a2e;--muted:#6b7280;--border:#e5e7eb;--accent:#2563eb;--accent-light:#eff6ff;--success:#16a34a;--warn:#d97706;--danger:#dc2626;--radius:6px}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:var(--fg);background:var(--bg);line-height:1.6;max-width:1200px;margin:0 auto;padding:24px}
h1{font-size:1.75rem;margin-bottom:4px}
h2{font-size:1.35rem;margin:32px 0 12px;padding-bottom:6px;border-bottom:2px solid var(--accent);color:var(--accent)}
h3{font-size:1.1rem;margin:20px 0 8px;color:var(--fg)}
h4{font-size:1rem;margin:16px 0 6px;color:var(--muted)}
.meta{color:var(--muted);font-size:.9rem;margin-bottom:4px}
table{border-collapse:collapse;width:100%;margin:8px 0 16px;font-size:.88rem}
th,td{border:1px solid var(--border);padding:6px 10px;text-align:left}
th{background:var(--accent-light);font-weight:600;white-space:nowrap}
td.num{text-align:right;font-variant-numeric:tabular-nums}
tr:nth-child(even){background:#fafafa}
tr.total-row{font-weight:700;background:var(--accent-light)}
.badge{display:inline-block;padding:2px 8px;border-radius:var(--radius);font-size:.8rem;font-weight:600}
.badge-pass{background:#dcfce7;color:var(--success)}
.badge-warn{background:#fef3c7;color:var(--warn)}
.badge-fail{background:#fecaca;color:var(--danger)}
.section{margin-bottom:24px}
.grid-2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:768px){.grid-2{grid-template-columns:1fr}}
ol,ul{margin:4px 0 12px 20px}
li{margin-bottom:2px}
.collapsible>summary{cursor:pointer;font-weight:600;padding:4px 0;user-select:none}
.collapsible>summary:hover{color:var(--accent)}
@media print{body{max-width:100%;padding:12px}h2{break-before:auto}table{font-size:.8rem;page-break-inside:auto}tr{page-break-inside:avoid}}
"""
    + r"""
</style>
</head>
<body>
<div id="app"></div>
<script>
const DATA = /* __ESTIMATE_JSON__ */null;

const $=id=>document.getElementById(id);
const el=(tag,attrs={},children=[])=>{const e=document.createElement(tag);Object.entries(attrs).forEach(([k,v])=>{if(k==='cls')e.className=v;else if(k==='html')e.innerHTML=v;else e.setAttribute(k,v)});children.forEach(c=>{if(typeof c==='string')e.appendChild(document.createTextNode(c));else if(c)e.appendChild(c)});return e};
function r2(v){return Math.round(v*100)/100;}

function tbl(headers, rows, opts={}) {
  const t = el('table');
  const thead = el('thead', {}, [el('tr', {}, headers.map(h => el('th', {html: h})))]);
  t.appendChild(thead);
  const tbody = el('tbody');
  rows.forEach((row, i) => {
    const isTotal = opts.totalRows && opts.totalRows.includes(i);
    const tr = el('tr', isTotal ? {cls:'total-row'} : {});
    row.forEach((c, ci) => {
      const isNum = typeof c === 'number' || (typeof c === 'string' && /^[\d,.¥$€-]+$/.test(c.replace(/\*+/g,'')));
      tr.appendChild(el('td', {cls: isNum ? 'num' : '', html: String(c)}));
    });
    tbody.appendChild(tr);
  });
  t.appendChild(tbody);
  return t;
}

function getRoles() {
  const p = DATA.parameters || {};
  return { roles: p.active_roles || ['fe','be','qa_manual'], names: p.role_names || {} };
}
function rd(slug, names) { return names[slug] || slug.toUpperCase(); }
function taskMd(task, role) {
  const e = (task.effort || {})[role];
  if (e == null) return null;
  return typeof e === 'object' ? (e.md || 0) : 0;
}
function taskTotal(task) {
  if (task.total_md != null) return task.total_md;
  return Object.values(task.effort || {}).reduce((s, e) => s + (typeof e === 'object' ? (e.md||0) : 0), 0);
}
function sumRole(tasks, role) { return tasks.reduce((s, t) => { const v = taskMd(t, role); return s + (v || 0); }, 0); }
function allTasks(opt) {
  const tasks = [];
  (opt.categories || []).forEach(c => tasks.push(...(c.tasks || [])));
  tasks.push(...(opt.tasks || []));
  return tasks;
}

function renderHeader() {
  const conf = DATA.confidence || {};
  const d = el('div', {cls:'section'});
  d.appendChild(el('h1', {}, [`Project Estimate: ${DATA.project_name}`]));
  d.appendChild(el('p', {cls:'meta'}, [`Generated: ${DATA.generated_date} | Estimator: ${DATA.estimator || 'Claude AI'}`]));
  d.appendChild(el('p', {cls:'meta'}, [`Confidence: ${conf.level || 'Medium'} (±${conf.range_pct || 25}%) | Source: ${DATA.source_document || '—'}`]));
  return d;
}

function renderExecSummary() {
  const opts = DATA.options || [];
  const {roles, names} = getRoles();
  const cost = (DATA.parameters || {}).cost_per_md || 40000;
  const currency = (DATA.parameters || {}).currency || 'JPY';
  const sym = currency === 'JPY' ? '¥' : currency === 'USD' ? '$' : currency;

  const headers = ['Metric'];
  const roleRows = Object.fromEntries(roles.map(r => [r, [`<b>${rd(r,names)} MD</b>`]]));
  const mdRow = ['<b>Total MD</b>'], bufRow = ['<b>Buffer</b>'], costRow = [`<b>Cost (${currency})</b>`];

  opts.forEach(opt => {
    const tasks = allTasks(opt);
    const roleMds = Object.fromEntries(roles.map(r => [r, sumRole(tasks, r)]));
    const totalMd = Object.values(roleMds).reduce((a,b)=>a+b, 0);
    const devMd = tasks.filter(t=>t.is_dev_task).reduce((s,t)=>s+taskTotal(t), 0);
    const nonDevMd = totalMd - devMd;
    const aiPct = (opt.ai_reduction_pct || 20) / 100;
    const hasCats = !!(opt.categories && opt.categories.length);
    const optBDiscount = 0.55;
    const aiMd = hasCats ? r2(devMd * (1-aiPct)) + nonDevMd : r2(totalMd * (1 - aiPct * optBDiscount));
    const name = opt.name || opt.id;

    headers.push(name, name + ' + AI');
    roles.forEach(r => {
      const factor = hasCats ? (1-aiPct) : (1 - aiPct * optBDiscount);
      roleRows[r].push(String(roleMds[r] || 0), String(r2((roleMds[r]||0) * factor)));
    });
    mdRow.push(`<b>${totalMd}</b>`, `<b>${aiMd}</b>`);
    bufRow.push('20% (embedded)', '20%');
    costRow.push(`${sym}${(totalMd*cost).toLocaleString()}`, `${sym}${(aiMd*cost).toLocaleString()}`);
  });

  const rows = [...roles.map(r => roleRows[r]), mdRow, bufRow, costRow];
  const d = el('div', {cls:'section'});
  d.appendChild(el('h2', {}, ['Executive Summary']));
  d.appendChild(tbl(headers, rows, {totalRows: [roles.length, roles.length + 2]}));
  return d;
}

function renderParams() {
  const p = DATA.parameters || {};
  if (!p.formula && !p.project_multipliers && !p.per_task_factors) return null;
  const d = el('div', {cls:'section'});
  d.appendChild(el('h2', {}, ['Estimation Parameters']));
  if (p.formula) { d.appendChild(el('h3', {}, ['Formula'])); d.appendChild(el('pre', {}, [p.formula])); }
  if (p.project_multipliers && p.project_multipliers.length) {
    d.appendChild(el('h3', {}, ['Project-Level Multipliers']));
    d.appendChild(tbl(['Factor','Value','Rationale'], p.project_multipliers.map(m => [m.name, m.value + 'x', m.rationale || ''])));
  }
  if (p.per_task_factors && p.per_task_factors.length) {
    d.appendChild(el('h3', {}, ['Per-Task Complexity Factors']));
    d.appendChild(tbl(['Factor','Value','Scope'], p.per_task_factors.map(f => [f.name, f.value + 'x', f.scope || ''])));
  }
  return d;
}

function renderOptionA() {
  const opt = (DATA.options || []).find(o => o.categories && o.categories.length);
  if (!opt) return null;
  const {roles, names} = getRoles();
  const d = el('div', {cls:'section'});
  d.appendChild(el('h2', {}, [`${opt.name || 'Option A'}: ${opt.subtitle || ''}`]));

  const headers = ['ID','Task', ...roles.map(r => rd(r,names)), '<b>Total</b>', 'SP', 'Orig MD', 'Notes'];
  (opt.categories || []).forEach(cat => {
    const tasks = cat.tasks || [];
    const catMd = tasks.reduce((s,t) => s + taskTotal(t), 0);
    const catSp = tasks.reduce((s,t) => s + (t.story_points||0), 0);
    d.appendChild(el('h4', {}, [`${cat.name} (${catMd} MD / ${catSp} SP)`]));
    const rows = tasks.map(t => [
      t.id, t.name, ...roles.map(r => { const v = taskMd(t,r); return v == null ? '-' : v; }),
      `<b>${taskTotal(t)}</b>`, t.split_recommended ? t.story_points + ' ⚡' : t.story_points,
      t.original_md ?? '—', t.notes || ''
    ]);
    d.appendChild(tbl(headers, rows));
  });

  // Summary
  const allT = allTasks(opt);
  const aiPct = (opt.ai_reduction_pct || 20) / 100;
  const devMd = allT.filter(t=>t.is_dev_task).reduce((s,t)=>s+taskTotal(t),0);
  const totalMd = allT.reduce((s,t)=>s+taskTotal(t),0);
  const nonDevMd = totalMd - devMd;
  const aiDev = r2(devMd * (1 - aiPct));
  const aiTotal = aiDev + nonDevMd;

  d.appendChild(el('h3', {}, ['With vs Without AI']));
  d.appendChild(tbl(['Scope','Without AI (MD)','With AI (MD)','Savings'],
    [['Dev tasks', devMd, aiDev, `−${devMd - aiDev}`],
     ['Non-dev tasks', nonDevMd, nonDevMd, '0'],
     ['<b>Total</b>', `<b>${totalMd}</b>`, `<b>${aiTotal}</b>`, `<b>−${totalMd - aiTotal}</b>`]],
    {totalRows: [2]}));
  return d;
}

function renderOptionB() {
  const opt = (DATA.options || []).find(o => o.scope_reductions);
  if (!opt) return null;
  const {roles, names} = getRoles();
  const d = el('div', {cls:'section'});
  d.appendChild(el('h2', {}, [`${opt.name || 'Option B'}: ${opt.subtitle || ''}`]));

  if (opt.scope_reductions && opt.scope_reductions.length) {
    d.appendChild(el('h3', {}, ['Scope Reductions']));
    d.appendChild(tbl(['Reduction','Impact'], opt.scope_reductions.map(r => [r.item, r.impact_md + ' MD'])));
  }
  const tasks = opt.tasks || [];
  if (tasks.length) {
    const headers = ['ID','Task', ...roles.map(r=>rd(r,names)), '<b>Total B</b>', 'SP', 'A MD', 'Reason'];
    const rows = tasks.map(t => [t.id, t.name, ...roles.map(r=>{const v=taskMd(t,r);return v==null?'-':v;}),
      `<b>${taskTotal(t)}</b>`, t.story_points, t.option_a_md ?? '—', t.reduction_reason || '']);
    const totB = tasks.reduce((s,t)=>s+taskTotal(t),0);
    const totSp = tasks.reduce((s,t)=>s+(t.story_points||0),0);
    const totA = tasks.reduce((s,t)=>s+(t.option_a_md||0),0);
    rows.push(['','<b>TOTAL</b>', ...roles.map(r=>sumRole(tasks,r)), `<b>${totB}</b>`, `<b>${totSp}</b>`, `<b>${totA}</b>`, '']);
    d.appendChild(el('h3', {}, ['Detailed Task Estimates']));
    d.appendChild(tbl(headers, rows, {totalRows: [rows.length-1]}));
  }
  return d;
}

function renderFuture() {
  const phases = DATA.future_phases || [];
  if (!phases.length) return null;
  const {roles, names} = getRoles();
  const d = el('div', {cls:'section'});
  d.appendChild(el('h2', {}, ['Future Phase Reference Estimates']));
  const headers = ['ID','Task', ...roles.map(r=>rd(r,names)), '<b>Total</b>', 'SP', 'Orig MD', 'Notes'];
  phases.forEach(ph => {
    d.appendChild(el('h3', {}, [ph.name]));
    const rows = (ph.tasks||[]).map(t=>[t.id, t.name, ...roles.map(r=>{const v=taskMd(t,r);return v==null?'-':v;}),
      `<b>${taskTotal(t)}</b>`, t.story_points ?? '—', t.original_md ?? '—', t.notes || '']);
    d.appendChild(tbl(headers, rows));
  });
  return d;
}

function renderRisks() {
  if (!DATA.risks || !DATA.risks.length) return null;
  const d = el('div', {cls:'section'});
  d.appendChild(el('h2', {}, ['Risk Assessment']));
  d.appendChild(tbl(['#','Risk','Category','Prob','Impact','Score','Mitigation'],
    DATA.risks.map(r=>[r.id, r.description, r.category||'', r.probability??'', r.impact??'', r.score??'', r.mitigation||''])));
  if (DATA.tbd_items && DATA.tbd_items.length) {
    d.appendChild(el('h3', {}, ['TBD Items (⚠)']));
    d.appendChild(tbl(['Item','Status','Risk Impact','Recommendation'],
      DATA.tbd_items.map(t=>[t.item, '⚠ ' + t.status, t.risk_impact, t.recommendation])));
  }
  return d;
}

function renderComparison() {
  const comp = DATA.comparison || [], checks = DATA.validation_checks || [];
  if (!comp.length && !checks.length) return null;
  const d = el('div', {cls:'section'});
  d.appendChild(el('h2', {}, ['Comparison with Original']));
  if (comp.length) d.appendChild(tbl(['Area','My Estimate','Original','Reason'], comp.map(c=>[c.area, c.my_md+' MD', c.original_md+' MD', c.reason])));
  if (checks.length) {
    d.appendChild(el('h3', {}, ['Validation Checks']));
    const badge = s => ({pass:'badge-pass',warning:'badge-warn',fail:'badge-fail'})[s] || '';
    d.appendChild(tbl(['Check','Result','Status'], checks.map(c=>[c.check, c.result, `<span class="badge ${badge(c.status)}">${c.status.toUpperCase()}</span>`])));
  }
  return d;
}

function renderLists() {
  const d = el('div', {cls:'section'});
  let any = false;
  [['assumptions','Assumptions'],['recommendations','Recommendations'],['unresolved_questions','Unresolved Questions']].forEach(([key,title])=>{
    const items = DATA[key];
    if (!items || !items.length) return;
    any = true;
    d.appendChild(el('h2', {}, [title]));
    const ol = el('ol');
    items.forEach(item => ol.appendChild(el('li', {}, [item])));
    d.appendChild(ol);
  });
  return any ? d : null;
}

function renderQuick() {
  const opt = (DATA.options || [{}])[0] || {};
  const tasks = allTasks(opt);
  const {roles, names} = getRoles();
  const totalSp = tasks.reduce((s,t)=>s+(t.story_points||0),0);
  const totalMd = tasks.reduce((s,t)=>s+taskTotal(t),0);
  const riskLevel = DATA.risks && DATA.risks[0] ? DATA.risks[0].category : 'Medium';

  const app = $('app');
  app.appendChild(renderHeader());

  const summary = el('div', {cls:'section'});
  summary.appendChild(el('h2', {}, ['Executive Summary']));
  summary.appendChild(tbl(['Metric','Value'], [['Total Story Points', totalSp],['Total Man-Days', totalMd],['Buffer','20%'],['Risk Level', riskLevel]]));
  app.appendChild(summary);

  if (tasks.length) {
    const sec = el('div', {cls:'section'});
    sec.appendChild(el('h2', {}, ['Requirements Breakdown']));
    const headers = ['ID','Requirement', ...roles.map(r=>rd(r,names)), '<b>Total</b>', 'SP'];
    const rows = tasks.map(t=>[t.id, t.name, ...roles.map(r=>{const v=taskMd(t,r);return v==null?'-':v;}), `<b>${taskTotal(t)}</b>`, t.story_points || '']);
    sec.appendChild(tbl(headers, rows));
    app.appendChild(sec);
  }

  if (DATA.risks && DATA.risks.length) {
    const sec = el('div', {cls:'section'});
    sec.appendChild(el('h2', {}, ['Risk Assessment']));
    sec.appendChild(tbl(['Risk','Category','Impact','Mitigation'], DATA.risks.map(r=>[r.description||'', r.category||'', r.impact||'', r.mitigation||''])));
    app.appendChild(sec);
  }
  const lists = renderLists(); if (lists) app.appendChild(lists);
}

function renderBidding() {
  const app = $('app');
  [renderHeader, renderExecSummary, renderParams, renderOptionA, renderOptionB, renderFuture, renderRisks, renderComparison, renderLists]
    .forEach(fn => { const node = fn(); if (node) app.appendChild(node); });
}

document.addEventListener('DOMContentLoaded', () => {
  document.title = `Estimate: ${DATA.project_name || 'Project'}`;
  if (DATA.template_tier === 'bidding') renderBidding(); else renderQuick();
});
</script>
</body>
</html>"""
)
