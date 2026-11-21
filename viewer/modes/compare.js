// Compare mode: two viewports plus a table of mass, CG, tiers and key numbers.
import { TIERS } from '../lib.js';

const KEY_NUMBERS = [
  ['static_margin', 'Static margin', 3], ['thrust_to_weight', 'Hover thrust/weight', 2],
  ['stall_mps', 'Stall speed (m/s)', 2], ['wing_loading_g_dm2', 'Wing loading (g/dm²)', 1],
];
function findNumber(sc, key) {
  for (const t of sc?.tiers || []) for (const r of t.results) if (r.data && r.data[key] != null) return r.data[key];
  return null;
}

export default async function render({ state, el, h, fmt, getJSON, byId, vp, setHighlight }) {
  const [a, b] = [byId(state.slotA), byId(state.slotB)];
  el.querySelector('#sel-a').value = state.slotA || ''; el.querySelector('#sel-b').value = state.slotB || '';
  setHighlight([]);
  vp.a.show(a); vp.b.show(b);
  const sc = async (d) => (d && d.scorecard && !d.error ? getJSON(d.scorecard).catch(() => null) : null);
  const [sa, sb] = await Promise.all([sc(a), sc(b)]);
  if (a?.id !== state.slotA || b?.id !== state.slotB) return;
  const box = el.querySelector('#compare-table'); box.replaceChildren();
  if (!a || !b) { box.append(h('p', { class: 'muted' }, 'Pick two designs (use A / B buttons in the list, or the menus above).')); el.dataset.ready = '1'; return; }
  const rows = [];
  const sect = (t) => rows.push(h('tr', { class: 'sect' }, h('td', { colspan: 4 }, t)));
  const row = (label, va, vb, { num = null, digits = 1, unit = '' } = {}) => {
    let delta = '';
    if (num && typeof va === 'number' && typeof vb === 'number') {
      const dv = vb - va; delta = h('span', { class: 'delta ' + (dv > 0 ? 'pos' : dv < 0 ? 'neg' : '') }, (dv > 0 ? '+' : '') + fmt(dv, digits) + unit);
    }
    const cell = (v) => (typeof v === 'number' ? fmt(v, digits) + unit : v ?? '–');
    rows.push(h('tr', {}, h('th', {}, label), h('td', { class: 'num' }, cell(va)), h('td', { class: 'num' }, cell(vb)), h('td', { class: 'num' }, delta)));
  };
  const pill = (s) => h('span', { class: 'pill ' + (s ?? 'NONE') }, s ?? '–');
  const pillRow = (label, sa_, sb_) => rows.push(h('tr', {}, h('th', {}, label), h('td', {}, pill(sa_)), h('td', {}, pill(sb_)), h('td', {})));
  sect('Summary');
  row('Name', a.name, b.name); row('Status', a.status, b.status);
  pillRow('Verdict', a.error ? 'ERROR' : a.accepted ? 'PASS' : 'FAIL', b.error ? 'ERROR' : b.accepted ? 'PASS' : 'FAIL');
  row('Mass (g)', a.mass_g, b.mass_g, { num: true, digits: 1 });
  ['x', 'y', 'z'].forEach((ax, i) => row(`CG ${ax} (mm)`, a.cg_mm?.[i], b.cg_mm?.[i], { num: true, digits: 1 }));
  sect('Tiers');
  TIERS.forEach((t) => pillRow(`Tier ${t}`, a.tiers?.[t], b.tiers?.[t]));
  sect('Key numbers');
  for (const [k, label, dg] of KEY_NUMBERS) row(label, findNumber(sa, k), findNumber(sb, k), { num: true, digits: dg });
  box.append(h('table', { class: 'cmp' }, h('thead', {}, h('tr', {}, h('th', {}, ''), h('th', {}, 'A'), h('th', {}, 'B'), h('th', {}, 'Δ (B − A)'))), h('tbody', {}, rows)));
  if (a.error || b.error) box.append(h('div', { class: 'errbox', style: 'margin-top:10px' }, [a, b].filter((d) => d.error).map((d) => `${d.id}: ${d.error}`).join('\n')));
  el.dataset.ready = '1';
}
