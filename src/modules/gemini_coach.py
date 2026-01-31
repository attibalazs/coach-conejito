import os
import requests
import json
import time
from modules.data_manager import load_journal_entries, load_user_profile, load_garmin_activities, load_model_prompt

# Global cache for MLX model to avoid reloading on every request
MLX_CACHE = {
    "model": None,
    "tokenizer": None,
    "path": None
}

def format_pace(speed_m_s):
    """Converts speed in m/s to pace in min/km."""
    if speed_m_s <= 0:
        return "0:00"
    pace_decimal = 16.6666666667 / speed_m_s
    minutes = int(pace_decimal)
    seconds = int((pace_decimal - minutes) * 60)
    return f"{minutes}:{seconds:02d}"

def format_garmin_for_ai(activities):
    """Summarizes Garmin activities for the LLM prompt with more detail."""
    if not activities:
        return "No recent activities recorded."
    
    summary = []
    for act in activities[:10]:
        dist = round(act.get('distance', 0) / 1000, 2)
        dur = round(act.get('duration', 0) / 60, 1)
        date = act.get('startTimeLocal', 'Unknown')[:10]
        type_key = act.get('activityType', {}).get('typeKey', 'run')
        avg_hr = act.get('averageHR', 'N/A')
        avg_speed = act.get('averageSpeed', 0)
        pace = format_pace(avg_speed)
        te = act.get('aerobicTrainingEffect', 'N/A')
        label = act.get('trainingEffectLabel', 'N/A')
        elev = act.get('elevationGain')
        cadence = act.get('averageRunningCadenceInStepsPerMinute')

        parts = [
            f"- {date}: {type_key.capitalize()}",
            f"{dist}km in {dur}min",
            f"{pace} min/km",
            f"Avg HR: {avg_hr}",
            f"Elev: {round(elev)}m" if elev else None,
            f"Cadence: {round(cadence)} spm" if cadence else None,
            f"TE: {te} ({label})",
        ]
        summary.append(" | ".join(p for p in parts if p))
    
    return "\n".join(summary)

DEFAULT_COACH_PROMPT = """You are Coach Conejito, an expert endurance and trail running coach.

RESPONSE FORMAT — use this structure:
1. **Flags**: Any injury or overtraining warnings. Check if soreness is rising on consecutive days, RPE >7 for 3+ days, HR elevated at same pace, or mood declining. If none, say "No flags."
2. **Review**: 2-3 sentences on recent training load trends and goal alignment.
3. **Prescription**: Next 2-3 days with distance, pace, HR zone, terrain. Use bullet list.
4. **Prehab**: One mobility or strength recommendation based on current injury status.

TRAINING RULES:
- Max 10% weekly volume increase. Down week (60-70%) every 3-4 weeks.
- Long run max 30% of weekly volume. Increase long run max 3km/week.
- For weekly plans, use a 7-day table.

STYLE: Be direct and professional. No filler. Distances in km, paces in min/km, HR in bpm. If an injury concern is serious, prescribe rest and professional assessment before any running."""

def compute_training_stats(activities):
    """Pre-compute weekly/monthly/yearly aggregates for the LLM prompt."""
    from datetime import datetime
    from collections import defaultdict

    if not activities:
        return "No training data available."

    today = datetime.now().date()

    weeks = defaultdict(list)
    for act in activities:
        date_str = act.get('startTimeLocal', '')[:10]
        if not date_str:
            continue
        act_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        week_key = act_date.strftime('%G-W%V')
        weeks[week_key].append(act)

    sorted_weeks = sorted(weeks.keys())
    lines = ["Weekly breakdown (last 4 weeks):"]

    for wk in sorted_weeks[-4:]:
        acts = weeks[wk]
        dist = sum(a.get('distance', 0) / 1000 for a in acts)
        dur = sum(a.get('duration', 0) / 60 for a in acts)
        elev = sum((a.get('elevationGain') or 0) for a in acts)
        n = len(acts)
        longest = max((a.get('distance', 0) / 1000 for a in acts), default=0)
        lines.append(
            f"  {wk}: {round(dist,1)}km | {n} sessions | {round(dur)}min | "
            f"Elev: {round(elev)}m | Longest: {round(longest,1)}km"
        )

    if len(sorted_weeks) >= 2:
        curr = sum(a.get('distance', 0) / 1000 for a in weeks[sorted_weeks[-1]])
        prev = sum(a.get('distance', 0) / 1000 for a in weeks[sorted_weeks[-2]])
        if prev > 0:
            pct = ((curr - prev) / prev) * 100
            lines.append(f"Week-over-week volume change: {'+' if pct >= 0 else ''}{round(pct)}%")

    this_month = today.strftime('%Y-%m')
    month_dist = sum(a.get('distance', 0) / 1000 for a in activities
                     if a.get('startTimeLocal', '')[:7] == this_month)
    lines.append(f"This month ({this_month}): {round(month_dist, 1)}km")

    this_year = str(today.year)
    year_dist = sum(a.get('distance', 0) / 1000 for a in activities
                    if a.get('startTimeLocal', '')[:4] == this_year)
    lines.append(f"This year ({this_year}): {round(year_dist, 1)}km")

    return "\n".join(lines)

def get_system_prompt(user_id, model_name="phi4-mini:3.8b"):
    from modules.data_manager import load_coach_plan
    from datetime import date as dt_date, timedelta

    profile = load_user_profile(user_id)
    journals = load_journal_entries(user_id)
    activities = load_garmin_activities(user_id)
    current_plan = load_coach_plan(user_id)

    today_date = dt_date.today()
    tomorrow_date = today_date + timedelta(days=1)

    today_str = today_date.strftime("%A, %Y-%m-%d")
    tomorrow_str = tomorrow_date.strftime("%A, %Y-%m-%d")

    recent_journals = journals[:7]
    garmin_summary = format_garmin_for_ai(activities)
    training_stats = compute_training_stats(activities)

    custom_prompt = load_model_prompt(user_id, model_name)
    coaching_instructions = custom_prompt if custom_prompt else DEFAULT_COACH_PROMPT

    data_block = f"""
TODAY: {today_str}
TOMORROW: {tomorrow_str}
Use ONLY these dates. Ignore conflicting dates in chat history.

ATHLETE:
- Name: {profile.get('name', 'Athlete')}
- Goal: {profile.get('goals', 'Unknown')}
- Injuries: {profile.get('injuries', 'None')}

ACTIVE PLAN:
{current_plan}

TRAINING LOG (recent sessions):
{garmin_summary}

TRAINING LOAD (pre-computed):
{training_stats}

SUBJECTIVE LOG (journals):
{recent_journals}"""

    return f"{coaching_instructions}\n{data_block}"

def get_ai_coach_response(api_key, user_id, model_name="deepseek-r1:8b", chat_mode=False, user_message=None, history=None):
    """
    Generates a coaching response. Supports Gemini (Cloud), Ollama (Local), and MLX (macOS Native).
    Returns (response_text, duration_seconds).
    """
    system_prompt = get_system_prompt(user_id, model_name)
    
    if chat_mode:
        messages_context = "\n".join([f"{m['role'].capitalize()}: {m['content']}" for m in history])
        full_prompt = f"{system_prompt}\n\n--- CHAT HISTORY ---\n{messages_context}\n\nAthlete: {user_message}\nCoach Conejito:"
    else:
        full_prompt = f"{system_prompt}\n\nPlease provide a brief, actionable assessment of my current state and a recommendation for the next 2 days."

    start_time = time.time()

    # --- MLX (macOS Native) ---
    if model_name.startswith("mlx-"):
        try:
            from mlx_lm import load, generate
            
            # Map shorthand to Hugging Face paths
            mlx_map = {
                "mlx-deepseek-8b": "mlx-community/DeepSeek-R1-Distill-Qwen-7B-4bit",
                "mlx-phi4": "mlx-community/phi-4-4bit"
            }
            repo_id = mlx_map.get(model_name, model_name[4:]) # fallback to user string if not in map

            if MLX_CACHE["path"] != repo_id:
                # Reload model if path changed
                MLX_CACHE["model"], MLX_CACHE["tokenizer"] = load(repo_id)
                MLX_CACHE["path"] = repo_id

            response = generate(
                MLX_CACHE["model"], 
                MLX_CACHE["tokenizer"], 
                prompt=full_prompt, 
                max_tokens=2048,
                verbose=False
            )
            duration = time.time() - start_time
            return response, duration
        except Exception as e:
            return f"Error with MLX: {str(e)}", 0

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
            duration = time.time() - start_time
            return response.json().get("response", "No response from Ollama."), duration
        except requests.exceptions.ConnectionError:
            return "Error: Could not connect to Ollama. Make sure it is running.", 0
        except Exception as e:
            return f"Error with Ollama: {str(e)}", 0

    # --- GEMINI (Cloud) ---
    if not api_key:
        return "Please provide a valid Gemini API Key in the settings.", 0

    try:
        import google.generativeai as genai
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        response = model.generate_content(full_prompt)
        duration = time.time() - start_time
        return response.text, duration
    except Exception as e:
        return f"Error contacting Coach Conejito: {str(e)}", 0