from flask import Flask,request,redirect,render_template,session, jsonify
from flask_bcrypt import Bcrypt
from flask_session import Session
from helpers import login_required, isPast, isActive, fetch_quote
from flask_sqlalchemy import SQLAlchemy
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
    habits = db.relationship('Habit', backref='users', lazy=True) # AI-assisted: Using relationships from sqlalchemy
    tasks = db.relationship('Task', backref='users', lazy=True)
    

class Habit(db.Model):
    __tablename__ = "habits"
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)
    habit = db.Column(db.String(100), nullable=False)
    created_on = db.Column(db.Date, nullable = False)
    deleted_on = db.Column(db.Date, nullable = True)
    habit_logs = db.relationship('Habit_log', backref = 'habit', lazy=True)
    def __repr__(self):
        return f'{self.habit}'

class Habit_log(db.Model):
    __tablename__ = "habit_logs"
    id = db.Column(db.Integer, primary_key = True)
    habit_id = db.Column(db.Integer, db.ForeignKey('habits.id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Boolean, default=False, nullable=False)
    def __repr__(self):
        return f'{self.date, self.done}'

class Task(db.Model):
    __tablename__ = "tasks"
    id = db.Column(db.Integer, primary_key = True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable = False)
    task = db.Column(db.String(100), nullable=False)
    done = db.Column(db.Boolean, default=False, nullable=False)
    priority = db.Column(db.String(10), nullable=False, default='Medium')
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    def __repr__(self):
        return f'{self.task}'
    
class Journal(db.Model):
    __tablename__ = "journals"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

class Quote(db.Model):
    __tablename__ = "quotes"
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, unique=True, nullable=False)
    quote = db.Column(db.String, nullable=False)
    author = db.Column(db.String, nullable=True)

class ImportantDate(db.Model):
    __tablename__ = "important_dates"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    date = db.Column(db.Date, nullable=False)

with app.app_context():
    db.create_all()
    

@app.route("/")
def index():
    session.clear()
    return render_template("homepage.html")
   
@app.route("/home", methods=["GET", "POST"])
@login_required
def home():
    user_id  = session["user_id"]
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
    if isPast(today.month, today.year, habit.created_on.month, habit.created_on.year) and isActive(today, habit.deleted_on)]
    days_in_month = calendar.monthrange(today.year, today.month)[1]

    # fetch logs for all habits in this month
    start_of_month = date(today.year, today.month, 1)
    logs = Habit_log.query.join(Habit).filter(
        Habit.user_id == user_id,
        Habit_log.date >= start_of_month,
        Habit_log.date <= date(today.year, today.month, days_in_month)
    ).all()
   
    marked_dates = [log.date for log in logs]
    # AI-assisted: learned to use a (habit_id, day) dictionary for quick habit log lookups
    # build dictionary {(habit_id, day): (done, log_id)}
    logs_dict = {}
    dates = []
    for day in range(1, days_in_month+1):
        dates.append(date(today.year, today.month, day))
    for log in logs:
        logs_dict[(log.habit_id, log.date)] = (log.status, log.id)
    date_today = date.today()
    quote = Quote.query.filter_by(date=date_today).first()
    if not quote:
        quote_dict = fetch_quote()
        new_quote = Quote(date=date_today, quote=quote_dict["quote"],author=quote_dict["author"])
        db.session.add(new_quote)
        db.session.commit()
        quote = Quote.query.filter_by(date=date_today).first()
    
    # Check for upcoming important dates (within 2 days)
    reminder = None
    important_dates = ImportantDate.query.filter_by(user_id=user_id).all()
    for d in important_dates:
        days_left = (d.date - date_today).days
        if 0 <= days_left <= 2:
            reminder = {
                'id': d.id,
                'title': d.title,
                'days_left': days_left
            }
            break
    
    return render_template("habits.html",
                           habits=habits_past,
                           days_in_month=days_in_month,
                              logs_dict=logs_dict,
                           month_name = calendar.month_name[today.month],
                           date=today,
                           today=today.day,dates=dates,quote=quote,reminder=reminder)

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


@app.route("/delete-habit", methods = ["POST"])
def delete_habit():
    data = request.get_json()
    habit_id = int(data["habit_id"])
    date_str = data["date"]
    date = datetime.strptime(date_str, "%Y-%m-%d").date()
    habit = Habit.query.filter_by(id=habit_id).first()
    habit.deleted_on = date
    db.session.commit()
    return jsonify({"success": True})

@app.route("/todo", methods=["GET", "POST"])
@login_required
def todo():
    user_id  = session["user_id"]
    if request.method == "POST":
        task = request.form.get("task")
        priority = request.form.get("priority", "Medium")
        new_task = Task(user_id=user_id, task=task, priority=priority)
        db.session.add(new_task)
        db.session.commit()
        return redirect("/todo")
    # Sort by priority (High > Medium > Low), then by creation date
    priority_order = {'High': 1, 'Medium': 2, 'Low': 3}
    tasks = Task.query.filter_by(user_id=user_id).all()
    tasks.sort(key=lambda x: (priority_order.get(x.priority, 2), x.created_at))
    return render_template("todo.html",tasks=tasks)

@app.route("/mark_done", methods=["POST"])
def mark_done():
    data = request.get_json()
    task_id = int(data["task_id"])
    task = Task.query.filter_by(id=task_id).first()
    task.done = not task.done
    db.session.commit()
    return jsonify({"done": task.done})

@app.route("/remove_task", methods=["POST"])
def remove_task():
    data = request.get_json()
    task_id = int(data["task_id"])
    task = Task.query.filter_by(id=task_id).first()
    db.session.delete(task)
    db.session.commit()
    return jsonify({"success": True})

@app.route("/clear_all_tasks", methods=["POST"])
def clear_all_tasks():
    user_id  = session["user_id"]
    Task.query.filter_by(user_id=user_id, done=True).delete()
    db.session.commit()
    return jsonify({"success": True})

@app.route("/dates", methods=["GET", "POST"])
@login_required
def dates():
    user_id = session["user_id"]
    if request.method == "POST":
        title = request.form.get("title")
        date_str = request.form.get("date")
        if title and date_str:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            new_date = ImportantDate(user_id=user_id, title=title, date=date_obj)
            db.session.add(new_date)
            db.session.commit()
        return redirect("/dates")
    
    # Get all important dates for user
    important_dates = ImportantDate.query.filter_by(user_id=user_id).all()
    
    # Sort by nearest upcoming date
    today = date.today()
    upcoming_dates = []
    for d in important_dates:
        days_left = (d.date - today).days
        upcoming_dates.append({
            'id': d.id,
            'title': d.title,
            'date': d.date,
            'days_left': days_left
        })
    upcoming_dates.sort(key=lambda x: (x['date'] < today, abs(x['days_left'])))
    
    # Check for reminders (events within 2 days)
    reminder = None
    for d in upcoming_dates:
        if 0 <= d['days_left'] <= 2:
            reminder = d
            break
    
    return render_template("dates.html", dates=upcoming_dates, reminder=reminder)

@app.route("/edit_date", methods=["POST"])
def edit_date():
    data = request.get_json()
    date_id = int(data["date_id"])
    title = data.get("title")
    date_str = data.get("date")
    
    important_date = ImportantDate.query.filter_by(id=date_id).first()
    if important_date:
        if title:
            important_date.title = title
        if date_str:
            important_date.date = datetime.strptime(date_str, "%Y-%m-%d").date()
        db.session.commit()
    return jsonify({"success": True})

@app.route("/delete_date", methods=["POST"])
def delete_date():
    data = request.get_json()
    date_id = int(data["date_id"])
    important_date = ImportantDate.query.filter_by(id=date_id).first()
    if important_date:
        db.session.delete(important_date)
        db.session.commit()
    return jsonify({"success": True})

@app.route("/journal", methods=["GET", "POST"])
@login_required
def journal():
    user_id  = session["user_id"]
    if request.method == "POST":
        content = request.form.get("content")
        if content.strip():  
            new_entry = Journal(user_id=user_id, content=content.strip())
            db.session.add(new_entry)
            db.session.commit()
        return redirect("/journal")
    entries = (
        Journal.query.filter_by(user_id=user_id)
        .order_by(Journal.created_at.desc())
        .all()
    )
    return render_template("journal.html", entries=entries)

@app.route("/delete-entry", methods = ["POST"])
def delete_entry():
    data = request.get_json()
    entry_id = int(data["entry_id"])
    entry = Journal.query.filter_by(id=entry_id).first()
    if entry:
        db.session.delete(entry)
        db.session.commit()
    return jsonify({"success": True})

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
        session["user_id"] = user.id
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


