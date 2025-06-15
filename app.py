import streamlit as st
import firebase_admin
from firebase_admin import credentials, auth, firestore, initialize_app
import datetime
import time
import os
import json
from dotenv import load_dotenv
import pandas as pd
import altair as alt
from textblob import TextBlob

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
    tag_list = [tag.strip().lower() for tag in tags.split(",") if tag]
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

load_dotenv()

# Load key from env and convert it to dict
firebase_key_dict = json.loads(os.getenv("FIREBASE_KEY_JSON"))

# Use it as credential
cred = credentials.Certificate(firebase_key_dict)
firebase_app = initialize_app(cred)

'''# Initialize Firebase only once
if not firebase_admin._apps:
    cred = credentials.Certificate("serviceAccountKey.json")
    firebase_admin.initialize_app(cred)
'''
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
tags = st.text_input("Add tags (comma separated)")

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
    last_entry = df.iloc[-1]["entry"]
    if last_entry:
        tone = TextBlob(last_entry).sentiment.polarity
        mood_msg = "You seem positive 😊" if tone > 0.2 else (
            "You may be feeling low 💭" if tone < -0.2 else "You're feeling neutral 🌿")
        st.info(f"Last journal tone: **{mood_msg}**")

        # add advice from last journal entry
        st.subheader("💡 Personalized Advice from your Journal")
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