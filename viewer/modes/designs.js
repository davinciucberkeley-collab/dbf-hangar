// Designs mode: 3D view plus scorecard (tiers, FAIL rows first).
import { TIERS } from '../lib.js';
import { renderTree } from '../ui/tree.js';
import { renderInspector, setInspectorScorecard } from '../ui/inspector.js';
import { rowParts, partStatus } from '../vp/status.js';
import { renderTimeline } from '../ui/timeline.js';
import { renderBom } from '../ui/bom.js';
import { alignTexts, groupRows } from '../ui/scorecard_rows.js';

const view = { mode: 'problem' }; // the group switch survives a design change

export default async function render(ctx) {
  const { state, el, byId, vp } = ctx;
  const d = byId(state.selected);
  ctx.setHighlight([]);
  await vp.main.show(d);
  const usable = d && !d.pending && !d.error;
  const parts = usable && d.parts ? await ctx.getJSON(d.parts).catch(() => null) : null;
  const mass = usable && d.mass ? await ctx.getJSON(d.mass).catch(() => null) : null;
  renderTree(ctx, d, parts); renderInspector(ctx, d, parts, mass);
  await renderScorecard(ctx, d, parts);
  renderBom(ctx, d, parts, mass);
  await renderTimeline(ctx, d);
  el.dataset.ready = '1';
}

async function renderScorecard({ state, el, h, fmt, getJSON, vp }, d, parts) {
  const box = el.querySelector('#scorecard'); box.replaceChildren();
  vp.main.setStatus(new Map());
  if (!d) { box.append(h('p', { class: 'muted' }, 'Select a design from the list.')); return; }
  box.append(h('h2', {}, d.name || d.id), h('div', { class: 'sub id' }, `${d.id} · ${d.status}`));
  window.planeViewer?.onScorecard?.(box, d);
  if (d.pending) { box.append(h('p', { class: 'muted' }, 'Running the checks on this design. This can take up to a minute for a detailed model.')); return; }
  if (d.error) { box.append(h('div', { class: 'errbox' }, d.error)); return; }
  box.append(h('div', { class: 'summary' },
    h('span', { class: 'badge ' + (d.accepted ? 'accepted' : 'rejected') }, d.accepted ? 'accepted' : 'rejected'),
    h('span', { class: 'pills' }, TIERS.map((t) => h('span', { class: 'pill ' + (d.tiers?.[t] ?? 'NONE') }, 'T' + t)))),
    h('div', { class: 'kv' }, h('span', {}, h('b', {}, 'mass '), `${fmt(d.mass_g, 0)} g`),
      h('span', {}, h('b', {}, 'cg '), (d.cg_mm || []).map((v) => fmt(v, 0)).join(', ') + ' mm')));
  let sc;
  try { sc = await getJSON(d.scorecard); } catch (e) { box.append(h('div', { class: 'errbox' }, 'Scorecard unavailable: ' + e.message)); return; }
  if (state.selected !== d.id) return; // user moved on
  let rowsJson = null;
  if (d.rows) try { rowsJson = await getJSON(d.rows); } catch { rowsJson = null; }
  if (state.selected !== d.id) return;
  const texts = alignTexts(sc, rowsJson);
  sc.tiers.forEach((t, i) => t.results.forEach((r, j) => { r.text = texts[i][j]; }));
  vp.main.setStatus(partStatus(sc, parts)); setInspectorScorecard(sc);
  const hasRows = !!rowsJson;
  const area = h('div', { class: 'rows-area' });
  const badge = (s) => h('span', { class: 'badge ' + s }, s);
  const row = (e) => {
    const r = e.row, text = e.text;
    const ids = rowParts(r, parts), has = ids.length > 0;
    const go = () => { const v = vp.main; if (v.focusKey === ids.join('|')) v.clearFocus(); else v.focusParts(ids); };
    const attrs = { class: `result ${r.status}` + (has ? ' has-parts' : ''), 'data-testid': 'check-row', 'data-check-id': r.check_id, 'data-parts': has ? ids.join('|') : null,
      tabindex: has ? 0 : null, role: has ? 'button' : null, title: r.check_id,
      onclick: has ? go : null, onkeydown: has ? (ev) => { if (ev.key === 'Enter') go(); } : null };
    if (text.fallback) {
      return h('div', attrs,
        h('div', { class: 'top' }, badge(r.status), h('span', { class: 'cid' }, r.check_id),
          has ? h('span', { class: 'partshint' }, 'show ' + ids.slice(0, 3).join(' + ') + (ids.length > 3 ? ` + ${ids.length - 3} more` : '')) : null),
        h('div', { class: 'msg' }, r.message), r.criterion ? h('div', { class: 'crit' }, r.criterion) : null);
    }
    const chips = text.parts.map((p) => h('span', { class: 'chip', onclick: has ? (ev) => { ev.stopPropagation(); go(); } : null }, p.label));
    return h('div', attrs,
      h('div', { class: 'top' }, badge(r.status), h('span', { class: 'title' }, text.title), chips,
        text.report_only ? h('span', { class: 'rtag' }, 'report-only until 2026-12-08' + (text.would_be ? ` (would be ${text.would_be})` : '')) : null),
      h('div', { class: 'sentence' }, text.sentence), text.hint ? h('div', { class: 'hint' }, 'Fix: ' + text.hint) : null,
      h('span', { class: 'cid' }, r.check_id),
      h('details', { class: 'raw', onclick: (ev) => ev.stopPropagation(), onkeydown: (ev) => ev.stopPropagation() }, h('summary', {}, 'details'),
        text.details ? h('div', {}, text.details) : null, text.source ? h('div', {}, 'Limit source: ' + text.source) : null));
  };
  const entry = (e) => {
    if (!e.fold) return row(e);
    const first = e.rows[0];
    return h('details', { class: 'fold', 'data-testid': 'check-fold' },
      h('summary', {}, badge(e.status), ' ', h('span', { class: 'title' }, e.title)),
      h('div', { class: 'sentence' }, first.text.sentence), first.text.hint ? h('div', { class: 'hint' }, 'Fix: ' + first.text.hint) : null,
      h('div', { class: 'results' }, e.rows.map(row)));
  };
  const renderRows = () => {
    area.replaceChildren();
    const mode = hasRows ? view.mode : 'tier';
    for (const g of groupRows(sc, texts, mode, parts)) {
      if (mode === 'tier') {
        const nfail = g.entries.filter((e) => e.row.status === 'FAIL').length;
        const det = h('details', { class: 'tier' },
          h('summary', {}, h('span', { class: 'pill ' + g.status }, g.key), h('span', { class: 'tname', 'data-testid': 'group-title' }, g.title.replace(/^T\d+ /, '')),
            nfail ? h('span', { class: 'muted small' }, `${nfail} failing`) : h('span', { class: 'muted small' }, `${g.entries.length} checks`),
            badge(g.status)),
          h('div', { class: 'results' }, g.entries.map(entry)));
        if (g.status === 'FAIL' || g.status === 'WARN' || g.entries.some((e) => e.row.status === 'FAIL' || e.row.status === 'WARN')) det.open = true;
        area.append(det);
        continue;
      }
      const open = mode === 'part' || g.key === 'fail' || g.key === 'warn' || (g.key === 'skip' && g.entries.length <= 20);
      const det = h('details', { class: 'tier group', 'data-key': g.key },
        h('summary', {}, badge(g.status), h('span', { class: 'tname', 'data-testid': 'group-title' }, g.title), h('span', { class: 'muted small' }, String(g.entries.length))),
        h('div', { class: 'results' }, g.entries.map(entry)));
      det.open = open;
      area.append(det);
    }
  };
  if (hasRows) {
    box.append(h('div', { class: 'group-by', 'data-testid': 'group-by' }, h('span', { class: 'muted small' }, 'Group by'),
      [['problem', 'Problem'], ['part', 'Part'], ['tier', 'Tier']].map(([m, label]) => h('button', { type: 'button', class: view.mode === m ? 'active' : '', 'data-testid': 'group-' + m,
        onclick: (ev) => { view.mode = m; ev.currentTarget.parentElement.querySelectorAll('button').forEach((b) => b.classList.toggle('active', b === ev.currentTarget)); renderRows(); } }, label))));
  }
  renderRows();
  box.append(area);
}
