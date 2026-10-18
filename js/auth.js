const API = '/api';

function currentUser() {
  return JSON.parse(localStorage.getItem('user') || 'null');
}

function logout() {
  localStorage.removeItem('user');
  window.location.href = '/frontend/index.html';
}

function requireRole(role) {
  const user = currentUser();
  if (!user) {
    window.location.href = '/frontend/index.html';
    return null;
  }
  if (role && user.role !== role) {
    window.location.href = user.role === 'admin' ? '/frontend/admin.html' : '/frontend/dashboard.html';
    return null;
  }
  return user;
}

function renderNav() {
  const user = currentUser();
  const slot = document.querySelector('[data-nav-links]');
  if (!slot) return;
  if (!user) {
    slot.innerHTML = `<a class="button small" href="login.html">Sign in</a>`;
    return;
  }
  if (user.role === 'admin') {
    slot.innerHTML = `
      <a href="admin.html">Admin view</a>
      <a href="items.html">All items</a>
      <button class="button small secondary" type="button" data-logout>Log out</button>
    `;
  } else {
    slot.innerHTML = `
      <a href="dashboard.html">Student view</a>
      <a href="items.html">Lost & found</a>
      <a href="report-lost.html">Report lost</a>
      <a href="my-reports.html">My reports</a>
      <button class="button small secondary" type="button" data-logout>Log out</button>
    `;
  }
  slot.querySelector('[data-logout]')?.addEventListener('click', logout);
}

function showLoginFor(role) {
  const roleStep = document.querySelector('#role-step');
  const loginStep = document.querySelector('#login-step');
  if (!roleStep || !loginStep) return;
  roleStep.hidden = true;
  loginStep.hidden = false;
  document.querySelector('[name="role"]').value = role;
  const isAdmin = role === 'admin';
  document.querySelector('#login-eyebrow').textContent = isAdmin ? 'ADMIN LOGIN' : 'STUDENT LOGIN';
  const loginTitle = document.querySelector('#login-title');
  if (loginTitle) loginTitle.textContent = isAdmin ? 'Admin view' : 'Student view';
  document.querySelector('#login-submit').textContent = isAdmin ? 'Enter admin view' : 'Enter student view';
  document.querySelector('#student-extra').hidden = isAdmin;
  document.querySelector('#admin-extra').hidden = !isAdmin;
  const accountLink = document.querySelector('#create-account-link');
  if (accountLink) {
    accountLink.href = `register.html?role=${role}`;
    accountLink.textContent = isAdmin ? 'Create an admin account' : 'Create a student account';
  }
  document.querySelector('#login-step input[name="email"]')?.focus();
}

function setupHomeGate() {
  const roleStep = document.querySelector('#role-step');
  const loginStep = document.querySelector('#login-step');
  const enterStep = document.querySelector('#enter-step');
  const registerStep = document.querySelector('#register-step');
  if (!roleStep) return;

  const user = currentUser();
  if (user && enterStep) {
    roleStep.hidden = true;
    if (loginStep) loginStep.hidden = true;
    enterStep.hidden = false;
    const isAdmin = user.role === 'admin';
    document.querySelector('#enter-title').textContent = isAdmin ? 'Open admin view' : 'Open student view';
    document.querySelector('#enter-note').textContent = `Signed in as ${user.name}. Continue to your ${isAdmin ? 'admin' : 'student'} desk.`;
    const link = document.querySelector('#enter-view');
    link.href = isAdmin ? 'admin.html' : 'dashboard.html';
    link.textContent = isAdmin ? 'Enter admin view' : 'Enter student view';
    return;
  }

  const setAuthTab = (tab) => {
    const register = tab === 'register';
    roleStep.hidden = register;
    if (loginStep) loginStep.hidden = true;
    if (registerStep) registerStep.hidden = !register;
    document.querySelectorAll('[data-auth-tab]').forEach((button) => {
      const active = button.dataset.authTab === tab;
      button.classList.toggle('active', active);
      button.setAttribute('aria-selected', String(active));
    });
  };
  document.querySelectorAll('[data-auth-tab]').forEach((button) => {
    button.addEventListener('click', () => setAuthTab(button.dataset.authTab));
  });
  document.querySelectorAll('[data-register-role]').forEach((button) => {
    button.addEventListener('click', () => {
      document.querySelector('#register-step [name="role"]').value = button.dataset.registerRole;
      document.querySelectorAll('[data-register-role]').forEach((roleButton) => roleButton.classList.toggle('selected', roleButton === button));
    });
  });

  document.querySelectorAll('[data-choose]').forEach((button) => {
    button.addEventListener('click', () => {
      setAuthTab('login');
      showLoginFor(button.dataset.choose);
    });
  });
  document.querySelector('#back-to-roles')?.addEventListener('click', () => {
    loginStep.hidden = true;
    roleStep.hidden = false;
  });
}

const authForm = document.querySelector('[data-auth]');
if (authForm) authForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const message = authForm.querySelector('.form-message');
  const data = Object.fromEntries(new FormData(authForm));
  if (authForm.dataset.auth === 'login') {
    data.role = authForm.querySelector('[name="role"]').value;
  }
  try {
    const response = await fetch(`${API}/auth/${authForm.dataset.auth}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    const result = await response.json();
    if (!response.ok) {
      message.textContent = result.error || 'Unable to continue.';
      return;
    }
    localStorage.setItem('user', JSON.stringify(result));
    message.textContent = 'Success! Opening your view...';
    const next = result.role === 'admin' ? '/frontend/admin.html' : '/frontend/dashboard.html';
    setTimeout(() => { window.location.href = next; }, 350);
  } catch (error) {
    message.textContent = 'Backend is not running. Start Flask and try again.';
  }
});

renderNav();
setupHomeGate();

const registerForm = document.querySelector('[data-auth="register"]');
if (registerForm) {
  const roleSelect = registerForm.querySelector('[name="role"]');
  const role = new URLSearchParams(window.location.search).get('role');
  if (roleSelect && (role === 'student' || role === 'admin')) roleSelect.value = role;
  const updateRegisterCopy = () => {
    const isAdmin = roleSelect?.value === 'admin';
    const eyebrow = document.querySelector('#register-eyebrow');
    const title = document.querySelector('#register-title');
    const submit = registerForm.querySelector('button[type="submit"]');
    if (eyebrow) eyebrow.textContent = isAdmin ? 'ADMIN ACCESS' : 'STUDENT ACCESS';
    if (title) title.textContent = isAdmin ? 'Create admin account' : 'Create student account';
    if (submit && !registerForm.classList.contains('portal-register-form')) {
      submit.textContent = isAdmin ? 'Create admin account' : 'Create student account';
    }
  };
  roleSelect?.addEventListener('change', updateRegisterCopy);
  updateRegisterCopy();
}
