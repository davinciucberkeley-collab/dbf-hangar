// Viewer: one app (Plane Studio). Reads only generated data (data/index.json + per-design files).
// Each mode is modes/<id>.js; modes/edit.js is loaded only when index.json has "studio": true.
import { h, $, fmt, getJSON, cache, TIERS } from './lib.js';
import { Viewport } from './vp/scene.js';
import { syncTree } from './ui/tree.js';
import { refreshInspector } from './ui/inspector.js';
import { initApplyBar, bindApplyBar } from './ui/applybar.js';

const DATA = 'data/';
const MODES = ['designs', 'compare', 'stress', 'updates', 'ledger'];
const LABELS = { designs: 'Model', compare: 'Compare', stress: 'Stress', updates: 'Updates', ledger: 'Ledger' };
const HINTS = { designs: 'Click a part, or a row in the list. Drag to orbit, scroll to zoom.', compare: 'Click designs in the list to fill slots A and B alternately.' };

const state = { timelineOpen: false, index: null, selected: null, mode: 'designs', slotA: null, slotB: null, nextSlot: 'a', text: '', vtol: '' };
const byId = (id) => state.index?.designs.find((d) => d.id === id);

// ---------- views ----------
// Viewports are created lazily, one WebGL context per visible viewport; setMode() releases the unused ones.
const vps = {};
const VP_EL = { main: 'vp-main', a: 'vp-a', b: 'vp-b' };
const VP_NEEDED = { designs: ['main'], compare: ['a', 'b'] };
function getVp(name) {
  if (vps[name]) return vps[name];
  const v = (vps[name] = new Viewport($(VP_EL[name]), name === 'main' ? { onPick, onSelect: onViewportChange, onModel: (x) => syncExplodeControls(x), onDiscard: (m) => window.planeViewer?.studio?.toast?.(m, 'err') } : { onPick }));
  if (name === 'main') { v.setAttached(attachedOn()); bindApplyBar(v); v.subscribe(() => { syncTool(); syncTree(); refreshInspector(); }); }
  return v;
}
let attachedOn = () => true, syncTool = () => {};
// Pending moves are lost on a design or mode change: ask first. Returns false when the person keeps them.
function confirmDiscard() {
  const n = vps.main?.pending().length ?? 0;
  if (!n) return true;
  if (!window.confirm('Discard ' + n + ' unsaved move' + (n === 1 ? '' : 's') + '?')) return false;
  vps.main.revertMoves();
  return true;
}
// A mode callback that resumes after the user left its mode must not re-create a viewport: its getters throw StaleMode.
class StaleMode extends Error {}
let renderGen = 0;
const vpAccessFor = (gen) => {
  const get = (n) => { if (gen !== renderGen) throw new StaleMode(); return getVp(n); };
  return { get main() { return get('main'); }, get a() { return get('a'); }, get b() { return get('b'); } };
};
let highlightIds = new Set();
let syncExplodeControls = () => {};

// Thin wrapper over the viewport's single selection setter (Designs) or the single-id highlight (Compare).
function setHighlight(ids) {
  highlightIds = new Set(ids);
  if (state.mode === 'designs') vps.main?.select([...highlightIds]);
  else if (state.mode === 'compare') [vps.a, vps.b].forEach((v) => v?.highlight(highlightIds));
  markActiveRows();
}
// A scorecard row is active while its parts are the focused set (vp.focusParts).
function markActiveRows() {
  const f = vps.main?.focusKey ?? null;
  document.querySelectorAll('.result[data-parts]').forEach((r) => r.classList.toggle('active', f != null && r.dataset.parts === f));
}
// The main viewport reports every selection or visibility change here.
function onViewportChange(selection) {
  highlightIds = new Set(selection);
  markActiveRows(); syncTree(); refreshInspector();
}
function onPick(id, vp, e) {
  const multi = !!(e && (e.ctrlKey || e.metaKey));
  if (!id) { if (!multi) { if (vps.main?.focusKey) vps.main.clearFocus(); else setHighlight([]); } return; }
  if (multi) { const s = new Set(highlightIds); if (s.has(id)) s.delete(id); else s.add(id); return setHighlight([...s]); }
  setHighlight(highlightIds.size === 1 && highlightIds.has(id) ? [] : [id]);
}
document.addEventListener('keydown', (e) => {
  if (e.target.closest?.('input, textarea, select') || e.ctrlKey || e.metaKey || e.altKey) return;
  const v = state.mode === 'designs' ? vps.main : null;
  if (e.key === 'Escape') { if (v?.axisLocked()) v.lockAxis(null); else if (v?.focusKey) v.clearFocus(); else if (highlightIds.size) setHighlight([]); return; }
  if (!v) return;
  if (e.key === 'm') v.setTool(v.state().tool === 'move' ? 'select' : 'move');
  else if (v.state().tool === 'move' && 'xyz'.includes(e.key) && e.key.length === 1) v.lockAxis(e.key);
  else if (e.key === 'h') v.setHidden([...highlightIds], true);
  else if (e.key === 'i') { if (highlightIds.size) v.isolate([...highlightIds]); }
  else if (e.key === 'H') v.showAll();
  else if (e.key === 'g') { const ids = [...highlightIds], gh = new Set(v.state().ghosted); if (ids.length) v.setGhost(ids, !ids.every((i) => gh.has(i))); }
});

function renderSidebar() {
  updatePicker();
  const list = $('design-list'); list.replaceChildren();
  const q = state.text.toLowerCase();
  const all = state.index.designs;
  const shown = all.filter((d) => {
    if (state.vtol && (d.morphology?.vtol_method ?? '') !== state.vtol) return false;
    if (!q) return true;
    const hay = [d.id, d.name, d.status, ...Object.values(d.morphology || {})].join(' ').toLowerCase();
    return q.split(/\s+/).every((t) => hay.includes(t));
  });
  $('count').textContent = `${shown.length} of ${all.length}`;
  if (!shown.length) list.append(h('li', { class: 'empty' }, 'No designs match.'));
  for (const d of shown) {
    const sel = state.mode !== 'compare' ? state.selected === d.id : (state.slotA === d.id || state.slotB === d.id);
    const badge = d.pending ? h('span', { class: 'badge pending' }, 'checking…') : d.error ? h('span', { class: 'badge error' }, 'error')
      : h('span', { class: 'badge ' + (d.accepted ? 'accepted' : 'rejected') }, d.accepted ? 'accepted' : 'rejected');
    const tags = Object.entries(d.morphology || {}).map(([k, v]) => h('span', { class: 'tag', title: k }, String(v)));
    const pills = TIERS.map((t) => { const s = d.tiers?.[t] ?? 'NONE'; return h('span', { class: 'pill ' + s, title: `Tier ${t}: ${s}` }, 'T' + t); });
    const li = h('li', { class: 'design-item' + (sel ? ' selected' : ''), tabindex: 0, 'data-id': d.id, onclick: () => choose(d.id), onkeydown: (e) => { if (e.key === 'Enter') choose(d.id); } },
      h('div', { class: 'row1' }, h('div', {}, h('div', { class: 'name' }, d.name || d.id), h('div', { class: 'id' }, d.id)), badge),
      h('div', { class: 'tags' }, h('span', { class: 'tag status' }, d.status), tags),
      h('div', { class: 'pills' }, pills),
      h('div', { class: 'ab' }, ['a', 'b'].map((s) => h('button', { class: state['slot' + s.toUpperCase()] === d.id ? 'on' : '', onclick: (e) => { e.stopPropagation(); assign(s, d.id); } }, s.toUpperCase()))));
    list.append(li);
  }
}


function choose(id) {
  if (state.mode === 'compare') { assign(state.nextSlot, id); return; }
  setPicker(false);
  if (id !== state.selected && !confirmDiscard()) return;
  state.selected = id; syncHash(); renderSidebar(); renderMode();
}
// The design picker: the old sidebar is its popover (filters, list, jobs, New/Import stay inside it).
function setPicker(open) {
  const pop = $('sidebar'), btn = $('design-picker');
  pop.hidden = !open; btn.setAttribute('aria-expanded', String(open));
  if (open) $('filter-text').focus();
}
function updatePicker() {
  const btn = $('design-picker'), d = byId(state.selected);
  btn.replaceChildren(d ? (d.name || d.id) : 'Pick a design', ' ▾');
  if (state.index?.designs.some((x) => x.pending)) btn.append(' ', h('span', { class: 'badge pending', 'data-testid': 'picker-pending' }, 'checking...'));
}
function assign(slot, id) {
  if (!confirmDiscard()) return;
  state['slot' + slot.toUpperCase()] = id; state.nextSlot = slot === 'a' ? 'b' : 'a';
  syncHash(); renderSidebar(); renderMode();
}

// ---------- modes / hash / init ----------
async function renderMode() {
  const id = state.mode, el = $('mode-' + id), gen = ++renderGen;
  delete el.dataset.ready;
  const vm = vps.main; // a re-render of the open design keeps what the person had set (view, selection, pending moves)
  if (id === 'designs' && vm?.transforms && vm.mountInfo?.id === state.selected) vm.keepNext = vm.snapshot();
  try {
    const ctx = { state, el, h, fmt, getJSON, byId, vp: vpAccessFor(gen), setHighlight, studio: state.index.studio === true };
    await (await import('./modes/' + id + '.js')).default(ctx);
  } catch (e) {
    if (e instanceof StaleMode) return;
    console.warn(e);
    el.append(h('div', { class: 'errbox' }, `${id}: ${e.message}`)); el.dataset.ready = 'error';
  }
}
function setMode(id) {
  if (id !== state.mode && !confirmDiscard()) return;
  state.mode = id; document.body.dataset.mode = id;
  for (const m of MODES) $('mode-' + m).hidden = m !== id;
  document.querySelectorAll('#modes button').forEach((b) => b.classList.toggle('active', b.dataset.mode === id));
  $('mode-hint').textContent = HINTS[id] || '';
  if (id === 'compare') {
    if (!state.slotA) state.slotA = state.selected || state.index.designs[0]?.id;
    if (!state.slotB) state.slotB = state.index.designs.find((d) => d.id !== state.slotA)?.id ?? null;
  }
  syncHash(); renderSidebar();
  for (const n of Object.keys(vps)) if (!(VP_NEEDED[id] || []).includes(n)) { vps[n].dispose(); delete vps[n]; }
  requestAnimationFrame(() => Object.values(vps).forEach((v) => v.resize()));
  renderMode();
}
function syncHash() {
  const p = new URLSearchParams({ m: state.mode });
  if (state.mode === 'compare') { p.set('a', state.slotA || ''); p.set('b', state.slotB || ''); } else if (state.selected) p.set('d', state.selected);
  try { history.replaceState(null, '', '#' + p.toString()); } catch { /* ignore */ }
}

async function init() {
  (function loop() { requestAnimationFrame(loop); Object.values(vps).forEach((v) => v.tick()); })();
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => setTimeout(() => Object.values(vps).forEach((v) => v.applyTheme()), 0));
  try { const t = localStorage.getItem('plane-theme'); if (t === 'light' || t === 'dark') document.documentElement.dataset.theme = t; } catch { /* ignore */ }
  $('theme-toggle').onclick = () => {
    const root = document.documentElement;
    const cur = root.dataset.theme || (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    const next = cur === 'dark' ? 'light' : 'dark';
    root.dataset.theme = next;
    try { localStorage.setItem('plane-theme', next); } catch { /* ignore */ }
    setTimeout(() => Object.values(vps).forEach((v) => v.applyTheme()), 0);
  };
  $('modes').append(...MODES.map((m) => h('button', { 'data-mode': m, role: 'tab', onclick: () => setMode(m) }, LABELS[m])));
  $('view-bar').append(...[['iso', 'Iso'], ['front', 'Front'], ['top', 'Top'], ['side', 'Side']].map(([n, t]) => h('button', { type: 'button', 'data-testid': 'view-' + n, onclick: () => vps.main?.view(n) }, t)),
    h('button', { type: 'button', 'data-testid': 'view-fit', onclick: () => vps.main?.fitTo(highlightIds.size ? [...highlightIds] : [...(vps.main.ids || [])]) }, 'Fit'));
  const si = $('see-inside'), q = (t) => si.querySelector(`[data-testid="${t}"]`);
  const sec = () => { const ax = q('section-axis').value; q('section-slider').disabled = ax === 'off'; vps.main?.section(ax === 'off' ? null : ax, q('section-slider').value / 1000, q('section-flip').checked); };
  const xb = h('button', { type: 'button', 'data-testid': 'btn-xray', 'aria-pressed': 'false', onclick: () => { const on = xb.getAttribute('aria-pressed') !== 'true'; xb.setAttribute('aria-pressed', String(on)); vps.main?.xray(on); } }, 'X-ray');
  si.append(xb,
    h('select', { 'data-testid': 'section-axis', 'aria-label': 'Section axis', onchange: sec }, ['off', 'x', 'y', 'z'].map((a) => h('option', { value: a }, a))),
    h('input', { type: 'range', min: '0', max: '1000', value: '500', disabled: true, 'data-testid': 'section-slider', 'aria-label': 'Section position', oninput: sec }),
    h('label', {}, h('input', { type: 'checkbox', 'data-testid': 'section-flip', onchange: sec }), ' flip'));
  initApplyBar();
  const tb = $('tool-bar'), pick = (t) => vps.main?.setTool(t);
  const tSel = h('button', { type: 'button', 'data-testid': 'tool-select', 'aria-pressed': 'true', title: 'Select parts (Esc)', onclick: () => pick('select') }, 'Select');
  const tMove = h('button', { type: 'button', 'data-testid': 'tool-move', 'aria-pressed': 'false', title: 'Move parts (m)', onclick: () => pick('move') }, 'Move');
  const att = h('input', { type: 'checkbox', checked: true, 'data-testid': 'move-with-attached', onchange: () => vps.main?.setAttached(att.checked) });
  attachedOn = () => att.checked;
  tb.append(tSel, tMove, h('label', { title: 'Parts attached below the moved part move with it' }, att, 'with attached parts'));
  const colourSel = h('select', { 'data-testid': 'colour-by', 'aria-label': 'Colour by', onchange: () => vps.main?.colourBy(colourSel.value) }, ['type', 'status', 'mass'].map((m) => h('option', { value: m }, m)));
  $('colour-bar').append(h('label', { class: 'colour-by' }, 'Colour by ', colourSel));
  syncTool = () => {
    const s = vps.main?.state(); if (!s) return;
    colourSel.value = s.colourBy;
    tSel.setAttribute('aria-pressed', String(s.tool === 'select')); tMove.setAttribute('aria-pressed', String(s.tool === 'move'));
    const off = s.explode?.t > 0; tMove.disabled = off; tMove.title = off ? 'Set explode to 0 to move parts' : 'Move parts (m)';
  };
  const eb = $('explode-bar'), strat = h('select', { 'data-testid': 'explode-strategy', 'aria-label': 'Explode strategy', onchange: () => { fillLevels(); explode(); } }, ['hierarchy', 'radial'].map((s) => h('option', { value: s }, s)));
  const lvl = h('select', { 'data-testid': 'explode-level', 'aria-label': 'Explode level', onchange: () => explode() });
  let depth = 0;
  // hierarchy: "All" would equal level 1 (top-level child of the root), so it is not offered there; radial offers All
  const fillLevels = () => {
    const keep = lvl.value, radial = strat.value === 'radial';
    lvl.replaceChildren(...(radial ? [h('option', { value: 'all' }, 'All')] : []), ...Array.from({ length: depth }, (_, k) => h('option', { value: String(k + 1) }, String(k + 1))));
    lvl.value = [...lvl.options].some((o) => o.value === keep) ? keep : lvl.options[0]?.value ?? '';
  };
  const slider = h('input', { type: 'range', min: '0', max: '1000', value: '0', 'data-testid': 'explode-slider', 'aria-label': 'Explode', oninput: () => explode() });
  const explode = () => vps.main?.explode(slider.value / 1000, lvl.value === 'all' || lvl.value === '' ? 'all' : +lvl.value, strat.value);
  syncExplodeControls = (vp) => { // a new model: controls back to 0 / All / hierarchy, levels from the part tree
    slider.value = '0'; strat.value = 'hierarchy';
    depth = Math.max(0, ...(vp.parts?.parts || []).map((x) => x.depth));
    lvl.replaceChildren(); fillLevels(); eb.hidden = !vp.parts;
  };
  eb.append(h('label', {}, 'Explode ', slider), lvl, strat);
  $('design-picker').onclick = () => setPicker($('sidebar').hidden);
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape' && !$('sidebar').hidden) { setPicker(false); $('design-picker').focus(); e.stopImmediatePropagation(); } }, true);
  document.addEventListener('click', (e) => { if (!$('sidebar').hidden && !e.composedPath().some((n) => n.classList?.contains('picker-wrap'))) setPicker(false); });
  const tabs = document.querySelectorAll('#side-tabs button');
  tabs.forEach((b) => { b.onclick = () => { const bom = b.dataset.testid === 'tab-bom'; $('scorecard').hidden = bom; $('bom-panel').hidden = !bom; tabs.forEach((x) => x.classList.toggle('active', x === b)); }; });
  $('filter-text').oninput = (e) => { state.text = e.target.value.trim(); renderSidebar(); };
  $('filter-vtol').onchange = (e) => { state.vtol = e.target.value; renderSidebar(); };
  $('sel-a').onchange = (e) => assign('a', e.target.value); $('sel-b').onchange = (e) => assign('b', e.target.value);

  try {
    const r = await fetch(DATA + 'index.json');
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    state.index = await r.json();
    if (!Array.isArray(state.index.designs)) throw new Error('index.json has no "designs" array');
  } catch (e) {
    $('design-list').append(h('li', { class: 'empty' }, `Could not load data/index.json (${e.message}). Run: plane build-index --out viewer/data`));
    getVp('main').message('No data loaded', true);
    return;
  }
  const methods = [...new Set(state.index.designs.map((d) => d.morphology?.vtol_method).filter(Boolean))].sort();
  $('filter-vtol').append(...methods.map((m) => h('option', { value: m }, m)));
  $('generated').textContent = state.index.generated_at ? 'Data generated ' + state.index.generated_at : '';
  for (const sel of [$('sel-a'), $('sel-b')]) sel.append(h('option', { value: '' }, '— none —'), ...state.index.designs.map((d) => h('option', { value: d.id }, d.name || d.id)));

  const p = new URLSearchParams(location.hash.slice(1));
  state.selected = byId(p.get('d')) ? p.get('d') : state.index.designs.find((d) => !d.error)?.id ?? state.index.designs[0]?.id ?? null;
  state.slotA = byId(p.get('a'))?.id ?? null; state.slotB = byId(p.get('b'))?.id ?? null;
  if (p.get('m') === 'physics') { state.timelineOpen = true; p.set('m', 'designs'); } // old Physics links open the model with the timeline
  setMode(MODES.includes(p.get('m')) ? p.get('m') : p.has('a') || p.has('b') ? 'compare' : 'designs');
  if (state.index.studio) import('./modes/edit.js').then((m) => m.default(window.planeViewer)).catch((e) => console.warn('studio UI failed to load', e));
}

// Hooks for the local studio app (modes/edit.js). The Pages build never calls these.
async function reload(selectId) {
  if (selectId && !confirmDiscard()) return;
  const r = await fetch(DATA + 'index.json', { cache: 'no-store' });
  if (!r.ok) return;
  const prev = state.index;
  state.index = await r.json();
  cache.json.clear(); cache.glb.clear();
  for (const sel of [$('sel-a'), $('sel-b')]) sel.replaceChildren(h('option', { value: '' }, '— none —'), ...state.index.designs.map((d) => h('option', { value: d.id }, d.name || d.id)));
  if (selectId && byId(selectId)) { state.selected = selectId; if (state.mode === 'compare') return setMode('designs'); }
  if (!byId(state.selected)) state.selected = state.index.designs[0]?.id ?? null;
  renderSidebar();
  const was = prev?.designs.find((d) => d.id === state.selected), now = byId(state.selected);
  if (state.mode === 'compare' || !was || JSON.stringify(was) !== JSON.stringify(now) || selectId) { syncHash(); renderMode(); }
}
window.planeViewer = { get vp() { return vps.main || null; }, reload, selected: () => state.selected, designs: () => state.index?.designs || [], refresh: () => state.mode === 'designs' && renderMode() };
init();
