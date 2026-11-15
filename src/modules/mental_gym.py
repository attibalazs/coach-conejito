import os
import json
from datetime import datetime
from pathlib import Path

DATA_DIR = "data"
USERS_DIR = os.path.join(DATA_DIR, "users")

def get_mental_dir(user_id):
    """Ensure and return the mental training directory for a user."""
    user_dir = os.path.join(USERS_DIR, user_id)
    mental_dir = os.path.join(user_dir, "mental")
    os.makedirs(mental_dir, exist_ok=True)
    return mental_dir

def save_mental_log(user_id, log_entry):
    """
    Saves a mental training session log.
    log_entry format:
    {
        "date": "2026-06-12",
        "timestamp": "2026-06-12T09:05:00",
        "type": "Stroop Test" | "Mental Math" | "Visualization" | "Mantra Builder" | "Mindful Breathing",
        "metrics": { ... },
        "notes": "..."
    }
    """
    mental_dir = get_mental_dir(user_id)
    timestamp_str = datetime.now().strftime("%Y-%m-%d_%H%M%S_%f")
    filename = os.path.join(mental_dir, f"session_{timestamp_str}.json")
    
    with open(filename, "w") as f:
        json.dump(log_entry, f, indent=4)
    return filename

def load_mental_logs(user_id):
    """Load all mental training logs for a user, sorted by timestamp descending."""
    mental_dir = get_mental_dir(user_id)
    logs = []
    if os.path.exists(mental_dir):
        for filename in os.listdir(mental_dir):
            if filename.endswith(".json") and filename.startswith("session_"):
                try:
                    with open(os.path.join(mental_dir, filename), "r") as f:
                        logs.append(json.load(f))
                except Exception as e:
                    print(f"Error loading mental log {filename}: {e}")
                    
    # Sort by timestamp descending (or date if timestamp is missing)
    return sorted(logs, key=lambda x: x.get('timestamp', x.get('date', '')), reverse=True)

# Preset practices/guides for Visualization, Mantras, and Breathing/Soul
VISUALIZATION_PRESETS = {
    "process": {
        "title": "Process Rehearsal",
        "summary": "Mentally practice pacing, form, breathing, and climbing hills on a specific course.",
        "steps": [
            "Find a quiet space and close your eyes. Inhale slowly for 4 seconds, hold for 4, exhale for 4.",
            "Visualize the start of your run: feel your muscles fresh, focus on establishing a steady rhythm.",
            "Mentally rehearse a challenging section (e.g., a steep hill). Visualize yourself maintaining short, quick steps, keeping your shoulders relaxed, and pushing over the crest with control.",
            "Picture your breathing: rhythmic, deep, and steady.",
            "End by visualizing finishing the run feeling tired but strong and in control."
        ]
    },
    "worst_case": {
        "title": "Worst-Case/Resilience Prep",
        "summary": "Rehearse coping strategies for common race obstacles: side stitches, severe fatigue, or negative thoughts.",
        "steps": [
            "Visualize a tough moment: you feel a side stitch developing or your legs feel incredibly heavy.",
            "Note the automatic response of panic or desire to stop, and visualize yourself taking a deep breath to stay calm.",
            "Visualize implementing the solution: for a side stitch, exhale hard when the opposite foot hits the ground; for heavy legs, shorten your stride and increase cadence.",
            "Visualize yourself talking to yourself in the second person: 'You are trained for this. Relax your hands. One mile at a time.'",
            "See yourself pushing through the obstacle and regaining a strong, steady rhythm."
        ]
    },
    "sensory": {
        "title": "Immersive Sensory Run",
        "summary": "Build strong mental representations of your run by engaging all 5 senses to improve confidence and reduce anxiety.",
        "steps": [
            "Close your eyes and paint the scene of your goal run.",
            "Sight: See the trail ahead, the trees, the mile markers, and other runners.",
            "Sound: Hear the rhythmic crunch of dirt under your shoes, your own steady breathing, the wind, or birds.",
            "Touch: Feel the cool air on your face, the light sweat on your forehead, and the impact of the ground.",
            "Smell/Taste: Notice the crisp scent of pine or rain, and the taste of your hydration mix.",
            "Dwell on these sensations for 5 minutes, associating them with a feeling of deep flow and enjoyment."
        ]
    }
}

MANTRA_PRESETS = {
    "instructional": {
        "title": "Instructional Mantras (Running Economy)",
        "summary": "Short phrases to correct running mechanics, form, and breathing when fatigue sets in.",
        "examples": [
            "Light feet, quick beat.",
            "Relax the hands, drop the shoulders.",
            "Drive the elbows, stand tall.",
            "Short strides, soft landing."
        ]
    },
    "motivational": {
        "title": "Motivational Mantras (Grit)",
        "summary": "Phrases designed to boost drive, manage discomfort, and keep your effort high.",
        "examples": [
            "This is what I trained for.",
            "Embrace the hill, earn the descent.",
            "Comfortable being uncomfortable.",
            "Strong legs, tough mind."
        ]
    },
    "soul": {
        "title": "Soul & Connection Mantras (Mindfulness)",
        "summary": "Phrases to connect with nature, find inner peace, and running with joy.",
        "examples": [
            "Run with gratitude.",
            "Breathe in strength, breathe out stress.",
            "At peace with the pace.",
            "Part of the trail, free in the wild."
        ]
    }
}

BREATHWORK_PRESETS = {
    "box": {
        "title": "Box Breathing (Pre-Run Calm)",
        "description": "Standard Navy SEAL technique to lower heart rate, reduce pre-run anxiety, and focus the mind.",
        "instructions": "Inhale for 4 seconds, hold for 4 seconds, exhale for 4 seconds, hold empty for 4 seconds. Repeat for 3-5 minutes."
    },
    "rhythmic": {
        "title": "3:3 Rhythmic Breathing (On-the-run Flow)",
        "description": "Aligning breath with footstrikes. Inhale for 3 steps, exhale for 3 steps. Prevents always landing on the same foot at the start of an exhalation (which reduces impact stress and injuries).",
        "instructions": "Begin running at an easy pace. Inhale: step-left, step-right, step-left. Exhale: step-right, step-left, step-right. Find the rhythm and lock it in. Transition to 2:2 for uphill/harder paces."
    },
    "gratitude": {
        "title": "Gratitude Walk/Run (Soul Connection)",
        "description": "An exercise to shift focus away from pain or performance metrics and ground yourself in gratitude.",
        "instructions": "During an easy run or warm-up, dedicate 5 minutes to cycle through: 3 things you are grateful for about your body (e.g. lungs breathing, feet landing), 3 things about the surroundings (e.g. morning sun, cool breeze), and 3 things in your life. Run with a gentle smile."
    }
}

STROOP_COLORS = {
    "Red": "#FF4B4B",
    "Blue": "#1C83E1",
    "Green": "#23C55E",
    "Yellow": "#F1C40F",
    "Orange": "#E67E22",
    "Purple": "#9B59B6"
}

def next_stroop_stimulus():
    import random
    word = random.choice(list(STROOP_COLORS.keys()))
    # 80% chance of incongruent color
    if random.random() < 0.8:
        color_name = random.choice([c for c in STROOP_COLORS.keys() if c != word])
    else:
        color_name = word
    color_hex = STROOP_COLORS[color_name]
    return word, color_name, color_hex

def next_math_stimulus():
    import random
    op = random.choice(["+", "-", "*"])
    if op == "+":
        a = random.randint(5, 50)
        b = random.randint(5, 50)
        q = f"{a} + {b}"
        ans = a + b
    elif op == "-":
        a = random.randint(20, 99)
        b = random.randint(5, a - 2)
        q = f"{a} - {b}"
        ans = a - b
    else: # op == "*"
        a = random.randint(3, 12)
        b = random.randint(3, 12)
        q = f"{a} × {b}"
        ans = a * b
        
    # Generate 3 wrong options
    options = {ans}
    while len(options) < 4:
        offset = random.choice([-10, -5, -2, -1, 1, 2, 5, 10, random.randint(-15, 15)])
        wrong = ans + offset
        if wrong > 0:
            options.add(wrong)
            
    options_list = list(options)
    random.shuffle(options_list)
    return q, ans, options_list


def generate_nback_sequence(n_level, total_trials, match_probability=0.35):
    """
    Generates a sequence of positions and letters for a Dual N-Back session.
    Guarantees approximately match_probability matches for both position and letter.
    """
    import random
    positions = []
    letters = []
    available_letters = ["C", "K", "H", "Q", "T", "R", "L", "P"]
    
    for i in range(total_trials):
        # 1. Determine position
        if i >= n_level and random.random() < match_probability:
            # Match
            pos = positions[i - n_level]
        else:
            # No match
            choices = [p for p in range(1, 10)]
            if i >= n_level and positions[i - n_level] in choices:
                choices.remove(positions[i - n_level])
            pos = random.choice(choices)
        positions.append(pos)
        
        # 2. Determine letter
        if i >= n_level and random.random() < match_probability:
            # Match
            let = letters[i - n_level]
        else:
            # No match
            choices = list(available_letters)
            if i >= n_level and letters[i - n_level] in choices:
                choices.remove(letters[i - n_level])
            let = random.choice(choices)
        letters.append(let)
        
    return list(zip(positions, letters))


