from flask import Flask,request,redirect,render_template,session
from flask_bcrypt import Bcrypt
from flask_session import Session
from helpers import login_required
from flask_sqlalchemy import SQLAlchemy
import re

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False     # Sessions expire when the browser is closed
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
bcrypt = Bcrypt(app) 

# Configure SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///odayssey.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Avoids a warning
# Create SQLAlchemy instance
db = SQLAlchemy(app)



class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    hash = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return f'Username: {self.username}, Hash: {self.hash}'

with app.app_context():
    db.create_all()
    

@app.route("/")
def index():
    return render_template("homepage.html")
   
@app.route("/home")
@login_required
def home():
    return render_template("index.html",username=session["username"])

@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        # Ensure username was submitted
        if not username or not password:
            return render_template("login.html",message="Invalid username or password")
        user = User.query.filter_by(username=username).first()
        if user:
            hash=user.hash
        else:
            return render_template("login.html",message="Username doesn't exist")
        is_valid = bcrypt.check_password_hash(hash, password)
        if not is_valid:
            return render_template("login.html",message="Incorrect password")
        session["username"] = username
        return redirect("/home")        
    # User reached route via GET (as by clicking a link or via redirect)
    return render_template("login.html")


@app.route("/logout")
def logout():   
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")

@app.route("/register",methods=["GET","POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        if not username :
            return render_template("register.html",message="Invalid username")
        user = User.query.filter_by(username=username).first()
        if user:
            return render_template("register.html",message="Username already exists")        
        password = request.form.get("password")
        if len(password) < 8 or not re.search(r"\d", password) or not re.search(r"[A-Z]", password):
            return render_template("register.html", message="Password must be minimum 8 characters and inlcude atlease one number and uppercase character")
        confirmation = request.form.get("confirmation")
        if not password or not confirmation:
            return render_template("register.html", message="Must enter password and confirmation")
        if password != confirmation:
            return render_template("register.html",message="Password and confirmation must match")
        hash = bcrypt.generate_password_hash(password).decode('utf-8')
        new_user = User(username=username,hash=hash)
        db.session.add(new_user)
        db.session.commit()
        return redirect("/login")
    return render_template("register.html")


