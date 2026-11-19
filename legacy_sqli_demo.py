"""
SQL Injection Before / After demonstration
"""

import hashlib
import sqlite3

from flask import Flask, request, render_template_string

app = Flask(__name__)

# Isolated temporary database for the demo
db = sqlite3.connect(":memory:", check_same_thread=False)
db.execute("""
    CREATE TABLE demo_users (
        username TEXT UNIQUE,
        password_hash TEXT,
        role TEXT
    )
""")


def md5(text):
    # Demo only: same weak hashing used in the "before" password demo
    return hashlib.md5(text.encode("utf-8")).hexdigest()


# Seed accounts. Nobody is told the admin password.
db.execute("INSERT INTO demo_users VALUES (?, ?, ?)",
           ("admin", md5("UnknownAdminPass!9"), "admin"))
db.execute("INSERT INTO demo_users VALUES (?, ?, ?)",
           ("demo_user", md5("DemoPass123!"), "user"))
db.commit()


# Page layout using the shared static/style.css. 
DEMO_STYLE = """
<style>
  .card.wide { max-width: 720px; }
  .nav { display: flex; gap: 16px; justify-content: center; margin: 0 0 20px; font-size: 14px; }
  .nav a { color: var(--muted); text-decoration: none; }
  .nav a:hover { color: var(--text); }
  .tag { display: inline-block; margin: 0 0 10px; padding: 3px 12px; font-size: 12px;
         font-weight: 700; border-radius: 999px; }
  .tag.before { background: var(--error-bg); color: var(--error-text); }
  .tag.after { background: #E8F5EC; color: #1E7B3A; }
  .center { text-align: center; }
  h3 { margin: 22px 0 8px; font-size: 14px; }
  pre { margin: 0; padding: 12px 14px; font-size: 13px; white-space: pre-wrap; word-break: break-all;
        background: var(--input); border: 1px solid var(--border); border-radius: 8px; }
  .params { margin: 8px 0 0; font-size: 13px; color: var(--muted); }
  .result { margin: 18px 0 0; padding: 12px 14px; font-size: 15px; font-weight: 600; border-radius: 8px; }
  .result.red { background: var(--error-bg); color: var(--error-text); }
  .result.green { background: #E8F5EC; color: #1E7B3A; }
  .result.orange { background: #FFF4E5; color: #9A5B00; }
  .result.black { background: var(--input); color: var(--text); }
  table { width: 100%; border-collapse: collapse; font-size: 14px; }
  th, td { padding: 10px 12px; text-align: left; border-bottom: 1px solid var(--border); }
  th { color: var(--muted); font-weight: 600; }
  .links { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
  .links a { margin-top: 8px; }
</style>
"""

HEAD = """
<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>SQLi Demo</title>
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
""" + DEMO_STYLE + "</head>"

PAGE = HEAD + """
<body>
<main class="card wide">
  <div class="nav"><a href="/">Home</a><a href="/users">View all users</a></div>
  <div class="center">
    {% if 'BEFORE' in title %}<span class="tag before">BEFORE - Vulnerable</span>{% endif %}
    {% if 'AFTER' in title %}<span class="tag after">AFTER - Secure</span>{% endif %}
  </div>
  <h1>{{ title.split(' - ')[-1] }}</h1>
  <p class="subtitle">SQL Injection demo (local testing only)</p>

  {% if form %}
  <form method="POST">
    <label for="username">Username</label>
    <input type="text" id="username" name="username">
    <label for="password">Password</label>
    <input type="password" id="password" name="password">
    <button type="submit">Submit</button>
  </form>
  {% endif %}

  {% if query %}
    <h3>Query sent to the database:</h3>
    <pre>{{ query }}</pre>
  {% endif %}
  {% if params %}<p class="params">Parameters (sent separately): {{ params }}</p>{% endif %}
  {% if result %}<p class="result {{ color }}">{{ result }}</p>{% endif %}

  {% if rows %}
    <table>
      <tr><th>Username</th><th>Role</th></tr>
      {% for r in rows %}<tr><td>{{ r[0] }}</td><td><span class="badge">{{ r[1] }}</span></td></tr>{% endfor %}
    </table>
  {% endif %}
</main>
</body></html>
"""

INDEX = HEAD + """
<body>
<main class="card wide">
  <h1>SQL Injection Demo</h1>
  <p class="subtitle">Local testing only. Restart the script to reset the demo database.</p>
  <div class="links">
    <div>
      <span class="tag before">BEFORE - Vulnerable</span>
      <a class="button button-secondary" href="/vulnerable/login">Vulnerable login</a>
      <a class="button button-secondary" href="/vulnerable/register">Vulnerable register</a>
    </div>
    <div>
      <span class="tag after">AFTER - Secure</span>
      <a class="button button-secondary" href="/secure/login">Secure login</a>
      <a class="button button-secondary" href="/secure/register">Secure register</a>
    </div>
  </div>
  <p class="footer-text"><a href="/users">View all users</a></p>
</main>
</body></html>
"""


@app.route("/")
def index():
    return render_template_string(INDEX)


# Before: vulnerable login

# User input is pasted directly into the SQL string, so the input can change the meaning of the query.
# Attack: username =  admin' --   password = anything
@app.route("/vulnerable/login", methods=["GET", "POST"])
def vulnerable_login():
    if request.method == "GET":
        return render_template_string(PAGE, title="BEFORE - Vulnerable Login", form=True)

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    # vulnerable: string formatting builds the query
    query = (
        "SELECT username, role FROM demo_users "
        f"WHERE username = '{username}' AND password_hash = '{md5(password)}'"
    )

    try:
        row = db.execute(query).fetchone()
    except sqlite3.Error as e:
        # Showing raw errors is another bad practice (information leak)
        return render_template_string(PAGE, title="BEFORE - Vulnerable Login", form=True,
                                      query=query, result=f"SQL error: {e}", color="orange")

    if row:
        result, color = f"Logged in as {row[0]} (role: {row[1]})", "red"
    else:
        result, color = "Invalid username or password.", "black"

    return render_template_string(PAGE, title="BEFORE - Vulnerable Login", form=True,
                                  query=query, result=result, color=color)


# Before: vulnerable register


# Attack (creates an ADMIN account with password "password"):
# username =  hacker', '5f4dcc3b5aa765d61d8327deb882cf99', 'admin') --
# password = anything
@app.route("/vulnerable/register", methods=["GET", "POST"])
def vulnerable_register():
    if request.method == "GET":
        return render_template_string(PAGE, title="BEFORE - Vulnerable Register", form=True)

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    # VULNERABLE: string formatting builds the query
    query = (
        "INSERT INTO demo_users (username, password_hash, role) "
        f"VALUES ('{username}', '{md5(password)}', 'user')"
    )

    try:
        db.execute(query)
        db.commit()
        result, color = "Account registered.", "black"
    except sqlite3.Error as e:
        result, color = f"SQL error: {e}", "orange"

    return render_template_string(PAGE, title="BEFORE - Vulnerable Register", form=True,
                                  query=query, result=result, color=color)


# After: secure login with a parameterized query
# The ? placeholders keep data separate from the SQL command.

@app.route("/secure/login", methods=["GET", "POST"])
def secure_login():
    if request.method == "GET":
        return render_template_string(PAGE, title="AFTER - Secure Login", form=True)

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    query = ("SELECT username, role FROM demo_users "
             "WHERE username = ? AND password_hash = ?")
    params = (username, md5(password))

    row = db.execute(query, params).fetchone()

    if row:
        result, color = f"Logged in as {row[0]} (role: {row[1]})", "green"
    else:
        result, color = "Invalid username or password.", "green"

    return render_template_string(PAGE, title="AFTER - Secure Login", form=True,
                                  query=query, params=params, result=result, color=color)


# After: secure register with a parameterized query
@app.route("/secure/register", methods=["GET", "POST"])
def secure_register():
    if request.method == "GET":
        return render_template_string(PAGE, title="AFTER - Secure Register", form=True)

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    query = ("INSERT INTO demo_users (username, password_hash, role) "
             "VALUES (?, ?, 'user')")
    params = (username, md5(password))

    try:
        db.execute(query, params)
        db.commit()
        result, color = "Account registered (role: user).", "green"
    except sqlite3.IntegrityError:
        result, color = "Username already exists.", "black"

    return render_template_string(PAGE, title="AFTER - Secure Register", form=True,
                                  query=query, params=params, result=result, color=color)


# Shows all accounts so you can see whether an injection created an admin
@app.route("/users")
def users():
    rows = db.execute("SELECT username, role FROM demo_users").fetchall()
    return render_template_string(PAGE, title="All demo users", rows=rows)


if __name__ == "__main__":
    # Local demonstration only - never deploy this file
    app.run(host="127.0.0.1", port=5002, debug=False, threaded=False)
