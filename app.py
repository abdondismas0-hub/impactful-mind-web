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

app = Flask(__name__)

# --- 1. DATABASE CONNECTION (FORCE POSTGRESQL ON RENDER) ---
database_url = os.environ.get('DATABASE_URL')

if database_url:
    # Render inatoa 'postgres://', SQLAlchemy inahitaji 'postgresql://'
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
    print(">>> SYSTEM: CONNECTED TO RENDER POSTGRESQL (SAFE DATA)", file=sys.stderr)
else:
    # Local Computer/Phone only
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DB_PATH = os.path.join(BASE_DIR, 'database.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
    print(">>> SYSTEM: RUNNING LOCALLY (SQLITE)", file=sys.stderr)

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'impactful_mind_final_key_2025')
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- HELPER: SAVE FILE (CLOUDINARY FORCE) ---
def save_file(file_storage):
    if not file_storage or file_storage.filename == '':
        return None
    
    # KAMA CLOUDINARY IPO, TUMA HUKO
    if os.environ.get('CLOUDINARY_URL'):
        try:
            # Upload (Auto detect: image/video/pdf)
            upload_result = cloudinary.uploader.upload(file_storage, resource_type="auto")
            # Rudisha Link kamili (https://...)
            return upload_result['secure_url'] 
        except Exception as e:
            print(f">>> CLOUDINARY ERROR: {e}", file=sys.stderr)
            return None
    else:
        # Local (Kama hakuna internet/Cloudinary)
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        filename = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + file_storage.filename
        file_storage.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return filename

# --- MODELS ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False) 
    is_admin = db.Column(db.Boolean, default=False)

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    # Hapa tunahifadhi URL ndefu ya Cloudinary
    image_file = db.Column(db.String(500), nullable=True) 
    is_carousel = db.Column(db.Boolean, default=False)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    description = db.Column(db.Text)
    category = db.Column(db.String(100))
    # Hapa tunahifadhi URL ndefu ya Cloudinary
    file_path = db.Column(db.String(500), nullable=False)
    date_uploaded = db.Column(db.DateTime, default=datetime.utcnow)

class Video(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    video_file = db.Column(db.String(500), nullable=False)
    date_uploaded = db.Column(db.DateTime, default=datetime.utcnow)

class About(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    founder_name = db.Column(db.String(100), default="Founder")
    founder_bio = db.Column(db.Text, default="Bio...")
    founder_image = db.Column(db.String(500))
    mission = db.Column(db.Text)
    vision = db.Column(db.Text)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)

class Visitor(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    count = db.Column(db.Integer, default=0)

@app.context_processor
def inject_vars():
    try: return dict(about_info=About.query.first())
    except: return dict(about_info=None)

# --- ROUTES ---

@app.route("/")
def home():
    try:
        # Visitor Counter
        v = Visitor.query.first()
        if not v: db.session.add(Visitor(count=1))
        else: v.count += 1
        db.session.commit()
    except: pass

    try:
        carousel = Post.query.filter_by(is_carousel=True).order_by(Post.date_posted.desc()).all()
        posts = Post.query.filter_by(is_carousel=False).order_by(Post.date_posted.desc()).limit(3).all()
        books = Book.query.order_by(Book.date_uploaded.desc()).limit(3).all()
        try: videos = Video.query.order_by(Video.date_uploaded.desc()).limit(2).all()
        except: videos = []
        about = About.query.first()
    except:
        carousel=[]; posts=[]; books=[]; videos=[]; about=None
    
    return render_template('index.html', title='Nyumbani', 
                           carousel_posts=carousel, posts=posts, 
                           books=books, videos=videos, about_info=about)

@app.route("/library")
def library():
    try: books = Book.query.all()
    except: books = []
    return render_template('library.html', title='Maktaba', books=books)

@app.route("/posts")
def posts():
    try: posts = Post.query.all()
    except: posts = []
    return render_template('posts.html', title='Daily Posts', posts=posts)

@app.route("/contact")
def contact():
    return render_template('contact.html', title='Wasiliana Nasi')

@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('view_post.html', title=post.title, post=post)

# ROUTE YA KUSOMA (HII HAILETI ERROR)
@app.route('/read/<int:book_id>')
def read_book(book_id):
    book = Book.query.get_or_404(book_id)
    return render_template('read_book.html', title=book.title, book=book)

@app.route('/download/<path:filename>')
def download_book(filename):
    # Smart Redirect: Kama ni URL, nenda huko moja kwa moja
    if filename.startswith('http'):
        return redirect(filename)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- ADMIN ROUTES ---
@app.route("/admin_login", methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        try:
            user = User.query.filter_by(username=username).first()
            if user and sha256_crypt.verify(password, user.password):
                login_user(user)
                return redirect(url_for('admin_dashboard'))
            flash('Login Failed', 'danger')
        except:
            flash('DB Error', 'danger')
    return render_template('login.html')

@app.route("/admin")
@login_required
def admin_dashboard():
    try:
        t_books = Book.query.count()
        t_posts = Post.query.count()
        try: t_videos = Video.query.count()
        except: t_videos = 0
        try: 
            v = Visitor.query.first()
            t_visit = v.count if v else 0
        except: t_visit = 0
        
        books = Book.query.order_by(Book.date_uploaded.desc()).all()
        posts = Post.query.order_by(Post.date_posted.desc()).all()
        try: videos = Video.query.order_by(Video.date_uploaded.desc()).all()
        except: videos = []
    except:
        t_books=0; t_posts=0; t_videos=0; t_visit=0
        books=[]; posts=[]; videos=[]
        
    return render_template('dashboard.html', 
                           total_books=t_books, total_posts=t_posts, 
                           total_videos=t_videos, total_visitors=t_visit,
                           books=books, posts=posts, videos=videos)

# ... (Add Routes: Add Post, Book, Video, Edit About - ZOTE ZINATUMIA save_file) ...
# Hakikisha una routes za kuongeza hapa (nimezifupisha ili kutoshea, tumia zilezile za mwanzo)
@app.route('/admin/add_post', methods=['GET', 'POST'])
@login_required
def add_post():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        is_carousel = request.form.get('is_carousel') == 'on'
        image_url = save_file(request.files.get('image_file'))
        new_post = Post(title=title, content=content, image_file=image_url, is_carousel=is_carousel)
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('add_post.html')

@app.route('/admin/add_book', methods=['GET', 'POST'])
@login_required
def add_book():
    if request.method == 'POST':
        title = request.form.get('title')
        author = request.form.get('author')
        description = request.form.get('description')
        category = request.form.get('category')
        file_url = save_file(request.files.get('pdf_file'))
        if file_url:
            new_book = Book(title=title, author=author, description=description, category=category, file_path=file_url)
            db.session.add(new_book)
            db.session.commit()
            return redirect(url_for('admin_dashboard'))
    return render_template('add_book.html')

@app.route('/admin/add_video', methods=['GET', 'POST'])
@login_required
def add_video():
    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        file_url = save_file(request.files.get('video_file'))
        if file_url:
            new_video = Video(title=title, description=description, video_file=file_url)
            db.session.add(new_video)
            db.session.commit()
            return redirect(url_for('admin_dashboard'))
    return render_template('add_video.html')

@app.route('/admin/edit_about', methods=['GET', 'POST'])
@login_required
def edit_about():
    try:
        about = About.query.first()
        if not about:
            about = About()
            db.session.add(about)
            db.session.commit()
    except: return "DB Error"
    
    if request.method == 'POST':
        about.founder_name = request.form.get('founder_name')
        about.founder_bio = request.form.get('founder_bio')
        about.mission = request.form.get('mission')
        about.vision = request.form.get('vision')
        img = save_file(request.files.get('founder_image'))
        if img: about.founder_image = img
        db.session.commit()
        return redirect(url_for('admin_dashboard'))
    return render_template('edit_about.html', about_info=about)

@app.route('/admin/delete_post/<int:id>', methods=['POST'])
@login_required
def delete_post(id):
    db.session.delete(Post.query.get_or_404(id))
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_book/<int:id>', methods=['POST'])
@login_required
def delete_book(id):
    db.session.delete(Book.query.get_or_404(id))
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete_video/<int:id>', methods=['POST'])
@login_required
def delete_video(id):
    db.session.delete(Video.query.get_or_404(id))
    db.session.commit()
    return redirect(url_for('admin_dashboard'))

@app.route('/admin_logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('home'))

# --- AUTO DB INIT ---
with app.app_context():
    try:
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            hashed = sha256_crypt.hash("adminpass")
            db.session.add(User(username='admin', password=hashed, is_admin=True))
            db.session.commit()
        if not About.query.first():
            db.session.add(About())
            db.session.commit()
        if not Visitor.query.first():
            db.session.add(Visitor(count=0))
            db.session.commit()
    except Exception as e:
        print(f"DB Init Error: {e}")

if __name__ == '__main__':
    app.run(debug=True)
