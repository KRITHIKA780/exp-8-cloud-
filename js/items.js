(() => {
const API = '/api';
const user = JSON.parse(localStorage.getItem('user') || 'null');

function statusLabel(item) {
  if (item.status === 'found') return 'FOUND';
  if (item.status === 'resolved') return 'RETURNED';
  return item.report_type === 'lost' ? 'STILL MISSING' : 'FOUND ITEM';
}

function itemCard(item, options = {}) {
  const photo = item.image
    ? `<img src="${item.image}" alt="${item.title}">`
    : `<div class="photo-fallback">No photo</div>`;
  const adminAction = options.admin && item.report_type === 'lost' && item.status === 'open'
    ? `<button class="button small" type="button" data-mark-found="${item.id}">Item was found</button>`
    : '';
  const studentFoundAction = user?.role === 'student' && item.report_type === 'lost' && item.status === 'open'
    ? `<button class="button small secondary" type="button" data-student-found="${item.id}">I found this item</button>`
    : '';
  const claimAction = user?.role === 'student' && item.report_type === 'found' && item.status === 'open'
    ? `<button class="button small secondary" type="button" data-claim="${item.id}">Claim this item</button>`
    : '';
  return `
    <article class="item-card" data-status="${item.status}">
      ${photo}
      <span>${item.report_type.toUpperCase()} · ${statusLabel(item)}</span>
      <h2>${item.title}</h2>
      <p>${item.description}</p>
      <small>Missed / found at ${item.location} · ${item.category} · ${item.reporter || 'Student'}</small>
      ${adminAction}${studentFoundAction}${claimAction}
    </article>
  `;
}

const reportForm = document.querySelector('[data-report]');
if (reportForm) reportForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const message = reportForm.querySelector('.form-message');
  if (!user) { message.textContent = 'Please sign in before creating a report.'; return; }
  const data = new FormData(reportForm);
  data.set('report_type', reportForm.dataset.report);
  data.set('user_id', user.id);
  try {
    const response = await fetch(`${API}/items`, {method:'POST', body:data});
    const result = await response.json();
    message.textContent = result.message || result.error;
    if (response.ok) reportForm.reset();
  } catch (error) {
    message.textContent = 'Backend is not running. Start Flask and try again.';
  }
});

async function loadItems(extra = {}) {
  const target = document.querySelector('#items');
  if (!target) return;
  const params = new URLSearchParams();
  const search = document.querySelector('#item-search');
  const typeFilter = document.querySelector('#type-filter');
  if (search?.value.trim()) params.set('q', search.value.trim());
  if (typeFilter?.value) params.set('type', typeFilter.value);
  if (extra.mine && user) params.set('q', params.get('q') || '');
  try {
    const response = await fetch(`${API}/items?${params.toString()}`);
    let items = await response.json();
    if (location.pathname.includes('my-reports') && user) {
      items = items.filter((item) => Number(item.user_id) === Number(user.id));
    }
    target.innerHTML = items.length
      ? items.map((item) => itemCard(item, extra)).join('')
      : '<p>No matching items yet.</p>';
  } catch (error) {
    target.innerHTML = '<p>Backend is not running. Start Flask and refresh this page.</p>';
  }
}

async function loadClaims() {
  const target = document.querySelector('#claims');
  if (!target || !user) return;
  try {
    const response = await fetch(`${API}/claims/${user.id}`);
    const claims = await response.json();
    target.innerHTML = claims.length
      ? claims.map((claim) => `<article class="item-card"><span>${claim.status.toUpperCase()}</span><h2>${claim.title}</h2><p>${claim.message}</p></article>`).join('')
      : '<p>No claims found.</p>';
  } catch (error) {
    target.innerHTML = '<p>Backend is not running. Start Flask and refresh this page.</p>';
  }
}

const searchForm = document.querySelector('#search-form');
if (searchForm) {
  searchForm.addEventListener('submit', (event) => {
    event.preventDefault();
    loadItems({ admin: Boolean(document.querySelector('[data-admin-board]')) });
  });
}

document.querySelector('#items')?.addEventListener('click', async (event) => {
  const button = event.target.closest('[data-mark-found]');
  if (!button || !user) return;
  const foundByName = window.prompt('Enter the student name who found this item:');
  if (!foundByName?.trim()) return;
  await fetch(`${API}/items/${button.dataset.markFound}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', 'X-User-Id': user.id },
    body: JSON.stringify({ status: 'found', found_by_name: foundByName.trim() }),
  });
  loadItems({ admin: true });
});

document.querySelector('#items')?.addEventListener('click', async (event) => {
  const button = event.target.closest('[data-student-found]');
  if (!button || !user) return;
  const response = await fetch(`${API}/items/${button.dataset.studentFound}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json', 'X-User-Id': user.id },
    body: JSON.stringify({ status: 'found', found_by_name: user.name }),
  });
  const result = await response.json();
  window.alert(result.message || result.error || 'Item updated');
  if (response.ok) loadItems();
});

document.querySelector('#items')?.addEventListener('click', async (event) => {
  const button = event.target.closest('[data-claim]');
  if (!button || !user) return;
  const message = window.prompt('Tell the admin how you can identify this item:');
  if (!message?.trim()) return;
  const response = await fetch(`${API}/claims`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ item_id: button.dataset.claim, claimant_id: user.id, message: message.trim() }),
  });
  const result = await response.json();
  window.alert(result.message || result.error || 'Claim submitted');
  if (response.ok) button.remove();
});

loadItems({ admin: Boolean(document.querySelector('[data-admin-board]')) });
loadClaims();
})();
