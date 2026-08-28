async function send() {
  const btn = document.getElementById('sendBtn');
  const msg = document.getElementById('msg');
  const emailVal = document.getElementById('email').value;
  msg.className = 'msg'; msg.textContent = '';
  btn.classList.add('loading'); btn.disabled = true;
  try {
    const res = await fetch('/forgot-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: emailVal })
    });
    const data = await res.json();
    if (res.ok) {
      document.getElementById('sentEmail').textContent = emailVal;
      document.getElementById('formState').style.display = 'none';
      document.getElementById('sentState').classList.add('active');
    } else {
      msg.textContent = data.error || 'Could not send reset link. Try again.';
      msg.classList.add('error');
      btn.classList.remove('loading'); btn.disabled = false;
    }
  } catch {
    msg.textContent = 'Network error. Please check your connection.';
    msg.classList.add('error');
    btn.classList.remove('loading'); btn.disabled = false;
  }
}
document.addEventListener('keydown', e => { if (e.key === 'Enter') send(); });
