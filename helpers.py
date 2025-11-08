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
    if api_key:
        api_key = api_key.strip()  # Remove any whitespace
    
    if not api_key:
        # Return fallback prompt if API key is not set
        print(f"⚠ GEMINI_API_KEY not found in environment variables, using fallback prompt for mood: {mood}")
        print(f"  → To enable AI prompts, add GEMINI_API_KEY=your_api_key to your .env file")
        return fallback_prompts.get(mood, f'How are you feeling about being {mood}? Reflect on your emotions and experiences.')
    
    # Try the new Gemini API approach first (from google import genai)
    try:
        from google import genai
        
        # Initialize client with API key (can also use environment variable GEMINI_API_KEY)
        # Set API key in environment for this call
        original_key = os.environ.get('GEMINI_API_KEY')
        os.environ['GEMINI_API_KEY'] = api_key
        
        try:
            client = genai.Client(api_key=api_key)
        except:
            # If api_key parameter doesn't work, try without it (uses env var)
            client = genai.Client()
        
        prompt_text = f"""Generate a thoughtful, empathetic journal prompt for someone feeling {mood}. 
The prompt should be encouraging, reflective, and help the person explore their emotions. 
Keep it concise (1-2 sentences) and avoid being too prescriptive. 
Focus on helping them understand and process their feelings. 
Return only the prompt text, no additional formatting or explanations."""
        
        # Try gemini-2.5-flash first, then fallback to gemini-1.5-flash
        model_name = "gemini-2.5-flash"
        response = None
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=prompt_text
            )
        except Exception as model_error:
            print(f"  → Model {model_name} not available, trying gemini-1.5-flash: {model_error}")
            model_name = "gemini-1.5-flash"
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt_text
                )
            except Exception as model_error2:
                print(f"  → Model {model_name} also failed: {model_error2}")
                raise model_error2
        
        # Restore original environment variable if it existed
        if original_key:
            os.environ['GEMINI_API_KEY'] = original_key
        elif 'GEMINI_API_KEY' in os.environ:
            del os.environ['GEMINI_API_KEY']
        
        # Extract text from response
        prompt_result = None
        if hasattr(response, 'text'):
            prompt_result = response.text
        elif hasattr(response, 'candidates') and len(response.candidates) > 0:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                if len(candidate.content.parts) > 0:
                    prompt_result = candidate.content.parts[0].text
            elif hasattr(candidate, 'text'):
                prompt_result = candidate.text
        
        # Clean up the result
        if prompt_result:
            prompt_result = prompt_result.strip()
            # Remove markdown formatting if present
            prompt_result = prompt_result.replace('*', '').replace('**', '').strip()
            # Remove quotes if the AI wrapped it in quotes
            if prompt_result.startswith('"') and prompt_result.endswith('"'):
                prompt_result = prompt_result[1:-1].strip()
            if prompt_result.startswith("'") and prompt_result.endswith("'"):
                prompt_result = prompt_result[1:-1].strip()
            
        # Validate the response isn't empty
        if prompt_result and len(prompt_result) > 10:
            print(f"✓ Successfully generated AI prompt for mood: {mood} (using {model_name})")
            return prompt_result
        else:
            print(f"⚠ AI returned empty/invalid prompt, using fallback for mood: {mood}")
            return fallback_prompts.get(mood, f'How are you feeling about being {mood}? Reflect on your emotions and experiences.')
            
    except ImportError as import_err:
        # If new API not available, try HTTP approach
        print(f"  → New Gemini API not available ({import_err}), trying HTTP approach...")
        # Fall through to HTTP approach
    except Exception as api_err:
        # If new API fails (e.g., Python 3.14 compatibility), try HTTP approach
        error_type = type(api_err).__name__
        error_msg = str(api_err)
        if 'Metaclass' in error_type or 'tp_new' in error_msg:
            print(f"  → Python 3.14 compatibility issue detected ({error_type}), trying HTTP approach...")
        else:
            print(f"  → New API error ({error_type}): {error_msg}, trying HTTP approach...")
        # Fall through to HTTP approach
    
    # Fallback to HTTP request approach if new API fails
    try:
        import json
        
        # Request payload
        payload = {
            "contents": [{
                "parts": [{
                    "text": f"""Generate a thoughtful, empathetic journal prompt for someone feeling {mood}. 
The prompt should be encouraging, reflective, and help the person explore their emotions. 
Keep it concise (1-2 sentences) and avoid being too prescriptive. 
Focus on helping them understand and process their feelings. 
Return only the prompt text, no additional formatting or explanations."""
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "topK": 40,
                "topP": 0.95,
                "maxOutputTokens": 200,
            }
        }
        
        # Make HTTP request
        headers = {
            "Content-Type": "application/json"
        }
        
        # Try v1beta endpoint first (more commonly available)
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response.raise_for_status()
        
        # Parse response
        data = response.json()
        
        # Extract text from response
        prompt_result = None
        if 'candidates' in data and len(data['candidates']) > 0:
            candidate = data['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content']:
                if len(candidate['content']['parts']) > 0:
                    prompt_result = candidate['content']['parts'][0].get('text', '')
        
        # Clean up the result
        if prompt_result:
            prompt_result = prompt_result.strip()
            # Remove markdown formatting if present
            prompt_result = prompt_result.replace('*', '').replace('**', '').strip()
            # Remove quotes if the AI wrapped it in quotes
            if prompt_result.startswith('"') and prompt_result.endswith('"'):
                prompt_result = prompt_result[1:-1].strip()
            if prompt_result.startswith("'") and prompt_result.endswith("'"):
                prompt_result = prompt_result[1:-1].strip()
                
        # Validate the response isn't empty
        if prompt_result and len(prompt_result) > 10:
            print(f"✓ Successfully generated AI prompt for mood: {mood} (using HTTP API)")
            return prompt_result
        else:
            print(f"⚠ HTTP API returned empty/invalid prompt, using fallback for mood: {mood}")
            return fallback_prompts.get(mood, f'How are you feeling about being {mood}? Reflect on your emotions and experiences.')
            
    except requests.exceptions.RequestException as http_err:
        # If HTTP request fails, use fallback
        error_msg = str(http_err)
        print(f"✗ Error with HTTP request to Gemini API for mood '{mood}': {error_msg}")
        
        if '401' in error_msg or '403' in error_msg:
            print("  → Authentication error. Please check your GEMINI_API_KEY in .env file.")
        elif '429' in error_msg:
            print("  → API quota or rate limit exceeded.")
        elif '404' in error_msg:
            print("  → API endpoint not found. The API endpoint may have changed.")
        
        return fallback_prompts.get(mood, f'How are you feeling about being {mood}? Reflect on your emotions and experiences.')
    except Exception as final_err:
        # If everything fails, use fallback
        error_type = type(final_err).__name__
        error_msg = str(final_err)
        print(f"✗ All API methods failed for mood '{mood}': {error_type}: {error_msg}")
        return fallback_prompts.get(mood, f'How are you feeling about being {mood}? Reflect on your emotions and experiences.')
 