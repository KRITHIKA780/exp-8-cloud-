(() => {
const API = '/api';
const user = JSON.parse(localStorage.getItem('user') || 'null');
if (!user || user.role !== 'admin') window.location.href = '/frontend/index.html';

const headers = { 'X-User-Id': String(user.id), 'Content-Type': 'application/json' };

fetch(`${API}/admin/stats`, { headers }).then((response) => response.json()).then((stats) => {
  const target = document.querySelector('#stats');
  if (!target || stats.error) {
    if (target) target.textContent = stats.error || 'Unable to load stats.';
    return;
  }
  target.innerHTML = Object.entries(stats).map(([label, value]) => `<div><strong>${value}</strong><span>${label.replaceAll('_', ' ')}</span></div>`).join('');
}).catch(() => {
  document.querySelector('#stats').textContent = 'Backend unavailable.';
});

async function loadNotifications() {
  const target = document.querySelector('#notifications');
  if (!target) return;
  try {
    const [notificationResponse, loginResponse] = await Promise.all([
      fetch(`${API}/admin/notifications`, { headers }),
      fetch(`${API}/admin/login-alerts`, { headers }),
    ]);
    const notes = await notificationResponse.json();
    const loginAlerts = await loginResponse.json();
    if (!notificationResponse.ok || !loginResponse.ok) throw new Error(notes.error || loginAlerts.error || 'Unable to load alerts.');
    const combined = [
      ...(Array.isArray(notes) ? notes.map((note) => ({ ...note, kind: 'item' })) : []),
      ...(Array.isArray(loginAlerts) ? loginAlerts.map((event) => ({ ...event, kind: 'login' })) : []),
    ].sort((first, second) => String(second.created_at).localeCompare(String(first.created_at)));
    if (!combined.length) {
      target.innerHTML = '<p>No alerts yet. New student lost reports will appear here.</p>';
      return;
    }
    target.innerHTML = combined.map((note) => `
      <article class="notice ${!note.is_read ? 'unread' : ''}">
        <strong>${note.kind === 'login' ? (note.event_type === 'registration' ? 'NEW STUDENT' : (note.is_read ? 'STUDENT LOGIN' : 'NEW STUDENT LOGIN')) : (note.is_read ? 'UPDATE' : 'NEW ALERT')}</strong>
        <p>${note.kind === 'login' ? (note.event_type === 'registration' ? `${note.name} registered a student account.` : `${note.name} signed in to the ${note.role} view.`) : note.message}</p>
        <small>${note.kind === 'login' ? note.email : `${note.title} · ${note.location}`}</small>
      </article>
    `).join('');
  } catch (error) {
    target.innerHTML = `<p>${error.message || 'Backend unavailable.'}</p>`;
  }
}

document.querySelector('#mark-read')?.addEventListener('click', async () => {
  await fetch(`${API}/admin/notifications/read`, { method: 'PATCH', headers });
  loadNotifications();
  window.location.reload();
});

loadNotifications();

async function loadClaims() {
  const target = document.querySelector('#claims');
  if (!target) return;
  try {
    const response = await fetch(`${API}/admin/claims`, { headers });
    const claims = await response.json();
    target.innerHTML = claims.length ? claims.map((claim) => `
      <article class="notice ${claim.status === 'pending' ? 'unread' : ''}">
        <strong>${claim.status.toUpperCase()} · ${claim.title}</strong>
        <p>${claim.message}</p>
        <small>Claimed by ${claim.claimant_name} · ${claim.claimant_email}</small>
        ${claim.status === 'pending' ? `<div class="claim-actions"><button class="button small" data-claim-action="${claim.id}" data-status="approved">Approve</button><button class="button small secondary" data-claim-action="${claim.id}" data-status="rejected">Reject</button></div>` : ''}
      </article>
    `).join('') : '<p>No claim requests yet.</p>';
  } catch (error) {
    target.innerHTML = '<p>Backend unavailable.</p>';
  }
}

document.querySelector('#claims')?.addEventListener('click', async (event) => {
  const button = event.target.closest('[data-claim-action]');
  if (!button) return;
  await fetch(`${API}/admin/claims/${button.dataset.claimAction}`, {
    method: 'PATCH',
    headers,
    body: JSON.stringify({ status: button.dataset.status }),
  });
  loadClaims();
});

loadClaims();
})();
