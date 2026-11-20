"""
Access Control (RBAC) Before / After demonstration
"""

from flask import Flask, session, abort, redirect, render_template_string

app = Flask(__name__)

# Demo only secret key, this file is never used in the real application
app.secret_key = "demo-only-key"

# Isolated demo accounts, nothing touches the main MySQL database
DEMO_USERS = {
    "demo_user": "user",
    "demo_admin": "admin",
}

PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
    <link rel="stylesheet" href="/static/style.css">
</head>
<body>
    <main class="wide-card">
        <h1>{{ title }}</h1>
        <p class="subtitle">{{ note }}</p>
        <p>Logged in as: <strong>{{ current }}</strong></p>
        <p><a href="/">Back</a></p>
    </main>
</body>
</html>
"""


@app.route("/")
def index():
    return ('<p><a href="/login/demo_user">Log in as standard user</a></p>'
            '<p><a href="/login/demo_admin">Log in as admin</a></p>'
            '<p><a href="/vulnerable/admin">BEFORE: /vulnerable/admin</a></p>'
            '<p><a href="/secure/admin">AFTER: /secure/admin</a></p>'
            '<p><a href="/logout">Log out</a></p>')


# Simple demo login, it only stores the username in the session
@app.route("/login/<username>")
def login(username):
    if username not in DEMO_USERS:
        abort(404)
    session.clear()
    session["username"] = username
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


# BEFORE: no role check, any visitor can open the admin page
@app.route("/vulnerable/admin")
def vulnerable_admin():
    return render_template_string(PAGE, title="BEFORE - Admin Page",
                                  note="No access control: anyone can see this page.",
                                  current=session.get("username", "nobody"))


# AFTER: the role is checked on the server before showing the page
@app.route("/secure/admin")
def secure_admin():
    username = session.get("username")
    if not username:
        return redirect("/")
    if DEMO_USERS.get(username) != "admin":
        abort(403)
    return render_template_string(PAGE, title="AFTER - Admin Page",
                                  note="Only administrators can see this page.",
                                  current=username)


if __name__ == "__main__":
    # Local demonstration only - never deploy this file
    app.run(host="127.0.0.1", port=5004, debug=False, threaded=False)
