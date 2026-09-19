async function login() {
  const btn = document.getElementById('loginBtn');
  const msg = document.getElementById('msg');
  msg.className = 'msg'; msg.textContent = '';
  btn.classList.add('loading'); btn.disabled = true;
  try {
    const res = await fetch('/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.value, password: password.value })
    });
    const data = await res.json();
    if (res.ok) {
      msg.textContent = 'Login successful! Redirecting…';
      msg.classList.add('success');
      const targetUrl = data.is_admin ? '/admin/dashboard' : '/dashboard';
      setTimeout(() => window.location.href = targetUrl, 1200);
    } else {
      msg.textContent = data.error || 'Something went wrong. Try again.';
      msg.classList.add('error');
      btn.classList.remove('loading'); btn.disabled = false;
    }
  } catch {
    msg.textContent = 'Network error. Please check your connection.';
    msg.classList.add('error');
    btn.classList.remove('loading'); btn.disabled = false;
  }
}
document.addEventListener('keydown', e => { if (e.key === 'Enter') login(); });
