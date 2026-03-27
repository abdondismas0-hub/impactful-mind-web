import os
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# ================= 1. APP CONFIGURATION =================
app = Flask(__name__)
# Tunatumia os.environ kupata siri, ikikosekana inatumia ya default
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'siri_nzito_sana_hapa')

# Mfumo sahihi wa kusoma URL ya Postgres kutoka Render
uri = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
if uri and uri.startswith("postgres://"):
    uri = uri.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = uri
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Usanidi wa Login Manager
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Tafadhali ingia kwenye akaunti kwanza."
login_manager.login_message_category = "warning"

# ================= 2. DATABASE MODELS =================
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    # Password imewekwa urefu wa 255 ili kubeba Hash ya usalama
    password = db.Column(db.String(255), nullable=False) 
    role = db.Column(db.String(20), default='admin')

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

# ================= 3. DATABASE INITIALIZATION =================
# Hii inatengeneza Tables kwenye Postgres
with app.app_context():
    db.create_all()

# ================= 4. PUBLIC ROUTES =================
@app.route("/")
def home():
    return render_template("index.html")

@app.route("/library")
def library():
    return render_template("library.html")

@app.route("/contact")
def contact():
    return render_template("contact.html")

@app.route("/search")
def search():
    return "mfumo wa kutafuta (search) unakuja hivi karibuni

# ================= 5. AUTHENTICATION & SETUP =================
@app.route("/setup_admin")
def setup_admin():
    """ HII NI NJIA YA SIRI YA KUTENGENEZA ADMIN MARA YA KWANZA """
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        # Tunaficha password isiweze kusomeka kwenye Database (Security Level Up)
        hashed_pw = generate_password_hash('admin123')
        new_admin = User(username='admin', password=hashed_pw, role='admin')
        db.session.add(new_admin)
        db.session.commit()
        return "Hongera! Akaunti ya Admin imetengenezwa. <br> Nenda kwenye <b>/login</b> utumie Username: <b>admin</b> na Password: <b>admin123</b>"
    return "Admin tayari yupo kwenye mfumo. Tafadhali nenda kwenye ukurasa wa /login"

@app.route("/login", methods=['GET', 'POST'])
def login():
    # Kama mtu asha-login, mpeleke moja kwa moja dashboard
    if current_user.is_authenticated:
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        # Kutumia check_password_hash kuhakiki kama password ni sahihi
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Umeingia kikamilifu kwenye mfumo!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Taarifa sio sahihi. Tafadhali jaribu tena.', 'danger')
            
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash('Umetoka kwenye mfumo kwa usalama.', 'info')
    return redirect(url_for('home'))

# ================= 6. ADMIN DASHBOARD =================
@app.route("/admin")
@login_required
def admin_dashboard():
    return render_template('dashboard.html')

# ================= 7. SERVER RUN =================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
