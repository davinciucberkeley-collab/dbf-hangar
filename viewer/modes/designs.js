// Designs mode: 3D view plus scorecard (tiers, FAIL rows first).
import { TIERS, STATUS_ORDER } from '../lib.js';
import { renderTree } from '../ui/tree.js';
import { renderInspector, setInspectorScorecard } from '../ui/inspector.js';
import { rowParts, partStatus } from '../vp/status.js';
import { renderTimeline } from '../ui/timeline.js';

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
  vp.main.setStatus(partStatus(sc, parts)); setInspectorScorecard(sc);
  const row = (r) => {
    const ids = rowParts(r, parts), has = ids.length > 0;
    const go = () => { const v = vp.main; if (v.focusKey === ids.join('|')) v.clearFocus(); else v.focusParts(ids); };
    return h('div', { class: `result ${r.status}` + (has ? ' has-parts' : ''), 'data-testid': 'check-row', 'data-check-id': r.check_id, 'data-parts': has ? ids.join('|') : null,
      tabindex: has ? 0 : null, role: has ? 'button' : null,
      onclick: has ? go : null, onkeydown: has ? (e) => { if (e.key === 'Enter') go(); } : null },
      h('div', { class: 'top' }, h('span', { class: 'badge ' + r.status }, r.status), h('span', { class: 'cid' }, r.check_id),
        has ? h('span', { class: 'partshint' }, 'show ' + ids.slice(0, 3).join(' + ') + (ids.length > 3 ? ` + ${ids.length - 3} more` : '')) : null),
      h('div', { class: 'msg' }, r.message), r.criterion ? h('div', { class: 'crit' }, r.criterion) : null);
  };
  for (const t of sc.tiers) {
    const results = [...t.results].sort((a, b) => (STATUS_ORDER[a.status] ?? 9) - (STATUS_ORDER[b.status] ?? 9));
    const nfail = results.filter((r) => r.status === 'FAIL').length;
    const det = h('details', { class: 'tier' },
      h('summary', {}, h('span', { class: 'pill ' + t.status }, 'T' + t.tier), h('span', { class: 'tname' }, t.name),
        nfail ? h('span', { class: 'muted small' }, `${nfail} failing`) : h('span', { class: 'muted small' }, `${results.length} checks`),
        h('span', { class: 'badge ' + t.status }, t.status)),
      h('div', { class: 'results' }, results.map(row)));
    if (t.status === 'FAIL' || t.status === 'WARN' || results.some((r) => r.status === 'FAIL' || r.status === 'WARN')) det.open = true;
    box.append(det);
  }
}
