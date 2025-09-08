from functools import wraps
from flask import session, redirect

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("username") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def isPast(today_month, today_year, created_month, created_year):
        if(created_year<today_year or (created_year == today_year and created_month <= today_month)):
            return True
        else:
            return False