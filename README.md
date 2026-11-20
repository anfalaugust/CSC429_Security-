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
- Session management and logout (integration/testing status must be confirmed)
- HTTPS/TLS and encryption of sensitive data (integration/testing status must be confirmed)

> **Implementation note:** This README reflects the components and tests reported by the team. Features marked as pending or requiring confirmation should not be considered fully integrated until they have been merged and tested together.

## 2. Technologies Used

- Python 3
- Flask
- MySQL
- MySQL Workbench
- PyMySQL
- bcrypt
- python-dotenv
- HTML
- CSS

## 3. Project Structure

```text
SecurityWebApp/
|
|-- app.py
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
|
|-- legacy_register_demo.py
|-- legacy_sqli_demo.py
|-- password_demo.py
|-- storage_demo.py
|-- test_db.py
```

The exact template and static-file names may vary slightly depending on the latest team integration.

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
   ```

   Generate a random Flask secret key with:

   ```powershell
   .\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_hex(32))"
   ```

9. Test the database connection:

   ```powershell
   .\.venv\Scripts\python.exe test_db.py
   ```

   A successful connection should display:

   ```text
   Database connected successfully!
   ```

10. Run the application:

    ```powershell
    .\.venv\Scripts\python.exe app.py
    ```

11. Open the registration page:

    `http://127.0.0.1:5000/register`

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

The dashboard should redirect unauthenticated users to the login page.

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

Use only the isolated local demonstration and the dummy values documented in the original project instructions. Do not attempt this against a real or shared database.

The vulnerable registration demonstrates how unsafe SQL construction can allow an attacker to manipulate inserted values. The secure registration should treat the submitted value as data and assign the normal user role.

#### Test 3: Main application

Try the SQL injection login input against the main application's login page. The expected result is that authentication is not bypassed and the application displays an invalid-credentials message.

## 8. Comments, XSS Prevention, and Role-Based Access Control (Student 3)

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
| Change the test account back to `user` and start a fresh login session | Access to `/admin` is denied with HTTP 403 | Passed |

The role-change tests were performed using the local MySQL database. A fresh login session was used after changing the role so that the application would load the updated role.

## 9. Logout, HTTPS/TLS, and Encryption (Student 4)

The team should add the final implementation details and test evidence for logout, session termination, HTTPS/TLS, and encryption of sensitive data in this section after those features have been integrated and verified.

**Integration status:** Do not mark these features as complete until the relevant routes/configuration are present in the shared project and their tests pass. In the local test session documented by the team, navigating directly to `/logout` returned `404 Not Found`; therefore, the logout route still requires integration or correction and verification.

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
- Use HTTPS/TLS in a production deployment.

## 11. Project Status

The project includes the registration and password-security work, login and dashboard work, and the comments, XSS-prevention, and RBAC work described above.

Logout, HTTPS/TLS, and sensitive-data encryption must be confirmed in the integrated shared version before they are reported as completed.

All team members should update this README after merging and testing their components. The final project should be tested as one integrated application before submission.
