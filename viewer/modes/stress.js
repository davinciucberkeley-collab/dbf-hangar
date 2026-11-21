// Stress mode: per-part stress-check results (fea.json). Running a check needs Studio (button has data-edit).
import { STATUS_ORDER } from '../lib.js';

export default async function render({ state, el, h, getJSON, byId, studio }) {
  const box = el.querySelector('.panel'); box.replaceChildren();
  const d = byId(state.selected);
  if (studio && d) box.append(h('button', { class: 'btn', 'data-edit': true, onclick: () => window.planeViewer.feaDialog?.(d.id) }, 'Run stress check'));
  if (!d?.fea) box.append(h('p', { class: 'muted' }, 'No stress results for this design.'));
  else {
    const fr = await getJSON(d.fea);
    const rank = (p) => (p.status == null ? 4 : STATUS_ORDER[p.status] ?? 3);
    const stale = (p) => p.status == null || p.up_to_date === false;
    box.append(h('p', {}, `Allowable ${fr.allowable_mpa ?? '–'} MPa, ultimate factor ${fr.ultimate_factor ?? '–'}`),
      h('table', { class: 'cmp' }, h('thead', {}, h('tr', {}, ['Part', 'Result', 'Worst case', 'SF'].map((c) => h('th', {}, c)))),
        h('tbody', {}, [...fr.parts].sort((a, b) => rank(a) - rank(b)).map((p) => h('tr', {},
          h('td', {}, h('code', {}, p.part)),
          h('td', {}, h('span', { class: 'badge ' + (stale(p) ? 'WARN' : p.status) }, p.status == null ? 'not run' : p.up_to_date === false ? 'out of date' : p.status)),
          h('td', {}, p.worst ? `${p.worst.name}: ${p.worst.stress_mpa} MPa` : p.error || '–'), h('td', {}, p.worst?.safety_factor ?? '–'))))));
  }
  el.dataset.ready = '1';
}
