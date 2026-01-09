# Secure Decentralized File Storage System Using Blockchain

A premium, secure web application for storing, locking, and converting files with Blockchain-backed integrity.

## Features
- 🔐 **Blockchain Integrity**: Every file hash is stored in a (simulated) blockchain ledger for tamper-proof verification.
- 🛡️ **AES-256 Encryption**: Files are encrypted before storage. Only the owner with the correct file password can unlock them.
- 🔄 **Smart Conversion**: Convert files between PDF, DOCX, JPG, PNG, and TXT while maintaining security.
- 📁 **Folder System**: Organize files into blockchain-linked folders.
- 🤖 **AI Assistant**: Built-in chatbot to help you navigate and understand blockchain security.
- 🎨 **Premium UI**: Modern glassmorphism design with smooth animations and dark mode aesthetics.

## Tech Stack
- **Backend**: Python, Flask, Flask-SQLAlchemy, Flask-Login, Flask-Bcrypt
- **Blockchain**: Simulation logic (extensible to Ethereum with Web3.py)
- **Security**: AES-256 (PyCryptodome), SHA-256
- **Frontend**: HTML5, Premium CSS (Glassmorphism), JavaScript, Bootstrap 5

## Setup Instructions
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   python app.py
   ```
3. Open `http://127.0.0.1:5000` in your browser.

## Security Architecture
1. **User Auth**: Password hashed with Bcrypt.
2. **File Storage**:
   - User uploads a file.
   - File is hashed (SHA-256) for blockchain recording.
   - File is encrypted (AES-256) using a per-file password.
   - Encrypted file is saved to the local secure file system.
3. **Download**:
   - User requests download.
   - System verifies file password.
   - System decrypts file in memory and serves the original stream.
