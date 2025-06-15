# MindMate: Streamlit App for Mental Wellbeing

import streamlit as st
import pandas as pd
import datetime
from textblob import TextBlob
import altair as alt

# Initialize mood log CSV
MOOD_FILE = "mood_logs.csv"

# Emojis for mood selection
MOODS = {"😄": 5, "🙂": 4, "😐": 3, "😕": 2, "😞": 1}

# Load or create mood logs
def load_data():
    try:
        return pd.read_csv(MOOD_FILE, parse_dates=["timestamp"])
    except:
        return pd.DataFrame(columns=["timestamp", "mood", "score", "entry", "tags"])

def save_data(df):
    df.to_csv(MOOD_FILE, index=False)

st.set_page_config(page_title="MindMate", layout="centered", page_icon="🧠")
st.title("🧠 MindMate – Your Daily Mental Wellness Companion")

st.header("1. How are you feeling today?")
col1, col2 = st.columns([1, 2])

with col1:
    mood = st.radio("Select your mood:", options=list(MOODS.keys()), horizontal=True)
with col2:
    entry = st.text_area("Write a short journal entry (optional):")
    tags = st.text_input("Add tags (comma-separated, e.g., anxiety, focus):")

if st.button("Save Entry"):
    data = load_data()
    new_entry = {
        "timestamp": datetime.datetime.now(),
        "mood": mood,
        "score": MOODS[mood],
        "entry": entry,
        "tags": tags
    }
    data = pd.concat([data, pd.DataFrame([new_entry])], ignore_index=True)
    save_data(data)
    st.success("Your mood has been logged. Great job checking in! 💖")

st.header("2. Mood Trends & Reflections")
data = load_data()
if not data.empty:
    data["date"] = data["timestamp"].dt.date
    mood_chart = alt.Chart(data).mark_line(point=True).encode(
        x="date:T", y="score:Q", tooltip=["date", "mood", "entry"]
    ).properties(height=300)
    st.altair_chart(mood_chart, use_container_width=True)

    # Word cloud or text summary
    if st.checkbox("Show AI Reflection"):
        recent_entry = data.iloc[-1]["entry"]
        if recent_entry:
            blob = TextBlob(recent_entry)
            tone = blob.sentiment.polarity
            summary = "You seem positive today 😊" if tone > 0.2 else (
                      "You may be feeling a bit down 💭" if tone < -0.2 else
                      "You're feeling neutral 🌿")
            st.markdown(f"**Latest Entry Tone:** {summary}")
else:
    st.info("No mood data yet. Log your first mood above!")

st.header("3. Mindfulness Corner")
st.markdown("Listen to a short calming track or ambient soundscape:")
st.video("https://www.youtube.com/embed/2OEL4P1Rz04")

st.header("4. Self-Care Checklist")
for habit in ["💧 Drink water", "🚶‍♂️ Take a 10-minute walk", "📞 Call a friend", "🧘‍♀️ 3-minute breathing"]:
    st.checkbox(habit)

st.caption("Built with 💙 by Bhavesh using Streamlit")
