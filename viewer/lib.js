// Helpers shared by app.js, every mode and modes/edit.js.
export const TIERS = [0, 1, 2, 3, 4, 5];
export const STATUS_ORDER = { FAIL: 0, WARN: 1, 'NOT CHECKED': 1, PASS: 2, SKIP: 3 };
export const cache = { json: new Map(), glb: new Map() };

export function h(tag, attrs = {}, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v == null || v === false) continue;
    if (k === 'class') el.className = v;
    else if (k.startsWith('on')) el.addEventListener(k.slice(2), v);
    else if (k === 'value') el.value = v;
    else el.setAttribute(k, v === true ? '' : v);
  }
  for (const kid of kids.flat()) if (kid != null && kid !== false) el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  return el;
}
export const $ = (id) => document.getElementById(id);
export const fmt = (v, n = 1) => (v == null || Number.isNaN(v) ? '–' : Number(v).toFixed(n));
export function getJSON(path) {
  if (!cache.json.has(path)) {
    cache.json.set(path, fetch('data/' + path).then((r) => { if (!r.ok) throw new Error(`${path}: HTTP ${r.status}`); return r.json(); }));
  }
  return cache.json.get(path);
}
export async function api(path, body) {
  const r = await fetch('api/' + path, body === undefined ? {} : {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body),
  });
  const data = await r.json().catch(() => ({ error: `HTTP ${r.status}` }));
  if (!r.ok || data.error) throw new Error(data.error || `HTTP ${r.status}`);
  return data;
}
export async function opCall(name, params = {}) {
  const r = await fetch('api/op/' + name, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(params) });
  const body = await r.json().catch(() => ({ ok: false, messages: [`HTTP ${r.status}`] }));
  if (!body.ok) throw new Error((body.messages || []).join('; ') || `HTTP ${r.status}`);
  return body.data;
}
