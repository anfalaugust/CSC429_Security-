
# Secure Web Application
## Detection and Mitigation of Security Vulnerabilities

### 1. Project Overview

This project aims to develop a secure web application
that demonstrates the detection and mitigation of
common web security vulnerabilities.

The application is developed using Python, Flask,
and MySQL.

The security features include:
- SQL Injection Prevention
- Secure Password Storage
- Cross-Site Scripting (XSS) Prevention
- Role-Based Access Control (RBAC)
- Encryption and HTTPS/TLS

### 2. Technologies Used

- Python 3
- Flask
- MySQL
- MySQL Workbench
- PyMySQL
- bcrypt
- python-dotenv
- HTML

### 3. Project Structure

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
|-- templates/
|   |-- register.html
|   |-- login.html
|   |-- dashboard.html
|
|-- legacy_register_demo.py
|-- legacy_sqli_demo.py
|-- password_demo.py
|-- storage_demo.py
|-- test_db.py

### 4. Installation and Setup

1. Install Python and MySQL.

2. Open the project folder in VS Code.

3. Create a virtual environment:

   py -m venv .venv

4. Install the required dependencies:

   .\.venv\Scripts\python.exe -m pip install -r requirements.txt

5. Open MySQL Workbench and execute schema.sql
   to create the security_webapp database and
   the users table.

6. Create a dedicated MySQL account for the
   application with SELECT, INSERT, UPDATE,
   and DELETE permissions on security_webapp.

7. Copy .env.example to a new file named .env.

8. Update the database settings in .env:

   DB_HOST=127.0.0.1
   DB_PORT=3306
   DB_NAME=security_webapp
   DB_USER=your_mysql_user
   DB_PASSWORD=your_mysql_password
   SECRET_KEY=your_random_secret_key

9. Run the application:

   .\.venv\Scripts\python.exe app.py

10. Open the registration page:

    http://127.0.0.1:5000/register

### 5. Implemented Features

#### User Registration

Users can register by providing a username,
password, and password confirmation.

The registration process includes:
- Username validation
- Duplicate username prevention
- Password confirmation
- Password strength validation
- Secure password hashing using bcrypt
- MySQL database integration

#### Password Requirements

Passwords must:
- Contain at least 8 characters
- Include an uppercase letter
- Include a lowercase letter
- Include a number
- Include a special character

### 6. Password Security Demonstration

The project includes isolated demonstrations
of insecure and secure password storage.

BEFORE:
- Uses MD5 hashing
- Uses no random salt
- Produces identical hashes for identical passwords

AFTER:
- Uses bcrypt
- Generates a random salt
- Provides stronger resistance to password guessing

To run the comparison:

    python password_demo.py

To demonstrate storage differences:

    python storage_demo.py

To run the isolated insecure registration demo:

    python legacy_register_demo.py

Open:

    http://127.0.0.1:5001/register

Use these dummy credentials only:

Username: demo_user
Password: DemoPass123!
Confirm Password: DemoPass123!

The insecure demo uses a temporary in-memory
SQLite database and does not modify the main
MySQL database.

### 7. Registration Security Tests

Completed tests:

1. Valid Registration: Passed
2. Weak Password Rejection: Passed
3. Password Mismatch: Passed
4. Duplicate Username Rejection: Passed
5. bcrypt Hash Storage: Passed
6. MD5 vs bcrypt Comparison: Passed

The rejected registration tests were checked
against the database to verify that no rejected
test accounts were stored.


### Login, Session Management and Dashboard (Student 2)

#### Setup

Add a secret key to your `.env` file (used to sign the session cookie):

    SECRET_KEY=paste_a_long_random_value_here

Generate one with:

    python -c "import secrets; print(secrets.token_hex(32))"


#### Features

- Login at `http://127.0.0.1:5000/login`
- Passwords are checked with `bcrypt.checkpw` against the stored hash
- The login query uses a parameterized query (SQL injection prevention)
- The same error message is shown for a wrong username or a wrong password
- The session is cleared before login to prevent session fixation
- `/dashboard` shows the username, role and account creation date
- `/dashboard` redirects to `/login` if the user is not logged in
- A reusable `@login_required` decorator protects pages

### SQL Injection Demonstration

The vulnerable version is isolated in `legacy_sqli_demo.py`.
It uses a temporary in-memory SQLite database and does not
modify the main MySQL database. Local testing only.

Run:

    python legacy_sqli_demo.py

Open:

    http://127.0.0.1:5002

Each page shows the exact SQL query sent to the database.

#### Test 1: Login bypass

1. Open `/vulnerable/login`
2. Username: `admin' --`   Password: anything
3. BEFORE result: logged in as admin without knowing the password
4. Repeat on `/secure/login`
5. AFTER result: "Invalid username or password."

#### Test 2: Creating an admin account through registration

1. Open `/vulnerable/register`
2. Username: `hacker', '5f4dcc3b5aa765d61d8327deb882cf99', 'admin') --`
   Password: anything
3. Open `/users`: a new user `hacker` with role `admin` appears
4. Log in on `/vulnerable/login` as `hacker` / `password` (role: admin)
5. Repeat step 2 on `/secure/register`
6. AFTER result: the whole input is saved as a plain username with role `user`

#### Test 3: Main application

Try `admin' --` on `http://127.0.0.1:5000/login`.
Expected result: "Invalid username or password."


### 8. Features Pending Integration

The following features will be implemented
by other team members:

- Comments and XSS prevention
- Admin page and RBAC
- Logout and session termination
- HTTPS/TLS and sensitive-data encryption

Their implementations and testing instructions
must be added to this README after integration.

### 9. Security Notes

- Database credentials are stored in .env.
- The .env file must not be uploaded to GitHub.
- A dedicated MySQL account is used instead of root.
- The final registration code uses parameterized queries.
- Passwords are stored using bcrypt, not plaintext.
- The insecure demonstrations must run locally only.
- The Flask development server is not intended
  for production deployment.

### 10. Project Status

This README documents the current Student 1
implementation. It will be updated when all
team components are integrated and tested.
