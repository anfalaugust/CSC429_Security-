# Secure Web Application
## Detection and Mitigation of Security Vulnerabilities

## 1. Project Overview

This project demonstrates the development of a web application and the detection and mitigation of common web security vulnerabilities.

The application is developed using Python, Flask, and MySQL.

The security features implemented or documented in this repository include:
- User registration and login
- Secure password storage using bcrypt
- SQL injection prevention using parameterized queries
- Comments functionality
- Cross-Site Scripting (XSS) prevention through HTML escaping
- Role-Based Access Control (RBAC)
- Administrator dashboard
- Session management and secure logout (server-side session revocation, Back-button protection)
- HTTPS/TLS and encryption of session cookies

## 2. Technologies Used

- Python 3
- Flask
- MySQL
- MySQL Workbench
- PyMySQL
- Jinja2 (Flask templates with automatic HTML escaping)
- bcrypt
- python-dotenv
- cryptography (Fernet session encryption, TLS certificate generation)
- HTML
- CSS

## 3. Project Structure

```text
SecurityWebApp/
|
|-- app.py
|-- secure_session.py
|-- generate_cert.py
|-- db.py
|-- schema.sql
|-- requirements.txt
|-- .env.example
|-- .gitignore
|-- README.md
|
|-- static/
|   |-- style.css
|
|-- templates/
|   |-- register.html
|   |-- login.html
|   |-- dashboard.html
|   |-- comments.html
|   |-- admin.html
|   |-- 403.html
|
|-- legacy_register_demo.py
|-- legacy_sqli_demo.py
|-- legacy_xss_demo.py
|-- legacy_rbac_demo.py
|-- legacy_session_demo.py
|-- password_demo.py
|-- storage_demo.py
|-- test_db.py
```

### Isolated vulnerability demonstrations

Each "before" (vulnerable) version runs as a separate local app with dummy data, so the main application and its MySQL database are never affected:

| File | Port | Demonstrates |
|---|---|---|
| `legacy_register_demo.py` | 5001 | Weak password storage (MD5) |
| `legacy_sqli_demo.py` | 5002 | SQL injection (vulnerable vs. secure login/registration) |
| `legacy_xss_demo.py` | 5003 | Stored XSS (vulnerable vs. secure comments) |
| `legacy_rbac_demo.py` | 5004 | Broken access control (vulnerable vs. secure admin page) |
| `legacy_session_demo.py` | 5005 | Unencrypted HTTP, readable session cookie, missing logout |

## 4. Installation and Setup

1. Install Python and MySQL Server.
2. Open the project folder in VS Code.
3. Create a virtual environment:

   ```powershell
   py -m venv .venv
   ```

4. Install the required dependencies:

   ```powershell
   .\.venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

5. Open MySQL Workbench and execute `schema.sql` to create the `security_webapp` database and its tables.
6. Create a dedicated MySQL account for the application. Grant only the permissions required by the application (`SELECT`, `INSERT`, `UPDATE`, and `DELETE` on `security_webapp.*`).
7. Copy `.env.example` to a new file named `.env`.
8. Update the database settings in `.env`:

   ```env
   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_NAME=security_webapp
   DB_USER=your_mysql_user
   DB_PASSWORD=your_mysql_password
   SECRET_KEY=your_random_secret_key
   SESSION_ENCRYPTION_KEY=your_fernet_key
   ```

   Generate a random Flask secret key with:

   ```powershell
   .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
   ```

   Generate the session encryption key with:

   ```powershell
   .\.venv\Scripts\python.exe -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
   ```

9. Test the database connection:

   ```powershell
   .\.venv\Scripts\python.exe test_db.py
   ```

   A successful connection should display:

   ```text
   Database connected successfully!
   ```

10. Generate the local TLS certificate (only once):

    ```powershell
    .\.venv\Scripts\python.exe generate_cert.py
    ```

11. Run the application (it runs over HTTPS):

    ```powershell
    .\.venv\Scripts\python.exe app.py
    ```

12. Open the registration page:

    `https://127.0.0.1:5000/register`

    The browser shows a warning because the certificate is self-signed. Click **Advanced → Proceed to 127.0.0.1** (local testing only).

    Optional: to remove the warning on Windows, trust the local certificate for your user account:

    ```powershell
    certutil -addstore -user Root certs\cert.pem
    ```

> **Important:** Never commit `.env` or share real database credentials or secret keys. Only `.env.example` should be committed.

## 5. User Registration

Users can register by providing a username, password, and password confirmation.

The registration process includes:
- Username validation
- Duplicate username prevention
- Password confirmation
- Password strength validation
- Secure password hashing using bcrypt
- MySQL database integration

### Password Requirements

Passwords must:
- Contain at least 8 characters
- Include at least one uppercase letter
- Include at least one lowercase letter
- Include at least one number
- Include at least one special character

## 6. Password Security Demonstration

The project includes isolated demonstrations of insecure and secure password storage.

**Before:**
- Uses MD5 hashing
- Uses no random salt
- Produces identical hashes for identical passwords

**After:**
- Uses bcrypt
- Generates a random salt
- Provides stronger resistance to password guessing

To run the comparison:

```powershell
.\.venv\Scripts\python.exe password_demo.py
```

To demonstrate storage differences:

```powershell
.\.venv\Scripts\python.exe storage_demo.py
```

To run the isolated insecure registration demo:

```powershell
.\.venv\Scripts\python.exe legacy_register_demo.py
```

Open:

`http://127.0.0.1:5001/register`

Use dummy credentials only:

```text
Username: demo_user
Password: DemoPass123!
Confirm Password: DemoPass123!
```

The insecure demo uses a temporary in-memory SQLite database and does not modify the main MySQL database.

## 7. Login, Session Management, Dashboard, and SQL Injection

### Login and Dashboard

The login and dashboard implementation includes:
- Login using the registered username and password
- Password verification using `bcrypt.checkpw`
- Parameterized login query
- A generic error message for an incorrect username or password
- Session clearing before login to help prevent session fixation
- A dashboard displaying the username, role, and account creation date
- A reusable `@login_required` decorator to protect authenticated pages

Unauthenticated users who open the dashboard are redirected to the login page.

### SQL Injection Demonstration

The vulnerable version is isolated in `legacy_sqli_demo.py`. It uses a temporary in-memory SQLite database and does not modify the main MySQL database. Run it locally for demonstration purposes only:

```powershell
.\.venv\Scripts\python.exe legacy_sqli_demo.py
```

Open:

`http://127.0.0.1:5002`

Each page shows the SQL query sent to the database.

#### Test 1: Login bypass

1. Open `/vulnerable/login`.
2. Enter the following username and any password:

   ```text
   admin' --
   ```

3. In the vulnerable version, the input may bypass authentication.
4. Repeat the test on `/secure/login`.
5. The secure version should reject the input with an invalid-credentials message.

#### Test 2: Creating an administrator account through vulnerable registration

1. Open `/vulnerable/register`.
2. Enter the following username and any password:

   ```text
   hacker', '5f4dcc3b5aa765d61d8327deb882cf99', 'admin') --
   ```

3. Open `/users`: a new account `hacker` appears with the `admin` role.
4. Repeat the test on `/secure/register`: the whole input is saved as a plain username with the `user` role.

Use only the isolated local demonstration. Do not attempt this against a real or shared database.

The vulnerable registration demonstrates how unsafe SQL construction can allow an attacker to manipulate inserted values. The secure registration should treat the submitted value as data and assign the normal user role.

#### Test 3: Main application

Try the SQL injection login input against the main application's login page. The expected result is that authentication is not bypassed and the application displays an invalid-credentials message.

## 8. Comments, XSS Prevention, and Role-Based Access Control

### 8.1 Comments Feature

Authenticated users can open the Comments page from the dashboard, submit a comment, and view recent comments.

The comments feature stores comment text and associates each comment with the signed-in user. The comments table is created by `schema.sql` and includes a user reference.

### 8.2 Cross-Site Scripting (XSS) Prevention

User-generated comments are untrusted input. If comment text is inserted into a page as executable HTML, an attacker could submit JavaScript that runs in another user's browser.

The application renders comment content using HTML escaping in the template. This causes HTML-sensitive characters to be displayed as text instead of being interpreted as markup or script.

**Manual XSS test:**

1. Sign in with a standard user account.
2. Open the Comments page.
3. Submit this harmless test payload as a comment:

   ```html
   <script>alert('XSS Attack')</script>
   ```

4. Check the Recent comments section.

**Expected secure result:**
- The submitted text is displayed as text.
- No JavaScript alert dialog appears.
- The browser does not execute the submitted script.

**Observed test result:** During the team's local test, the payload appeared as visible text in the comments list and no alert dialog appeared.

### 8.3 Role-Based Access Control (RBAC)

The application distinguishes between standard users and administrators using the user's role.

- A standard user can access the normal dashboard and comments functionality.
- An administrator can access the administrator page.
- A standard user attempting to access `/admin` directly should receive an HTTP `403 Forbidden` response.

Authorization must be enforced on the server side. Hiding an admin link in the interface alone is not sufficient.

### 8.4 Admin Dashboard

The administrator dashboard displays user-management information, including user IDs, usernames, roles, and account creation dates.

The team tested administrator access using an account whose role was set to `admin` in the local database. The administrator page loaded and displayed the user list.

**Local role setup used during testing:**

```sql
UPDATE users
SET role = 'admin'
WHERE username = 'maram_user';
```

To restore the account to a standard user after testing:

```sql
UPDATE users
SET role = 'user'
WHERE username = 'maram_user';
```

These statements are for local testing only. Do not promote users to administrator without authorization in a real deployment.

### 8.5 Access-Control Matrix

| Action | Standard User | Administrator |
|---|---|---|
| View own dashboard | Allowed | Allowed |
| View comments | Allowed | Allowed |
| Post comments | Allowed | Allowed |
| Access `/admin` | Denied | Allowed |
| View administrator user list | Denied | Allowed |

### 8.6 Security Testing Results

The following tests were performed locally by the team:

| Test | Expected secure result | Observed result |
|---|---|---|
| Submit a normal comment | Comment is saved and displayed | Passed |
| Submit the XSS test payload | Payload is displayed as text; script is not executed | Passed |
| Standard user opens `/admin` directly | Access is denied with HTTP 403 | Passed |
| Administrator opens `/admin` | Admin dashboard is displayed | Passed |
| Change the test account role back to `user` | Access to `/admin` is denied with HTTP 403 | Passed |

The role-change tests were performed using the local MySQL database. The application retrieves the user's current role from the database when checking access to the admin page.

### 8.7 Isolated XSS Before-and-After Demonstration

The project includes an isolated demonstration in `legacy_xss_demo.py` to compare vulnerable and secure comment rendering.

Run the demonstration:

```powershell
.\.venv\Scripts\python.exe legacy_xss_demo.py
```

Open:

`http://127.0.0.1:5003`

The demonstration provides two versions:

- **Before – Vulnerable Comments:** Uses unsafe HTML rendering (`|safe`), allowing submitted JavaScript to execute.
- **After – Secure Comments:** Uses HTML escaping to display submitted content as text instead of executing it.

**Test payload:**

```html
<script>alert('XSS Attack')</script>
```

**Observed results:**
- Vulnerable version: The JavaScript executed and displayed an alert dialog.
- Secure version: The payload appeared as visible text, and no alert dialog appeared.

This demonstration shows how HTML escaping prevents stored XSS when displaying user-generated content.

### 8.8 Isolated RBAC Before-and-After Demonstration

The project includes an isolated demonstration in `legacy_rbac_demo.py` to show the importance of server-side authorization.

Run the demonstration:

```powershell
.\.venv\Scripts\python.exe legacy_rbac_demo.py
```

Open:

`http://127.0.0.1:5004`

The demonstration provides two user accounts:

- `demo_user`: Standard user.
- `demo_admin`: Administrator.

It also provides two administrator routes:

- **Before – `/vulnerable/admin`:** No role verification is performed, allowing a standard user to access the administrator page.
- **After – `/secure/admin`:** Checks the authenticated user's role and allows access only to administrators.

**Observed test results:**

| Test | Expected result | Observed result |
|---|---|---|
| Standard user accesses `/vulnerable/admin` | Access allowed due to missing authorization | Passed |
| Standard user accesses `/secure/admin` | HTTP 403 Forbidden | Passed |
| Administrator accesses `/secure/admin` | Access allowed | Passed |

These isolated demonstrations use local test accounts and are intended for educational purposes only. They do not modify the main application's MySQL database.

## 9. Logout, HTTPS/TLS, and Encryption

### 9.0 Isolated Before demonstration

The vulnerable state is isolated in `legacy_session_demo.py`. It runs over plain HTTP with one dummy account and does not touch the MySQL database:

```powershell
.\.venv\Scripts\python.exe legacy_session_demo.py
```

Open `http://127.0.0.1:5005` and log in with the account shown on the page (password `DemoPass123!`).

- **Plain HTTP:** the browser reports that the connection is not secure.
- **Readable cookie:** click **Inspect my session cookie**. The page decodes Flask's default (signed, not encrypted) cookie without the secret key and shows the username and role.
- **No logout:** click **Logout** → `404 Not Found`, so the session cannot be ended.

### 9.1 Logout and session termination

The dashboard has a **Logout** button that sends a `POST` request to `/logout`. The route:

1. Removes the user's random session id (`sid`) from the server-side `ACTIVE_SESSIONS` set (server-side revocation).
2. Calls `session.clear()` to delete `user_id`, `username`, `role` and `sid`.
3. Sends a `Set-Cookie` header that expires the session cookie in the browser.
4. Redirects the user to `/login`.

Each login creates a new random `sid` (`secrets.token_urlsafe(32)`). Before every request, `reject_revoked_sessions()` checks that the `sid` is still active. If someone copied the cookie before logout, the copy stops working after logout.

### 9.2 Back button and direct-URL protection

- **Back button:** every protected page (`/dashboard`, `/comments`, `/admin`) is sent with `Cache-Control: no-store, no-cache, must-revalidate, max-age=0`, `Pragma: no-cache` and `Expires: 0`. The browser keeps no copy of the page, so after logout the Back button asks the server again, and the server redirects to `/login`.
- **Direct URL:** typing `https://127.0.0.1:5000/dashboard` after logout reaches the `@login_required` check, finds no session and redirects to `/login`.

### 9.3 HTTPS/TLS

- `generate_cert.py` creates a self-signed certificate (RSA 2048, SHA-256, valid for 365 days) in `certs/`. The `certs/` folder is listed in `.gitignore`, so the private key is never committed.
- `app.py` runs Flask with an `ssl.SSLContext` that accepts **TLS 1.2 or newer** only (TLS 1.0/1.1 are rejected).
- `Strict-Transport-Security` (HSTS) is sent over HTTPS. In a real deployment with a domain name and a trusted certificate, it tells the browser to use HTTPS only; browsers ignore it for local IP addresses and self-signed certificates.
- Extra headers: `X-Content-Type-Options: nosniff` and `X-Frame-Options: DENY` (prevents clickjacking).
- Because the certificate is self-signed, the browser shows "Not secure" until the certificate is trusted locally (see Installation step 12). The connection is encrypted either way (TLS 1.3 with AES_256_GCM, visible in DevTools → Security). In production, a certificate from a trusted CA (e.g. Let's Encrypt) would be used.

### 9.4 Encrypted and secure session cookies

Flask's default session cookie is **signed but not encrypted**: anyone can base64-decode it and read the username and role. `secure_session.py` replaces the cookie serializer with **Fernet** encryption from the `cryptography` library (AES-128-CBC for confidentiality + HMAC-SHA256 for integrity). The key (`SESSION_ENCRYPTION_KEY`) is stored only in `.env`.

Cookie flags configured in `app.py`:

| Flag | Value | Why |
|---|---|---|
| `Secure` | True | Cookie is sent over HTTPS only |
| `HttpOnly` | True | JavaScript cannot read the cookie (reduces XSS impact) |
| `SameSite` | Lax | Cookie is not sent with cross-site POST or embedded requests (reduces CSRF) |
| Lifetime | 30 minutes | Session expires after 30 minutes of inactivity; Fernet also rejects older tokens |

### 9.5 How to test

1. **HTTPS:** open `https://127.0.0.1:5000/login` and press `F12` → **Security**: the connection uses TLS. Opening `http://127.0.0.1:5000/login` (without the s) does not work.
2. **Encrypted cookie:** log in, press `F12` → **Application** → **Cookies** → `session`. The value starts with `gAAAAA` (Fernet token); the username is not readable. The columns show `Secure` ✓, `HttpOnly` ✓, `SameSite = Lax`.
3. **Logout:** click **Logout** → you are sent to `/login` and the `session` cookie disappears.
4. **Back button:** after logout, press the browser Back button → you are redirected to `/login`, the dashboard is not shown.
5. **Direct URL:** after logout, type `https://127.0.0.1:5000/dashboard` → redirected to `/login`.
6. **Tampered cookie:** edit a few characters of the cookie value in DevTools and refresh → the session is rejected and you are redirected to `/login`.

### 9.6 Security testing results

The TLS 1.1, copied-cookie and modified-cookie tests were also run as automated tests against the application code.

| Test | Expected secure result | Observed result |
|---|---|---|
| Open the app over HTTPS | Page loads over TLS 1.2/1.3 | Passed (TLS 1.3) |
| Connect using TLS 1.1 | Connection refused | Passed |
| Inspect the session cookie | Content encrypted, not readable | Passed |
| Check cookie flags | `Secure`, `HttpOnly`, `SameSite=Lax` set | Passed |
| Click Logout | Session cleared, cookie deleted, redirect to `/login` | Passed |
| Press Back after logout | Redirect to `/login`, dashboard not shown | Passed |
| Open `/dashboard` by URL after logout | Redirect to `/login` | Passed |
| Reuse a copied cookie after logout | Rejected, redirect to `/login` | Passed |
| Modify the cookie value | Rejected, redirect to `/login` | Passed |

### 9.7 Page integration

The pages were connected into one flow:

- `/` redirects to `/login` (or to `/dashboard` if already logged in).
- Registration errors are shown on the registration page itself; a successful registration redirects to `/login` with a success message.
- The dashboard has a **Comments** button for all users and an **Admin Page** button shown only to administrators. Hiding the button is only for usability: `/admin` is still protected on the server by `@admin_required`.
- A standard user who opens `/admin` sees a friendly **403 Access denied** page with a link back to the dashboard.

## 10. Security Notes

- Database credentials and the Flask secret key belong in `.env`.
- The `.env` file must not be uploaded to GitHub.
- Commit `.env.example` with placeholder values only.
- Use a dedicated MySQL account instead of the MySQL `root` account.
- Use parameterized queries for database operations involving user input.
- Store passwords using bcrypt, not plaintext or MD5.
- Treat comments and all other user-generated content as untrusted input.
- Escape user-generated content when rendering it in HTML.
- Enforce role checks on the server side for protected routes.
- Keep vulnerable demonstrations isolated and run them locally only.
- The Flask development server is not intended for production deployment.
- In production, replace the self-signed certificate with one from a trusted CA and use a production WSGI server.

## 11. Conclusion

This project developed a user management web application using Python, Flask and MySQL to demonstrate five common web security vulnerabilities and their mitigations. For each one, we built an isolated vulnerable demo, showed how it could be attacked, and then applied and tested the fix in the main application.

SQL injection was prevented with parameterized queries, and weak MD5 password storage was replaced with salted bcrypt hashing and server-side password rules. Cross-Site Scripting was prevented by escaping user content when it is displayed, and broken access control was fixed with server-side role checks that return HTTP 403 Forbidden to standard users. Finally, data is now protected by HTTPS with TLS 1.2 or newer, an encrypted and secured session cookie, and a logout that ends the session on the server. All tests in the security testing tables produced the expected secure result.

The main lesson is that security needs several layers working together, and that the best fixes address the root cause instead of filtering input. A real deployment would also need a trusted certificate, a production web server, CSRF tokens, and a shared session store such as Redis.

## 12. References

[1] OWASP Foundation. "OWASP Top 10:2025." OWASP. Accessed: Nov. 21, 2026. [Online]. Available: https://owasp.org/Top10/2025/

[2] OWASP Foundation. "SQL Injection Prevention Cheat Sheet." OWASP Cheat Sheet Series. Accessed: Nov. 21, 2026. [Online]. Available: https://cheatsheetseries.owasp.org/cheatsheets/SQL_Injection_Prevention_Cheat_Sheet.html

[3] OWASP Foundation. "Password Storage Cheat Sheet." OWASP Cheat Sheet Series. Accessed: Nov. 21, 2026. [Online]. Available: https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html

[4] Python Cryptographic Authority. "bcrypt." Python Package Index (PyPI). Accessed: Nov. 21, 2026. [Online]. Available: https://pypi.org/project/bcrypt/

[5] OWASP Foundation. "Cross Site Scripting Prevention Cheat Sheet." OWASP Cheat Sheet Series. Accessed: Nov. 21, 2026. [Online]. Available: https://cheatsheetseries.owasp.org/cheatsheets/Cross_Site_Scripting_Prevention_Cheat_Sheet.html

[6] OWASP Foundation. "Authorization Cheat Sheet." OWASP Cheat Sheet Series. Accessed: Nov. 21, 2026. [Online]. Available: https://cheatsheetseries.owasp.org/cheatsheets/Authorization_Cheat_Sheet.html

[7] E. Rescorla, "The Transport Layer Security (TLS) Protocol Version 1.3," Internet Engineering Task Force, RFC 8446, Aug. 2018. [Online]. Available: https://www.rfc-editor.org/rfc/rfc8446

[8] OWASP Foundation. "Transport Layer Security Cheat Sheet." OWASP Cheat Sheet Series. Accessed: Nov. 21, 2026. [Online]. Available: https://cheatsheetseries.owasp.org/cheatsheets/Transport_Layer_Security_Cheat_Sheet.html

[9] Python Cryptographic Authority. "Fernet (symmetric encryption)." Cryptography Documentation. Accessed: Nov. 21, 2026. [Online]. Available: https://cryptography.io/en/latest/fernet/

[10] Pallets Projects. "Security Considerations." Flask Documentation. Accessed: Nov. 21, 2026. [Online]. Available: https://flask.palletsprojects.com/en/stable/web-security/

[11] OWASP Foundation. "Session Management Cheat Sheet." OWASP Cheat Sheet Series. Accessed: Nov. 21, 2026. [Online]. Available: https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html

[12] Mozilla. "Cache-Control header." MDN Web Docs. Accessed: Nov. 21, 2026. [Online]. Available: https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Headers/Cache-Control

[13] PyMySQL Contributors. "PyMySQL Documentation." Read the Docs. Accessed: Nov. 21, 2026. [Online]. Available: https://pymysql.readthedocs.io/

[14] Pallets Projects. "Template Designer Documentation: HTML Escaping." Jinja Documentation. Accessed: Nov. 21, 2026. [Online]. Available: https://jinja.palletsprojects.com/en/stable/templates/#html-escaping