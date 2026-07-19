import re

with open('owner-dashboard.html', 'r') as f:
    content = f.read()

# 1. Styles and scripts
content = content.replace('<style>', '<link rel="stylesheet" href="assets/styles.css">\n<style>')
# Remove the :root variables that were moved, to avoid duplication (though harmless).
# Let's just insert scripts
scripts = """<script src="assets/config.js"></script>
<script src="assets/api.js"></script>
<script>
  function escapeHtml(unsafe) {
    if (unsafe == null) return "";
    return String(unsafe)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }"""
content = content.replace('<script>\n  const API_BASE = "http://127.0.0.1:8000";\n  let ownerPassword = "";', scripts)

# 2. login()
old_login = """  async function login() {
    const input = document.getElementById("password-input");
    const errorDiv = document.getElementById("login-error");
    const pwd = input.value.trim();

    if (!pwd) {
      errorDiv.textContent = "Please enter a password.";
      return;
    }

    try {
      const res = await fetch(`${API_BASE}/chat/owner`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-owner-password": pwd
        },
        body: JSON.stringify({ message: "hello", history: [] })
      });

      if (res.status === 401) {
        errorDiv.textContent = "Incorrect password.";
        return;
      }

      if (!res.ok) {
        errorDiv.textContent = `Server error ${res.status}`;
        return;
      }

      ownerPassword = pwd;"""
new_login = """  async function login() {
    const input = document.getElementById("password-input");
    const errorDiv = document.getElementById("login-error");
    const loginBtn = document.querySelector(".login-box button");
    const pwd = input.value.trim();

    if (!pwd) {
      errorDiv.textContent = "Please enter a password.";
      return;
    }
    
    loginBtn.disabled = true;

    try {
      const res = await fetchApi(`/auth/login`, {
        method: "POST",
        body: JSON.stringify({ password: pwd })
      });

      if (res.status === 401) {
        errorDiv.textContent = "Incorrect password.";
        return;
      }

      if (!res.ok) {
        errorDiv.textContent = `Server error ${res.status}`;
        return;
      }

      const data = await res.json();
      setSessionToken(data.token);"""
content = content.replace(old_login, new_login)
content = content.replace('      errorDiv.textContent = `Could not reach server: ${err.message}`;', '      errorDiv.textContent = `Could not reach server: ${err.message}`;\n    } finally {\n      loginBtn.disabled = false;')

# 3. send()
content = content.replace("""      const res = await fetch(`${API_BASE}/chat/owner`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-owner-password": ownerPassword
        },
        body: JSON.stringify({
          message: text,
          history: conversationHistory
        })
      });""", """      const res = await fetchApi(`/chat/owner`, {
        method: "POST",
        body: JSON.stringify({
          message: text,
          history: conversationHistory
        })
      });""")

# 4. loadApprovals()
content = content.replace("""      const res = await fetch(`${API_BASE}/approvals`, {
        method: "GET",
        headers: {
          "x-owner-password": ownerPassword
        }
      });""", """      const res = await fetchApi(`/approvals`, {
        method: "GET"
      });""")

old_card = """        card.innerHTML = `
          <h3>${approval.approval_type.toUpperCase()} — ${approval.title}</h3>
          <p><strong>ID:</strong> ${approval.id}</p>
          <p><strong>Reference:</strong> ${approval.reference_id}</p>
          <p><strong>Status:</strong> ${approval.status}</p>
          <p><strong>Description:</strong> ${approval.description || ""}</p>
          <pre>${payloadText}</pre>
          <button onclick="approveApproval(${approval.id})">Approve</button>
          <button class="reject-btn" onclick="rejectApproval(${approval.id})">Reject</button>
        `;"""
new_card = """        card.innerHTML = `
          <h3>${escapeHtml(approval.approval_type.toUpperCase())} — ${escapeHtml(approval.title)}</h3>
          <p><strong>ID:</strong> ${escapeHtml(approval.id)}</p>
          <p><strong>Reference:</strong> ${escapeHtml(approval.reference_id)}</p>
          <p><strong>Status:</strong> ${escapeHtml(approval.status)}</p>
          <p><strong>Description:</strong> ${escapeHtml(approval.description || "")}</p>
          <pre>${escapeHtml(payloadText)}</pre>
          <button onclick="approveApproval(${escapeHtml(approval.id)}, this)">Approve</button>
          <button class="reject-btn" onclick="rejectApproval(${escapeHtml(approval.id)}, this)">Reject</button>
        `;"""
content = content.replace(old_card, new_card)

# Disable buttons during loadApprovals
content = content.replace('    const approvalsDiv = document.getElementById("approvals");', '    const btn = document.querySelector(".approval-box button");\n    if(btn) btn.disabled = true;\n    const approvalsDiv = document.getElementById("approvals");')
content = content.replace('      approvalsDiv.innerHTML = `<p style="color: var(--warn);">Could not load approvals: ${err.message}</p>`;\n    }', '      approvalsDiv.innerHTML = `<p style="color: var(--warn);">Could not load approvals: ${err.message}</p>`;\n    } finally {\n      if(btn) btn.disabled = false;\n    }')

# 5. approveApproval / rejectApproval
old_app = """  async function approveApproval(id) {
    try {
      const res = await fetch(`${API_BASE}/approvals/${id}/approve`, {
        method: "POST",
        headers: {
          "x-owner-password": ownerPassword
        }
      });"""
new_app = """  async function approveApproval(id, btnElement) {
    if(btnElement) btnElement.disabled = true;
    try {
      const res = await fetchApi(`/approvals/${id}/approve`, {
        method: "POST"
      });"""
content = content.replace(old_app, new_app)
content = content.replace('      addMsg(`Approval failed: ${err.message}`, "error");\n    }\n  }', '      addMsg(`Approval failed: ${err.message}`, "error");\n    } finally {\n      if(btnElement) btnElement.disabled = false;\n    }\n  }')

old_rej = """  async function rejectApproval(id) {
    try {
      const res = await fetch(`${API_BASE}/approvals/${id}/reject`, {
        method: "POST",
        headers: {
          "x-owner-password": ownerPassword
        }
      });"""
new_rej = """  async function rejectApproval(id, btnElement) {
    if(btnElement) btnElement.disabled = true;
    try {
      const res = await fetchApi(`/approvals/${id}/reject`, {
        method: "POST"
      });"""
content = content.replace(old_rej, new_rej)
content = content.replace('      addMsg(`Reject failed: ${err.message}`, "error");\n    }\n  }', '      addMsg(`Reject failed: ${err.message}`, "error");\n    } finally {\n      if(btnElement) btnElement.disabled = false;\n    }\n  }')

with open('owner-dashboard.html', 'w') as f:
    f.write(content)

