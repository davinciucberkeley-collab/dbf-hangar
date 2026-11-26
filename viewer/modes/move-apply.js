// Studio only: Review & Apply for pending moves. One design.set call through the same edit op as the editor.
import { h } from '../lib.js';

const list = (a) => '[' + a.join(', ') + ']';

function warnings(vp, pend) {
  const ids = new Set(pend.map((p) => p.id)), parts = vp.parts?.parts || [], atts = vp.parts?.attachments || [];
  const byId = new Map(parts.map((p) => [p.id, p])), out = [];
  for (const p of pend) if (byId.get(p.id)?.position_expr) out.push(`${p.id} has an expression position ($name); Apply replaces it with plain numbers`);
  for (const a of atts) if (byId.get(a.child)?.articulated && (ids.has(a.parent) || ids.has(a.child))) out.push(`the pivot of joint ${a.label} is a fixed point in plane.yaml and does not move with ${ids.has(a.child) ? a.child : a.parent}: check T1.articulation after the re-run`);
  for (const p of parts) if (p.has_cavities && !ids.has(p.id)) out.push(`${p.id} has cavities that stay where they are: a part inside one will not carry it with it`);
  const split = atts.filter((a) => (ids.has(a.parent) || ids.has(a.child)) && !(ids.has(a.parent) && ids.has(a.child))).length;
  if (split) out.push(`${split} attachment(s) touching moved parts keep their literal joint location: T1.attachment may flag them`);
  return out;
}

export default function boot(V) {
  const bar = document.getElementById('apply-bar');
  if (!bar) return;
  const btn = h('button', { type: 'button', class: 'btn primary', 'data-edit': true, 'data-testid': 'btn-review-apply', title: 'Show what will be written to plane.yaml', onclick: () => review(V) }, 'Review & Apply');
  const rev = bar.querySelector('[data-testid="btn-revert"]');
  if (rev) rev.before(btn); else bar.append(btn);
}

function review(V) {
  const vp = V.vp, pend = vp?.pending() || [];
  if (!pend.length) return;
  const { op, designPath, toast, dialog, primary } = V.studio, id = V.selected();
  const why = h('input', { type: 'text', 'data-testid': 'apply-why', placeholder: 'One line: why this move' });
  const key = (p) => `components[${p.id}].position`;
  const cli = h('pre', { 'data-testid': 'apply-cli', class: 'mono small' });
  const line = () => {
    const [first, ...rest] = pend;
    cli.textContent = `plane design set designs/${id} "${key(first)}" "${list(first.to_mm)}"` + rest.map((p) => ` --also "${key(p)}=${list(p.to_mm)}"`).join('')
      + ` --kind modify --why "${why.value.replace(/"/g, '\\"')}"`;
  };
  why.addEventListener('input', line); line();
  const warns = warnings(vp, pend);
  const table = h('table', { class: 'edit' }, h('thead', {}, h('tr', {}, ['Part', 'Key', 'Old -> new (mm)'].map((t) => h('th', {}, t)))),
    h('tbody', {}, pend.map((p) => h('tr', {}, h('td', {}, h('code', {}, p.id)), h('td', {}, h('code', {}, key(p))), h('td', { class: 'mono' }, `${list(p.from_mm)} -> ${list(p.to_mm)}`)))));
  const dlg = dialog('Review moves', [
    h('p', { class: 'muted' }, 'Nothing is written until you click Apply. The checks re-run on the new positions.'), table,
    warns.length ? h('div', { class: 'warn', 'data-testid': 'apply-warnings' }, warns.map((w) => h('p', {}, w))) : null,
    h('p', { class: 'muted small' }, 'Command that Apply runs:'), cli, h('label', { class: 'field' }, h('span', { class: 'lbl' }, 'Why'), why),
  ], primary('Apply', async (d) => {
    const reason = why.value.trim();
    if (!reason) throw new Error('Say why in one line.');
    const [first, ...rest] = pend;
    await op('design.set', { path: designPath(id), key: key(first), value: list(first.to_mm), why: reason, kind: 'modify',
      also: rest.map((p) => `${key(p)}=${list(p.to_mm)}`) });
    vp.clearMovesAfterSave();
    d.close(); toast(`Saved ${pend.length} moved part${pend.length === 1 ? '' : 's'}. Checks are re-running.`);
    await V.reload(id);
  }, { 'data-testid': 'apply-go', 'data-edit': true }));
  dlg.classList.add('wide');
}
