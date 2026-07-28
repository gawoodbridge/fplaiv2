document.addEventListener('DOMContentLoaded', () => {
  if (Auth.isLoggedIn()) {
    window.location.href = 'dashboard.html';
    return;
  }

  const tabs = document.querySelectorAll('.auth-tab');
  const loginForm = document.getElementById('login-form');
  const registerForm = document.getElementById('register-form');

  tabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      tabs.forEach((t) => t.classList.remove('active'));
      tab.classList.add('active');
      const isLogin = tab.dataset.tab === 'login';
      loginForm.classList.toggle('hidden', !isLogin);
      registerForm.classList.toggle('hidden', isLogin);
    });
  });

  loginForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const errorEl = document.getElementById('login-error');
    errorEl.textContent = '';
    const submitBtn = document.getElementById('login-submit');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Logging in...';
    try {
      const { token, user } = await Api.login({
        email: document.getElementById('login-email').value.trim(),
        password: document.getElementById('login-password').value,
      });
      Auth.setSession(token, user);
      window.location.href = 'dashboard.html';
    } catch (err) {
      errorEl.textContent = err.message;
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Log in';
    }
  });

  registerForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const errorEl = document.getElementById('register-error');
    errorEl.textContent = '';
    const submitBtn = document.getElementById('register-submit');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Creating account...';
    try {
      const { token, user } = await Api.register({
        displayName: document.getElementById('reg-name').value.trim(),
        email: document.getElementById('reg-email').value.trim(),
        password: document.getElementById('reg-password').value,
      });
      Auth.setSession(token, user);
      window.location.href = 'dashboard.html';
    } catch (err) {
      errorEl.textContent = err.message;
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Create account';
    }
  });
});
