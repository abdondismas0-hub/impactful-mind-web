import os
import sys
from datetime import datetime
from flask import Flask, render_template, url_for, flash, redirect, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from passlib.hash import sha256_crypt 
from sqlalchemy import or_
import cloudinary
import cloudinary.uploader
import cloudinary.api

# --- MWANZO WA CONFIGURATION ---
app = Flask(__name__)

# 1. DATABASE LOGIC (PostgreSQL kwa Render, SQLite kwa Local)
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "impactful_mind.db")}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'impactful_mind_professional_2025')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')

# Hakikisha folder la uploads lipo kwa ajili ya local testing
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- MIFUMO YA USALAMA NA FILE UPLOADS ---
def save_file(file_storage):
    """
    Inapakia faili Cloudinary (Online) au Static folder (Local).
    """
    if not file_storage or file_storage.filename == '':
        return None
        
    if os.environ.get('CLOUDINARY_URL'):
        try:
            upload_result = cloudinary.uploader.upload(file_storage, resource_type="auto")
            return upload_result['secure_url'] 
        except Exception as e:
            print(f">>> Kosa la Cloudinary: {e}", file=sys.stderr)
            return None
    else:
        filename = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + file_storage.filename
        file_storage.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename

# --- MODELS (DATA STRUCTURE) ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False) 
    is_admin = db.Column(db.Boolean, default=True)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    image_file = db.Column(db.String(500))
    is_carousel = db.Column(db.Boolean, default=False)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    description = db.Column(db.Text)
    file_path = db.Column(db.String(500))
    date_uploaded = db.Column(db.DateTime, default=datetime.utcnow)

class About(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    founder_name = db.Column(db.String(100), default="Mwanzilishi")
    founder_bio = db.Column(db.Text)
    founder_image = db.Column(db.String(500))

# --- CONTEXT PROCESSOR (Kuepusha Errors kwenye Templates) ---
@app.context_processor
def inject_global_data():
    try:
        about = About.query.first()
        return dict(about_info=about)
    except:
        return dict(about_info=None)

# --- ROUTES ---
@app.route("/")
def home():
    try:
        carousel = Post.query.filter_by(is_carousel=True).order_by(Post.date_posted.desc()).all()
        posts = Post.query.filter_by(is_carousel=False).order_by(Post.date_posted.desc()).limit(3).all()
        books = Book.query.order_by(Book.date_uploaded.desc()).limit(3).all()
        return render_template('index.html', carousel_posts=carousel, posts=posts, books=books)
    except Exception as e:
        print(f">>> Home Route Error: {e}", file=sys.stderr)
        return render_template('index.html', carousel_posts=[], posts=[], books=[])

@app.route("/admin_login", methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and sha256_crypt.verify(request.form.get('password'), user.password):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        flash('Ingizo si sahihi!', 'danger')
    return render_template('login.html')

@app.route("/admin")
@login_required
def admin_dashboard():
    posts = Post.query.all()
    books = Book.query.all()
    return render_template('dashboard.html', posts=posts, books=books)

@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))

# --- DB INITIALIZER ---
with app.app_context():
    try:
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            hashed_pw = sha256_crypt.hash("admin123")
            admin_user = User(username='admin', password=hashed_pw)
            db.session.add(admin_user)
        if not About.query.first():
            db.session.add(About(founder_name="Impactful Mind", founder_bio="Karibu."))
        db.session.commit()
    except Exception as e:
        print(f">>> DB Init Error: {e}", file=sys.stderr)

if __name__ == '__main__':
    app.run(debug=True)
