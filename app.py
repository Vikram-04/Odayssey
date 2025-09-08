from flask import Flask,request,redirect,render_template,session, jsonify
from flask_bcrypt import Bcrypt
from flask_session import Session
from helpers import login_required, isPast
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
import re
from datetime import date, datetime
import calendar

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
    habits = db.relationship('Habit', backref='users', lazy=True)
    

class Habit(db.Model):
    __tablename__ = "habits"
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)
    habit = db.Column(db.String(100), nullable=False)
    created_on = db.Column(db.Date, nullable = False)
    habit_logs = db.relationship('Habit_log', backref = 'habit', lazy=True)
    def __repr__(self):
        return f'{self.habit}'

class Habit_log(db.Model):
    __tablename__ = "habit_log"
    id = db.Column(db.Integer, primary_key = True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habits.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Boolean, default=False, nullable=False)
    def __repr__(self):
        return f'{self.date, self.done}'

with app.app_context():
    db.create_all()
    

@app.route("/")
def index():
    session.clear()
    return render_template("homepage.html")
   
@app.route("/home", methods=["GET", "POST"])
@login_required
def home():
    user_id  = User.query.filter_by(username=session["username"]).first().id
    # Get month from query parameter
    month_str = request.args.get("month")
    if month_str:
        # month_str format: YYYY-MM
        try:
            year, month = map(int, month_str.split("-"))
            today = date(year, month, 1)
        except Exception:
            today = date.today()
    else:
        today = date.today()

    if request.method == "POST":
        habit = request.form.get("habit")
        new_habit = Habit(user_id=user_id, habit=habit, created_on = date.today())
        db.session.add(new_habit)
        db.session.commit()
        return redirect("/home")
    habits = Habit.query.filter_by(user_id=user_id).all()
    habits_past = [
    habit for habit in habits
    if isPast(today.month, today.year, habit.created_on.month, habit.created_on.year)]
    days_in_month = calendar.monthrange(today.year, today.month)[1]

    # fetch logs for all habits in this month
    start_of_month = date(today.year, today.month, 1)
    logs = Habit_log.query.join(Habit).filter(
        Habit.user_id == user_id,
        Habit_log.date >= start_of_month,
        Habit_log.date <= date(today.year, today.month, days_in_month)
    ).all()
   
    marked_dates = [log.date for log in logs]
    # build dictionary {(habit_id, day): (done, log_id)}
    logs_dict = {}
    dates = []
    for day in range(1, days_in_month+1):
        dates.append(date(today.year, today.month, day))
    for log in logs:
        logs_dict[(log.habit_id, log.date)] = (log.status, log.id)
    return render_template("habits.html",
                           habits=habits_past,
                           days_in_month=days_in_month,
                           logs_dict=logs_dict,
                           month_name = calendar.month_name[today.month],
                           date=today,
                           today=today.day,dates=dates)

@app.route("/toggle_habit", methods=["POST"])
def toggle_habit():
    data = request.get_json()
    habit_id = int(data["habit_id"])
    date_str = data["date"]
    log_date = datetime.strptime(date_str, "%Y-%m-%d").date()

    log = Habit_log.query.filter_by(habit_id=habit_id, date=log_date).first()
    if not log:
        log = Habit_log(habit_id=habit_id, date=log_date, status=True)
        db.session.add(log)
    else:
        log.status = not log.status

    db.session.commit()
        
    return jsonify({"done": log.status})


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


