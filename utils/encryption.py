import os
import hashlib
from Crypto.Cipher import AES
from Crypto.Util import Counter

def get_file_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read and update hash string value in blocks of 4K
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def encrypt_file(file_path, password):
    # Derive a key from the password
    key = hashlib.sha256(password.encode()).digest()
    
    # Use CTR mode for simplicity and no padding needed
    # In a production app, use GCM for authentication
    iv = os.urandom(8)
    ctr = Counter.new(64, prefix=iv)
    cipher = AES.new(key, AES.MODE_CTR, counter=ctr)
    
    with open(file_path, "rb") as f:
        data = f.read()
    
    encrypted_data = iv + cipher.encrypt(data)
    
    with open(file_path, "wb") as f:
        f.write(encrypted_data)

def decrypt_file_data(encrypted_data, password):
    try:
        key = hashlib.sha256(password.encode()).digest()
        iv = encrypted_data[:8]
        ctr = Counter.new(64, prefix=iv)
        cipher = AES.new(key, AES.MODE_CTR, counter=ctr)
        
        decrypted_data = cipher.decrypt(encrypted_data[8:])
        return decrypted_data
    except Exception as e:
        print(f"Decryption failed: {e}")
        return None
