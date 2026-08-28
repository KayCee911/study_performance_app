// Tokens removed â€” requests are public in this deployment
    async function logout() {
      try {
        const response = await fetch('/logout', { method: 'POST' });
        if (!response.ok) throw new Error('Logout failed');
        window.location.href = '/login';
      } catch (error) {
        alert(error.message);
      }
    }

    function authHeaders() {
      return { 'Content-Type': 'application/json' };
    }

    function showMessage(el, msg, isError = false) {
      el.textContent = msg;
      el.style.color = isError ? '#dc2626' : '#15803d';
    }

    async function fetchJson(url, options = {}) {
      const res = await fetch(url, {
        ...options,
        headers: { ...authHeaders(), ...(options.headers || {}) }
      });
      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.error || 'Request failed');
      }
      return data;
    }

    async function loadDashboard() {
      try {
        const users = await fetchJson('/admin/users');
        const courses = await fetchJson('/admin/courses');
        const students = await fetchJson('/admin/students');

        document.getElementById('user-count').textContent = users.length;
        document.getElementById('course-count').textContent = courses.length;
        document.getElementById('student-count').textContent = students.length;

        const usersBody = document.getElementById('users-table-body');
        usersBody.innerHTML = users.map(u => `
          <tr>
            <td>${u.id}</td>
            <td>${u.email}</td>
            <td>${u.is_admin ? 'Admin' : 'Student'}</td>
            <td><button class="btn btn-danger" onclick="deleteUser(${u.id})">Delete</button></td>
          </tr>
        `).join('');

        const coursesBody = document.getElementById('courses-table-body');
        coursesBody.innerHTML = courses.map(c => `
          <tr>
            <td>${c.id}</td>
            <td>${c.course_code}</td>
            <td>${c.semester_id}</td>
            <td>${c.unit}</td>
            <td>${c.difficulty}</td>
          </tr>
        `).join('');

        const studentsBody = document.getElementById('students-table-body');
        studentsBody.innerHTML = students.map(s => `
          <tr>
            <td>${s.student_id}</td>
            <td>${s.email}</td>
            <td>${s.username || '-'}</td>
            <td>${s.student_id_code || '-'}</td>
            <td>${s.department || '-'}</td>
            <td>${s.level || '-'}</td>
          </tr>
        `).join('');
      } catch (err) {
        showMessage(document.getElementById('user-message'), err.message, true);
      }
    }

    document.getElementById('create-user-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const email = document.getElementById('user-email').value;
      const password = document.getElementById('user-password').value;
      const is_admin = document.getElementById('user-role').value === 'true';
      const msg = document.getElementById('user-message');

      try {
        await fetchJson('/admin/users', {
          method: 'POST',
          body: JSON.stringify({ email, password, is_admin })
        });
        showMessage(msg, 'User created successfully');
        document.getElementById('create-user-form').reset();
        await loadDashboard();
      } catch (err) {
        showMessage(msg, err.message, true);
      }
    });

    document.getElementById('add-course-form').addEventListener('submit', async (e) => {
      e.preventDefault();
      const msg = document.getElementById('course-message');
      try {
        await fetchJson('/admin/courses', {
          method: 'POST',
          body: JSON.stringify({
            semester_id: Number(document.getElementById('semester-id').value),
            course_code: document.getElementById('course-code').value,
            unit: Number(document.getElementById('unit').value),
            difficulty: Number(document.getElementById('difficulty').value)
          })
        });
        showMessage(msg, 'Course added successfully');
        document.getElementById('add-course-form').reset();
        await loadDashboard();
      } catch (err) {
        showMessage(msg, err.message, true);
      }
    });

    window.deleteUser = async function(userId) {
      if (!confirm('Delete this user?')) return;
      try {
        await fetchJson(`/admin/users/${userId}`, { method: 'DELETE' });
        await loadDashboard();
      } catch (err) {
        alert(err.message);
      }
    };

    loadDashboard();
