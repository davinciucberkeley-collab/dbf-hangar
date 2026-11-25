// Viewer: one app (Plane Studio). Reads only generated data (data/index.json + per-design files).
// Each mode is modes/<id>.js; modes/edit.js is loaded only when index.json has "studio": true.
import { h, $, fmt, getJSON, cache, TIERS } from './lib.js';
import { Viewport } from './vp/scene.js';

const DATA = 'data/';
const MODES = ['designs', 'compare', 'physics', 'stress', 'updates', 'ledger'];
const LABELS = { designs: 'Designs', compare: 'Compare', physics: 'Physics', stress: 'Stress', updates: 'Updates', ledger: 'Ledger' };
const HINTS = { designs: 'Click a part to highlight it. Drag to orbit, scroll to zoom.', compare: 'Click designs in the list to fill slots A and B alternately.' };

const state = { index: null, selected: null, mode: 'designs', slotA: null, slotB: null, nextSlot: 'a', text: '', vtol: '' };
const byId = (id) => state.index?.designs.find((d) => d.id === id);

// ---------- views ----------
// Viewports are created lazily, one WebGL context per visible viewport; setMode() releases the unused ones.
const vps = {};
const VP_EL = { main: 'vp-main', a: 'vp-a', b: 'vp-b', phys: 'vp-phys' };
const VP_NEEDED = { designs: ['main'], compare: ['a', 'b'], physics: ['phys'] };
function getVp(name) {
  return (vps[name] ||= new Viewport($(VP_EL[name]), name === 'phys' ? {} : { onPick }));
}
const vpAccess = { get main() { return getVp('main'); }, get a() { return getVp('a'); }, get b() { return getVp('b'); }, get phys() { return getVp('phys'); } };
let highlightIds = new Set();

function setHighlight(ids) {
  highlightIds = new Set(ids);
  (state.mode === 'designs' ? [vps.main] : state.mode === 'compare' ? [vps.a, vps.b] : []).forEach((v) => v?.highlight(highlightIds));
  document.querySelectorAll('.result.has-pair').forEach((r) => {
    const pair = r.dataset.pair.split('|');
    r.classList.toggle('active', pair.length === highlightIds.size && pair.every((p) => highlightIds.has(p)));
  });
}
function onPick(id) {
  if (!id) return setHighlight([]);
  setHighlight(highlightIds.size === 1 && highlightIds.has(id) ? [] : [id]);
}

function renderSidebar() {
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
  state.selected = id; syncHash(); renderSidebar(); renderMode();
}
function assign(slot, id) {
  state['slot' + slot.toUpperCase()] = id; state.nextSlot = slot === 'a' ? 'b' : 'a';
  syncHash(); renderSidebar(); renderMode();
}

// ---------- modes / hash / init ----------
async function renderMode() {
  const id = state.mode, el = $('mode-' + id);
  delete el.dataset.ready;
  try {
    const ctx = { state, el, h, fmt, getJSON, byId, vp: vpAccess, setHighlight, studio: state.index.studio === true };
    await (await import('./modes/' + id + '.js')).default(ctx);
  } catch (e) {
    console.warn(e);
    el.append(h('div', { class: 'errbox' }, `${id}: ${e.message}`)); el.dataset.ready = 'error';
  }
}
function setMode(id) {
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
  $('modes').append(...MODES.map((m) => h('button', { 'data-mode': m, role: 'tab', onclick: () => setMode(m) }, LABELS[m])));
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
  setMode(MODES.includes(p.get('m')) ? p.get('m') : p.has('a') || p.has('b') ? 'compare' : 'designs');
  if (state.index.studio) import('./modes/edit.js').then((m) => m.default(window.planeViewer)).catch((e) => console.warn('studio UI failed to load', e));
}

// Hooks for the local studio app (modes/edit.js). The Pages build never calls these.
async function reload(selectId) {
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
