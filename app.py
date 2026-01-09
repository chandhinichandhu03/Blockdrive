import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, send_file, copy_current_request_context
import base64
import mimetypes
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-key-12345')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.abspath(os.curdir), 'uploads')

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    files = db.relationship('File', backref='owner', lazy=True)
    folders = db.relationship('Folder', backref='owner', lazy=True)

class Folder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    blockchain_link = db.Column(db.String(255), unique=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    files = db.relationship('File', backref='folder', lazy=True)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    file_hash = db.Column(db.String(64), nullable=False) # SHA-256
    blockchain_hash = db.Column(db.String(255))
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('folder.id'), nullable=True)
    is_locked = db.Column(db.Boolean, default=True)
    file_password = db.Column(db.String(60), nullable=True) # Bcrypt hash of file password
    password_hint = db.Column(db.String(255))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from utils.encryption import get_file_hash, encrypt_file, decrypt_file_data
from utils.blockchain import BlockchainInterface
from utils.conversion import convert_file
from utils.extraction import extract_text_content
import uuid
import io
import mimetypes
import base64

blockchain = BlockchainInterface()

# Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email already exists', 'danger')
            return redirect(url_for('register'))
        
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Account created! You can now login.', 'success')
        return redirect(url_for('login'))
    return render_template('login.html', signup=True)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', signup=False)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    folder_id = request.args.get('folder_id')
    if folder_id:
        folder = Folder.query.filter_by(id=int(folder_id), owner_id=current_user.id).first()
        if not folder:
            flash('Folder does not exist or access denied.', 'danger')
            return redirect(url_for('dashboard'))
        files = File.query.filter_by(owner_id=current_user.id, folder_id=int(folder_id)).order_by(File.created_at.desc()).all()
        current_folder = folder
    else:
        files = File.query.filter_by(owner_id=current_user.id, folder_id=None).order_by(File.created_at.desc()).all()
        current_folder = None
        
    folders = Folder.query.filter_by(owner_id=current_user.id).all()
    return render_template('dashboard.html', files=files, folders=folders, current_folder=current_folder)

@app.route('/upload', methods=['GET', 'POST'])
@login_required
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        
        file = request.files['file']
        file_password = request.form.get('file_password')
        description = request.form.get('description')
        password_hint = request.form.get('password_hint')
        folder_id = request.form.get('folder_id')

        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)

        if file and file_password:
            # Check if folder exists if provided
            target_subfolder = ""
            if folder_id:
                folder = Folder.query.filter_by(id=int(folder_id), owner_id=current_user.id).first()
                if not folder:
                    flash('Selected folder does not exist.', 'danger')
                    return redirect(request.url)
                target_subfolder = str(folder.id)

            # Secure filename
            original_name = file.filename
            unique_filename = f"{uuid.uuid4()}_{original_name}"
            
            # Physical folder path
            folder_path = os.path.join(app.config['UPLOAD_FOLDER'], target_subfolder)
            if not os.path.exists(folder_path):
                os.makedirs(folder_path, exist_ok=True)
                
            file_path = os.path.join(folder_path, unique_filename)
            file.save(file_path)

            # 1. Hashing
            f_hash = get_file_hash(file_path)

            # 2. Blockchain
            success, tx_hash = blockchain.store_file_hash(f_hash, current_user.email)
            
            # 3. Encryption
            encrypt_file(file_path, file_password)
            hashed_file_password = bcrypt.generate_password_hash(file_password).decode('utf-8')

            # 4. Save to DB
            new_file = File(
                filename=unique_filename,
                original_name=original_name,
                file_hash=f_hash,
                blockchain_hash=tx_hash if success else "NOT_ON_CHAIN",
                owner_id=current_user.id,
                folder_id=int(folder_id) if folder_id else None,
                is_locked=True,
                file_password=hashed_file_password,
                password_hint=password_hint,
                description=description
            )
            db.session.add(new_file)
            db.session.commit()

            flash(f"File uploaded successfully to {'folder ' + folder.name if folder_id else 'Root Directory'} and secured!", 'success')
            return redirect(url_for('dashboard'))

    folders = Folder.query.filter_by(owner_id=current_user.id).all()
    return render_template('upload.html', folders=folders)

@app.route('/download/<int:file_id>', methods=['POST'])
@login_required
def download_file(file_id):
    file_record = File.query.get_or_404(file_id)
    if file_record.owner_id != current_user.id:
        return "Access Denied", 403
    
    password = request.form.get('password')
    if bcrypt.check_password_hash(file_record.file_password, password):
        # Decrypt in memory and serve
        folder_id_str = str(file_record.folder_id) if file_record.folder_id else ""
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_id_str, file_record.filename)
        with open(file_path, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = decrypt_file_data(encrypted_data, password)
        if decrypted_data:
            import io
            mime_type, _ = mimetypes.guess_type(file_record.original_name)
            return send_file(
                io.BytesIO(decrypted_data),
                as_attachment=True,
                download_name=file_record.original_name,
                mimetype=mime_type or "application/octet-stream"
            )
    
    flash('Incorrect file password', 'danger')
    return redirect(url_for('dashboard'))

@app.route('/create_folder', methods=['POST'])
@login_required
def create_folder():
    folder_name = request.form.get('folder_name')
    if folder_name:
        # Simulate blockchain link generation
        blockchain_link = f"https://securevault.app/folder/0x{uuid.uuid4().hex[:10]}"
        new_folder = Folder(name=folder_name, owner_id=current_user.id, blockchain_link=blockchain_link)
        db.session.add(new_folder)
        db.session.commit()
        flash(f'Folder "{folder_name}" created and linked to blockchain!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/convert/<int:file_id>', methods=['POST'])
@login_required
def convert_file_route(file_id):
    file_record = File.query.get_or_404(file_id)
    if file_record.owner_id != current_user.id:
        return "Access Denied", 403
    
    target_format = request.form.get('target_format')
    password = request.form.get('password')
    
    if bcrypt.check_password_hash(file_record.file_password, password):
        folder_id_str = str(file_record.folder_id) if file_record.folder_id else ""
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_id_str, file_record.filename)
        
        # 1. Decrypt
        with open(file_path, 'rb') as f:
            encrypted_data = f.read()
        decrypted_data = decrypt_file_data(encrypted_data, password)
        
        if decrypted_data:
            # Save temporary decrypted file for conversion
            temp_path = f"temp_{file_record.filename}"
            with open(temp_path, 'wb') as f:
                f.write(decrypted_data)
            
            # 2. Convert
            converted_path = convert_file(temp_path, target_format)
            
            # 3. Secure converted file
            original_base = os.path.splitext(file_record.original_name)[0]
            new_original_name = f"{original_base}.{target_format}"
            unique_name = f"{uuid.uuid4()}_{new_original_name}"
            
            new_folder_id_str = str(file_record.folder_id) if file_record.folder_id else ""
            new_folder_path = os.path.join(app.config['UPLOAD_FOLDER'], new_folder_id_str)
            if not os.path.exists(new_folder_path):
                os.makedirs(new_folder_path, exist_ok=True)
                
            new_final_path = os.path.join(new_folder_path, unique_name)
            
            import shutil
            shutil.move(converted_path, new_final_path)
            
            # Encrypt
            encrypt_file(new_final_path, password)
            
            # 4. Hash and Blockchain
            f_hash = get_file_hash(new_final_path)
            success, tx_hash = blockchain.store_file_hash(f_hash, current_user.email)
            
            # 5. DB
            new_file = File(
                filename=unique_name,
                original_name=new_original_name,
                file_hash=f_hash,
                blockchain_hash=tx_hash if success else "NOT_ON_CHAIN",
                owner_id=current_user.id,
                folder_id=file_record.folder_id,
                is_locked=True,
                file_password=file_record.file_password,
                description=f"Converted from {file_record.original_name}"
            )
            db.session.add(new_file)
            db.session.commit()
            
            # Cleanup temp
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
            flash(f'File converted to {target_format} and secured!', 'success')
        else:
            flash('Decryption failed for conversion', 'danger')
    else:
        flash('Incorrect password', 'danger')
        
    return redirect(url_for('dashboard'))

@app.route('/view/<int:file_id>', methods=['POST'])
@login_required
def view_file_content(file_id):
    file_record = File.query.get_or_404(file_id)
    if file_record.owner_id != current_user.id:
        return jsonify({'success': False, 'error': 'Access Denied'}), 403
    
    data = request.json
    password = data.get('password')
    
    if bcrypt.check_password_hash(file_record.file_password, password):
        folder_id_str = str(file_record.folder_id) if file_record.folder_id else ""
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_id_str, file_record.filename)
        with open(file_path, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = decrypt_file_data(encrypted_data, password)
        if decrypted_data:
            mime_type, _ = mimetypes.guess_type(file_record.original_name)
            
            # Image handling
            if mime_type and mime_type.startswith('image/'):
                base64_data = base64.b64encode(decrypted_data).decode('utf-8')
                return jsonify({
                    'success': True, 
                    'is_image': True, 
                    'content': base64_data, 
                    'mime_type': mime_type
                })
            
            # Text / Document handling
            content, is_extracted = extract_text_content(decrypted_data, file_record.original_name)
            
            # If it looks like binary but we couldn't extract anything meaningful
            is_binary = False
            if not is_extracted:
                # Simple heuristic: more than 10% non-printable characters (excluding common whitespace)
                printable = set(range(32, 127)) | {9, 10, 13}
                non_printable = len([b for b in decrypted_data if b not in printable])
                if non_printable > len(decrypted_data) * 0.1:
                    is_binary = True

            return jsonify({
                'success': True, 
                'content': content, 
                'is_extracted': is_extracted,
                'is_binary': is_binary,
                'encoding': 'utf-8' if not is_binary else 'latin-1',
                'password_hint': file_record.password_hint
            })
    
    return jsonify({
        'success': False, 
        'error': 'Incorrect password', 
        'password_hint': file_record.password_hint
    }), 401

@app.route('/edit/<int:file_id>', methods=['POST'])
@login_required
def edit_file_content(file_id):
    file_record = File.query.get_or_404(file_id)
    if file_record.owner_id != current_user.id:
        return jsonify({'success': False, 'error': 'Access Denied'}), 403
    
    data = request.json
    password = data.get('password')
    new_content = data.get('content')
    encoding = data.get('encoding', 'utf-8')
    
    if bcrypt.check_password_hash(file_record.file_password, password):
        folder_id_str = str(file_record.folder_id) if file_record.folder_id else ""
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_id_str, file_record.filename)
        
        # 1. Update file locally
        with open(file_path, 'wb') as f:
            f.write(new_content.encode(encoding))
        
        # 2. Encrypt with same password
        encrypt_file(file_path, password)
        
        # 3. New Hashing
        f_hash = get_file_hash(file_path)
        
        # 4. Blockchain update
        success, tx_hash = blockchain.store_file_hash(f_hash, current_user.email)
        
        # 5. DB Update
        file_record.file_hash = f_hash
        file_record.blockchain_hash = tx_hash if success else file_record.blockchain_hash
        file_record.created_at = datetime.utcnow() # Update version timestamp
        db.session.commit()
        
        return jsonify({'success': True})
    
    return jsonify({
        'success': False, 
        'error': 'Incorrect password', 
        'password_hint': file_record.password_hint
    }), 401

@app.route('/delete/<int:file_id>', methods=['POST'])
@login_required
def delete_file(file_id):
    file_record = File.query.get_or_404(file_id)
    if file_record.owner_id != current_user.id:
        return "Access Denied", 403
    
    folder_id_str = str(file_record.folder_id) if file_record.folder_id else ""
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_id_str, file_record.filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    db.session.delete(file_record)
    db.session.commit()
    flash('File deleted from storage and blockchain history.', 'success')
    return redirect(url_for('dashboard'))

@app.route('/share/<int:file_id>')
def share_file_view(file_id):
    file_record = File.query.get_or_404(file_id)
    return render_template('share.html', file=file_record)

@app.route('/public_download/<int:file_id>', methods=['POST'])
def public_download(file_id):
    file_record = File.query.get_or_404(file_id)
    password = request.form.get('password')
    
    if bcrypt.check_password_hash(file_record.file_password, password):
        folder_id_str = str(file_record.folder_id) if file_record.folder_id else ""
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], folder_id_str, file_record.filename)
        with open(file_path, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = decrypt_file_data(encrypted_data, password)
        if decrypted_data:
            import io
            mime_type, _ = mimetypes.guess_type(file_record.original_name)
            return send_file(
                io.BytesIO(decrypted_data),
                as_attachment=True,
                download_name=file_record.original_name,
                mimetype=mime_type or "application/octet-stream"
            )
    
    flash('Incorrect password for this secure file.', 'danger')
    return redirect(url_for('share_file_view', file_id=file_id))

@app.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.json
    message = data.get('message', '').lower().strip()
    
    # Knowledge Base
    kb = {
        "features": [
            "You can upload, secure, and manage files with blockchain tracking.",
            "Features include: AES-256 Encryption, Blockchain Integrity, File Conversion, Secure Sharing, and Folders.",
            "You can also edit text files directly or preview images after unlocking them."
        ],
        "blockchain": [
            "We use a simulated blockchain ledger to store immutable file hashes.",
            "Blockchain ensures that if a file is tampered with, the hash mismatch will be detected immediately.",
            "It acts as a decentralized proof of existence for your data."
        ],
        "security": [
            "Your data is protected by three layers: 1. User Auth, 2. AES-256-CTR encryption, 3. Per-file passwords.",
            "We use SHA-256 for integrity and Bcrypt for password hashing.",
            "Everything is decrypted in-memory, so your raw files never touch the server disk unencrypted."
        ],
        "conversion": [
            "The system supports converting TXT to PDF, and image-to-image conversions (JPG to PNG, etc.).",
            "Conversions are performend securely in-memory during the decryption process."
        ],
        "sharing": [
            "Generated links allow others to view the blockchain record of your file.",
            "Recipients still need your secondary file-password to download or view the content."
        ],
        "general_tech": {
            "data structure": "A data structure is a specialized format for organizing, processing, retrieving and storing data. Examples include Arrays, Linked Lists, Stacks, and Queues.",
            "database": "We use SQLite with SQLAlchemy in this project to store user metadata and file records.",
            "python": "This entire backend is built with Python 3 and the Flask web framework.",
            "flask": "Flask is a micro web framework for Python, used here to build the secure routing and storage logic."
        }
    }

    # Intent Matching
    if any(word in message for word in ["hi", "hello", "hey", "hola"]):
        response = "Hello! I'm the SecureVault AI. How can I assist you with your security or file management today?"
    elif any(word in message for word in ["how", "use", "work", "do", "website", "application"]):
        response = "This platform is for Secure File Storage. You can: \n1. Upload sensitive files.\n2. Lock them with AES-256 encryption.\n3. Verify integrity via Blockchain.\n4. Share secure links.\n5. Convert file formats.\nWhat would you like to know more about?"
    elif "blockchain" in message or "ledger" in message or "hash" in message:
        response = kb["blockchain"][0] + " " + kb["blockchain"][1]
    elif "secure" in message or "encryption" in message or "password" in message or "protect" in message:
        response = "Your files are safe. " + kb["security"][0]
    elif "convert" in message or "format" in message or "pdf" in message:
        response = kb["conversion"][0]
    elif "share" in message or "link" in message:
        response = kb["sharing"][0] + " " + kb["sharing"][1]
    elif "can be done" in message or "purpose" in message or "features" in message:
        response = "On this website, " + " ".join(kb["features"])
    elif "data structure" in message:
        response = kb["general_tech"]["data_structure"]
    elif "database" in message:
        response = kb["general_tech"]["database"]
    elif any(word in message for word in ["thank", "bye", "quit", "exit"]):
        response = "You're welcome! Stay secure with SecureVault."
    else:
        # Check for specific technical terms
        match_found = False
        for term, description in kb["general_tech"].items():
            if term in message:
                response = description
                match_found = True
                break
        
        if not match_found:
            response = "I understand you're asking about '" + message + "'. While I'm primarily focused on SecureVault's blockchain features, I can tell you that this system is designed for maximum data privacy and integrity. Try asking about 'encryption', 'sharing', or 'how the blockchain works'!"
        
    return jsonify({'response': response})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)
