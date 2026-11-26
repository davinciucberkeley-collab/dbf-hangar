// Designs mode: 3D view plus scorecard (tiers, FAIL rows first).
import { TIERS, STATUS_ORDER } from '../lib.js';
import { renderTree } from '../ui/tree.js';
import { renderInspector } from '../ui/inspector.js';
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
  await renderScorecard(ctx, d);
  await renderTimeline(ctx, d);
  el.dataset.ready = '1';
}

async function renderScorecard({ state, el, h, fmt, getJSON, setHighlight }, d) {
  const box = el.querySelector('#scorecard'); box.replaceChildren();
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
  const row = (r) => {
    // interference rows carry `pair`; T6.link rows carry `link_pairs` (list of pairs) and `parts` (their union)
    const lp = Array.isArray(r.data?.link_pairs) ? [...new Set(r.data.link_pairs.flat())].sort() : null;
    const pair = Array.isArray(r.data?.pair) && r.data.pair.length === 2 ? r.data.pair : lp?.length ? lp : null;
    return h('div', { class: `result ${r.status}` + (pair ? ' has-pair' : ''), 'data-pair': pair ? pair.join('|') : null,
      tabindex: pair ? 0 : null, role: pair ? 'button' : null,
      onclick: pair ? () => setHighlight(pair) : null, onkeydown: pair ? (e) => { if (e.key === 'Enter') setHighlight(pair); } : null },
      h('div', { class: 'top' }, h('span', { class: 'badge ' + r.status }, r.status), h('span', { class: 'cid' }, r.check_id),
        pair ? h('span', { class: 'pairhint' }, `show ${pair.join(' + ')}`) : null),
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
    if (t.status === 'FAIL' || t.status === 'WARN') det.open = true;
    box.append(det);
  }
}
