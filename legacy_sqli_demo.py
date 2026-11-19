"""
SQL Injection Bfore and after demonstration.
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
    # same weak hashing used in the "before" password demo
    return hashlib.md5(text.encode("utf-8")).hexdigest()


# Seed accounts. Nobody is told the admin password.
db.execute("INSERT INTO demo_users VALUES (?, ?, ?)",
           ("admin", md5("UnknownAdminPass!9"), "admin"))
db.execute("INSERT INTO demo_users VALUES (?, ?, ?)",
           ("demo_user", md5("DemoPass123!"), "user"))
db.commit()


# Simple page layout. {{ }} auto-escapes output, so the demo itself is not vulnerable to XSS while showing the SQL query.
PAGE = """
<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>SQLi Demo</title></head>
<body>
  <p><a href="/">Home</a> | <a href="/users">View all users</a></p>
  <h1>{{ title }}</h1>
  {% if form %}
  <form method="POST">
    <label>Username</label><br>
    <input name="username" size="60"><br><br>
    <label>Password</label><br>
    <input name="password" type="password"><br><br>
    <button type="submit">Submit</button>
  </form>
  {% endif %}
  {% if query %}
    <h3>Query sent to the database:</h3>
    <pre style="background:#eee;padding:8px">{{ query }}</pre>
  {% endif %}
  {% if params %}<p>Parameters (sent separately): {{ params }}</p>{% endif %}
  {% if result %}<h3 style="color:{{ color }}">{{ result }}</h3>{% endif %}
  {% if rows %}
    <table border="1" cellpadding="6">
      <tr><th>username</th><th>role</th></tr>
      {% for r in rows %}<tr><td>{{ r[0] }}</td><td>{{ r[1] }}</td></tr>{% endfor %}
    </table>
  {% endif %}
</body></html>
"""


@app.route("/")
def index():
    return """
    <h1>SQL Injection Demo (local only)</h1>
    <h2>BEFORE - vulnerable</h2>
    <ul>
      <li><a href="/vulnerable/login">Vulnerable login</a></li>
      <li><a href="/vulnerable/register">Vulnerable register</a></li>
    </ul>
    <h2>AFTER - parameterized queries</h2>
    <ul>
      <li><a href="/secure/login">Secure login</a></li>
      <li><a href="/secure/register">Secure register</a></li>
    </ul>
    <p><a href="/users">View all users</a></p>
    """



# Before: vulnerable login
# User input is pasted directly into the SQL string, so the input can change the meaning of the query

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
# creates an admin account with password "password"

# username =  hacker', '5f4dcc3b5aa765d61d8327deb882cf99', 'admin') -- password = anything
@app.route("/vulnerable/register", methods=["GET", "POST"])
def vulnerable_register():
    if request.method == "GET":
        return render_template_string(PAGE, title="BEFORE - Vulnerable Register", form=True)

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    # vulnerable: string formatting builds the query
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

@app.route("/secure/login", methods=["GET", "POST"])
def secure_login():
    if request.method == "GET":
        return render_template_string(PAGE, title="AFTER - Secure Login", form=True)

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    # The ? placeholders keep data separate from the SQL command
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


# AFTER: secure register with a parameterized query

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
