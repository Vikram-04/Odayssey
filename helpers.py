import requests
from functools import wraps
from flask import session, redirect, jsonify
from datetime import date

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function

def isPast(today_month, today_year, created_month, created_year):
        if(created_year<today_year or (created_year == today_year and created_month <= today_month)):
            return True
        else:
            return False
        
def isActive(today, deleted_on):
     if((deleted_on is None) or (deleted_on.year>today.year or (deleted_on.year == today.year and deleted_on.month > today.month))):
         return True
     else:
         return False

def fetch_quote():
    api_url = "https://quoteslate.vercel.app/api/quotes/random?tags=inspiration&motivation&success&happiness&perseverance&change&mindfulness&growth&courage&gratitude&resilience&maxLength=100"
    headers = {"User-Agent": "Mozilla/5.0"} # AI-assisted: added a User-Agent header to requests.get() to fix 429 error

    try:
        r = requests.get(api_url, headers=headers, timeout=5)
        r.raise_for_status()
        data = r.json()
        return {
            "date":date.today(),
            "quote":data["quote"],
            "author":data["author"]
        }
    except Exception as e:
        return {
            "date": date.today(),
            "quote": "Successful people are simply those with successful habits.",
            "author": "Brian Tracy"
        }
 