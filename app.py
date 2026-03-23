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

app = Flask(__name__)

# --- DATABASE CONFIG ---
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "database.db")}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'impactful_mind_secret_2025'
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static/uploads')

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'admin_login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- MODELS ---
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)

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
    file_path = db.Column(db.String(500))
    date_uploaded = db.Column(db.DateTime, default=datetime.utcnow)

class About(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    founder_name = db.Column(db.String(100), default="Founder")
    founder_bio = db.Column(db.Text)
    founder_image = db.Column(db.String(500))

# --- ROUTES (HIZI NDIZO ZINAZOTATUA ERROR ZAKO) ---

@app.route("/")
def home():
    try:
        carousel = Post.query.filter_by(is_carousel=True).all()
        posts = Post.query.filter_by(is_carousel=False).limit(6).all()
        books = Book.query.limit(3).all()
        return render_template('index.html', carousel_posts=carousel, posts=posts, books=books)
    except:
        return render_template('index.html', carousel_posts=[], posts=[], books=[])

# 1. SEARCH ROUTE (Iliyokuwa inakosekana kwenye Jan 5 logs)
@app.route("/search")
def search():
    query = request.args.get('q', '')
    posts = Post.query.filter(Post.title.ilike(f'%{query}%')).all()
    books = Book.query.filter(Book.title.ilike(f'%{query}%')).all()
    return render_template('search_results.html', posts=posts, books=books, query=query)

# 2. CONTACT ROUTE (Iliyokuwa inakosekana kwenye Mar 23 logs)
@app.route("/contact")
def contact():
    return render_template('contact.html', title='Wasiliana Nasi')

@app.route("/post/<int:post_id>")
def view_post(post_id):
    post = Post.query.get_or_404(post_id)
    return render_template('view_post.html', post=post)

@app.route("/admin_login", methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and sha256_crypt.verify(request.form.get('password'), user.password):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
    return render_template('login.html')

@app.route("/admin")
@login_required
def admin_dashboard():
    return render_template('dashboard.html')

# --- DB INIT ---
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        db.session.add(User(username='admin', password=sha256_crypt.hash("admin123")))
        db.session.commit()

if __name__ == '__main__':
    app.run(debug=True)
