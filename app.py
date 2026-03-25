from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'siri_yako_hapa'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ================= MODELS =================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='user')

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)

class Book(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ================= ROUTES ZA KAWAIDA =================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form.get('username')).first()
        if user and user.password == request.form.get('password'):
            login_user(user)
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Login Failed. Check username and password', 'danger')
            
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ================= ADMIN DASHBOARD YAKO =================
@app.route("/admin")
@login_required
def admin_dashboard():
    # Zuia watu wasio admins kuingia hapa
    if current_user.role != 'admin':
        flash("Huna ruhusa ya kuingia hapa.", "danger")
        return redirect(url_for('home')) # HAPA NDIPO BANO LILIKUWA LIMESAHAULIKA

    posts = Post.query.all()
    books = Book.query.all()
    users = User.query.all()
    return render_template('dashboard.html', posts=posts, books=books, users=users)

# ================= ROUTES ZA MPITO (KUZUIA ERROR) =================
# Hizi ndizo zinazuia "Could not build url for endpoint"

@app.route("/add_book") # HAPA NDIPO ULIPOWEKA BACKSLASH (\) BADALA YA FORWARD SLASH (/)
@login_required
def add_book():
    return "Sehemu ya kuongeza vitabu inajengwa."

@app.route("/add_post")
@login_required
def add_post():
    return "Sehemu ya kuongeza makala inajengwa."

# ================= KUWASHA SERVER =================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
