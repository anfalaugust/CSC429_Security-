"""
Unencrypted session / No HTTPS - Before demonstration 

This isolated demo shows the VULNERABLE state before our fixes:
  - It runs over plain HTTP (no TLS), so all data is sent as readable text.
  - It uses Flask's default session cookie, which is only signed, not encrypted.
    The /inspect-cookie page decodes the cookie WITHOUT the secret key to prove
    that anyone holding the cookie can read the username and role.
  - There is no /logout route and no Cache-Control header on the dashboard.
"""
import base64
import json
import zlib

from flask import Flask, request, session, redirect, url_for, render_template_string

app = Flask(__name__)
# Demo only: a fixed dummy key. The real app loads its keys from .env
app.secret_key = "demo-only-secret-key"

DEMO_USER = {"username": "Maha", "password": "DemoPass123!", "role": "user"}

PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Session Demo (Before)</title>
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
<style>
  .card.wide { max-width: 720px; }
  .tag { display: inline-block; margin: 0 0 10px; padding: 3px 12px; font-size: 12px;
         font-weight: 700; border-radius: 999px; background: var(--error-bg); color: var(--error-text); }
  h3 { margin: 20px 0 8px; font-size: 14px; }
  pre { margin: 0; padding: 12px 14px; font-size: 13px; white-space: pre-wrap; word-break: break-all;
        background: var(--input); border: 1px solid var(--border); border-radius: 8px; }
  .result { margin: 18px 0 0; padding: 12px 14px; font-size: 15px; font-weight: 600; border-radius: 8px;
            background: var(--error-bg); color: var(--error-text); }
</style>
</head>
<body>
<main class="card wide">
  <div style="text-align:center"><span class="tag">BEFORE (vulnerable)</span></div>
  {{ body|safe }}
</main>
</body>
</html>
"""


def page(body):
    return render_template_string(PAGE, body=body)


@app.route("/")
def home():
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    error = ""
    if request.method == "POST":
        if (request.form.get("username") == DEMO_USER["username"]
                and request.form.get("password") == DEMO_USER["password"]):
            # VULNERABLE: default Flask session -> signed only, NOT encrypted
            session["user_id"] = 1
            session["username"] = DEMO_USER["username"]
            session["role"] = DEMO_USER["role"]
            return redirect(url_for("dashboard"))
        error = '<p class="error">Invalid username or password.</p>'
    return page(f"""
      <h1>Login (HTTP)</h1>
      <p class="subtitle">Use the dummy account: {DEMO_USER["username"]} / {DEMO_USER["password"]}</p>
      {error}
      <form method="POST">
        <label>Username</label><input type="text" name="username" required>
        <label>Password</label><input type="password" name="password" required>
        <button type="submit">Login</button>
      </form>""")


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))
    # VULNERABLE: no Cache-Control header, and the Logout link points to a
    # route that does not exist (same as the original application).
    return page(f"""
      <h1>Welcome, {session['username']}</h1>
      <p class="subtitle">Role: {session['role']}</p>
      <a class="button" href="/inspect-cookie">Inspect my session cookie</a>
      <a class="button button-secondary" href="/logout">Logout</a>""")


def decode_flask_cookie(cookie_value):
    """Decode a Flask session cookie WITHOUT knowing the secret key."""
    payload = cookie_value.split(".")[0] if not cookie_value.startswith(".") \
        else cookie_value.split(".")[1]
    data = base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
    if cookie_value.startswith("."):
        data = zlib.decompress(data)
    return json.loads(data)


@app.route("/inspect-cookie")
def inspect_cookie():
    raw = request.cookies.get("session", "")
    if not raw:
        return redirect(url_for("login"))
    decoded = decode_flask_cookie(raw)
    return page(f"""
      <h1>Session cookie</h1>
      <h3>Raw cookie value (sent over plain HTTP)</h3>
      <pre>{raw}</pre>
      <h3>Decoded with base64 only - no secret key needed</h3>
      <pre>{json.dumps(decoded, indent=2)}</pre>
      <p class="result">The username and role are readable by anyone who gets this cookie.</p>
      <a class="button button-secondary" href="/dashboard">Back to Dashboard</a>""")


if __name__ == "__main__":
    # VULNERABLE: plain HTTP, no ssl_context
    app.run(host="127.0.0.1", port=5005, debug=False)