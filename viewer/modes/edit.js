// Plane Studio edit controls (new, copy, edit, import, check, stress, download). Loaded only when the page is served
// by `plane studio` (index.json has "studio": true); the GitHub Pages build never loads it. Every control carries
// data-edit. Every action calls the local API, which runs the same core library as the CLI and CI.
import { h, $, api, opCall as op, opRaw, getJSON, STATUS_ORDER } from '../lib.js';

let V;
let ping = {};
let lastRev = -1;
let lastJobState = '';
const results = {}; // design id -> {validate?, pr?}; cleared for a design when it is saved

const designPath = (id) => ping.designs_dir + '/' + id;
const keyOf = (path) => path.map((s, i) => typeof s === 'string' ? (i ? '.' : '') + s : `[${s.id}]`).join('');

function toast(text, kind = '') {
  const t = h('div', { class: 'toast ' + kind, role: 'status' }, text);
  $('toasts').append(t);
  setTimeout(() => t.remove(), kind === 'err' ? 9000 : 4000);
}
// A toast that holds a link: it stays until the person dismisses it.
function toastLink(text, url) {
  const t = h('div', { class: 'toast', role: 'status' }, text + ' ',
    /^https?:\/\//.test(url) ? h('a', { href: url, target: '_blank', rel: 'noopener' }, url) : url,
    h('button', { class: 'icon', 'aria-label': 'Dismiss', onclick: () => t.remove() }, '×'));
  $('toasts').append(t);
}

// ---------- dialogs ----------
function dialog(title, body, actions) {
  const err = h('div', { class: 'dlg-err', hidden: true });
  const dlg = h('dialog', { class: 'dlg' },
    h('form', { method: 'dialog' },
      h('header', {}, h('h2', {}, title), h('button', { class: 'icon', value: 'cancel', 'aria-label': 'Close', type: 'submit' }, '×')),
      h('div', { class: 'dlg-body' }, body), err,
      h('footer', {}, h('button', { value: 'cancel', type: 'submit', class: 'ghost' }, 'Cancel'), actions)));
  dlg.showError = (m) => { err.textContent = m; err.hidden = !m; };
  dlg.addEventListener('close', () => dlg.remove());
  document.body.append(dlg);
  dlg.showModal();
  return dlg;
}
function field(label, input, hint) {
  return h('label', { class: 'field' }, h('span', { class: 'lbl' }, label), input, hint ? h('span', { class: 'hint' }, hint) : null);
}
function primary(label, onclick, extra = {}) {
  return h('button', { type: 'button', class: 'primary', ...extra, onclick: async (e) => {
    const b = e.currentTarget; const dlg = b.closest('dialog');
    b.disabled = true; dlg.showError('');
    try { await onclick(dlg); } catch (err) { dlg.showError(err.message); } finally { b.disabled = false; }
  } }, label);
}
const slug = (s) => s.toLowerCase().trim().replace(/[^a-z0-9_-]+/g, '-').replace(/^-+|-+$/g, '');

function newDesignDialog(fromId) {
  const designs = V.designs();
  const from = h('select', {}, designs.map((d) => h('option', { value: d.id, selected: d.id === (fromId || V.selected()) }, d.name ? `${d.name} (${d.id})` : d.id)));
  const name = h('input', { type: 'text', placeholder: 'e.g. concept-a-bigger-wing', autofocus: true });
  dialog('New design', [
    field('Start from', from, 'Copies its file and 3D parts; the original is not touched.'),
    field('Name', name, 'Lowercase letters, numbers and dashes.'),
  ], primary('Create', async (dlg) => {
    const id = slug(name.value);
    if (!id) throw new Error('Give the new design a name.');
    await op('design.new', { new_id: id, template: from.value });
    dlg.close(); toast(`Created ${id}. Checking it now.`);
    await V.reload(id);
  }));
}

function importDialog() {
  const root = h('input', { type: 'text', value: ping.dbf_root_guess || '', placeholder: 'C:\\Users\\you\\Documents\\dbf-combined' });
  const concept = h('input', { type: 'text', value: 'A', maxlength: 4, style: 'width:70px' });
  const id = h('input', { type: 'text', value: 'concept-a' });
  const warn = h('p', { class: 'hint warn' });
  const upd = () => { const v = slug(id.value); warn.textContent = V.designs().some((d) => d.id === v) ? `“${v}” already exists and will be replaced by the fresh import.` : ''; };
  id.addEventListener('input', upd); upd();
  dialog('Import from DBF-Combined', [
    h('p', { class: 'muted' }, 'Rebuilds a concept from Dillon’s CAD scripts as exact solids. It only reads that folder.'),
    field('DBF-Combined folder', root, 'Paste the folder path from File Explorer (right-click the folder › Copy as path).'),
    h('div', { class: 'row' }, field('Concept', concept), field('Save as', id)), warn,
  ], primary('Import', async (dlg) => {
    await api('import-dbf', { root: root.value, concept: concept.value, id: slug(id.value) });
    dlg.close(); toast('Import started. It shows up in the list when it is done.');
  }));
}

// ---------- editor: forms for the common edits, the raw file for everything else ----------
const num = (v) => (v === '' || v == null ? null : Number(v));
function input(value, attrs = {}) {
  const el = h('input', { type: attrs.type || 'number', step: 'any', class: 'cell', ...attrs, value: value ?? '' });
  el.dataset.orig = value ?? '';
  return el;
}
function select(value, options, attrs = {}) {
  const opts = [...new Set([...(value ? [value] : []), ...options])];
  const el = h('select', { class: 'cell', ...attrs }, (value ? [] : [h('option', { value: '' }, '—')]).concat(opts.map((o) => h('option', { value: o, selected: o === value }, o))));
  el.dataset.orig = value ?? '';
  return el;
}
const changed = (el) => String(el.value) !== String(el.dataset.orig);

async function editDialog(id) {
  const d = V.designs().find((x) => x.id === id);
  const [{ data, enums }, , sc] = await Promise.all([
    api('design?id=' + encodeURIComponent(id)), op('design.get', { path: designPath(id) }),
    d?.scorecard ? getJSON(d.scorecard).catch(() => null) : null]);
  const failMsgs = (sc?.tiers || []).flatMap((t) => t.results).filter((r) => r.status === 'FAIL').map((r) => r.message);
  const failsFor = (jid) => failMsgs.filter((m) => m.includes(jid + ':') || m.includes(jid + ' '));
  const edits = []; // {el, path, kind}
  const track = (el, path, kind = 'num') => { edits.push({ el, path, kind }); el.addEventListener('input', () => el.classList.toggle('dirty', changed(el))); el.addEventListener('change', () => el.classList.toggle('dirty', changed(el))); return el; };

  // Overview
  const req = data.requirements || {};
  const overview = h('div', { class: 'tabpane' },
    h('div', { class: 'grid2' },
      field('Name', track(input(data.name, { type: 'text' }), ['name'], 'text')),
      field('Status', track(select(data.status, enums.status), ['status'], 'text'))),
    field('Description', track(Object.assign(h('textarea', { class: 'cell desc', rows: 3 }), { value: data.description || '' }), ['description'], 'text')),
    h('h3', {}, 'Requirements'),
    h('div', { class: 'grid3' }, enums.requirements.map((k) => field(k.replace(/_/g, ' '), track(input(req[k]), ['requirements', k])))));
  overview.querySelector('textarea').dataset.orig = data.description || '';

  // Parts
  const comps = data.components || [];
  const partRows = comps.map((c) => {
    const pos = Array.isArray(c.position) ? c.position : [null, null, null];
    const px = pos.map((v) => input(v, { class: 'cell xs' }));
    const posEdit = { el: px[0], path: ['components', { id: c.id }, 'position'], kind: 'pos', els: px };
    px.forEach((e) => e.addEventListener('input', () => e.classList.toggle('dirty', changed(e))));
    edits.push(posEdit);
    return h('tr', { 'data-q': `${c.id} ${c.type} ${c.description || ''}`.toLowerCase() },
      h('td', {}, h('code', {}, c.id), c.description ? h('div', { class: 'hint' }, c.description) : null),
      h('td', {}, c.type),
      h('td', {}, track(input(c.mass_g, { class: 'cell sm' }), ['components', { id: c.id }, 'mass_g'])),
      h('td', { class: 'xyz' }, px),
      h('td', {}, track(select(c.manufacturing?.method, enums.manufacturing), ['components', { id: c.id }, 'manufacturing', 'method'], 'text')));
  });
  const partFilter = h('input', { type: 'search', placeholder: `Filter ${comps.length} parts`, oninput: (e) => { const q = e.target.value.toLowerCase(); partRows.forEach((r) => (r.hidden = q && !r.dataset.q.includes(q))); } });
  const parts = h('div', { class: 'tabpane', hidden: true }, partFilter,
    h('table', { class: 'edit' }, h('thead', {}, h('tr', {}, ['Part', 'Type', 'Mass (g)', 'Position x, y, z (mm)', 'Made by'].map((t) => h('th', {}, t)))), h('tbody', {}, partRows)));

  // Joints
  const atts = data.attachments || [];
  const jointRows = atts.map((a) => {
    const f = failsFor(a.id);
    return h('tr', { class: f.length ? 'failing' : '', 'data-q': `${a.id} ${a.parent} ${a.child} ${a.method} ${f.length ? 'failing' : ''} ${a.rating_basis || ''}`.toLowerCase() },
      h('td', {}, h('code', {}, a.id), f.map((m) => h('div', { class: 'hint fail' }, m))),
      h('td', {}, h('span', { class: 'mono small' }, `${a.parent} → ${a.child}`)),
      h('td', {}, track(select(a.method, enums.joint_method), ['attachments', { id: a.id }, 'method'], 'text')),
      h('td', {}, track(input(a.rated_load_n, { class: 'cell sm' }), ['attachments', { id: a.id }, 'rated_load_n'])),
      h('td', {}, track(select(a.rating_basis, enums.rating_basis), ['attachments', { id: a.id }, 'rating_basis'], 'text')));
  });
  const nFail = jointRows.filter((r) => r.classList.contains('failing')).length;
  const jointFilter = h('input', { type: 'search', placeholder: `Filter ${atts.length} joints (try “failing” or “placeholder”)`, oninput: (e) => { const q = e.target.value.toLowerCase(); jointRows.forEach((r) => (r.hidden = q && !q.split(/\s+/).every((t) => r.dataset.q.includes(t)))); } });
  const joints = h('div', { class: 'tabpane', hidden: true }, jointFilter,
    h('table', { class: 'edit' }, h('thead', {}, h('tr', {}, ['Joint', 'Connects', 'Method', 'Strength (N)', 'Strength source'].map((t) => h('th', {}, t)))), h('tbody', {}, jointRows)));

  const panes = { Overview: overview, Parts: parts, [`Joints${nFail ? ` (${nFail} failing)` : ''}`]: joints };
  const tabs = h('div', { class: 'seg tabs' }, Object.entries(panes).map(([name, pane], i) => h('button', { type: 'button', class: i ? '' : 'active', onclick: (e) => {
    tabs.querySelectorAll('button').forEach((b) => b.classList.toggle('active', b === e.currentTarget));
    Object.values(panes).forEach((p) => (p.hidden = p !== pane));
  } }, name)));
  const kindSel = h('select', { 'data-testid': 'save-kind' }, ['modify', 'subtract', 'add'].map((k) => h('option', { value: k, selected: k === 'modify' }, k)));
  const whyIn = h('input', { type: 'text', 'data-testid': 'save-why', placeholder: 'One line: why this change' });

  const dlg = dialog(`Edit ${d?.name || id}`, [
    h('p', { class: 'muted' }, 'Change values, then Save.'), tabs, overview, parts, joints,
    h('div', { class: 'row' }, field('Kind', kindSel, 'add: the field was blank; subtract: you removed or reduced something'), field('Why', whyIn)),
  ], primary('Save', async (dd) => {
    const BLANK = 'Blank values are not supported here. Type a value.';
    const pairs = [];
    for (const e of edits) {
      if (e.kind === 'pos') {
        if (!e.els.some(changed)) continue;
        const v = e.els.map((x) => num(x.value));
        if (v.some((x) => x == null)) throw new Error(BLANK);
        if (v.some(Number.isNaN)) throw new Error(`${e.path[1].id}: not a number`);
        v.forEach((x, i) => pairs.push({ key: `${keyOf(e.path)}[${i}]`, value: String(x) }));
      } else if (changed(e.el)) {
        if (e.kind === 'num') {
          const v = num(e.el.value);
          if (v == null) throw new Error(BLANK);
          if (Number.isNaN(v)) throw new Error(`Not a number: ${e.el.value}`);
          pairs.push({ key: keyOf(e.path), value: String(v) });
        } else {
          if (e.el.value === '') throw new Error(BLANK);
          pairs.push({ key: keyOf(e.path), value: JSON.stringify(e.el.value) });
        }
      }
    }
    if (!pairs.length) { dd.close(); return; }
    const why = whyIn.value.trim();
    if (!why) throw new Error('Say why in one line.');
    await op('design.set', { path: designPath(id), key: pairs[0].key, value: pairs[0].value, why, kind: kindSel.value,
      also: pairs.slice(1).map((p) => p.key + '=' + p.value) });
    delete results[id];
    dd.close(); toast(`Saved ${id} (${pairs.length} change${pairs.length > 1 ? 's' : ''}). Click Validate to see the checks.`);
    await V.reload(id);
  }, { 'data-testid': 'save', 'data-edit': true }));
  dlg.classList.add('wide');
}

// ---------- stress check (OpenCAE) ----------
function feaSetup(oc, after) {
  const py = h('input', { type: 'text', value: oc?.python || '', placeholder: 'C:\\Users\\you\\.conda\\envs\\qt_test\\python.exe' });
  const root = h('input', { type: 'text', value: oc?.root || '', placeholder: 'C:\\Users\\you\\Documents\\OpenCAE-Studio' });
  dialog('Connect OpenCAE', [
    h('p', { class: 'muted' }, 'The stress check runs in OpenCAE Studio. Point the app at it once.'),
    field('OpenCAE’s Python', py, 'python.exe of the environment that runs OpenCAE (the one with PySide6, gmsh and OCP). Tip: in that environment run  where python'),
    field('OpenCAE folder', root, 'The folder that contains the opencae folder and launch_opencae.bat.'),
  ], primary('Save', async (dlg) => {
    await api('fea-setup', { python: py.value, root: root.value });
    dlg.close(); toast('OpenCAE connected.'); after?.();
  }));
}

async function feaDialog(id) {
  const st = await api('fea?id=' + encodeURIComponent(id));
  if (!st.opencae.found) return feaSetup(st.opencae, () => feaDialog(id));
  const badge = (r) => !r.status ? h('span', { class: 'badge NONE' }, 'not run')
    : r.up_to_date === false ? h('span', { class: 'badge WARN' }, 'out of date')
    : r.status === 'NOT CHECKED' ? h('span', { class: 'badge WARN', title: (r.cases || []).map((c) => c.message).filter(Boolean).join('\n') }, 'not checked')
    : h('span', { class: 'badge ' + (r.status === 'ERROR' ? 'FAIL' : r.status) }, r.status === 'FAIL' && r.error ? 'error' : r.status);
  const boxes = [];
  const rows = st.parts.map((r) => {
    const cb = h('input', { type: 'checkbox', checked: !r.status || r.up_to_date === false || r.status === 'FAIL' });
    cb.dataset.part = r.part; boxes.push(cb);
    const worst = (r.cases || []).filter((c) => c.safety_factor_at_ultimate != null).sort((a, b) => a.safety_factor_at_ultimate - b.safety_factor_at_ultimate)[0];
    return h('tr', { class: r.status === 'FAIL' ? 'failing' : '' },
      h('td', {}, cb), h('td', {}, h('code', {}, r.part), h('div', { class: 'hint' }, r.description)),
      h('td', {}, badge(r)),
      h('td', { class: 'mono small' }, worst ? `${worst.max_von_mises_away_mpa} MPa · SF ${worst.safety_factor_at_ultimate} (${worst.name})` : (r.error ? r.error.slice(0, 80) : '—')),
      h('td', {}, (r.files || []).filter((f) => f.kind !== 'ocae').map((f) => h('a', { href: `api/fea-file?id=${encodeURIComponent(id)}&part=${encodeURIComponent(r.part)}&name=${encodeURIComponent(f.name)}`, target: f.kind === 'html' ? '_blank' : null, class: 'filelink' }, `${/thrust/.test(f.name) ? 'thrust' : 'landing'} ${f.kind === 'html' ? 'report' : '(ParaView)'}`))));
  });
  const allow = st.allowable_mpa, uf = st.ultimate_factor;
  const dlg = dialog(`Stress check: ${id}`, [
    h('p', { class: 'muted' }, `Each printed part is meshed and solved in OpenCAE (CalculiX) for two load cases: the joint loads from the landing drop test, and hover at full thrust, both ×${uf}. It passes when the stress away from the clamps stays under ${allow} MPa (printed PETG, interlayer strength). Expect a few seconds to a few minutes per part.`),
    h('div', { class: 'row' }, h('button', { type: 'button', class: 'btn', onclick: () => boxes.forEach((b) => (b.checked = true)) }, 'All'),
      h('button', { type: 'button', class: 'btn', onclick: () => boxes.forEach((b) => (b.checked = false)) }, 'None'),
      h('button', { type: 'button', class: 'btn', 'data-edit': true, onclick: () => { dlg.close(); feaSetup(st.opencae); } }, 'OpenCAE settings')),
    h('div', { class: 'tabpane' }, h('table', { class: 'edit' }, h('thead', {}, h('tr', {}, ['', 'Part', 'Result', 'Worst case', 'Files'].map((t) => h('th', {}, t)))), h('tbody', {}, rows))),
  ], primary('Run selected', async (d) => {
    const parts = boxes.filter((b) => b.checked).map((b) => b.dataset.part);
    if (!parts.length) throw new Error('Tick at least one part.');
    await api('fea', { id, parts });
    d.close(); toast(`Stress check started for ${parts.length} part${parts.length > 1 ? 's' : ''}. Progress shows on the left.`);
  }, { 'data-edit': true }));
  dlg.classList.add('wide');
}

// ---------- action bar on the scorecard ----------
const EXPORTS = [
  ['glb', '3D model (.glb)', 'Opens in Windows 3D Viewer, Blender, web viewers'],
  ['stl', 'Parts for printing (.stl, zipped)', 'One file per part, in mm'],
  ['report', 'Scorecard report (.md)', 'For a PR, a review or Douglas'],
  ['mjcf', 'Physics sim model (MuJoCo, zipped)', ''],
  ['json', 'Design data (.json)', ''],
];
// ---------- validate and propose (results stay on the scorecard until the design is saved) ----------
function validatePanel(data) {
  const rows = data.tiers.flatMap((t) => t.results).sort((a, b) => (STATUS_ORDER[a.status] ?? 9) - (STATUS_ORDER[b.status] ?? 9));
  const nFail = rows.filter((r) => r.status === 'FAIL').length;
  return [h('h3', {}, `Validation: ${data.accepted ? 'accepted' : 'rejected'} (${nFail} FAIL)`),
    ...rows.map((r) => h('div', { class: 'result ' + r.status },
      h('div', { class: 'top' }, h('span', { class: 'badge ' + r.status }, r.status), h('span', { class: 'cid' }, r.check_id)),
      h('div', { class: 'msg' }, r.message)))];
}
function prPanel(pr) {
  const url = pr.pr_url || '';
  return [h('h3', {}, 'Pull request'),
    /^https?:\/\//.test(url) ? h('a', { 'data-testid': 'pr-link', href: url, target: '_blank', rel: 'noopener' }, url) : url,
    h('div', { class: 'muted' }, `branch ${pr.branch}`)];
}
function renderResults(box, d) {
  const r = results[d.id] || {};
  const panels = [];
  const pr = r.pr ? h('div', { class: 'studio-result', tabindex: -1, 'data-edit': true, 'data-testid': 'pr-result' }, prPanel(r.pr)) : null;
  if (pr) panels.push(pr);
  if (r.validate) panels.push(h('div', { class: 'studio-result', 'data-edit': true, 'data-testid': 'validate-result' }, validatePanel(r.validate)));
  box.querySelector('.studio-bar')?.after(...panels);
  if (r.focus) { delete r.focus; pr?.scrollIntoView({ block: 'center' }); pr?.focus(); }
}
async function validate(id, btn) {
  const label = btn.textContent;
  btn.textContent = 'Validating…'; btn.disabled = true;
  try {
    const body = await opRaw('design.validate', { path: designPath(id) });
    if (!body.data?.tiers) throw new Error((body.messages || []).join('; ') || 'Validation failed');
    results[id] = { ...results[id], validate: body.data };
    V.refresh();
  } catch (e) { toast(e.message, 'err'); } finally { btn.textContent = label; btn.disabled = false; }
}
function proposeDialog(id) {
  const titleInput = h('input', { type: 'text', 'data-testid': 'propose-title', value: 'Edit ' + id });
  dialog('Propose change', [
    h('p', { class: 'muted' }, `Commits the saved changes in designs/${id} on a new branch and opens a pull request against main.`),
    field('Title', titleInput, 'One line; becomes the PR title.'),
  ], primary('Open pull request', async (dlg) => {
    const title = titleInput.value.trim();
    if (!title) throw new Error('Give the change a title.');
    const pr = await op('design.propose', { path: designPath(id), title });
    results[id] = { ...results[id], pr, focus: true };
    dlg.close(); toastLink('Pull request opened:', pr.pr_url);
    V.refresh();
  }, { 'data-testid': 'propose-go', 'data-edit': true }));
}

function actionBar(box, d) {
  const exp = h('details', { class: 'menu' }, h('summary', { class: 'btn' }, 'Download ▾'),
    h('div', { class: 'menu-list' }, EXPORTS.map(([f, label, hint]) =>
      h('a', { href: `api/export?id=${encodeURIComponent(d.id)}&format=${f}`, download: '', onclick: () => toast('Preparing the download…') },
        h('b', {}, label), hint ? h('span', {}, hint) : null))));
  const bar = h('div', { class: 'studio-bar', 'data-edit': true },
    h('button', { class: 'btn', disabled: d.pending, onclick: async () => { await api('check', { id: d.id }); toast(`Checking ${d.id}…`); } }, d.pending ? 'Checking…' : 'Check again'),
    h('button', { class: 'btn', 'data-testid': 'btn-edit', onclick: () => editDialog(d.id).catch((e) => toast(e.message, 'err')) }, 'Edit design'),
    h('button', { class: 'btn', 'data-testid': 'btn-validate', 'data-edit': true, disabled: d.pending || d.error, title: 'Run all checks on the saved file and show the scorecard', onclick: (e) => validate(d.id, e.currentTarget) }, 'Validate'),
    h('button', { class: 'btn', 'data-testid': 'btn-propose', 'data-edit': true, title: 'Commit the saved changes on a new branch and open a pull request', onclick: () => proposeDialog(d.id) }, 'Propose change'),
    h('button', { class: 'btn', onclick: () => newDesignDialog(d.id) }, 'Make a copy'),
    h('button', { class: 'btn', onclick: () => feaDialog(d.id).catch((e) => toast(e.message, 'err')) }, 'Stress check'),
    d.error || d.pending ? null : exp);
  box.querySelector('.sub')?.after(bar);
  renderResults(box, d);
}

// ---------- jobs ----------
function renderJobs(st) {
  const box = $('jobs');
  const running = st.jobs.filter((j) => j.state === 'running' || j.state === 'queued');
  const recent = st.jobs.filter((j) => j.state === 'done' || j.state === 'error').slice(0, 3);
  const rows = recent.map((j) => h('div', { class: 'job ' + j.state, title: j.message }, j.state === 'error' ? '✕ ' : '✓ ', `${j.label}: `, h('span', { class: 'muted' }, j.message)));
  if (running.length) {
    const cur = running.find((j) => j.state === 'running') || running[0];
    rows.unshift(h('div', { class: 'job running' }, h('span', { class: 'spin' }), cur.label + (cur.message ? `: ${cur.message}` : ''), running.length > 1 ? h('span', { class: 'muted' }, ` +${running.length - 1} waiting`) : null));
  }
  box.replaceChildren(...rows);
  box.hidden = !running.length && !recent.length;
}
async function poll() {
  try {
    const st = await api('state');
    renderJobs(st);
    const sig = st.jobs.map((j) => j.id + j.state).join();
    if (st.rev !== lastRev) {
      if (lastRev !== -1) await V.reload();
      lastRev = st.rev;
    }
    for (const j of st.jobs) {
      const key = j.id + j.state;
      if (j.state === 'error' && !lastJobState.includes(key) && lastJobState) toast(`${j.label} failed: ${j.message}`, 'err');
    }
    lastJobState = sig;
    setTimeout(poll, st.busy ? 1000 : 3000);
  } catch {
    $('jobs').hidden = false;
    $('jobs').replaceChildren(h('div', { class: 'job error' }, 'Lost contact with Plane Studio. Is its window still open?'));
    setTimeout(poll, 4000);
  }
}

// ---------- boot ----------
export default async function boot(viewer) {
  V = viewer;
  V.feaDialog = feaDialog;
  ping = await api('ping').catch(() => ({}));
  document.title = 'Plane Studio';
  document.body.classList.add('studio');
  document.querySelector('.brand h1').textContent = 'Plane Studio';
  document.querySelector('.filters').before(h('div', { class: 'studio-top', 'data-edit': true },
    h('button', { class: 'btn primary', onclick: () => newDesignDialog() }, '+ New design'),
    h('button', { class: 'btn', onclick: importDialog }, 'Import'),
    h('button', { class: 'btn', title: 'Re-run every check', onclick: async () => { await api('check-all', {}); toast('Checking every design…'); } }, 'Check all')));
  document.querySelector('#sidebar footer').before(h('div', { id: 'jobs', class: 'jobs', hidden: true, 'aria-live': 'polite' }));
  document.body.append(h('div', { id: 'toasts', class: 'toasts' }));
  V.onScorecard = actionBar;
  V.studio = { op, designPath, toast, dialog, field, primary };
  V.refresh();
  poll();
  import('./move-apply.js').then((m) => m.default(V)).catch((e) => console.warn('move apply failed to load', e));
}
