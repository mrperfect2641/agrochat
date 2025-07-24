function addMessageToChat(sender, message) {
    const chat = document.getElementById('chat-messages');
    const div = document.createElement('div');
    Object.assign(div.style, {
      marginBottom: '10px',
      padding: '8px 12px',
      borderRadius: '6px',
      backgroundColor: sender === 'user' ? '#e3f2fd' : '#f1f8e9',
      maxWidth: '80%',
      marginLeft: sender === 'user' ? 'auto' : '0',
      fontSize: '14px',
      wordBreak: 'break-word'
    });
    div.textContent = message;
    chat.appendChild(div);
    chat.scrollTop = chat.scrollHeight;
}

// Check if user is logged in; update UI state (unchanged)
async function checkLoginState() {
    try {
        const res = await fetch('/api/check_auth', { credentials: 'include' });
        const { authenticated } = await res.json();
        document.getElementById('login-btn').style.display = authenticated ? 'none' : 'block';
        document.getElementById('profile-dropdown').style.display = authenticated ? 'block' : 'none';
    } catch {
        console.error('Auth check failed');
    }
}

function showAuthModal() { document.getElementById('auth-modal').style.display = 'block'; }
function closeAuthModal() {
    document.getElementById('auth-modal').style.display = 'none';
    document.getElementById('auth-message').style.display = 'none';
}

// If not logged in, open the auth modal
async function promptLoginIfNeeded() {
  try {
    const res  = await fetch('/api/check_auth', { credentials: 'include' });
    const { authenticated } = await res.json();
    if (!authenticated) {
      showAuthModal();    // opens #auth-modal
    }
  } catch (err) {
    console.error('Auth check failed:', err);
    // Optionally: still show the modal if the check itself errors
    showAuthModal();
  }
}

function switchTab(tab) {
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.querySelectorAll('.auth-form').forEach(f => f.style.display = 'none');
    document.getElementById(`${tab}-form`).style.display = 'flex';
    document.querySelector(`.tab[onclick="switchTab('${tab}')"]`).classList.add('active');
}

async function handleLogin(username, password) {
    const res = await fetch('/api/login', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
        credentials: 'include',
        body: JSON.stringify({ username, password })
    });
    const data = await res.json();
    if (data.success) {
        checkLoginState();
        // closeAuthModal();
        location.reload();
    } else {
        showMessage('error', data.message);
    }
    return data.success;
}

async function handleRegistration(username, email, password) {
    const res = await fetch('/api/register', {
        method: 'POST',
        headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
        credentials: 'include',
        body: JSON.stringify({ username, email, password })
    });
    const data = await res.json();
    if (data.success) {
        showMessage('success', 'Registration successful! Please login.');
        switchTab('login');
    } else {
        showMessage('error', data.message);
    }
}

function showMessage(type, text) {
    const m = document.getElementById('auth-message');
    m.className = type;
    m.textContent = text;
    m.style.display = 'block';
}

// Load saved chat history into the chat window
async function loadChatHistory() {
    try {
        const res = await fetch('/api/chat_history', { credentials: 'include' });
        const { history } = await res.json();
        history.forEach(entry => {
            addMessageToChat(entry.sender, entry.message);
        });
    } catch (e) {
        console.warn('Could not load chat history:', e);
    }
}

let messageSending = false;

async function sendMessage() {
    if (messageSending) return;
    messageSending = true;

    const input = document.getElementById('user-input');
    const msg = input.value.trim();
    if (!msg) {
        messageSending = false;
        return;
    }

    let isAuthenticated = false;
    try {
        const authRes = await fetch('/api/check_auth', { credentials: 'include' });
        const authData = await authRes.json();
        isAuthenticated = authData.authenticated;
    } catch {
        console.error("Failed to check authentication");
    }

    if (!isAuthenticated) {
        // Prevent duplicate login message
        const chat = document.getElementById('chat-messages');
        const lastMessage = chat.lastElementChild?.textContent;
        if (lastMessage !== 'Please log in to access.') {
            addMessageToChat('bot', 'Please log in to access.');
        }
        messageSending = false;
        return;
    }

    addMessageToChat('user', msg);
    input.value = '';

    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ message: msg })
        });
        const data = await res.json();
        addMessageToChat('bot', data.response);
    } catch {
        addMessageToChat('bot', 'Sorry, there was an error processing your request.');
    }

    messageSending = false;
}

function handleKeyPress(e) {
    if (e.key === 'Enter') sendMessage();
}

// Logout function
function logout() {
    if (confirm("Are you sure to Logout?")) {
        fetch('/api/logout', {
            method: 'GET',
            credentials: 'include'
        })
        .then(res => res.json())
        .then(data => {
            if (data.success) {
                // checkLoginState();
                location.reload();
            }
        })
        .catch(err => console.error('Logout failed:', err));
    }
}

// Event listener for login form submission
document.getElementById('login-form').addEventListener('submit', e => {
    e.preventDefault();
    const formData = e.target.elements;
    handleLogin(formData[0].value, formData[1].value);
});

// Event listener for registration form submission
document.getElementById('register-form').addEventListener('submit', e => {
    e.preventDefault();
    handleRegistration(e.target[0].value, e.target[1].value, e.target[2].value);
});

// Main initialization when page loads
window.addEventListener('DOMContentLoaded', () => {
    checkLoginState();     // updates header buttons
    loadChatHistory();     // loads previous chat messages
    
    // Set up chat input event listeners
    document.getElementById('user-input').addEventListener('keypress', handleKeyPress);
    document.querySelector('.chat-input button').addEventListener('click', sendMessage);
    
    // Close modal when clicking outside of it
    window.onclick = e => {
        if (e.target === document.getElementById('auth-modal')) closeAuthModal();
        // FIXED: Close contact modal when clicking outside
        if (e.target === document.getElementById('contact-popup')) closeContactForm();
    };

    // Check if user needs to login
    promptLoginIfNeeded();
});

// Change Username functionality (for dashboard page)
document.addEventListener('DOMContentLoaded', () => {
    const changeUsernameBtn = document.getElementById('change-username-btn');
    if (changeUsernameBtn) {
        changeUsernameBtn.addEventListener('click', async () => {
            const newU = document.getElementById('settings-username').value.trim();
            if (!newU) return alert('Please enter a username.');
            const res = await fetch('/api/change_username', {
                method: 'POST',
                credentials: 'include',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({ new_username: newU })
            });
            const data = await res.json();
            alert(data.success ? 'Username updated!' : data.message);
            if (data.success) {
                document.getElementById('profile-username').value = data.username;
                document.getElementById('user-name').textContent = data.username;
                document.getElementById('settings-username').value = '';
            }
        });
    }
});

// Change Email functionality (for dashboard page)
document.addEventListener('DOMContentLoaded', () => {
    const changeEmailBtn = document.getElementById('change-email-btn');
    if (changeEmailBtn) {
        changeEmailBtn.addEventListener('click', async () => {
            const newE = document.getElementById('settings-email').value.trim();
            if (!newE) return alert('Please enter an email.');
            const res = await fetch('/api/change_email', {
                method: 'POST',
                credentials: 'include',
                headers: {'Content-Type':'application/json'},
                body: JSON.stringify({ new_email: newE })
            });
            const data = await res.json();
            alert(data.success ? 'Email updated!' : data.message);
            if (data.success) {
                document.getElementById('profile-email').value = data.email;
                document.getElementById('settings-email').value = '';
            }
        });
    }
});

// Clear Chat History functionality (for dashboard page)
document.addEventListener('DOMContentLoaded', () => {
    const clearHistoryBtn = document.getElementById('clear-history-btn');
    if (clearHistoryBtn) {
        clearHistoryBtn.addEventListener('click', async () => {
            if (!confirm('Are you sure you want to clear your chat history?')) return;
            const res = await fetch('/api/clear_history', {
                method: 'POST',
                credentials: 'include'
            });
            const data = await res.json();
            alert(data.success ? 'Chat history cleared!' : 'Failed to clear history.');
            if (data.success) {
                document.getElementById('chat-history').innerHTML = '';
            }
        });
    }
});

// FIXED: Contact form functions
function openContactForm() {
  // Show the contact popup modal
  document.getElementById('contact-popup').style.display = 'block';
  
  // Try to pre-fill email from user info if logged in
  fetch('/api/user_info', { credentials: 'include' })
    .then(res => res.json())
    .then(data => {
      document.getElementById('contact-email').value = data.email || '';
    })
    .catch(() => {
      // If not logged in or error, leave email empty
      document.getElementById('contact-email').value = '';
    });
}

function closeContactForm() {
  // Hide the contact popup modal
  document.getElementById('contact-popup').style.display = 'none';
}

// FIXED: Contact form submission handler
document.addEventListener('DOMContentLoaded', () => {
    const contactForm = document.getElementById("contact-form");
    if (contactForm) {
        contactForm.addEventListener("submit", async function(e) {
            // Prevent default form submission (which causes page redirect)
            e.preventDefault();
            
            const form = e.target;
            const submitButton = form.querySelector('button[type="submit"]');
            
            // Disable submit button to prevent double submission
            submitButton.disabled = true;
            submitButton.textContent = 'Sending...';
            
            try {
                // Send form data via fetch API (AJAX)
                const res = await fetch(form.action, {
                    method: "POST",
                    body: new FormData(form)
                });
                
                const json = await res.json();
                
                if (json.status === "success") {
                    // Show success message and reset form
                    alert("Message sent successfully! We'll be in touch soon.");
                    form.reset(); // Clear all form fields
                    closeContactForm(); // Close the popup
                } else {
                    // Show error message
                    alert("Error: " + (json.error || "Please try again later."));
                }
            } catch (error) {
                // Handle network or other errors
                console.error('Contact form submission error:', error);
                alert("Network error. Please check your connection and try again.");
            } finally {
                // Re-enable submit button
                submitButton.disabled = false;
                submitButton.textContent = 'Send';
            }
        });
    }
});