// Inspector (right column of Designs mode): facts about the selected part(s).
import { h, fmt } from '../lib.js';

const cur = { ctx: null, parts: null, mass: null, vp: null };

export function renderInspector(ctx, d, parts, mass) {
  Object.assign(cur, { ctx, parts, mass, vp: ctx.vp.main });
  refreshInspector();
}

export function refreshInspector() {
  const { ctx, parts, mass, vp } = cur;
  const box = ctx?.el.querySelector('#inspector');
  if (!box || !vp) return;
  box.replaceChildren();
  const sel = vp.state().selection;
  if (!sel.length) { box.removeAttribute('data-id'); box.append(h('p', { class: 'muted' }, 'Click a part, or a row in the list.')); return; }
  box.setAttribute('data-id', sel[0]);
  if (sel.length > 1) { box.append(h('h3', {}, `${sel.length} parts selected`), h('p', { class: 'small' }, sel.join(', '))); return; }
  const id = sel[0], p = parts?.parts?.find((x) => x.id === id);
  const m = (mass?.per_component || []).find((c) => c.id === id);
  box.append(h('h3', {}, id));
  if (!p) return;
  const parent = p.parent
    ? h('a', { href: '#', class: 'plink', 'data-testid': 'inspector-parent', onclick: (e) => { e.preventDefault(); ctx.setHighlight([p.parent]); } }, p.parent)
    : '-';
  const pend = vp.pending().find((x) => x.id === id), lock = vp.state().explode?.t > 0;
  box.append(h('dl', {},
    h('dt', {}, 'type'), h('dd', {}, p.type ?? '-'),
    h('dt', {}, 'mass'), h('dd', {}, m ? `${fmt(m.mass_g, 1)} g` : '-'),
    h('dt', {}, 'position (mm)'), h('dd', {}, p.position_mm.map((v) => fmt(v, 1)).join(', ')),
    h('dt', {}, 'parent'), h('dd', {}, parent),
    h('dt', {}, 'attachment'), h('dd', {}, p.attachment ?? '-'),
    h('dt', {}, 'depth'), h('dd', {}, String(p.depth)),
    h('dt', {}, 'articulated'), h('dd', {}, p.articulated ? 'yes' : 'no')),
  ...(p.local_only ? [h('span', { class: 'tag', 'data-testid': 'tag-local-cad' }, 'local CAD')] : []),
  ...(pend ? [h('span', { class: 'tag', 'data-testid': 'tag-moved' }, 'moved')] : []),
  ...(p.visual_only ? [] : [nudge(vp, id, pend?.delta_mm ?? [0, 0, 0], lock)]));
}

// Numeric nudge: the three inputs show the part's pending offset (mm); typing one moves the part to that offset.
function nudge(vp, id, delta, lock) {
  return h('div', { class: 'nudge', title: lock ? 'Set explode to 0 to move parts' : 'Move by (mm), 0.1 mm steps' }, h('span', { class: 'muted' }, 'move (mm)'),
    ['x', 'y', 'z'].map((axis, k) => h('input', { type: 'number', step: '0.1', value: String(delta[k]), disabled: lock ? '' : null, 'aria-label': 'Move ' + axis, 'data-testid': 'nudge-' + axis,
      onchange: (e) => {
        const v = Math.round(Number(e.target.value) * 10) / 10;
        if (e.target.value === '' || Number.isNaN(v)) { e.target.value = String(delta[k]); return; }
        const d = [0, 0, 0]; d[k] = v - delta[k];
        if (d[k] !== 0) vp.moveBy(id, d);
      } })));
}
