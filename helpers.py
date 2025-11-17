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
    fallback_prompts = {
        'Happy': 'What made you smile today? Reflect on the moments that brought you joy.',
        'Sad': 'What\'s on your mind? It\'s okay to feel down sometimes. Write about what\'s troubling you.',
        'Anxious': 'What are you worried about? Sometimes writing down our fears can help us understand them better.',
        'Motivated': 'What are you excited to accomplish? Write about your goals and what drives you forward.',
        'Calm': 'How do you feel at peace? Reflect on the tranquility in your life.',
        'Frustrated': 'What\'s been challenging you? Express your frustrations and think about potential solutions.',
        'Grateful': 'What are you thankful for today? Count your blessings and reflect on them.',
        'Tired': 'How are you feeling? Rest is important. Write about what\'s been draining your energy.',
        'Excited': 'What has you feeling energized? Capture the excitement and anticipation you\'re experiencing.',
        'Nervous': 'What\'s making you feel uneasy? Acknowledge your nerves and explore what\'s beneath them.',
        'Peaceful': 'What brings you serenity? Savor this moment of calm and reflect on what creates peace in your life.',
        'Stressed': 'What\'s weighing on you? Take a moment to identify the sources of stress and consider what you can control.',
        'Content': 'What makes you feel satisfied? Appreciate the present moment and the things that bring you contentment.',
        'Lonely': 'How are you feeling? It\'s okay to feel alone sometimes. What connections or activities might help?',
        'Energetic': 'What\'s fueling your enthusiasm? Channel this energy and explore what\'s driving your vitality.',
        'Overwhelmed': 'What feels like too much right now? Break it down and identify what you need most in this moment.',
        'Hopeful': 'What are you looking forward to? Embrace your optimism and explore the possibilities ahead.',
        'Disappointed': 'What didn\'t go as expected? Allow yourself to feel this disappointment and consider what you can learn.',
        'Proud': 'What achievement are you celebrating? Take a moment to recognize your accomplishments and growth.',
        'Confused': 'What questions are on your mind? Embrace the uncertainty and explore what you\'re trying to understand.',
        'Relaxed': 'What helps you unwind? Savor this feeling of ease and reflect on what brings you relaxation.',
        'Worried': 'What concerns are on your mind? Acknowledge your worries and consider what steps might help ease them.',
        'Joyful': 'What\'s filling your heart with joy? Celebrate these moments and reflect on what brings you happiness.',
        'Melancholy': 'What\'s on your heart? Honor these deeper feelings and explore what\'s stirring within you.'
    }
    
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        return fallback_prompts.get(mood, f'How are you feeling about being {mood}? Reflect on your emotions and experiences.')
    
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Generate a thoughtful journal prompt for someone feeling {mood}. Keep it 1-2 sentences and empathetic. Return only the prompt text."
        )
        
        # Extract text from response - handle different response structures
        prompt_result = None
        if hasattr(response, 'text') and response.text:
            prompt_result = response.text.strip()
        elif hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                if candidate.content.parts:
                    prompt_result = candidate.content.parts[0].text.strip()
        
        # Return if valid response
        if prompt_result and len(prompt_result) > 10:
            return prompt_result
    except Exception as e:
        print(f"Error generating prompt for mood '{mood}': {e}")
    
    return fallback_prompts.get(mood, f'How are you feeling about being {mood}? Reflect on your emotions and experiences.')
 