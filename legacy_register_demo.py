
import hashlib
import sqlite3

from flask import Flask, render_template, request

app = Flask(__name__)

# Isolated temporary database for the insecure demo
db = sqlite3.connect(":memory:", check_same_thread=False)

db.execute("""
    CREATE TABLE demo_users (
        username TEXT,
        password_hash TEXT
    )
""")
db.commit()


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "GET":
        return render_template("register.html")

    username = request.form.get("username", "")
    password = request.form.get("password", "")

    # Only allow fixed dummy credentials for this demo
    if username != "demo_user" or password != "DemoPass123!":
        return "Use the provided dummy test credentials.", 400

    # BEFORE: Insecure password storage using MD5
    weak_hash = hashlib.md5(
        password.encode("utf-8")
    ).hexdigest()

    db.execute(
        "INSERT INTO demo_users VALUES (?, ?)",
        (username, weak_hash)
    )
    db.commit()

    stored_hash = db.execute(
        "SELECT password_hash FROM demo_users WHERE username = ?",
        (username,)
    ).fetchone()[0]

    return (
        "BEFORE - Insecure Registration<br>"
        "Password stored using MD5:<br>"
        f"{stored_hash}"
    )


if __name__ == "__main__":
    # Local demonstration only
    app.run(host="127.0.0.1", port=5001, debug=False, threaded=False)
