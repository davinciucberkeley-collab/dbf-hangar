// "N parts moved, not saved" bar with Revert. Present in both builds; the Studio module adds Review & Apply to it.
import { h, $ } from '../lib.js';

let count, revert, bar;
const cur = { vp: null };

export function initApplyBar() {
  bar = $('apply-bar');
  if (!bar || bar.dataset.ready) return;
  count = h('span', { 'data-testid': 'apply-count' });
  revert = h('button', { type: 'button', class: 'btn', 'data-testid': 'btn-revert', title: 'Put every moved part back', onclick: () => cur.vp?.revertMoves() }, 'Revert');
  bar.append(count, revert); bar.dataset.ready = '1';
}

function render(vp) {
  if (!bar || vp !== cur.vp) return;
  const n = vp.pending().length;
  bar.hidden = n === 0;
  count.textContent = `${n} part${n === 1 ? '' : 's'} moved, not saved`;
}

export function bindApplyBar(vp) {
  cur.vp = vp;
  vp.subscribe(render);
  render(vp);
}
