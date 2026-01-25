import os
import requests
import json
from modules.data_manager import load_journal_entries, load_user_profile, load_garmin_activities

def format_garmin_for_ai(activities):
    """Summarizes Garmin activities for the LLM prompt."""
    if not activities:
        return "No recent activities recorded."
    
    summary = []
    for act in activities[:10]: # Last 10
        # Convert distance from meters to km
        dist = round(act.get('distance', 0) / 1000, 2)
        # Convert duration from seconds to min
        dur = round(act.get('duration', 0) / 60, 1)
        date = act.get('startTimeLocal', 'Unknown')[:10]
        type_key = act.get('activityType', {}).get('typeKey', 'run')
        avg_hr = act.get('averageHR', 'N/A')
        te = act.get('aerobicTrainingEffect', 'N/A')
        
        summary.append(f"- {date}: {type_key.capitalize()} | {dist}km in {dur}min | Avg HR: {avg_hr} | TE: {te}")
    
    return "\n".join(summary)

def get_system_prompt(user_id):
    from modules.data_manager import load_coach_plan
    profile = load_user_profile(user_id)
    journals = load_journal_entries(user_id)
    activities = load_garmin_activities(user_id)
    current_plan = load_coach_plan(user_id)
    
    recent_journals = journals[:7]
    garmin_summary = format_garmin_for_ai(activities)
    
    prompt = f"""
    You are 'Coach Conejito', an elite endurance sports coach. 
    Your athlete is: {profile.get('name', 'Athlete')}
    Goals: {profile.get('goals', 'Unknown')}
    Injuries/Limitations: {profile.get('injuries', 'None')}

    --- CURRENT ACTIVE PLAN ---
    {current_plan}

    --- RECENT ACTIVITY (Garmin) ---
    {garmin_summary}

    --- RECENT SUBJECTIVE FEEDBACK (Journal) ---
    {recent_journals}

    Your goal is to provide expert training advice. 
    - If analyzing status, be concise and actionable.
    - If chatting, be encouraging, professional, and data-driven.
    - If the athlete asks to change the plan, provide a revised version.
    - Always consider the balance between the 'Work' (Garmin) and the 'Feeling' (Journal).
    """
    return prompt

def get_ai_coach_response(api_key, user_id, model_name="deepseek-r1:8b", chat_mode=False, user_message=None, history=None):
    """
    Generates a coaching response. Supports status analysis and interactive chat.
    """
    system_prompt = get_system_prompt(user_id)
    
    if chat_mode:
        full_prompt = f"{system_prompt}\n\nChat History:\n{history}\n\nAthlete: {user_message}\nCoach Conejito:"
    else:
        full_prompt = f"{system_prompt}\n\nPlease provide a brief, actionable assessment of my current state and a recommendation for the next 2 days. Structure it with 'Status Check', 'Analysis', and 'Recommendation'."

    # --- OLLAMA (Local) ---
    if not model_name.startswith("gemini"):
        try:
            url = "http://localhost:11434/api/generate"
            payload = {
                "model": model_name,
                "prompt": full_prompt,
                "stream": False
            }
            response = requests.post(url, json=payload)
            response.raise_for_status()
            return response.json().get("response", "No response from Ollama.")
        except requests.exceptions.ConnectionError:
            return "Error: Could not connect to Ollama. Make sure it is running."
        except Exception as e:
            return f"Error with Ollama: {str(e)}"

    # --- GEMINI (Cloud) ---
    if not api_key:
        return "Please provide a valid Gemini API Key in the settings."

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        
        # Simple string prompt for now to keep it consistent with Ollama implementation
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Error contacting Coach Conejito: {str(e)}"