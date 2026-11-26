// Part tree (left column of Designs mode): built from parts.json, kept in step with the viewport selection.
import { h } from '../lib.js';

const cur = { ctx: null, vp: null, root: null };

export function renderTree(ctx, d, parts) {
  const box = ctx.el.querySelector('#parts-tree'); box.replaceChildren();
  cur.ctx = ctx; cur.vp = null; cur.root = box;
  if (!parts?.parts) { box.append(h('p', { class: 'muted' }, 'No part list for this design.')); return; }
  const vp = cur.vp = ctx.vp.main;
  const mesh = new Set(vp.state().all);
  const byParent = new Map();
  for (const p of parts.parts) {
    if (p.visual_only || p.parent == null) continue;
    if (!byParent.has(p.parent)) byParent.set(p.parent, []);
    byParent.get(p.parent).push(p);
  }
  const placed = new Set();
  const row = (p) => {
    placed.add(p.id);
    const kids = (byParent.get(p.id) || []).filter((k) => !placed.has(k.id));
    const li = h('li', { class: 'part-row' + (mesh.has(p.id) ? '' : ' no-mesh'), 'data-id': p.id, 'data-type': p.type ?? '', 'aria-selected': 'false', 'data-hidden': '0', 'data-ghost': '0' });
    const ul = h('ul', {});
    const caret = kids.length
      ? h('button', { class: 'caret', type: 'button', 'aria-label': 'Expand or collapse', onclick: (e) => { e.stopPropagation(); ul.hidden = !ul.hidden; caret.textContent = ul.hidden ? '▸' : '▾'; } })
      : h('span', { class: 'caret-gap' });
    const eye = h('button', { class: 'eye', type: 'button', 'data-testid': 'eye-' + p.id, title: 'Hide or show', disabled: mesh.has(p.id) ? null : true,
      onclick: (e) => { e.stopPropagation(); vp.setHidden([p.id], !vp.hidden.has(p.id)); } }, '◉');
    const ghost = h('button', { class: 'ghost', type: 'button', 'data-testid': 'ghost-' + p.id, title: 'Ghost or solid', disabled: mesh.has(p.id) ? null : true,
      onclick: (e) => { e.stopPropagation(); vp.setGhost([p.id], !vp.state().ghosted.includes(p.id)); } }, '\u25cc');
    const main = h('div', { class: 'row-main', tabindex: 0,
      onclick: (e) => {
        const sel = vp.state().selection;
        if (e.ctrlKey || e.metaKey) ctx.setHighlight(sel.includes(p.id) ? sel.filter((i) => i !== p.id) : [...sel, p.id]);
        else ctx.setHighlight([p.id]);
      },
      ondblclick: () => { ctx.setHighlight([p.id]); vp.fitTo([p.id]); } },
    caret, eye, ghost, h('span', { class: 'pid' }, p.id), h('span', { class: 'ptype muted small' }, p.type ?? ''));
    li.append(main);
    if (kids.length) {
      ul.append(...kids.map(row));
      const open = p.depth < 2;
      ul.hidden = !open; caret.textContent = open ? '▾' : '▸';
      li.append(ul);
    }
    return li;
  };
  const top = h('ul', { class: 'tree-top' });
  const rootPart = parts.parts.find((p) => p.id === parts.root);
  if (rootPart) top.append(row(rootPart));
  const group = (name, items) => h('li', { class: 'part-group', 'data-group': name },
    h('div', { class: 'group-head' }, name, h('span', { class: 'muted small' }, ` ${items.length}`)), h('ul', {}, items));
  const unattached = parts.parts.filter((p) => !p.visual_only && !placed.has(p.id) && p.parent == null).map(row);
  const orphans = parts.parts.filter((p) => !p.visual_only && !placed.has(p.id)).map(row); // children of a skipped parent
  if (unattached.length || orphans.length) top.append(group('Unattached', [...unattached, ...orphans]));
  const wiring = parts.parts.filter((p) => p.visual_only).map(row);
  if (wiring.length) top.append(group('Wiring', wiring));
  const filter = h('input', { type: 'search', placeholder: 'Filter parts', 'aria-label': 'Filter parts', 'data-testid': 'tree-filter', oninput: (e) => applyFilter(box, e.target.value.trim().toLowerCase()) });
  const showAll = h('button', { class: 'btn', type: 'button', 'data-testid': 'tree-show-all', onclick: () => vp.showAll() }, 'Show all');
  box.append(h('div', { class: 'tree-head' }, filter, showAll), top);
  syncTree();
}

function applyFilter(box, q) {
  const rows = [...box.querySelectorAll('li.part-row')].reverse(); // descendants before ancestors
  for (const li of rows) {
    const self = !q || li.dataset.id.toLowerCase().includes(q) || li.dataset.type.toLowerCase().includes(q);
    li.hidden = !(self || li.querySelector('li.part-row:not([hidden])'));
  }
  for (const g of box.querySelectorAll('li.part-group')) g.hidden = !g.querySelector('li.part-row:not([hidden])');
}

export function syncTree() {
  const { vp, root } = cur;
  if (!vp || !root?.isConnected) return;
  const st = vp.state(), sel = new Set(st.selection), hid = new Set(st.hidden), gh = new Set(st.ghosted);
  let first = null;
  for (const li of root.querySelectorAll('li.part-row')) {
    const on = sel.has(li.dataset.id);
    li.setAttribute('aria-selected', on ? 'true' : 'false');
    li.dataset.hidden = hid.has(li.dataset.id) ? '1' : '0';
    li.dataset.ghost = gh.has(li.dataset.id) ? '1' : '0';
    if (on && !first) first = li;
  }
  if (first) {
    for (let u = first.parentElement; u && u !== root; u = u.parentElement) if (u.tagName === 'UL' && u.hidden) u.hidden = false;
    first.querySelector(':scope > .row-main')?.scrollIntoView({ block: 'nearest' });
  }
}
