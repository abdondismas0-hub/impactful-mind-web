from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import os

# ================= 1. APP CONFIGURATION =================
app = Flask(__name__)
app.config['SECRET_KEY'] = 'siri_nzito_sana_hapa' 
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login' # Inaelekeza watumiaji wasio na login kwenda /login
login_manager.login_message = "Tafadhali ingia kwenye akaunti kwanza."
login_manager.login_message_category = "info"

# ================= 2. DATABASE MODELS =================
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

with app.app_context():
    db.create_all()

# ================= 3. PUBLIC ROUTES (Kuzuia BuildErrors) =================
# Hapa tumeweka endpoints zote ambazo HTML inazitafuta ili zisivunje app

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/library")
def library():
    try:
        return render_template("library.html")
    except:
        return "Ukurasa wa Library unajengwa. (Template haijapatikana)"

@app.route("/contact")
def contact():
    # HII NDIO ILIKUWA INALETA ERROR KWENYE LOGS ZAKO MPYA
    try:
        return render_template("contact.html")
    except:
        return "Ukurasa wa Mawasiliano (Contact) unajengwa."

@app.route("/about")
def about():
    try:
        return render_template("about.html")
    except:
        return "Ukurasa wa Kuhusu Sisi unajengwa."

@app.route("/search")
def search():
    return "Mfumo wa kutafuta (Search) unakuja hivi karibuni."

# ================= 4. AUTHENTICATION (Login / Logout) =================
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
            flash('Taarifa sio sahihi. Jaribu tena.', 'danger')
            
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ================= 5. ADMIN & PROTECTED ROUTES =================
@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash("Huna ruhusa ya kuingia hapa.", "danger")
        return redirect(url_for('home'))

    posts = Post.query.all()
    books = Book.query.all()
    users = User.query.all()
    return render_template('dashboard.html', posts=posts, books=books, users=users)

@app.route("/add_book")
@login_required
def add_book():
    return "Fomu ya kuongeza vitabu inakuja hivi karibuni."

@app.route("/add_post")
@login_required
def add_post():
    return "Fomu ya kuongeza makala inakuja hivi karibuni."

# ================= 6. SERVER INITIALIZATION =================
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
        
