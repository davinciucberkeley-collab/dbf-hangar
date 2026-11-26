// Per-part check status derived from scorecard rows and parts.json. Pure: no DOM.
import { STATUS_ORDER } from '../lib.js';

const okId = (s) => typeof s === 'string' && s !== '' && !/[\s&]/.test(s);

// Part ids a scorecard row names, kept only when parts.json knows them (old index files carry free text).
export function rowParts(row, parts) {
  const d = row?.data;
  if (!d || typeof d !== 'object') return [];
  const known = new Set((parts?.parts || []).map((p) => p.id));
  const atts = parts?.attachments || [];
  const raw = [];
  if (okId(d.component)) raw.push(d.component);
  if (Array.isArray(d.parts)) raw.push(...d.parts.filter(okId));
  if (Array.isArray(d.pair) && d.pair.length === 2 && d.pair.every(okId)) raw.push(...d.pair);
  for (const j of Array.isArray(d.joint) ? d.joint : d.joint != null ? [d.joint] : []) {
    if (typeof j !== 'string') continue;
    const a = atts.find((x) => x.label === j);
    if (a) raw.push(a.parent, a.child);
  }
  if (Array.isArray(d.link_pairs)) for (const p of d.link_pairs) if (Array.isArray(p)) raw.push(...p.filter(okId));
  const out = [];
  for (const id of raw) if (known.has(id) && !out.includes(id)) out.push(id);
  return out;
}

const rank = (s) => STATUS_ORDER[s] ?? 9;
const rowsOf = (scorecard) => (scorecard?.tiers || []).flatMap((t) => t.results || []);

export function partStatus(scorecard, parts) {
  const map = new Map();
  for (const r of rowsOf(scorecard)) {
    if (r.status !== 'FAIL' && r.status !== 'WARN') continue;
    if (r.status === 'WARN' && r.data?.raw_status === 'SKIP') continue; // report-only wrapper of a SKIP: not judged, so no colour
    for (const id of rowParts(r, parts)) {
      if (!map.has(id)) map.set(id, { status: r.status, rows: [] });
      const e = map.get(id);
      if (r.status === 'FAIL') e.status = 'FAIL';
      e.rows.push({ check_id: r.check_id, status: r.status, message: r.message });
    }
  }
  for (const e of map.values()) e.rows.sort((a, b) => rank(a.status) - rank(b.status));
  return map;
}

export function partChecks(scorecard, parts, id) {
  return rowsOf(scorecard).filter((r) => rowParts(r, parts).includes(id)).sort((a, b) => rank(a.status) - rank(b.status));
}
