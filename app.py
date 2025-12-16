import os
from datetime import datetime
from flask import Flask, render_template, url_for, flash, redirect, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from passlib.hash import sha256_crypt 

# --- CONFIGURATION ---
app = Flask(__name__)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'database.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'impactful_final_key_2025' 
app.config['UPLOAD_FOLDER'] = os.path.join(BASE_DIR, 'static/uploads')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- MODELS ---
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

# --- ROUTES ---

@app.route("/")
def home():
    # Hii inahakikisha Home inafunguka hata kama DB ina shida kidogo
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
    
    # MUHIMU: Inatafuta 'index.html' moja kwa moja
    return render_template('index.html', title='Nyumbani', carousel_posts=carousel_posts, posts=latest_posts, books=latest_books, about_info=about_info)

@app.route("/library")
def library():
    try:
        books = Book.query.all()
    except:
        books = []
    return render_template('library.html', title='Maktaba', books=books)

@app.route("/posts")
def posts():
    try:
        posts = Post.query.all()
    except:
        posts = []
    return render_template('posts.html', title='Daily Posts', posts=posts)

@app.route("/contact")
def contact():
    return render_template('contact.html', title='Wasiliana Nasi')

@app.route('/post/<int:post_id>')
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('view_post.html', title=post.title, post=post)

@app.route('/download/<filename>')
def download_book(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- ADMIN ---
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
            else:
                flash('Login imeshindikana', 'danger')
        except:
            flash('DB Error', 'danger')
    return render_template('login.html')

@app.route("/admin")
@login_required
def admin_dashboard():
    try:
        total_books = Book.query.count()
        total_posts = Post.query.count()
    except:
        total_books = 0
        total_posts = 0
    return render_template('dashboard.html', total_books=total_books, total_posts=total_posts)

# ... (Routes za kuongeza vitabu/posts ziweke hapa kama kawaida) ...
# Kwa ufupi naziacha, lakini hakikisha zipo kwenye faili lako kamili

@app.route('/admin_logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('home'))

# --- DB AUTO-INIT ---
with app.app_context():
    try:
        db.create_all()
        if not User.query.filter_by(username='admin').first():
            hashed_pw = sha256_crypt.hash("adminpass")
            user = User(username='admin', password=hashed_pw, is_admin=True)
            db.session.add(user)
            db.session.commit()
        if not About.query.first():
            db.session.add(About())
            db.session.commit()
    except Exception as e:
        print(f"DB Init Error: {e}")

if __name__ == '__main__':
    app.run(debug=True)
