// Scorecard rows as plain text and groups (U19.2). Pure functions: no DOM, no wording of their own beyond group names.
import { STATUS_ORDER } from '../lib.js';
import { rowParts, isDesignLevel } from '../vp/status.js';

const rank = (s) => STATUS_ORDER[s] ?? 9;
const family = (id) => String(id).split('.').slice(0, 2).join('.');
const worst = (statuses) => statuses.reduce((a, s) => (rank(s) < rank(a) ? s : a), 'SKIP');

const fallbackText = (r) => ({
  check_id: r.check_id, status: r.status, title: r.check_id, sentence: r.message, hint: '', details: '', parts: [], group: 'problem',
  source: '', report_only: false, would_be: '', not_applicable: false, fold: false, fold_noun: 'rows', fallback: true,
});

// One array per tier, one text object per row; a tier whose texts do not line up with the scorecard falls back on its own.
export function alignTexts(sc, rowsJson) {
  return (sc.tiers || []).map((t, i) => {
    const texts = rowsJson?.tiers?.[i]?.rows;
    const ok = Array.isArray(texts) && texts.length === t.results.length && texts.every((x, j) => x.check_id === t.results[j].check_id);
    return t.results.map((r, j) => (ok ? texts[j] : fallbackText(r)));
  });
}

function flat(sc, texts) {
  const out = [];
  (sc.tiers || []).forEach((t, i) => t.results.forEach((row, j) => out.push({ row, text: texts[i][j], tier: t, index: j })));
  return out;
}

function foldEntries(entries) {
  const fams = new Map();
  for (const e of entries) if (e.text.fold) { const k = family(e.row.check_id); fams.set(k, (fams.get(k) || []).concat(e)); }
  const out = [], done = new Set();
  for (const e of entries) {
    const k = family(e.row.check_id), members = e.text.fold ? fams.get(k) : null;
    if (!members || members.length < 3) { out.push(e); continue; }
    if (done.has(k)) continue;
    done.add(k);
    out.push({ fold: true, title: `${e.text.title}: ${members.length} ${e.text.fold_noun}`, status: worst(members.map((m) => m.row.status)), rows: members });
  }
  return out;
}

const PROBLEM = [
  ['fail', 'Needs fixing', 'FAIL', (e) => e.row.status === 'FAIL'],
  ['warn', 'Warnings', 'WARN', (e) => e.row.status === 'WARN'],
  ['skip', 'Not checked', 'SKIP', (e) => e.row.status === 'SKIP' && !e.text.not_applicable],
  ['na', 'Not applicable', 'SKIP', (e) => e.text.not_applicable && e.row.status !== 'FAIL' && e.row.status !== 'WARN'],
  ['pass', 'Passing', 'PASS', (e) => e.row.status === 'PASS'],
];

export function groupRows(sc, texts, mode, parts) {
  const all = flat(sc, texts);
  if (mode === 'tier') {
    return (sc.tiers || []).map((t, i) => ({
      key: 'T' + t.tier, title: `T${t.tier} ${t.name}`, status: t.status,
      entries: all.filter((e) => e.tier === t).sort((a, b) => rank(a.row.status) - rank(b.row.status)),
    }));
  }
  if (mode === 'part') {
    const groups = new Map();
    for (const e of all) {
      if (e.row.status === 'PASS') continue;
      const ids = rowParts(e.row, parts);
      const keys = !ids.length || isDesignLevel(e.row, parts) ? [['', 'Whole aircraft']]
        : ids.map((id) => [id, e.text.parts.find((p) => p.id === id)?.label ?? id]);
      for (const [id, label] of keys) {
        if (!groups.has(id)) groups.set(id, { key: id || 'whole', title: label, status: 'SKIP', entries: [] });
        const g = groups.get(id); g.entries.push(e); g.status = worst([g.status, e.row.status]);
      }
    }
    return [...groups.values()].sort((a, b) => rank(a.status) - rank(b.status));
  }
  return PROBLEM.map(([key, title, status, test]) => ({ key, title, status, entries: foldEntries(all.filter(test)) })).filter((g) => g.entries.length);
}
