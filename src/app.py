import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
import time
from datetime import date, timedelta, datetime
from modules.data_manager import (
    save_journal_entry, load_journal_entries,
    save_user_profile, load_user_profile,
    list_users, create_user, load_garmin_activities,
    save_coach_plan, load_coach_plan,
    save_chat_history, load_chat_history,
    load_model_prompt, save_model_prompt
)
from modules.gemini_coach import get_ai_coach_response, DEFAULT_COACH_PROMPT
from modules.garmin_client import sync_garmin_activities, is_garmin_authenticated
from modules.mental_gym import (
    save_mental_log, load_mental_logs,
    STROOP_COLORS, next_stroop_stimulus, next_math_stimulus,
    VISUALIZATION_PRESETS, MANTRA_PRESETS, BREATHWORK_PRESETS,
    generate_nback_sequence
)

MODEL_OPTIONS = [
    "deepseek-r1:8b", 
    "mlx-deepseek-8b",
    "mlx-phi4",
    "gemini-1.5-flash", 
    "gemini-1.5-pro", 
    "qwen2.5-coder:latest", 
    "phi4-mini:3.8b", 
    "phi4"
]

# Page Config
st.set_page_config(
    page_title="Coach Conejito HQ",
    page_icon="🐰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Ensure at least one user exists
users = list_users()
if not users:
    create_user("default")
    users = ["default"]

# --- SIDEBAR ---
st.sidebar.title("🐰 Coach Conejito")
current_user = st.sidebar.selectbox("Athlete", users, index=0)

# Detect user change and reload chat history
if "last_user" not in st.session_state:
    st.session_state.last_user = current_user

if st.session_state.last_user != current_user:
    st.session_state.messages = load_chat_history(current_user)
    st.session_state.last_user = current_user

if st.sidebar.button("🗑️ Clear Chat History"):
    save_chat_history(current_user, [])
    st.session_state.messages = []
    st.sidebar.success("Chat cleared!")
    st.rerun()

page = st.sidebar.radio("Go to", ["Command Center", "Journal", "Mental Gym", "Settings"])

st.sidebar.markdown("---")
with st.sidebar.expander("➕ New Athlete"):
    new_user_id = st.text_input("Athlete ID")
    if st.button("Create"):
        if new_user_id and new_user_id not in users:
            create_user(new_user_id)
            st.rerun()

# Global Model Config
if "gemini_api_key" not in st.session_state:
    st.session_state.gemini_api_key = ""
if "model_name" not in st.session_state:
    st.session_state.model_name = "deepseek-r1:8b"

# --- COMMAND CENTER ---
if page == "Command Center":
    col_chat, col_data = st.columns([1.2, 1])

    with col_chat:
        col_header, col_model = st.columns([1, 1])
        with col_header:
            st.subheader("💬 Coach Chat")
        with col_model:
            # Ensure current model is in options
            if st.session_state.model_name not in MODEL_OPTIONS:
                MODEL_OPTIONS.append(st.session_state.model_name)
            
            st.session_state.model_name = st.selectbox(
                "Model", 
                MODEL_OPTIONS, 
                index=MODEL_OPTIONS.index(st.session_state.model_name),
                label_visibility="collapsed",
                key="chat_model_selector"
            )
        
        # 1. Initialize and Load history
        if "messages" not in st.session_state:
            st.session_state.messages = load_chat_history(current_user)

        # 2. Display existing history
        with st.container(height=600):
            for i, msg in enumerate(st.session_state.messages):
                with st.chat_message(msg["role"]):
                    c1, c2 = st.columns([0.9, 0.1])
                    with c1:
                        st.markdown(msg["content"])
                    with c2:
                        if st.button("❌", key=f"del_{i}", help="Delete this message"):
                            st.session_state.messages.pop(i)
                            save_chat_history(current_user, st.session_state.messages)
                            st.rerun()

        # 3. Handle Chat Input
        if prompt := st.chat_input("Ask Coach Conejito..."):
            # Append and display user message
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Generate and display assistant response
            with st.chat_message("assistant"):
                with st.spinner("Coach is thinking..."):
                    # Use a rolling window of history for context
                    history_context = st.session_state.messages[-6:-1] if len(st.session_state.messages) > 1 else []
                    
                    response, duration = get_ai_coach_response(
                        st.session_state.gemini_api_key,
                        current_user,
                        model_name=st.session_state.model_name,
                        chat_mode=True,
                        user_message=prompt,
                        history=history_context
                    )
                    st.markdown(response)
                    st.caption(f"Generated in {duration:.2f}s")
                    
                    # Persist to state and disk immediately
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    save_chat_history(current_user, st.session_state.messages)

        # 4. Action Button for the LAST message
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
            st.markdown("---")
            if st.button("📌 Set last response as Active Plan", key="apply_plan_btn"):
                save_coach_plan(current_user, st.session_state.messages[-1]["content"])
                st.success("Plan updated!")
                st.rerun()

    with col_data:
        st.subheader("📊 Athlete Data")
        
        tab_plan, tab1, tab2 = st.tabs(["📋 Active Plan", "🏃 Garmin Activities", "📓 Subjective Journals"])
        
        with tab_plan:
            plan = load_coach_plan(current_user)
            st.markdown(plan)

        with tab1:
            activities = load_garmin_activities(current_user)
            if activities:
                for act in activities:
                    date_str = act.get('startTimeLocal', 'Unknown')[:10]
                    dist = round(act.get('distance', 0) / 1000, 2)
                    label = act.get('trainingEffectLabel', 'N/A')
                    type_key = act.get('activityType', {}).get('typeKey', 'unknown')
                    act_name = act.get('activityName', '')
                    title = f"{date_str} — {type_key} — {dist}km ({label})"
                    if act_name:
                        title = f"{date_str} — {type_key}: {act_name} — {dist}km ({label})"
                    with st.expander(title):
                        duration_min = round(act.get('duration', 0) / 60, 1)
                        is_running = 'running' in type_key.lower()

                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.write(f"**Duration:** {duration_min} min")
                            if is_running and dist > 0:
                                pace_sec = act.get('duration', 0) / (dist if dist else 1)
                                pace_min = int(pace_sec // 60)
                                pace_rem = int(pace_sec % 60)
                                st.write(f"**Avg Pace:** {pace_min}:{pace_rem:02d} min/km")
                            avg_hr = act.get('averageHR')
                            st.write(f"**Avg HR:** {avg_hr if avg_hr else 'N/A'} bpm")
                            max_hr = act.get('maxHR')
                            st.write(f"**Max HR:** {max_hr if max_hr else 'N/A'} bpm")
                        with col_b:
                            elev = act.get('elevationGain')
                            st.write(f"**Elevation Gain:** {round(elev, 1) if elev else 'N/A'} m")
                            cals = act.get('calories')
                            st.write(f"**Calories:** {round(cals) if cals else 'N/A'} kcal")
                            if is_running:
                                cadence = act.get('averageRunningCadenceInStepsPerMinute')
                                st.write(f"**Cadence:** {round(cadence) if cadence else 'N/A'} spm")
                            vo2 = act.get('vO2MaxValue')
                            st.write(f"**VO2 Max:** {vo2 if vo2 else 'N/A'}")
                            te = act.get('aerobicTrainingEffect')
                            st.write(f"**Training Effect:** {te if te else 'N/A'} / 5.0")
            else:
                st.info("No Garmin data. Sync in Settings.")

        with tab2:
            entries = load_journal_entries(current_user)
            if entries:
                for entry in entries[:5]:
                    with st.expander(f"{entry['date']} | RPE: {entry['rpe']}"):
                        st.write(f"**Mood:** {entry['mood']} | **Soreness:** {entry['soreness']}")
                        st.caption(entry['notes'])

# --- JOURNAL ---
elif page == "Journal":
    st.header("Daily Journal")
    with st.form("journal_entry", clear_on_submit=True):
        entry_date = st.date_input("Date", value=date.today())
        rpe = st.slider("RPE (Effort)", 1, 10, 5)
        mood = st.select_slider("Mood", options=["😩", "😕", "😐", "🙂", "🤩"], value="😐")
        soreness = st.slider("Soreness", 0, 10, 0)
        notes = st.text_area("Notes")
        if st.form_submit_button("Save"):
            save_journal_entry(current_user, entry_date, {"date": entry_date.isoformat(), "rpe": rpe, "mood": mood, "soreness": soreness, "notes": notes})
            st.success("Saved!")

# --- MENTAL GYM ---
elif page == "Mental Gym":
    st.header("🧠 Coach Conejito Mental Gym")
    st.markdown("Train your brain to handle fatigue, build mental toughness, and connect with your running soul.")

    tab_bet, tab_practices, tab_logs = st.tabs([
        "🧠 Brain Endurance Training (BET)",
        "🧘 Practices for the Soul",
        "📈 Mental Training Logs"
    ])

    with tab_bet:
        st.subheader("Brain Endurance Training (BET)")
        st.markdown(
            "Performing cognitively demanding tasks trains your brain to resist the mental fatigue "
            "that causes your perceived exertion (RPE) to skyrocket during long runs. "
            "Do these before a run to warm up your brain, or after a run to train focus under fatigue."
        )

        game_selection = st.selectbox("Select Exercise", ["Stroop Color Test", "Mental Math Challenge", "Dual N-Back Task"])

        if game_selection == "Stroop Color Test":
            st.write("### Stroop Color Test")
            st.write(
                "**Goal:** Click the button matching the **COLOR of the text**, not the word itself! "
                "Tests reaction speed and response inhibition."
            )

            # Initialize states
            if "stroop_active" not in st.session_state:
                st.session_state.stroop_active = False
            if "stroop_finished" not in st.session_state:
                st.session_state.stroop_finished = False

            if not st.session_state.stroop_active and not st.session_state.stroop_finished:
                st.info("💡 Pro Tip: Try to respond as fast and accurately as possible.")
                if st.button("Start 30-Second Stroop Test", type="primary"):
                    st.session_state.stroop_score = 0
                    st.session_state.stroop_total = 0
                    st.session_state.stroop_reaction_times = []
                    st.session_state.stroop_start_time = time.time()
                    st.session_state.stroop_duration_limit = 30.0
                    
                    w, cn, ch = next_stroop_stimulus()
                    st.session_state.stroop_current_word = w
                    st.session_state.stroop_current_color_name = cn
                    st.session_state.stroop_current_color_hex = ch
                    st.session_state.stroop_question_start_time = time.time()
                    
                    st.session_state.stroop_active = True
                    st.session_state.stroop_finished = False
                    st.rerun()

            elif st.session_state.stroop_active:
                elapsed = time.time() - st.session_state.stroop_start_time
                time_left = max(0.0, st.session_state.stroop_duration_limit - elapsed)
                
                if time_left <= 0:
                    st.session_state.stroop_active = False
                    st.session_state.stroop_finished = True
                    st.rerun()
                
                # Progress bar
                st.progress(time_left / st.session_state.stroop_duration_limit, text=f"Time remaining: {time_left:.1f}s")
                st.write(f"Score: **{st.session_state.stroop_score} / {st.session_state.stroop_total}**")
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(
                    f"<h1 style='color:{st.session_state.stroop_current_color_hex}; text-align:center; font-size:64px; font-weight:bold;'>{st.session_state.stroop_current_word}</h1>",
                    unsafe_allow_html=True
                )
                st.markdown("<br>", unsafe_allow_html=True)
                
                # Grid of color buttons
                cols = st.columns(3)
                color_options = sorted(list(STROOP_COLORS.keys()))
                
                clicked_color = None
                for idx, c_name in enumerate(color_options):
                    col = cols[idx % 3]
                    if col.button(c_name, use_container_width=True, key=f"stroop_btn_{c_name}_{idx}"):
                        clicked_color = c_name

                if clicked_color:
                    now = time.time()
                    rt = now - st.session_state.stroop_question_start_time
                    is_correct = (clicked_color == st.session_state.stroop_current_color_name)
                    
                    st.session_state.stroop_total += 1
                    if is_correct:
                        st.session_state.stroop_score += 1
                        st.session_state.stroop_reaction_times.append(rt)
                        
                    # Pick next
                    w, cn, ch = next_stroop_stimulus()
                    st.session_state.stroop_current_word = w
                    st.session_state.stroop_current_color_name = cn
                    st.session_state.stroop_current_color_hex = ch
                    st.session_state.stroop_question_start_time = now
                    st.rerun()
                    
                if st.button("Cancel Test"):
                    st.session_state.stroop_active = False
                    st.session_state.stroop_finished = False
                    st.rerun()

            elif st.session_state.stroop_finished:
                st.success("🎉 Stroop Test Completed!")
                total = st.session_state.stroop_total
                correct = st.session_state.stroop_score
                accuracy = (correct / total * 100) if total > 0 else 0
                avg_rt = (sum(st.session_state.stroop_reaction_times) / len(st.session_state.stroop_reaction_times)) if st.session_state.stroop_reaction_times else 0
                bei = (correct / avg_rt * 10) if avg_rt > 0 else 0
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Brain Endurance Index", f"{bei:.1f}")
                col2.metric("Correct Answers", f"{correct} / {total}")
                col3.metric("Accuracy", f"{accuracy:.1f}%")
                col4.metric("Avg Reaction Time", f"{avg_rt:.2f}s")
                
                st.write("Save your session to log your brain fatigue level and track progress:")
                with st.form("save_stroop_result"):
                    fatigue_level = st.select_slider("Brain Fatigue level right now", options=["Fresh 🍃", "Normal 😐", "Tired 🥱", "Exhausted 🧠💤"])
                    user_notes = st.text_input("Notes (e.g. Done pre-run, felt distracted)", value=f"Fatigue: {fatigue_level}")
                    
                    if st.form_submit_button("Save Session"):
                        log_data = {
                            "date": date.today().isoformat(),
                            "timestamp": datetime.now().isoformat(),
                            "type": "Stroop Test",
                            "metrics": {
                                "score": round(bei, 1),
                                "correct": correct,
                                "total": total,
                                "accuracy": round(accuracy, 1),
                                "reaction_time": round(avg_rt, 2)
                            },
                            "notes": user_notes
                        }
                        save_mental_log(current_user, log_data)
                        st.session_state.stroop_finished = False
                        st.success("Stroop Test session saved!")
                        st.rerun()
                        
                if st.button("Try Again"):
                    st.session_state.stroop_finished = False
                    st.rerun()

        elif game_selection == "Mental Math Challenge":
            st.write("### Mental Math Challenge")
            st.write(
                "**Goal:** Solve as many arithmetic equations as you can in 30 seconds. "
                "Tests working memory and cognitive speed under pressure."
            )

            # Initialize states
            if "math_active" not in st.session_state:
                st.session_state.math_active = False
            if "math_finished" not in st.session_state:
                st.session_state.math_finished = False

            if not st.session_state.math_active and not st.session_state.math_finished:
                if st.button("Start 30-Second Math Challenge", type="primary"):
                    st.session_state.math_score = 0
                    st.session_state.math_total = 0
                    st.session_state.math_reaction_times = []
                    st.session_state.math_start_time = time.time()
                    st.session_state.math_duration_limit = 30.0
                    
                    q, ans, options = next_math_stimulus()
                    st.session_state.math_current_q = q
                    st.session_state.math_current_ans = ans
                    st.session_state.math_current_options = options
                    st.session_state.math_question_start_time = time.time()
                    
                    st.session_state.math_active = True
                    st.session_state.math_finished = False
                    st.rerun()

            elif st.session_state.math_active:
                elapsed = time.time() - st.session_state.math_start_time
                time_left = max(0.0, st.session_state.math_duration_limit - elapsed)
                
                if time_left <= 0:
                    st.session_state.math_active = False
                    st.session_state.math_finished = True
                    st.rerun()
                
                st.progress(time_left / st.session_state.math_duration_limit, text=f"Time remaining: {time_left:.1f}s")
                st.write(f"Score: **{st.session_state.math_score} / {st.session_state.math_total}**")
                
                st.markdown("<br>", unsafe_allow_html=True)
                st.markdown(
                    f"<h1 style='text-align:center; font-size:64px; font-weight:bold;'>{st.session_state.math_current_q}</h1>",
                    unsafe_allow_html=True
                )
                st.markdown("<br>", unsafe_allow_html=True)
                
                cols = st.columns(2)
                clicked_option = None
                for idx, opt in enumerate(st.session_state.math_current_options):
                    col = cols[idx % 2]
                    if col.button(str(opt), use_container_width=True, key=f"math_btn_{opt}_{idx}"):
                        clicked_option = opt

                if clicked_option is not None:
                    now = time.time()
                    rt = now - st.session_state.math_question_start_time
                    is_correct = (clicked_option == st.session_state.math_current_ans)
                    
                    st.session_state.math_total += 1
                    if is_correct:
                        st.session_state.math_score += 1
                        st.session_state.math_reaction_times.append(rt)
                        
                    # Pick next
                    q, ans, options = next_math_stimulus()
                    st.session_state.math_current_q = q
                    st.session_state.math_current_ans = ans
                    st.session_state.math_current_options = options
                    st.session_state.math_question_start_time = now
                    st.rerun()
                    
                if st.button("Cancel Challenge"):
                    st.session_state.math_active = False
                    st.session_state.math_finished = False
                    st.rerun()

            elif st.session_state.math_finished:
                st.success("🎉 Math Challenge Completed!")
                total = st.session_state.math_total
                correct = st.session_state.math_score
                accuracy = (correct / total * 100) if total > 0 else 0
                avg_rt = (sum(st.session_state.math_reaction_times) / len(st.session_state.math_reaction_times)) if st.session_state.math_reaction_times else 0
                bei = (correct / avg_rt * 10) if avg_rt > 0 else 0
                
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Brain Endurance Index", f"{bei:.1f}")
                col2.metric("Correct Answers", f"{correct} / {total}")
                col3.metric("Accuracy", f"{accuracy:.1f}%")
                col4.metric("Avg Response Time", f"{avg_rt:.2f}s")
                
                st.write("Save your session to log your brain fatigue level and track progress:")
                with st.form("save_math_result"):
                    fatigue_level = st.select_slider("Brain Fatigue level right now", options=["Fresh 🍃", "Normal 😐", "Tired 🥱", "Exhausted 🧠💤"], key="math_fatigue")
                    user_notes = st.text_input("Notes (e.g. Done post-run)", value=f"Fatigue: {fatigue_level}", key="math_notes")
                    
                    if st.form_submit_button("Save Session"):
                        log_data = {
                            "date": date.today().isoformat(),
                            "timestamp": datetime.now().isoformat(),
                            "type": "Mental Math",
                            "metrics": {
                                "score": round(bei, 1),
                                "correct": correct,
                                "total": total,
                                "accuracy": round(accuracy, 1),
                                "reaction_time": round(avg_rt, 2)
                            },
                            "notes": user_notes
                        }
                        save_mental_log(current_user, log_data)
                        st.session_state.math_finished = False
                        st.success("Math Challenge session saved!")
                        st.rerun()
                        
                if st.button("Try Again", key="math_again"):
                    st.session_state.math_finished = False
                    st.rerun()

        elif game_selection == "Dual N-Back Task":
            st.write("### Dual N-Back Fluid Intelligence Task")
            st.write(
                "**Goal:** Press the match buttons if the current stimulus matches the one shown **N steps back**! "
                "Train working memory capacity and fluid intelligence. Try to use keyboard shortcuts: **A** for Position, **L** for Letter."
            )

            # Initialize states
            if "nback_active" not in st.session_state:
                st.session_state.nback_active = False
            if "nback_finished" not in st.session_state:
                st.session_state.nback_finished = False

            if not st.session_state.nback_active and not st.session_state.nback_finished:
                st.write("#### Setup Session")
                n_level_select = st.slider("N-Back Level (N)", min_value=1, max_value=5, value=2, help="How many steps back to remember.")
                total_trials_select = st.slider("Number of Trials", min_value=10, max_value=40, value=20, step=5)
                trial_dur_select = st.slider("Trial Duration (seconds)", min_value=2.0, max_value=5.0, value=3.0, step=0.5)

                if st.button("Start Dual N-Back Challenge", type="primary"):
                    st.session_state.nback_active = True
                    st.session_state.nback_finished = False
                    st.session_state.nback_n_level = n_level_select
                    st.session_state.nback_total_trials = total_trials_select
                    st.session_state.nback_trial_duration = trial_dur_select
                    st.session_state.nback_current_idx = 0
                    st.session_state.nback_sequence = generate_nback_sequence(n_level_select, total_trials_select)
                    st.session_state.nback_user_pos_clicked = False
                    st.session_state.nback_user_let_clicked = False
                    st.session_state.nback_hits_pos = 0
                    st.session_state.nback_hits_let = 0
                    st.session_state.nback_misses_pos = 0
                    st.session_state.nback_misses_let = 0
                    st.session_state.nback_false_alarms_pos = 0
                    st.session_state.nback_false_alarms_let = 0
                    st.session_state.nback_trial_start_time = time.time()
                    st.session_state.nback_last_speech_trial = -1
                    st.rerun()

            elif st.session_state.nback_active:
                idx = st.session_state.nback_current_idx
                seq = st.session_state.nback_sequence
                N = st.session_state.nback_n_level
                trial_duration = st.session_state.nback_trial_duration
                
                current_pos, current_letter = seq[idx]
                
                # Check elapsed time
                elapsed = time.time() - st.session_state.nback_trial_start_time
                time_remaining = max(0.0, trial_duration - elapsed)
                
                if time_remaining <= 0:
                    # Grade current trial
                    is_pos_match = (idx >= N and seq[idx][0] == seq[idx - N][0])
                    is_let_match = (idx >= N and seq[idx][1] == seq[idx - N][1])
                    
                    if is_pos_match:
                        if st.session_state.nback_user_pos_clicked:
                            st.session_state.nback_hits_pos += 1
                        else:
                            st.session_state.nback_misses_pos += 1
                    else:
                        if st.session_state.nback_user_pos_clicked:
                            st.session_state.nback_false_alarms_pos += 1
                            
                    if is_let_match:
                        if st.session_state.nback_user_let_clicked:
                            st.session_state.nback_hits_let += 1
                        else:
                            st.session_state.nback_misses_let += 1
                    else:
                        if st.session_state.nback_user_let_clicked:
                            st.session_state.nback_false_alarms_let += 1
                            
                    # Advance to next
                    st.session_state.nback_current_idx += 1
                    if st.session_state.nback_current_idx >= st.session_state.nback_total_trials:
                        st.session_state.nback_active = False
                        st.session_state.nback_finished = True
                    else:
                        st.session_state.nback_user_pos_clicked = False
                        st.session_state.nback_user_let_clicked = False
                        st.session_state.nback_trial_start_time = time.time()
                    st.rerun()
                
                # Show active visual stimulus for first 1.2 seconds
                show_stimulus = elapsed < 1.2
                
                # Timer / Progress bar
                st.progress(time_remaining / trial_duration, text=f"Trial {idx + 1} of {st.session_state.nback_total_trials} | Remember {N}-back")
                
                # Speech synthesis injection
                if show_stimulus and st.session_state.nback_last_speech_trial != idx:
                    st.session_state.nback_last_speech_trial = idx
                    tts_html = f"""
                    <script>
                    if ('speechSynthesis' in window) {{
                        var msg = new SpeechSynthesisUtterance('{current_letter}');
                        msg.rate = 1.1;
                        window.speechSynthesis.speak(msg);
                    }}
                    </script>
                    """
                    st.components.v1.html(tts_html, height=0)
                
                # CSS & Grid rendering
                css_grid = """
                <style>
                .nback-container {
                    display: flex;
                    flex-direction: column;
                    align-items: center;
                    margin: 10px 0;
                }
                .grid-container {
                    display: grid;
                    grid-template-columns: repeat(3, 80px);
                    grid-gap: 12px;
                    justify-content: center;
                    margin: 15px auto;
                }
                .grid-cell {
                    width: 80px;
                    height: 80px;
                    background-color: #1e293b;
                    border: 2px solid #334155;
                    border-radius: 12px;
                    transition: all 0.1s ease-in-out;
                }
                .grid-cell.active {
                    background-color: #3b82f6;
                    border-color: #60a5fa;
                    box-shadow: 0 0 15px rgba(59, 130, 246, 0.6);
                    transform: scale(1.04);
                }
                .letter-display {
                    font-size: 44px;
                    font-weight: 800;
                    color: #f8fafc;
                    height: 60px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    margin-bottom: 15px;
                }
                </style>
                """
                grid_cells = ""
                for cell_id in range(1, 10):
                    is_active = show_stimulus and (current_pos == cell_id)
                    active_class = "active" if is_active else ""
                    grid_cells += f"<div class='grid-cell {active_class}'></div>"
                
                letter_text = current_letter if show_stimulus else "+"
                full_html = f"{css_grid}<div class='nback-container'><div class='letter-display'>{letter_text}</div><div class='grid-container'>{grid_cells}</div></div>"
                st.markdown(full_html, unsafe_allow_html=True)
                
                # Match Buttons
                col1, col2 = st.columns(2)
                with col1:
                    pos_btn_label = "✅ Position Matched!" if st.session_state.nback_user_pos_clicked else "Match Position [A]"
                    if st.button(pos_btn_label, use_container_width=True, key="nback_pos_btn"):
                        st.session_state.nback_user_pos_clicked = True
                        st.rerun()
                with col2:
                    let_btn_label = "✅ Letter Matched!" if st.session_state.nback_user_let_clicked else "Match Letter [L]"
                    if st.button(let_btn_label, use_container_width=True, key="nback_let_btn"):
                        st.session_state.nback_user_let_clicked = True
                        st.rerun()
                        
                # Keyboard listener
                keys_html = """
                <script>
                const doc = window.parent.document;
                const handleKeyDown = (e) => {
                    if (e.key === 'a' || e.key === 'A') {
                        const buttons = Array.from(doc.querySelectorAll("button"));
                        const btn = buttons.find(b => b.innerText.includes("Match Position") || b.innerText.includes("Position Matched"));
                        if (btn) btn.click();
                    }
                    if (e.key === 'l' || e.key === 'L') {
                        const buttons = Array.from(doc.querySelectorAll("button"));
                        const btn = buttons.find(b => b.innerText.includes("Match Letter") || b.innerText.includes("Letter Matched"));
                        if (btn) btn.click();
                    }
                };
                doc.addEventListener('keydown', handleKeyDown);
                window.onbeforeunload = () => {
                    doc.removeEventListener('keydown', handleKeyDown);
                };
                </script>
                """
                st.components.v1.html(keys_html, height=0)

                # Quit Button
                st.write("")
                if st.button("Quit Game", type="secondary", key="nback_quit"):
                    st.session_state.nback_active = False
                    st.session_state.nback_finished = False
                    st.rerun()
                    
                # Small delay and rerun
                time.sleep(0.15)
                st.rerun()

            elif st.session_state.nback_finished:
                st.success("🎉 Dual N-Back Completed!")
                N = st.session_state.nback_n_level
                total = st.session_state.nback_total_trials
                seq = st.session_state.nback_sequence
                
                # Calculations
                pos_matches = sum(1 for i in range(N, total) if seq[i][0] == seq[i - N][0])
                let_matches = sum(1 for i in range(N, total) if seq[i][1] == seq[i - N][1])
                pos_non_matches = (total - N) - pos_matches
                let_non_matches = (total - N) - let_matches
                
                hits_pos = st.session_state.nback_hits_pos
                hits_let = st.session_state.nback_hits_let
                fa_pos = st.session_state.nback_false_alarms_pos
                fa_let = st.session_state.nback_false_alarms_let
                
                # Rates
                pos_hit_rate = (hits_pos / pos_matches * 100) if pos_matches > 0 else 100.0
                let_hit_rate = (hits_let / let_matches * 100) if let_matches > 0 else 100.0
                pos_fa_rate = (fa_pos / pos_non_matches * 100) if pos_non_matches > 0 else 0.0
                let_fa_rate = (fa_let / let_non_matches * 100) if let_non_matches > 0 else 0.0
                
                overall_score = round(max(0.0, ((pos_hit_rate - pos_fa_rate) + (let_hit_rate - let_fa_rate)) / 2), 1)
                
                col1, col2, col3 = st.columns(3)
                col1.metric("Cognitive Score", f"{overall_score}%")
                col2.metric("Position Performance", f"Hits: {hits_pos}/{pos_matches} | FAs: {fa_pos}")
                col3.metric("Letter Performance", f"Hits: {hits_let}/{let_matches} | FAs: {fa_let}")
                
                st.write("Save your session to log your working memory capacity and track cognitive growth:")
                with st.form("save_nback_result"):
                    fatigue_level = st.select_slider("Brain Fatigue level right now", options=["Fresh 🍃", "Normal 😐", "Tired 🥱", "Exhausted 🧠💤"], key="nback_fatigue")
                    user_notes = st.text_input("Notes (e.g. Felt focused, done in afternoon)", value=f"N-Level: {N}, Fatigue: {fatigue_level}", key="nback_notes")
                    
                    if st.form_submit_button("Save Session"):
                        log_data = {
                            "date": date.today().isoformat(),
                            "timestamp": datetime.now().isoformat(),
                            "type": f"Dual {N}-Back",
                            "metrics": {
                                "score": overall_score,
                                "pos_hits": hits_pos,
                                "pos_matches": pos_matches,
                                "pos_false_alarms": fa_pos,
                                "let_hits": hits_let,
                                "let_matches": let_matches,
                                "let_false_alarms": fa_let,
                                "n_level": N
                            },
                            "notes": user_notes
                        }
                        save_mental_log(current_user, log_data)
                        st.session_state.nback_finished = False
                        st.success("Dual N-Back session saved!")
                        st.rerun()
                        
                if st.button("Try Again", key="nback_again"):
                    st.session_state.nback_finished = False
                    st.rerun()

    with tab_practices:
        st.subheader("Practices for the Soul")
        st.markdown(
            "Sports psychology techniques to improve emotional resilience, focus, and mental toughness. "
            "Integrate these into your running schedule."
        )

        practice_cat = st.selectbox("Choose Category", ["Visualization Rehearsal", "Self-Talk & Mantras", "Mindful Breathing & Soul"])

        if practice_cat == "Visualization Rehearsal":
            st.write("### Visualization Rehearsal")
            st.markdown(
                "Visualization involves mentally simulating your run or race before it happens. "
                "Research shows it reduces anxiety, prepares the nervous system, and builds self-efficacy."
            )
            
            viz_preset_key = st.selectbox("Choose a Rehearsal Type", list(VISUALIZATION_PRESETS.keys()), format_func=lambda k: VISUALIZATION_PRESETS[k]["title"])
            preset = VISUALIZATION_PRESETS[viz_preset_key]
            
            st.info(f"**Description:** {preset['summary']}")
            
            st.write("**Step-by-step instructions:**")
            for step in preset["steps"]:
                st.write(f"- {step}")
                
            st.write("---")
            st.write("### Log your Visualization Session")
            with st.form("viz_form", clear_on_submit=True):
                st.write("Close your eyes, run through the visualization for 5-10 minutes, then log it here:")
                viz_notes = st.text_area("Reflections / What did you focus on?", placeholder="e.g. Visualized pushing hard up the final climb of the 10k course, keeping shoulders loose, and talking to myself to stay calm.")
                if st.form_submit_button("Log Session"):
                    log_data = {
                        "date": date.today().isoformat(),
                        "timestamp": datetime.now().isoformat(),
                        "type": f"Visualization ({preset['title']})",
                        "metrics": {},
                        "notes": viz_notes
                    }
                    save_mental_log(current_user, log_data)
                    st.success("Visualization session logged!")
                    st.rerun()

        elif practice_cat == "Self-Talk & Mantras":
            st.write("### Self-Talk & Mantras")
            st.markdown(
                "How you talk to yourself directly impacts your perceived fatigue. "
                "Use mantras to correct form (instructional) or keep grit high (motivational)."
            )
            
            mantra_preset_key = st.selectbox("Choose Mantra Type", list(MANTRA_PRESETS.keys()), format_func=lambda k: MANTRA_PRESETS[k]["title"])
            preset = MANTRA_PRESETS[mantra_preset_key]
            
            st.write(f"**Explanation:** {preset['summary']}")
            st.write("**Examples:**")
            for ex in preset["examples"]:
                st.write(f'- *"{ex}"*')
                
            st.write("---")
            st.write("### Build & Save Your Mantra")
            with st.form("mantra_form", clear_on_submit=True):
                custom_mantra = st.text_input("My Custom Mantra", placeholder="e.g. Strong hips, relaxed lips.")
                usage = st.text_input("When will you use this?", placeholder="e.g. During the final 2km of my tempo run when legs feel heavy")
                if st.form_submit_button("Save Mantra"):
                    log_data = {
                        "date": date.today().isoformat(),
                        "timestamp": datetime.now().isoformat(),
                        "type": "Mantra Builder",
                        "metrics": {},
                        "notes": f"Mantra: '{custom_mantra}' | Usage: {usage}"
                    }
                    save_mental_log(current_user, log_data)
                    st.success("Mantra saved!")
                    st.rerun()

        elif practice_cat == "Mindful Breathing & Soul":
            st.write("### Mindful Breathing & Soul")
            st.markdown(
                "Mindfulness practices help you connect with nature, manage acute running pain, "
                "and shift your focus from rigid metrics to the pure joy of movement."
            )
            
            breast_preset_key = st.selectbox("Choose a Practice", list(BREATHWORK_PRESETS.keys()), format_func=lambda k: BREATHWORK_PRESETS[k]["title"])
            preset = BREATHWORK_PRESETS[breast_preset_key]
            
            st.info(f"**Description:** {preset['description']}")
            st.write("**Instructions:**")
            st.write(preset["instructions"])
            
            st.write("---")
            st.write("### Log your Mindful/Breathwork Practice")
            with st.form("breath_form", clear_on_submit=True):
                duration_min = st.slider("Duration (minutes)", 1, 60, 10)
                breath_notes = st.text_area("Reflections (e.g. Practiced box breathing pre-run, felt very calm and focused; or focused on gratitude for lungs/legs)", placeholder="Write down how you felt after the session...")
                if st.form_submit_button("Log Session"):
                    log_data = {
                        "date": date.today().isoformat(),
                        "timestamp": datetime.now().isoformat(),
                        "type": f"Mindful Breathing ({preset['title']})",
                        "metrics": {"duration_min": duration_min},
                        "notes": breath_notes
                    }
                    save_mental_log(current_user, log_data)
                    st.success("Mindful practice logged!")
                    st.rerun()

    with tab_logs:
        st.subheader("Mental Training Logs")
        st.markdown("Your historic mental strength exercises, cognitive performance, and soul training logs.")
        
        logs = load_mental_logs(current_user)
        if not logs:
            st.info("No mental training logs found. Start an exercise above!")
        else:
            for log in logs:
                log_date = log.get("date", "Unknown")
                log_type = log.get("type", "Unknown")
                metrics = log.get("metrics", {})
                notes = log.get("notes", "")
                
                header = f"{log_date} — {log_type}"
                if "score" in metrics:
                    header += f" (Score: {metrics['score']})"
                elif "duration_min" in metrics:
                    header += f" ({metrics['duration_min']} min)"
                    
                with st.expander(header):
                    if "score" in metrics:
                        col1, col2, col3 = st.columns(3)
                        col1.write(f"**Accuracy:** {metrics.get('accuracy')}%")
                        col2.write(f"**Reaction Time:** {metrics.get('reaction_time')}s")
                        col3.write(f"**Correct / Total:** {metrics.get('correct')} / {metrics.get('total')}")
                    elif "duration_min" in metrics:
                        st.write(f"**Duration:** {metrics.get('duration_min')} minutes")
                    
                    st.write(f"**Notes/Reflections:**")
                    st.write(notes if notes else "No notes.")

# --- SETTINGS ---
elif page == "Settings":
    st.header("Settings")
    
    st.subheader("🧠 AI")
    st.session_state.gemini_api_key = st.text_input("Gemini API Key", value=st.session_state.gemini_api_key, type="password")
    
    # Ensure current model is in options
    if st.session_state.model_name not in MODEL_OPTIONS:
        MODEL_OPTIONS.append(st.session_state.model_name)

    st.session_state.model_name = st.selectbox("Model", MODEL_OPTIONS, index=MODEL_OPTIONS.index(st.session_state.model_name))

    st.markdown("---")
    st.subheader("📝 System Prompt")
    st.caption(f"Custom coaching instructions for **{st.session_state.model_name}**. Athlete data (profile, Garmin, journals) is appended automatically.")
    custom_prompt = load_model_prompt(current_user, st.session_state.model_name)
    prompt_value = custom_prompt if custom_prompt else DEFAULT_COACH_PROMPT
    edited_prompt = st.text_area(
        "Coaching Instructions",
        value=prompt_value,
        height=300,
        key="system_prompt_editor"
    )
    col_save, col_reset = st.columns(2)
    with col_save:
        if st.button("Save Prompt"):
            save_model_prompt(current_user, st.session_state.model_name, edited_prompt)
            st.success(f"Prompt saved for {st.session_state.model_name}")
    with col_reset:
        if st.button("Reset to Default"):
            save_model_prompt(current_user, st.session_state.model_name, DEFAULT_COACH_PROMPT)
            st.success("Reset to default prompt")
            st.rerun()

    st.markdown("---")
    st.subheader("🔗 Garmin")
    is_auth = is_garmin_authenticated(current_user)
    
    if is_auth:
        st.success("Status: Authenticated ✅")
        if st.button("Sync Last 7 Days"):
            with st.spinner("Syncing..."):
                result = sync_garmin_activities(current_user)
                if "Session expired" in result:
                    st.error(result)
                    is_auth = False # Force login fields
                else:
                    st.info(result)
        
        with st.expander("Bulk Sync"):
            start_date = st.date_input("Since", value=date.today() - timedelta(days=30))
            if st.button("Start Bulk Sync"):
                with st.spinner("Bulk Syncing..."):
                    result = sync_garmin_activities(current_user, start_date_obj=start_date)
                    if "Session expired" in result:
                        st.error(result)
                        is_auth = False
                    else:
                        st.info(result)
        
        if st.checkbox("Force Re-login"): is_auth = False
    
    if not is_auth:
        st.warning("Please login to Garmin Connect")
        with st.form("login_form"):
            g_email = st.text_input("Email")
            g_pass = st.text_input("Password", type="password")
            do_bulk = st.checkbox("Bulk Sync (Last 30 days)?", value=False)
            
            if st.form_submit_button("Login & Sync"):
                with st.spinner("Logging in..."):
                    start_date = date.today() - timedelta(days=30) if do_bulk else None
                    result = sync_garmin_activities(current_user, g_email, g_pass, start_date_obj=start_date)
                    st.info(result)
                    if "Successfully" in result:
                        st.rerun()

    st.markdown("---")
    st.subheader("👤 Profile")
    profile = load_user_profile(current_user)
    with st.form("profile"):
        goals = st.text_area("Goals", value=profile.get("goals", ""))
        injuries = st.text_area("Injuries", value=profile.get("injuries", ""))
        if st.form_submit_button("Save Profile"):
            save_user_profile(current_user, {"name": profile.get("name"), "goals": goals, "injuries": injuries})
            st.success("Updated!")
