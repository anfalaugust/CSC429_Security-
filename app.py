import os
from functools import wraps
import bcrypt
import pymysql
import string

from flask import Flask, render_template, request, session, redirect, url_for
from db import get_db_connection

# Initialize Flask application
app = Flask(__name__)

# Load the secret key from .env to sign the session cookie and prevent tampering
app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY is missing. Add it to your .env file.")


# Home page
@app.route("/")
def home():
    return "Security Web Application is running!"


# User registration page
@app.route("/register", methods=["GET", "POST"])
def register():

    # Display registration form
    if request.method == "GET":
        return render_template("register.html")

    # Retrieve registration data
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")
    confirm_password = request.form.get("confirm_password", "")

    # Validate username
    if not username or len(username) > 50:
        return "Username must be between 1 and 50 characters.", 400

    # Validate password length
    if len(password) < 8:
        return "Password must be at least 8 characters.", 400

    # bcrypt supports passwords up to 72 bytes
    if len(password.encode("utf-8")) > 72:
        return "Password must not exceed 72 bytes.", 400

    # Require at least one uppercase letter
    if not any(c.isupper() for c in password):
        return "Password needs an uppercase letter.", 400

    # Require at least one lowercase letter
    if not any(c.islower() for c in password):
        return "Password needs a lowercase letter.", 400

    # Require at least one number
    if not any(c.isdigit() for c in password):
        return "Password needs a number.", 400

    # Require at least one special character
    if not any(c in string.punctuation for c in password):
        return "Password needs a special character.", 400

    # Confirm that both passwords match
    if password != confirm_password:
        return "Passwords do not match.", 400

    # Secure password hashing using bcrypt
    # A unique random salt is generated for each password
    hashed_password = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt()
    ).decode("utf-8")

    connection = None

    try:
        # Connect to MySQL database
        connection = get_db_connection()

        with connection.cursor() as cursor:

            # Parameterized query prevents SQL injection
            cursor.execute(
                """
                INSERT INTO users (username, password_hash)
                VALUES (%s, %s)
                """,
                (username, hashed_password)
            )

        # Save the new user
        connection.commit()

    except pymysql.err.IntegrityError as error:
        if connection:
            connection.rollback()

        # MySQL error 1062: Duplicate entry
        if error.args[0] == 1062:
            return "Username already exists.", 409

        return "Registration failed. Please try again.", 500

    except pymysql.MySQLError:
        if connection:
            connection.rollback()

        # Avoid exposing internal database errors to users
        return "Registration failed. Please try again.", 500

    finally:
        # Always close the database connection
        if connection:
            connection.close()

    return "Account registered successfully!"


# Login, session management and dashboard


# Dummy hash keeps response time the same so attackers can't guess valid usernames
DUMMY_HASH = bcrypt.hashpw(b"dummy-password", bcrypt.gensalt())

GENERIC_LOGIN_ERROR = "Invalid username or password."


def login_required(view):
    """Decorator that blocks access to a page unless the user is logged in.

    Other team members can reuse it on their own pages, e.g.:
        @app.route("/comments")
        @login_required
        def comments(): ...
    """
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped_view


# User login page
@app.route("/login", methods=["GET", "POST"])
def login():

    # Display login form or go straight to dashboard if already logged in
    if request.method == "GET":
        if "user_id" in session:
            return redirect(url_for("dashboard"))
        return render_template("login.html")

    # Retrieve login data
    username = request.form.get("username", "").strip()
    password = request.form.get("password", "")

    # Reject empty or oversized input before touching the database
    if (not username or not password
            or len(username) > 50
            or len(password.encode("utf-8")) > 72):
        return render_template("login.html", error=GENERIC_LOGIN_ERROR), 401

    connection = None
    user = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:

            # Parameterized query prevents SQL injection by treating input as plain text
            cursor.execute(
                """
                SELECT id, username, password_hash, role
                FROM users
                WHERE username = %s
                """,
                (username,)
            )
            
            user = cursor.fetchone()

    except pymysql.MySQLError:
        # Do not expose internal database errors to the user
        return render_template(
            "login.html", error="Login failed. Please try again."
        ), 500

    finally:
        if connection:
            connection.close()

    # Verify the password with bcrypt: compares against the stored salted hash
    stored_hash = user["password_hash"].encode("utf-8") if user else DUMMY_HASH
    password_ok = bcrypt.checkpw(password.encode("utf-8"), stored_hash)

    # Same message for wrong username and wrong password so attackers cannot tell which usernames exist
    if not user or not password_ok:
        return render_template("login.html", error=GENERIC_LOGIN_ERROR), 401

    # Clear any old session data first to prevent session fixation then store only the minimum information needed
    session.clear()
    session["user_id"] = user["id"]
    session["username"] = user["username"]
    session["role"] = user["role"]

    return redirect(url_for("dashboard"))


# User dashboard: only for logged-in users
@app.route("/dashboard")
@login_required
def dashboard():

    connection = None
    user = None

    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:

            # Load fresh profile data using the id stored in the session
            cursor.execute(
                """
                SELECT username, role, created_at
                FROM users
                WHERE id = %s
                """,
                (session["user_id"],)
            )
            user = cursor.fetchone()

    except pymysql.MySQLError:
        return "Could not load dashboard. Please try again.", 500

    finally:
        if connection:
            connection.close()

    # If the account no longer exists, end the session
    if not user:
        session.clear()
        return redirect(url_for("login"))

    return render_template("dashboard.html", user=user)


# Run locally with debug mode disabled
if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
