import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth, firestore, initialize_app, get_app
import datetime
import time
import os
import json
import pandas as pd
import altair as alt
from textblob import TextBlob

# generate advice based on journal entry
def generate_advice(entry, tags):
    suggestions = []

    # Analyze tone using TextBlob
    polarity = TextBlob(entry).sentiment.polarity
    if polarity < -0.3:
        suggestions.append("It seems you're feeling down. Consider taking a short walk or talking to someone you trust.")
    elif polarity < 0:
        suggestions.append("You may be slightly low. Maybe try journaling your thoughts in more detail.")
    elif polarity > 0.4:
        suggestions.append("You're feeling upbeat! Celebrate small wins to keep that energy going.")

    # Tag-based suggestions
    tag_list = [tag.strip().lower() for tag in tags if tag]
    if "stress" in tag_list:
        suggestions.append("Try a 5-minute breathing exercise to reduce stress.")
    if "sleep" in tag_list:
        suggestions.append("Consider winding down early and avoiding screens before bed.")
    if "work" in tag_list:
        suggestions.append("Take short breaks during your work hours to maintain focus.")
    if "anxiety" in tag_list:
        suggestions.append("Write down what's worrying you — sometimes clarity comes through expression.")
    if "focus" in tag_list:
        suggestions.append("Try the Pomodoro technique (25 min focus, 5 min rest).")

    if not suggestions:
        suggestions.append("Keep tracking your feelings — awareness is the first step to balance.")

    return suggestions

# generate advice based on the mood (1-5)
def generate_reflection_from_mood(mood_rating: int) -> str:
    mood_rating = int(mood_rating)
    if mood_rating <= 2:
        return "It's okay to have tough days. Take it easy and be kind to yourself today. Even small steps matter."
    elif mood_rating == 3:
        return "You're hanging in there. Maybe try a short walk or talk to a friend to recharge a bit."
    elif mood_rating == 4:
        return "You're doing well! Keep up the good energy and consider reflecting on what made today a good one."
    elif mood_rating == 5:
        return "You're thriving today — that's amazing! Think about how to carry this momentum forward."
    else:
        return "How you're feeling matters. Stay aware and take care of yourself."

# Load key from secrets
firebase_key_dict = json.loads(st.secrets["FIREBASE_KEY_JSON"])
cred = credentials.Certificate(firebase_key_dict)

# Initialize app only if not already done
try:
    firebase_admin.get_app()
except ValueError:
    firebase_admin.initialize_app(cred)

db = firestore.client()

# Session state
if "user_email" not in st.session_state:
    st.session_state.user_email = None

# Login or Register
def login_page():
    st.title("🧠 MindMate – Login")
    option = st.selectbox("Select option", ["Login", "Register"])
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    if st.button(option):
        try:
            if option == "Register":
                user = auth.create_user(email=email, password=password)
                st.success("Registered successfully! Please login.")
            else:
                # Simulate login (firebase-admin has no client-side auth)
                st.session_state.user_email = email
                st.success("Logged in successfully!")
                time.sleep(1)
                st.rerun()  # 🔁 This will reload the app and show the dashboard
        except Exception as e:
            st.error(str(e))


if not st.session_state.user_email:
    login_page()
    st.stop()

# Mood Logger
st.title("🧠 MindMate – Your Wellness Dashboard")

user_id = st.session_state.user_email.replace(".", "_")  # Firestore safe
moods = {"😄": 5, "🙂": 4, "😐": 3, "😕": 2, "😞": 1}
mood = st.radio("How do you feel today?", list(moods.keys()), horizontal=True)
entry = st.text_area("Write a journal entry (optional)")
tag_input = st.text_input(
    "Add tags", 
    placeholder="e.g., anxiety, sleep, motivation"
)

# Convert to list after user inputs
tags = [tag.strip() for tag in tag_input.split(',') if tag.strip()] if tag_input else []

if st.button("Save Entry"):
    log_ref = db.collection("mood_logs").document(user_id).collection("logs")
    log_ref.add({
        "timestamp": datetime.datetime.now(),
        "mood": mood,
        "score": moods[mood],
        "entry": entry,
        "tags": tags
    })
    st.success("Mood saved!")

    # AI Advice Generator
    advice_list = generate_advice(entry, tags)
    st.subheader("💡 MindMate Advice")
    for a in advice_list:
        st.markdown(f"✅ {a}")

# Fetch Logs
logs_ref = db.collection("mood_logs").document(user_id).collection("logs")
docs = logs_ref.order_by("timestamp").stream()
data = [{
    "timestamp": doc.to_dict()["timestamp"],
    "mood": doc.to_dict()["mood"],
    "score": doc.to_dict()["score"],
    "entry": doc.to_dict().get("entry", ""),
    "tags": doc.to_dict().get("tags", "")
} for doc in docs]

if data:
    df = pd.DataFrame(data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['date'] = df['timestamp'].dt.date

    st.subheader("📈 Mood Over Time")
    chart = alt.Chart(df).mark_line(point=True).encode(
        x='date:T', y='score:Q', tooltip=['mood', 'entry']
    ).properties(height=300)
    st.altair_chart(chart, use_container_width=True)

    st.subheader("🧠 AI Reflection")
    last_mood_score = df.iloc[-1]["score"]
    reflection = generate_reflection_from_mood(last_mood_score)
    mood_emojis = {
        1: "😞 Very Low",
        2: "😕 Low",
        3: "😐 Neutral",
        4: "🙂 Good",
        5: "😄 Great"
    }

    st.markdown(f"**Last mood:** {mood_emojis.get(last_mood_score, 'Unknown')} ({last_mood_score})")
    st.info(reflection)
    

    # add advice from last journal entry
    st.subheader("💡 Advice based on Your Recent Thoughts")
    last_tags = df.iloc[-1]["tags"]
    last_text = df.iloc[-1]["entry"]
    advice = generate_advice(last_text, last_tags)
    for tip in advice:
        st.markdown(f"✅ {tip}")

if st.button("Logout"):
    del st.session_state.user_email
    st.success("Logged out successfully!")
    time.sleep(1)
    st.rerun()