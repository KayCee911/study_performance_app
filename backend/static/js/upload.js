let selectedFile = null;

function onFileSelect(input) {
  const file = input.files[0];
  if (!file) return;
  selectedFile = file;
  document.getElementById('fileName').textContent = file.name;
  document.getElementById('fileSize').textContent = formatSize(file.size);
  document.getElementById('filePreview').classList.add('active');
  document.getElementById('dropZone').classList.add('has-file');
  document.getElementById('uploadBtn').disabled = false;
}

function removeFile() {
  selectedFile = null;
  document.getElementById('fileInput').value = '';
  document.getElementById('filePreview').classList.remove('active');
  document.getElementById('dropZone').classList.remove('has-file');
  document.getElementById('uploadBtn').disabled = true;
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B';
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

// Drag and drop
const dz = document.getElementById('dropZone');
dz.addEventListener('dragover', e => { e.preventDefault(); dz.classList.add('hover'); });
dz.addEventListener('dragleave', () => dz.classList.remove('hover'));
dz.addEventListener('drop', e => {
  e.preventDefault(); dz.classList.remove('hover');
  const file = e.dataTransfer.files[0];
  if (file && file.name.endsWith('.csv')) {
    const dt = new DataTransfer();
    dt.items.add(file);
    document.getElementById('fileInput').files = dt.files;
    onFileSelect(document.getElementById('fileInput'));
  }
});

async function upload() {
  if (!selectedFile) return;
  const btn = document.getElementById('uploadBtn');
  const msg = document.getElementById('msg');
  const prog = document.getElementById('progressWrap');
  msg.className = 'msg'; msg.textContent = '';
  btn.classList.add('loading'); btn.disabled = true;
  prog.classList.add('active');

  // Simulate progress
  let pct = 0;
  const tick = setInterval(() => {
    pct = Math.min(pct + Math.random() * 15, 90);
    document.getElementById('progressFill').style.width = pct + '%';
    document.getElementById('pct').textContent = Math.round(pct) + '%';
  }, 200);

  const formData = new FormData();
  formData.append('file', selectedFile);

  try {
    const res = await fetch('/upload-survey', { method: 'POST', body: formData });
    clearInterval(tick);
    document.getElementById('progressFill').style.width = '100%';
    document.getElementById('pct').textContent = '100%';
    const data = await res.json();
    if (res.ok) {
      const feedback = data.feedback;
      let feedbackHtml = '';

      if (feedback && feedback.summary) {
        const recommendations = feedback.recommendations || [];
        const top = recommendations.slice(0, 3).map(r => {
          const ways = (r.ways_to_improve || []).map(w => `<li>${w}</li>`).join('');
          return `
            <div style="margin-top: 10px; padding: 10px; background: rgba(255,255,255,0.02); border: 1px solid rgba(255,255,255,0.06); border-radius: 10px;">
              <div style="font-weight:600; margin-bottom: 4px;">${r.course}</div>
              <div>Projected GPA: <span style="color:#00d2aa; font-weight:600;">${Number(r.projected_gpa || 0).toFixed(2)}</span></div>
              <div>Recommended: ${r.recommended_study_hours} hrs using ${r.recommended_method}</div>
              <ul style="padding-left: 18px; margin-top: 6px; color:#b7bed8; font-size: 12px;">${ways}</ul>
            </div>`;
        }).join('');

        feedbackHtml = `
          <div style="margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(0,210,170,0.2);">
            <strong>Projected feedback</strong><br>
            ${feedback.summary}<br>
            <span style="color:#f4a62a; font-weight:600;">Average projected GPA: ${Number(feedback.average_projected_gpa || 0).toFixed(2)}</span>
            ${top}
          </div>`;
      }

      msg.innerHTML = `${data.message || 'Upload successful! Redirecting to dashboardâ€¦'}${feedbackHtml}`;
      msg.classList.add('success');
      setTimeout(() => window.location.href = '/dashboard', 1500);
    } else {
      msg.textContent = data.error || 'Upload failed. Please try again.';
      msg.classList.add('error');
      prog.classList.remove('active');
      btn.classList.remove('loading'); btn.disabled = false;
    }
  } catch {
    clearInterval(tick);
    msg.textContent = 'Network error. Please check your connection.';
    msg.classList.add('error');
    prog.classList.remove('active');
    btn.classList.remove('loading'); btn.disabled = false;
  }
}
