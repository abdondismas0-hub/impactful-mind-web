import os
import sys
from datetime import datetime
from flask import Flask, render_template, url_for, flash, redirect, request, send_from_directory, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required
from passlib.hash import sha256_crypt 
from sqlalchemy import or_

# ==========================================
# 1. APP CONFIGURATION & ARCHITECTURE
# ==========================================
app = Flask(__name__)

# Database Logic (PostgreSQL kwa Live, SQLite kwa Local)
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "impactful_mind.db")}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'super_secret_production_key_2026')

db = SQLAlchemy(app)

# Authentication Setup
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Ikiitwa bila login, inakuleta hapa
login_manager.login_message_category = "info"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ==========================================
# 2. DATABASE MODELS (Data Structure)
# ==========================================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='user') # admin au user

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_posted = db.Column(db.DateTime, default=datetime.utcnow)
    image_url = db.Column(db.String(500)) # Link ya Cloudinary
    is_carousel = db.Column(db.Boolean, default=False) # Kwa ajili ya Slideshow

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(100))
    file_url = db.Column(db.String(500))
    date_uploaded = db.Column(db.DateTime, default=datetime.utcnow)

class About(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    founder_name = db.Column(db.String(100), default="Jina la Founder")
    founder_bio = db.Column(db.Text)
    founder_image = db.Column(db.String(500))

# Inject data kwenye kurasa zote (Kuepusha errors)
@app.context_processor
def inject_global():
    try: about = About.query.first()
    except: about = None
    return dict(about_info=about)

# ==========================================
# 3. PUBLIC ROUTES (Kurasa za Nje)
# ==========================================
@app.route("/")
def home():
    try:
        # Vuta posts za Slideshow (Carousel)
        carousel = Post.query.filter_by(is_carousel=True).order_by(Post.date_posted.desc()).all()
        # Vuta posts za kawaida
        posts = Post.query.filter_by(is_carousel=False).order_by(Post.date_posted.desc()).limit(6).all()
        # Vuta vitabu
        books = Book.query.order_by(Book.date_uploaded.desc()).limit(3).all()
        return render_template('index.html', carousel_posts=carousel, posts=posts, books=books)
    except Exception as e:
        print(f"Error on Home: {e}")
        return render_template('index.html', carousel_posts=[], posts=[], books=[])

@app.route("/search")
def search():
    query = request.args.get('q', '')
    posts = Post.query.filter(Post.title.ilike(f'%{query}%')).all()
    books = Book.query.filter(Book.title.ilike(f'%{query}%')).all()
    return render_template('search.html', posts=posts, books=books, query=query)

@app.route("/library")
def library():
    books = Book.query.all()
    return render_template('library.html', books=books)

@app.route("/contact")
def contact():
    # Mfumo wako wa wasiliana nasi unabaki hapa (Kama ulivyoomba)
    return render_template('contact.html')

# ==========================================
# 4. AUTHENTICATION (Ulinzi na Login)
# ==========================================
@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and sha256_crypt.verify(request.form.get('password'), user.password):
            login_user(user)
            flash('Umefanikiwa kuingia!', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Jina au Nenosiri sio sahihi.', 'danger')
    return render_template('login.html')

@app.route("/logout")
@login_required
def auth_logout():
    logout_user()
    flash('Umetoka kwenye mfumo.', 'info')
    return redirect(url_for('home'))

# ==========================================
# 5. ADMIN DASHBOARD (Portal ya Ndani)
# ==========================================
@app.route("/admin")
@login_required
def admin_dashboard():
    # Zuia watu wasio admins kuingia hapa
    if current_user.role != 'admin':
        flash("Huna ruhusa ya kuingia hapa.", "danger")
        return redirect(url_for('home'))
                          
    posts = Post.query.all()
    books = Book.query.all()
    users = User.query.all()
    return render_template('dashboard.html', posts=posts, books=books, users=users)

# ==========================================
# 6. SYSTEM INITIALIZATION (Kuwasha Database)
# ==========================================
with app.app_context():
    db.create_all()
    # Tengeneza Admin wa kwanza kama hayupo
    if not User.query.filter_by(username='admin').first():
        hashed = sha256_crypt.hash("admin123")
        db.session.add(User(username='admin', password=hashed, role='admin'))
        db.session.commit()
    # Tengeneza About section kama haipo
    if not About.query.first():
        db.session.add(About(founder_name="Mkurugenzi", founder_bio="Karibu Impactful Mind."))
        db.session.commit()

@app.route("/add_book")
@login_required
def add_book():
    return "sehemu ya vitabu inakuja ivi karibumi"
    
if __name__ == '__main__':
    app.run(debug=True)
