# app.py - Toleo la Render (Database Auto-Create)

import os
from datetime import datetime
from flask import Flask, render_template, url_for, flash, redirect, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from passlib.hash import sha256_crypt 

# --- Configuration ---
app = Flask(__name__)

# Njia Sahihi ya Database kwa Render
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'siri_kali_sana' 
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static/uploads')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Models ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False) 
    is_admin = db.Column(db.Boolean, default=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    image_file = db.Column(db.String(200), nullable=True) 
    is_carousel = db.Column(db.Boolean, default=False)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    author = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=True)
    category = db.Column(db.String(50), nullable=True)
    file_path = db.Column(db.String(200), nullable=False)
    date_uploaded = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class About(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    founder_name = db.Column(db.String(100), nullable=False, default="Jina la Founder")
    founder_bio = db.Column(db.Text, nullable=False, default="Maelezo...")
    founder_image = db.Column(db.String(200), nullable=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

# --- MUHIMU: KUUNDA DATABASE KIOTOMATIKI ---
# Code hii inaendeshwa kila Gunicorn inapoanza
with app.app_context():
    db.create_all()
    
    # Hakikisha folda ya uploads ipo
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        try:
            os.makedirs(app.config['UPLOAD_FOLDER'])
        except:
            pass

    # Unda Admin wa Default kama hayupo
    if not User.query.filter_by(username='admin').first():
        hashed_pw = sha256_crypt.hash("adminpass")
        user = User(username='admin', password=hashed_pw, is_admin=True)
        db.session.add(user)
        db.session.commit()
        
    # Unda About info kama haipo
    if not About.query.first():
        db.session.add(About())
        db.session.commit()

# --- Routes ---
@app.route("/")
def home():
    try:
        carousel_posts = Post.query.filter_by(is_carousel=True).order_by(Post.date_posted.desc()).all()
        latest_posts = Post.query.filter_by(is_carousel=False).order_by(Post.date_posted.desc()).limit(3).all()
        latest_books = Book.query.order_by(Book.date_uploaded.desc()).limit(3).all()
        about_info = About.query.first()
    except:
        carousel_posts = []
        latest_posts = []
        latest_books = []
        about_info = None
        
    return render_template('public/index.html', 
                           title='Nyumbani', 
                           carousel_posts=carousel_posts,
                           posts=latest_posts, 
                           books=latest_books,
                           about_info=about_info)

@app.route("/library")
def library():
    try:
        books = Book.query.all()
    except:
        books = []
    return render_template('public/library.html', title='Maktaba', books=books)

@app.route("/posts")
def posts():
    try:
        posts = Post.query.all()
    except:
        posts = []
    return render_template('public/posts.html', title='Daily Posts', posts=posts)

@app.route("/contact")
def contact():
    return render_template('public/contact.html', title='Wasiliana Nasi')

@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('public/view_post.html', title=post.title, post=post)

@app.route('/download/<filename>')
def download_book(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route("/admin_login", methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and sha256_crypt.verify(password, user.password):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Login imeshindikana', 'danger')
    return render_template('admin/login.html')

@app.route("/admin")
@login_required
def admin_dashboard():
    return render_template('admin/dashboard.html', 
                           total_books=Book.query.count(), 
                           total_posts=Post.query.count())

# ... (Routes za kuongeza post/book zinabaki kama zilivyo) ...
@app.route('/admin/add_post', methods=['GET', 'POST'])
@login_required
def add_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        is_carousel = request.form.get('is_carousel') == 'on'
        image = request.files.get('image_file')
        image_filename = None
        if image and image.filename != '':
            image_filename = "Post_" + datetime.now().strftime("%Y%m%d%H%M%S") + ".jpg"
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
        new_post = Post(title=title, content=content, image_file=image_filename, is_carousel=is_carousel)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/add_post.html')

@app.route('/admin/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    return render_template('admin/add_book.html') # Placeholder

@app.route('/admin/edit_about', methods=['GET', 'POST'])
@login_required
def edit_about():
    about_info = About.query.first()
    if not about_info:
        about_info = About()
        db.session.add(about_info)
        db.session.commit()
    if request.method == 'POST':
        about_info.founder_name = request.form.get('founder_name')
        about_info.founder_bio = request.form.get('founder_bio')
        image = request.files.get('founder_image')
        if image and image.filename != '':
            image_filename = "Founder_" + datetime.now().strftime("%Y%m%d%H%M%S") + ".jpg"
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))
            about_info.founder_image = image_filename
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('admin/edit_about.html', about_info=about_info)

@app.route('/admin_logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('home'))

if __name__ == '__main__':
    app.run(debug=True)
