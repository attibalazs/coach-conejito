import streamlit as st
import os
from datetime import date, timedelta
from modules.data_manager import (
    save_journal_entry, load_journal_entries, 
    save_user_profile, load_user_profile, 
    list_users, create_user, load_garmin_activities,
    save_coach_plan, load_coach_plan,
    save_chat_history, load_chat_history
)
from modules.gemini_coach import get_ai_coach_response
from modules.garmin_client import sync_garmin_activities, is_garmin_authenticated

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
        st.subheader("💬 Coach Chat")
        
        # Load history
        if "messages" not in st.session_state:
            st.session_state.messages = load_chat_history(current_user)

        # Chat container for scrolling
        chat_container = st.container()
        with chat_container:
            for msg in st.session_state.messages:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

        # Chat Input
        if prompt := st.chat_input("Ask Coach Conejito..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with chat_container:
                with st.chat_message("user"):
                    st.markdown(prompt)

                with st.chat_message("assistant"):
                    with st.spinner("Coach is thinking..."):
                        response = get_ai_coach_response(
                            st.session_state.gemini_api_key,
                            current_user,
                            model_name=st.session_state.model_name,
                            chat_mode=True,
                            user_message=prompt,
                            history=st.session_state.messages[-5:]
                        )
                        st.markdown(response)
                        st.session_state.messages.append({"role": "assistant", "content": response})
                        save_chat_history(current_user, st.session_state.messages)
            st.rerun() # Refresh to show 'Apply' button on last message

        # Action Button for the LAST message
        if st.session_state.messages and st.session_state.messages[-1]["role"] == "assistant":
            if st.button("📌 Set last response as Active Plan"):
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
                for act in activities[:5]:
                    date_str = act.get('startTimeLocal', 'Unknown')[:10]
                    dist = round(act.get('distance', 0) / 1000, 2)
                    label = act.get('trainingEffectLabel', 'N/A')
                    with st.expander(f"{date_str} - {dist}km ({label})"):
                        st.write(f"**Duration:** {round(act.get('duration', 0)/60, 1)} min")
                        st.write(f"**Avg HR:** {act.get('averageHR', 'N/A')}")
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
    model_options = ["gemini-1.5-flash", "gemini-1.5-pro", "qwen2.5-coder:latest", "phi4-mini:3.8b", "deepseek-r1:8b", "phi4"]
    st.session_state.model_name = st.selectbox("Model", model_options, index=model_options.index(st.session_state.model_name))

    st.markdown("---")
    st.subheader("🔗 Garmin")
    if is_garmin_authenticated(current_user):
        st.success("Authenticated ✅")
        if st.button("Sync Last 7 Days"):
            st.info(sync_garmin_activities(current_user))
        with st.expander("Bulk Sync"):
            start_date = st.date_input("Since", value=date.today() - timedelta(days=30))
            if st.button("Start Bulk Sync"):
                st.info(sync_garmin_activities(current_user, start_date_obj=start_date))
        if st.checkbox("Logout/Switch"): 
            # We don't have a formal logout, but showing the inputs allows re-auth
            pass
    
    # Always show login if not authenticated or checkbox checked
    if not is_garmin_authenticated(current_user) or st.checkbox("Show Login Fields"):
        g_email = st.text_input("Email")
        g_pass = st.text_input("Password", type="password")
        if st.button("Login"):
            st.info(sync_garmin_activities(current_user, g_email, g_pass))
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