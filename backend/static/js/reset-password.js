const levels = ['', 'Weak', 'Fair', 'Good', 'Strong'];
function checkStrength(val) {
  let score = 0;
  const len = val.length >= 8;
  const cas = /[A-Z]/.test(val) && /[a-z]/.test(val);
  const num = /\d/.test(val);
  if (len) score++;
  if (cas) score++;
  if (num) score++;
  if (/[^A-Za-z0-9]/.test(val)) score++;
  const bar = document.getElementById('strengthBar');
  bar.className = 'strength-bar' + (val.length ? ' s' + Math.max(1, score) : '');
  document.getElementById('strengthLabel').textContent = val.length ? levels[Math.max(1, score)] : 'Enter a password';
  document.getElementById('r-len').className = 'req' + (len ? ' met' : '');
  document.getElementById('r-case').className = 'req' + (cas ? ' met' : '');
  document.getElementById('r-num').className = 'req' + (num ? ' met' : '');
}
let visible = false;
function toggleVis() {
  visible = !visible;
  document.getElementById('password').type = visible ? 'text' : 'password';
  document.querySelector('.toggle-vis').textContent = visible ? 'hide' : 'show';
}
async function reset() {
  const btn = document.getElementById('resetBtn');
  const msg = document.getElementById('msg');
  msg.className = 'msg'; msg.textContent = '';
  btn.classList.add('loading'); btn.disabled = true;
  const token = window.location.pathname.split('/').pop();
  try {
    const res = await fetch(`/reset-password/${token}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ password: document.getElementById('password').value })
    });
    const data = await res.json();
    if (res.ok) {
      msg.textContent = data.message || 'Password updated! Redirecting to loginâ€¦';
      msg.classList.add('success');
      setTimeout(() => window.location.href = '/login', 1500);
    } else {
      msg.textContent = data.error || 'Reset failed. Your link may have expired.';
      msg.classList.add('error');
      btn.classList.remove('loading'); btn.disabled = false;
    }
  } catch {
    msg.textContent = 'Network error. Please check your connection.';
    msg.classList.add('error');
    btn.classList.remove('loading'); btn.disabled = false;
  }
}
