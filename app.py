import streamlit as st
import sqlite3
import datetime
import pandas as pd

st.set_page_config(page_title="Swasthya AI", layout="wide")

# ---------------- DATABASE SETUP ----------------
conn = sqlite3.connect("health_data.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS vitals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT,
    heart_rate INTEGER,
    bp INTEGER,
    sugar INTEGER
)
""")
conn.commit()

# ---------------- TITLE ----------------
st.title("🩺 Swasthya AI")
st.subheader("24×7 Intelligent Health Monitoring & Emergency System")

mode = st.sidebar.selectbox(
    "Select Mode",
    ["🏠 Smart Dashboard", "📈 Health History"]
)

# ---------------- DASHBOARD ----------------
if mode == "🏠 Smart Dashboard":

    st.header("📊 Real-Time Health Monitoring")

    col1, col2, col3 = st.columns(3)

    with col1:
        heart_rate = st.number_input("Heart Rate (BPM)", 40, 200, 80)
    with col2:
        bp = st.number_input("Systolic BP", 80, 200, 120)
    with col3:
        sugar = st.number_input("Blood Sugar (mg/dL)", 50, 400, 100)

    if st.button("💾 Save Health Data"):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        c.execute(
            "INSERT INTO vitals (timestamp, heart_rate, bp, sugar) VALUES (?, ?, ?, ?)",
            (timestamp, heart_rate, bp, sugar)
        )
        conn.commit()

        st.success("Health data saved successfully!")

    # AI Risk Score
    risk_score = 0

    if heart_rate > 110 or heart_rate < 50:
        risk_score += 30
    if bp > 160:
        risk_score += 35
    if sugar > 250:
        risk_score += 35

    st.metric("⚡ AI Health Risk Score", f"{risk_score}%")

# ---------------- HEALTH HISTORY ----------------
elif mode == "📈 Health History":

    st.header("📈 Stored Health Records")

    data = pd.read_sql_query("SELECT * FROM vitals", conn)

    if data.empty:
        st.info("No records found.")
    else:
        st.dataframe(data)

        st.subheader("📊 Health Trends")

        st.line_chart(data[["heart_rate", "bp", "sugar"]])
