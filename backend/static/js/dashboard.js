let chartInstance = null;

async function logout() {
  try {
    const response = await fetch('/logout', { method: 'POST' });
    if (!response.ok) throw new Error('Logout failed');
    window.location.href = '/login';
  } catch (error) {
    alert(error.message);
  }
}

async function loadDashboard() {
  const email = document.getElementById('email').value.trim();
  if (!email) { flashInput(); return; }

  const btn = document.getElementById('loadBtn');
  btn.classList.add('loading'); btn.disabled = true;

  // Update sidebar avatar
  const initials = email.split('@')[0].slice(0, 2).toUpperCase();
  document.getElementById('sidebarAvatar').textContent = initials;
  document.getElementById('sidebarEmail').textContent = email.split('@')[0];

  showSkeletons();

    try {
        // Load insights (public endpoint)
        const res1 = await fetch(`/user/${email}/insights`);
    if (!res1.ok) throw new Error('User not found');
    const insights = await res1.json();

    animateValue('gpa', insights.avg_gpa ?? 0);
    animateValue('hours', insights.avg_study_hours ?? 0);
    animateValue('difficulty', insights.avg_difficulty ?? 0);
    animateValue('courses', insights.total_courses ?? 0);

    // Load ML recommendations
    const res2 = await fetch(`/ml-recommend/${email}`);
    const response = await res2.json();
    const data = response.results || [];
    const summary = response.summary || 'No insights available.';

    // AI summary
    document.getElementById('aiSummary').innerHTML =
      `<span class="ai-pulse"></span>${escHtml(summary)}`;

    const container = document.getElementById('recommendations');
    container.innerHTML = '';
    document.getElementById('recsCount').textContent = data.length;

    if (data.length === 0) {
      container.innerHTML = `<div class="alert-box warn">No recommendations found for this account.</div>`;
      btn.classList.remove('loading'); btn.disabled = false;
      return;
    }

    const labels = [], currentData = [], improvedData = [];

    data.forEach((item, i) => {
      labels.push(item.course);
      currentData.push(item.current_gpa);
      improvedData.push(item.improved_gpa);

      const risk = (item.risk || 'low').toLowerCase();
      const confPct = Math.round((item.confidence || 0) * 100);
      const whyItems = (item.why || []).map(e =>
        `<div class="why-item"><div class="why-dot"></div>${escHtml(e)}</div>`
      ).join('');

      container.innerHTML += `
      <div class="rec-card risk-${risk}" style="animation-delay:${i * 0.08}s">
        <div class="rec-top">
          <div class="rec-course">${escHtml(item.course)}</div>
          <div class="rec-badge ${risk}">
            <div class="badge-dot"></div>${risk.toUpperCase()} RISK
          </div>
        </div>
        <div class="rec-meta">
          <div class="rec-meta-item">
            <div class="rec-meta-label">Current GPA</div>
            <div class="rec-meta-val current">${item.current_gpa}</div>
          </div>
          <div class="rec-meta-item">
            <div class="rec-meta-label">Projected GPA</div>
            <div class="rec-meta-val improved">${item.improved_gpa}</div>
          </div>
        </div>
        ${item.suggestion ? `<div class="rec-suggestion">${escHtml(item.suggestion)}</div>` : ''}
        <div class="conf-row">
          <span class="conf-label">Confidence</span>
          <div class="conf-bar"><div class="conf-fill ${risk}" style="width:${confPct}%"></div></div>
          <span class="conf-pct">${confPct}%</span>
        </div>
        ${whyItems ? `<div class="why-list">${whyItems}</div>` : ''}
        ${item.peer_insight ? `<div class="peer-insight">${escHtml(item.peer_insight)}</div>` : ''}
      </div>`;
    });

    // Chart
    const ctx = document.getElementById('gpaChart');
    if (chartInstance) chartInstance.destroy();
    chartInstance = new Chart(ctx, {
      type: 'bar',
      data: {
        labels,
        datasets: [
          {
            label: 'Current GPA',
            data: currentData,
            backgroundColor: 'rgba(107,116,148,0.35)',
            borderColor: 'rgba(107,116,148,0.6)',
            borderWidth: 1,
            borderRadius: 6,
          },
          {
            label: 'Projected GPA',
            data: improvedData,
            backgroundColor: 'rgba(0,210,170,0.25)',
            borderColor: '#00d2aa',
            borderWidth: 1.5,
            borderRadius: 6,
          }
        ]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: {
              color: '#6b7494',
              font: { family: 'Sora', size: 11 },
              boxWidth: 10, boxHeight: 10,
            }
          },
          tooltip: {
            backgroundColor: '#121929',
            titleColor: '#e8eaf2',
            bodyColor: '#6b7494',
            borderColor: 'rgba(255,255,255,0.07)',
            borderWidth: 1,
          }
        },
        scales: {
          x: { ticks: { color: '#6b7494', font: { family: 'DM Mono', size: 10 } }, grid: { color: 'rgba(255,255,255,0.04)' } },
          y: { ticks: { color: '#6b7494', font: { family: 'DM Mono', size: 10 } }, grid: { color: 'rgba(255,255,255,0.04)' }, beginAtZero: true, max: 4 }
        }
      }
    });

  } catch (err) {
    document.getElementById('recommendations').innerHTML =
      `<div class="alert-box err">${escHtml(err.message)}</div>`;
  }

  btn.classList.remove('loading'); btn.disabled = false;
}

function showSkeletons() {
  const rec = document.getElementById('recommendations');
  rec.innerHTML = [1,2,3].map(() => `
    <div class="rec-card" style="animation:none">
      <div class="skeleton" style="height:18px;width:55%;margin-bottom:14px;"></div>
      <div class="rec-meta">
        <div class="rec-meta-item"><div class="skeleton" style="height:36px;"></div></div>
        <div class="rec-meta-item"><div class="skeleton" style="height:36px;"></div></div>
      </div>
      <div class="skeleton" style="height:48px;"></div>
    </div>`).join('');
}

function animateValue(id, target) {
  const el = document.getElementById(id);
  const num = parseFloat(target);
  if (isNaN(num)) { el.textContent = target; return; }
  let start = 0, duration = 800, startTime = null;
  function step(ts) {
    if (!startTime) startTime = ts;
    const prog = Math.min((ts - startTime) / duration, 1);
    const ease = 1 - Math.pow(1 - prog, 3);
    el.textContent = Number.isInteger(num) ? Math.round(start + (num - start) * ease) : (start + (num - start) * ease).toFixed(1);
    if (prog < 1) requestAnimationFrame(step);
    else el.textContent = Number.isInteger(num) ? num : num.toFixed(1);
  }
  requestAnimationFrame(step);
}

function escHtml(str) {
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function flashInput() {
  const el = document.getElementById('email');
  el.style.borderColor = '#ff5c6a';
  el.style.boxShadow = '0 0 0 3px rgba(255,92,106,0.15)';
  el.focus();
  setTimeout(() => { el.style.borderColor = ''; el.style.boxShadow = ''; }, 1200);
}

document.getElementById('email').addEventListener('keydown', e => {
  if (e.key === 'Enter') loadDashboard();
});
