from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)

# 1. CONFIGURATION (Mipangilio)
# ==========================================
app.config['SECRET_KEY'] = 'tech-vibes-2026-secret' # Unaweza kubadilisha hii baadaye
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///impactful_mind.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Inamlinda mtu asiyeingia asione dashboard

# 2. DATABASE MODELS (Ramani ya Data)
# ==========================================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='user') # 'admin' ndio anaruhusiwa kuona dashboard

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)

# 3. AUTHENTICATION HELPERS
# ==========================================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 4. ROUTES (Njia za Website)
# ==========================================

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.password == password: # Kumbuka: Baadaye tutatumia Hashing kwa usalama
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Jina au Nenosiri sio sahihi. Jaribu tena.', 'danger')
            
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# 5. ADMIN DASHBOARD (Portal ya Ndani)
# ==========================================
@app.route("/admin")
@login_required
def admin_dashboard():
    # Zuia watumiaji wa kawaida wasio ma-admin
    if current_user.role != 'admin':
        flash("Huna ruhusa ya kuingia hapa.", "danger")
        return redirect(url_for('home')) # Hapa tulirekebisha bano lililokuwa limepotea
        
    posts = Post.query.all()
    books = Book.query.all()
    users = User.query.all()
    return render_template('dashboard.html', posts=posts, books=books, users=users)

# 6. PLACEHOLDERS (Kuziba Mapengo ya Error)
# Hizi zinazuia Internal Server Error kwani HTML yako inatafuta hizi link
# ==========================================

@app.route("/add_book")
@login_required
def add_book():
    return "<h1>Ukurasa wa kuongeza vitabu unakuja hivi karibuni!</h1><a href='/admin'>Rudi Dashboard</a>"

@app.route("/add_post")
@login_required
def add_post():
    return "<h1>Ukurasa wa kuongeza makala (Posts) unakuja hivi karibuni!</h1><a href='/admin'>Rudi Dashboard</a>"

@app.route("/contact")
def contact():
    return "<h1>Wasiliana nasi kupitia: techvibes@example.com</h1><a href='/'>Rudi Nyumbani</a>"

# 7. SERVER INITIALIZATION (Kuwasha Website)
# ==========================================
if __name__ == "__main__":
    with app.app_context():
        db.create_all() # Inatengeneza database file kama halipo
    
    # Kwenye Render, port inatolewa na mfumo wao
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
