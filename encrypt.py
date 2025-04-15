import os
import sys
from cryptography.fernet import Fernet

if len(sys.argv) != 3:
    print("Usage: python cry.py <username> <password>")
    sys.exit(1)

username = sys.argv[1]
password = sys.argv[2]

# Generate or load encryption key
key_file = "encryption_key.key"
if os.path.exists(key_file):
    with open(key_file, "rb") as f:
        key = f.read()
else:
    key = Fernet.generate_key()
    with open(key_file, "wb") as f:
        f.write(key)

# Encrypt credentials
cipher = Fernet(key)
encrypted_username = cipher.encrypt(username.encode())
encrypted_password = cipher.encrypt(password.encode())

# Save encrypted credentials
with open("credentials.encrypted", "wb") as f:
    f.write(encrypted_username + b"\n" + encrypted_password)

print("✅ Credentials encrypted and saved to 'credentials.encrypted'")
print(f"🔐 Encryption key saved to '{key_file}' - keep this secure!")
