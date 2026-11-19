
import hashlib
import bcrypt

# Dummy password for local testing only
password = "DemoPass123!"

# BEFORE: Weak password hashing using MD5
md5_hash = hashlib.md5(password.encode()).hexdigest()

print("BEFORE - MD5:")
print("MD5 Hash:", md5_hash)

# AFTER: Secure password hashing using bcrypt
bcrypt_hash = bcrypt.hashpw(
    password.encode(),
    bcrypt.gensalt()
)

print("\nAFTER - bcrypt:")
print("bcrypt Hash:", bcrypt_hash.decode())

# Verify the password using bcrypt
is_valid = bcrypt.checkpw(
    password.encode(),
    bcrypt_hash
)

print("Password verification:", is_valid)

# Compare hashing the same password twice
md5_second = hashlib.md5(password.encode()).hexdigest()

bcrypt_second = bcrypt.hashpw(
    password.encode(),
    bcrypt.gensalt()
).decode()

print("\n--- Hash Comparison ---")
print("MD5 hashes identical:", md5_hash == md5_second)
print("bcrypt hashes identical:", bcrypt_hash.decode() == bcrypt_second)
