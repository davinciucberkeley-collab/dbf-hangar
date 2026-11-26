// BOM tab (right column of Model mode): parts and mass from parts.json + mass.json.
import { fmt } from '../lib.js';

export function renderBom(ctx, d, parts, mass) {
  const { h, el } = ctx;
  const box = el.querySelector('#bom-panel'); box.replaceChildren();
  const list = parts?.parts;
  if (!d || !list) { box.append(h('p', { class: 'muted' }, d ? 'No parts data for this design.' : 'Select a design from the list.')); return; }
  const pc = mass?.per_component;
  const massOf = (id) => (Array.isArray(pc) ? pc.find((c) => c.id === id)?.mass_g : pc?.[id]?.mass_g);
  const rows = list.map((p) => ({ p, m: massOf(p.id) })).sort((a, b) => (b.m ?? -1) - (a.m ?? -1));
  const sum = rows.reduce((t, r) => t + (r.m ?? 0), 0);
  const pick = (id) => ctx.setHighlight([id]);
  box.append(h('table', { class: 'cmp bom' },
    h('thead', {}, h('tr', {}, ['Part', 'Type', 'Mass (g)', 'Position (mm)'].map((t) => h('th', {}, t)))),
    h('tbody', {}, rows.map(({ p, m }) => h('tr', { 'data-testid': 'bom-row', 'data-id': p.id, tabindex: 0, onclick: () => pick(p.id), onkeydown: (e) => { if (e.key === 'Enter') pick(p.id); } },
      h('td', { class: 'mono' }, p.id), h('td', {}, p.type ?? '-'), h('td', { class: 'num' }, m == null ? '-' : fmt(m, 1)),
      h('td', { class: 'num' }, (p.position_mm || []).map((v) => fmt(v, 0)).join(', '))))),
    h('tfoot', {}, h('tr', {}, h('td', {}, `Total (${rows.length} parts)`), h('td', {}, ''), h('td', { class: 'num', 'data-testid': 'bom-total' }, fmt(sum, 1)), h('td', {}, '')))),
    h('p', { class: 'muted small' }, 'Parts and mass from the model; the full bill of materials is in plane.yaml.'));
}
