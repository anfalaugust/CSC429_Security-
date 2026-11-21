import os
from functools import wraps
import bcrypt
import pymysql
import string
import secrets
import ssl
from datetime import timedelta

from flask import Flask, render_template, request, session, redirect, url_for, abort
from db import get_db_connection
from secure_session import EncryptedCookieSessionInterface

# Initialize Flask application
app = Flask(__name__)

# Load the secret key from .env to sign the session cookie and prevent tampering
app.secret_key = os.getenv("SECRET_KEY")
if not app.secret_key:
    raise RuntimeError("SECRET_KEY is missing. Add it to your .env file.")


SESSION_ENCRYPTION_KEY = os.getenv("SESSION_ENCRYPTION_KEY")
if not SESSION_ENCRYPTION_KEY:
    raise RuntimeError(
        "SESSION_ENCRYPTION_KEY is missing. Generate one with: "
        "python -c \"from cryptography.fernet import Fernet; "
        "print(Fernet.generate_key().decode())\""
    )

app.session_interface = EncryptedCookieSessionInterface(SESSION_ENCRYPTION_KEY)

app.config.update(
    # Secure: browser sends the cookie over HTTPS only, never plain HTTP
    SESSION_COOKIE_SECURE=True,
    # HttpOnly: JavaScript cannot read the cookie (limits damage of XSS)
    SESSION_COOKIE_HTTPONLY=True,
    # SameSite=Lax: cookie is not sent with cross-site POST requests (CSRF help)
    SESSION_COOKIE_SAMESITE="Lax",
    # Sessions expire automatically after 30 minutes
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
)


ACTIVE_SESSIONS = set()


@app.before_request
def reject_revoked_sessions():
    """Treat a session whose sid was revoked (or is unknown) as logged out."""
    if "user_id" in session and session.get("sid") not in ACTIVE_SESSIONS:
        session.clear()


# Pages that must never be shown from the browser cache after logout
PROTECTED_PATHS = ("/dashboard", "/comments", "/admin")


@app.after_request
def add_security_headers(response):
    """Add security headers to every response.

    - Cache-Control no-store on protected pages: the browser keeps no copy of
      them, so pressing Back after logout re-requests the page from the server,
      and the server redirects to /login because the session is gone.
    """
    if request.path.startswith(PROTECTED_PATHS) or "user_id" in session:
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"

    if request.is_secure:
        response.headers["Strict-Transport-Security"] = "max-age=31536000"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    return response


# Home page
@app.route("/")
def home():
    # Send users to the right page instead of showing plain text
    if "user_id" in session:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


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
        return render_template("register.html", error="Username must be between 1 and 50 characters."), 400

    # Validate password length
    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters."), 400

    # bcrypt supports passwords up to 72 bytes
    if len(password.encode("utf-8")) > 72:
        return render_template("register.html", error="Password must not exceed 72 bytes."), 400

    # Require at least one uppercase letter
    if not any(c.isupper() for c in password):
        return render_template("register.html", error="Password needs an uppercase letter."), 400

    # Require at least one lowercase letter
    if not any(c.islower() for c in password):
        return render_template("register.html", error="Password needs a lowercase letter."), 400

    # Require at least one number
    if not any(c.isdigit() for c in password):
        return render_template("register.html", error="Password needs a number."), 400

    # Require at least one special character
    if not any(c in string.punctuation for c in password):
        return render_template("register.html", error="Password needs a special character."), 400

    # Confirm that both passwords match
    if password != confirm_password:
        return render_template("register.html", error="Passwords do not match."), 400

        # Why bcrypt instead of MD5:
    # - MD5 is very fast, so an attacker with a stolen database can test billions
    #   of guesses per second. bcrypt is slow on purpose (default cost factor 12),
    #   which makes offline password guessing much harder.
    # - bcrypt.gensalt() creates a unique random salt for every password, so two
    #   users with the same password get different hashes and precomputed
    #   (rainbow) tables are useless.
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
            return render_template("register.html", error="Username already exists."), 409

        return render_template("register.html", error="Registration failed. Please try again."), 500

    except pymysql.MySQLError:
        if connection:
            connection.rollback()

        # Avoid exposing internal database errors to users
        return render_template("register.html", error="Registration failed. Please try again."), 500

    finally:
        # Always close the database connection
        if connection:
            connection.close()

    # Go to the login page and show a success message there
    return redirect(url_for("login", registered=1))


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


def admin_required(view):
    """Allow access only when the current database record has the admin role.

    The role is reloaded from MySQL instead of trusting the role value in the
    client-side signed session. This prevents a stale session from retaining
    admin access after an administrator's role has been changed.
    """
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))

        connection = None
        try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT role FROM users WHERE id = %s",
                    (session["user_id"],)
                )
                current_user = cursor.fetchone()
        except pymysql.MySQLError:
            return "Could not verify permissions. Please try again.", 500
        finally:
            if connection:
                connection.close()

        if not current_user:
            session.clear()
            return redirect(url_for("login"))

        if current_user["role"] != "admin":
            abort(403)

        # Keep the session role in sync for display purposes only.
        session["role"] = current_user["role"]
        return view(*args, **kwargs)
    return wrapped_view


# User login page
@app.route("/login", methods=["GET", "POST"])
def login():

    # Display login form or go straight to dashboard if already logged in
    if request.method == "GET":
        if "user_id" in session:
            return redirect(url_for("dashboard"))
        message = None
        if request.args.get("registered"):
            message = "Account registered successfully! You can log in now."
        return render_template("login.html", message=message)

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
    # random, unguessable session id registered on the server
    session["sid"] = secrets.token_urlsafe(32)
    ACTIVE_SESSIONS.add(session["sid"])
    # make the session expire after PERMANENT_SESSION_LIFETIME
    session.permanent = True

    return redirect(url_for("dashboard"))


# Logout 
@app.route("/logout", methods=["GET", "POST"])
def logout():

    # Revoke the session on the server so a copied cookie stops working
    ACTIVE_SESSIONS.discard(session.get("sid"))
    session.clear()
    response = redirect(url_for("login"))
    # Belt and braces: explicitly expire the cookie as well
    response.delete_cookie(
        app.config.get("SESSION_COOKIE_NAME", "session"),
        secure=True, httponly=True, samesite="Lax"
    )
    return response


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


# Comments feature and XSS protection 
@app.route("/comments", methods=["GET", "POST"])
@login_required
def comments():
    """Let signed-in users post plain-text comments and read the discussion.

    Comment content is stored as text, never marked safe as HTML. Jinja2's
    automatic HTML escaping is enabled in the template when values are shown.
    """
    if request.method == "POST":
        comment_text = request.form.get("comment", "").strip()

        # Remove NUL characters and reject empty/oversized comments.
        comment_text = comment_text.replace("\x00", "")
        if not comment_text:
            return render_template(
                "comments.html", comments=[], error="Please enter a comment."
            ), 400
        if len(comment_text) > 1000:
            return render_template(
                "comments.html", comments=[],
                error="Comments must be 1000 characters or fewer."
            ), 400

        connection = None
        try:
            connection = get_db_connection()
            with connection.cursor() as cursor:
                # Parameterized SQL keeps comment text separate from the query.
                cursor.execute(
                    "INSERT INTO comments (user_id, comment_text) VALUES (%s, %s)",
                    (session["user_id"], comment_text)
                )
            connection.commit()
        except pymysql.MySQLError:
            if connection:
                connection.rollback()
            return "Could not save your comment. Please try again.", 500
        finally:
            if connection:
                connection.close()

        return redirect(url_for("comments"))

    connection = None
    comment_rows = []
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                """SELECT comments.id, comments.comment_text,
                          comments.created_at, users.username
                   FROM comments
                   JOIN users ON users.id = comments.user_id
                   ORDER BY comments.created_at DESC, comments.id DESC"""
            )
            comment_rows = cursor.fetchall()
    except pymysql.MySQLError:
        return "Could not load comments. Please try again.", 500
    finally:
        if connection:
            connection.close()

    return render_template("comments.html", comments=comment_rows)


# Admin-only user management page
@app.route("/admin")
@admin_required
def admin():
    connection = None
    users = []
    try:
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT id, username, role, created_at FROM users ORDER BY id ASC"
            )
            users = cursor.fetchall()
    except pymysql.MySQLError:
        return "Could not load user management. Please try again.", 500
    finally:
        if connection:
            connection.close()

    return render_template("admin.html", users=users)


# Friendly page for HTTP 403 (standard user opens /admin)
@app.errorhandler(403)
def forbidden(error):
    return render_template("403.html"), 403


# Run locally over HTTPS (TLS) with debug mode disabled 
if __name__ == "__main__":
    cert_file = os.path.join("certs", "cert.pem")
    key_file = os.path.join("certs", "key.pem")
    if not (os.path.exists(cert_file) and os.path.exists(key_file)):
        raise RuntimeError("TLS certificate not found. Run: python generate_cert.py")

    # Secure communication: HTTPS encrypts everything sent between the browser
    # and the server (passwords, session cookie), so an attacker on the same
    # network cannot read or modify it.
    # Accept TLS 1.2 or newer only; SSL and TLS 1.0/1.1 have known weaknesses.
    tls_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    tls_context.minimum_version = ssl.TLSVersion.TLSv1_2
    tls_context.load_cert_chain(cert_file, key_file)

    app.run(host="127.0.0.1", port=5000, debug=False, ssl_context=tls_context)