import streamlit as st
import os
from datetime import date, timedelta
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

page = st.sidebar.radio("Go to", ["Command Center", "Journal", "Settings"])

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
