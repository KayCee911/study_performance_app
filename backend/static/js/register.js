const levels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
function checkStrength(val) {
  let score = 0;
  if (val.length >= 8) score++;
  if (/[A-Z]/.test(val) && /[a-z]/.test(val)) score++;
  if (/\d/.test(val)) score++;
  if (/[^A-Za-z0-9]/.test(val)) score++;
  const bar = document.getElementById('strengthBar');
  bar.className = 'strength-bar' + (val.length ? ' s' + Math.max(1, score) : '');
  document.getElementById('strengthLabel').textContent = val.length ? levels[Math.max(1, score)] : 'Enter a password';
}
async function register() {
  const btn = document.getElementById('regBtn');
  const msg = document.getElementById('msg');
  msg.className = 'msg'; msg.textContent = '';
  btn.classList.add('loading'); btn.disabled = true;
  try {
    const res = await fetch('/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.value, password: password.value })
    });
    const data = await res.json();
    if (res.ok) {
      msg.textContent = data.message || 'Account created! Redirecting to loginâ€¦';
      msg.classList.add('success');
      setTimeout(() => window.location.href = '/login', 1500);
    } else {
      msg.textContent = data.error || 'Registration failed. Please try again.';
      msg.classList.add('error');
      btn.classList.remove('loading'); btn.disabled = false;
    }
  } catch {
    msg.textContent = 'Network error. Please check your connection.';
    msg.classList.add('error');
    btn.classList.remove('loading'); btn.disabled = false;
  }
}
