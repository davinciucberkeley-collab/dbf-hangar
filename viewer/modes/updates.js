// Updates mode: weekly updates from index.updates, newest first.
export default async function render({ state, el, h }) {
  const box = el.querySelector('.panel'); box.replaceChildren();
  const weeks = state.index.updates || [];
  if (!weeks.length) box.append(h('p', { class: 'muted' }, 'No weekly updates yet.'));
  for (const w of weeks) {
    box.append(h('h3', {}, w.week), h('ul', {}, w.entries.map((e) => h('li', {}, h('b', {}, e.person), ': ', e.changed,
      e.link ? [' (', /^https?:\/\//.test(e.link) ? h('a', { href: e.link, rel: 'noopener' }, e.link) : e.link, ')'] : null))));
  }
  el.dataset.ready = '1';
}
