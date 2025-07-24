async function fetchJSON(url, opts = {}) {
  const res = await fetch(url, {
    credentials: 'include',
    headers: { 'Content-Type': 'application/json' },
    ...opts
  });
  return res.json();
}

async function initDashboard() {
  // guard: redirect to login if not authenticated
  const { authenticated } = await fetchJSON('/api/check_auth');
  if (!authenticated) {
    window.location.href = '/';
    return;
  }

  // load profile info
  const user = await fetchJSON('/api/user_info');
  document.getElementById('dashboard-username').textContent = user.username;
  document.getElementById('dashboard-username-input').value = user.username;
  document.getElementById('dashboard-email-input').value = user.email;

  // load chat history
  const { history } = await fetchJSON('/api/chat_history');
  const box = document.getElementById('dashboard-chat');
  box.innerHTML = ''; 
  history.forEach(h => {
    const d = document.createElement('div');
    d.className = 'chat-item';
    d.textContent = (h.sender === 'user' ? 'You: ' : 'Bot: ') + h.message;
    box.appendChild(d);
  });
}

// password reset
document.getElementById('reset-password-btn').addEventListener('click', async () => {
  const pw = document.getElementById('new-password').value;
  if (!pw) return alert('Enter a new password');
  const resp = await fetchJSON('/api/reset_password', {
    method: 'POST',
    body: JSON.stringify({ password: pw })
  });
  alert(resp.success ? 'Password updated' : 'Failed: ' + (resp.message||''));
});

// logout
async function logout() {
  if (!confirm('Are you sure you want to logout?')) return;
  await fetch('/api/logout', { credentials: 'include' });
  window.location.href = '/';
}

window.addEventListener('DOMContentLoaded', initDashboard);

