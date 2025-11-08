import requests
from functools import wraps
from flask import session, redirect, jsonify
from datetime import date
import os

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

def generate_journal_prompt(mood):
    """Generate a journal prompt based on mood using Gemini API"""
    # Fallback prompts if API is not available
    fallback_prompts = {
        'Happy': 'What made you smile today? Reflect on the moments that brought you joy.',
        'Sad': 'What\'s on your mind? It\'s okay to feel down sometimes. Write about what\'s troubling you.',
        'Anxious': 'What are you worried about? Sometimes writing down our fears can help us understand them better.',
        'Motivated': 'What are you excited to accomplish? Write about your goals and what drives you forward.',
        'Calm': 'How do you feel at peace? Reflect on the tranquility in your life.',
        'Frustrated': 'What\'s been challenging you? Express your frustrations and think about potential solutions.',
        'Grateful': 'What are you thankful for today? Count your blessings and reflect on them.',
        'Tired': 'How are you feeling? Rest is important. Write about what\'s been draining your energy.'
    }
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        # Return fallback prompt if API key is not set
        return fallback_prompts.get(mood, f'How are you feeling about being {mood}? Reflect on your emotions and experiences.')
    
    try:
        # Lazy import to avoid errors if package is not available or incompatible
        import google.generativeai as genai
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        
        prompt_text = f"""Generate a thoughtful, empathetic journal prompt for someone feeling {mood}. 
        The prompt should be encouraging, reflective, and help the person explore their emotions. 
        Keep it concise (1-2 sentences) and avoid being too prescriptive. 
        Focus on helping them understand and process their feelings."""
        
        response = model.generate_content(prompt_text)
        return response.text.strip()
    except ImportError:
        # If google.generativeai is not installed or incompatible, use fallback
        return fallback_prompts.get(mood, f'How are you feeling about being {mood}? Reflect on your emotions and experiences.')
    except Exception as e:
        # If API call fails, use fallback
        print(f"Error generating prompt with Gemini API: {e}")
        return fallback_prompts.get(mood, f'How are you feeling about being {mood}? Reflect on your emotions and experiences.')
 