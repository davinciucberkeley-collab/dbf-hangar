// Ledger mode: index.ledger as a filterable table (open first).
export default async function render({ state, el, h }) {
  const box = el.querySelector('.panel'); box.replaceChildren();
  const items = state.index.ledger || [];
  if (!items.length) box.append(h('p', { class: 'muted' }, 'No ledger items.'));
  else {
    const pick = (k) => h('select', { 'aria-label': k, onchange: draw }, h('option', { value: '' }, 'all ' + k),
      [...new Set(items.map((i) => i[k]))].sort().map((v) => h('option', { value: v }, v)));
    const [kind, status] = [pick('kind'), pick('status')];
    const body = h('tbody');
    function draw() {
      const rows = items.filter((i) => (!kind.value || i.kind === kind.value) && (!status.value || i.status === status.value))
        .sort((a, b) => (a.status === 'open' ? 0 : 1) - (b.status === 'open' ? 0 : 1) || a.status.localeCompare(b.status) || a.id.localeCompare(b.id));
      body.replaceChildren(...rows.map((i) => h('tr', {}, ['id', 'kind', 'status', 'owner', 'due'].map((k) => h('td', {}, i[k] ?? '')), h('td', {}, i.text ?? i.summary ?? ''))));
    }
    draw();
    box.append(h('div', { class: 'row' }, kind, status), h('table', { class: 'cmp' },
      h('thead', {}, h('tr', {}, ['id', 'kind', 'status', 'owner', 'due', 'text'].map((c) => h('th', {}, c)))), body));
  }
  el.dataset.ready = '1';
}
