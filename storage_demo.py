
import sqlite3
import hashlib
import bcrypt

# Dummy password for demonstration only
password = "DemoPass123!"

# Temporary database for the demonstration
connection = sqlite3.connect(":memory:")
cursor = connection.cursor()

cursor.execute("""
    CREATE TABLE demo_users (
        version TEXT,
        username TEXT,
        password_hash TEXT
    )
""")

# BEFORE: Weak MD5 password storage
md5_hash = hashlib.md5(
    password.encode()
).hexdigest()

cursor.execute(
    "INSERT INTO demo_users VALUES (?, ?, ?)",
    ("BEFORE - MD5", "demo_user", md5_hash)
)

# AFTER: Secure bcrypt password storage
bcrypt_hash = bcrypt.hashpw(
    password.encode(),
    bcrypt.gensalt()
).decode()

cursor.execute(
    "INSERT INTO demo_users VALUES (?, ?, ?)",
    ("AFTER - bcrypt", "demo_user", bcrypt_hash)
)

# Display the stored hash information
cursor.execute(
    "SELECT version, password_hash FROM demo_users"
)

for version, stored_hash in cursor.fetchall():
    print(version)
    print("Stored hash:", stored_hash)
    print("Hash length:", len(stored_hash))
    print()

connection.close()
