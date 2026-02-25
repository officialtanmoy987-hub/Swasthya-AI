import streamlit as st
import datetime
import time

st.set_page_config(page_title="Swasthya AI", layout="wide")

st.title("🩺 Swasthya AI - Smart Health Monitoring System")

# Sidebar Navigation
mode = st.sidebar.selectbox(
    "Select Mode",
    ["🏠 Dashboard", "✈ Traveller Mode", "💊 Medicine Reminder"]
)

# ---------------- DASHBOARD ----------------
if mode == "🏠 Dashboard":
    st.header("📊 Health Monitoring Dashboard")

    col1, col2, col3 = st.columns(3)

    with col1:
        heart_rate = st.number_input("Heart Rate (BPM)", 40, 200, 72)
    with col2:
        bp = st.number_input("Systolic BP", 80, 200, 120)
    with col3:
        sugar = st.number_input("Blood Sugar (mg/dL)", 50, 400, 100)

    st.subheader("🧠 AI Health Analysis")

    if heart_rate > 100:
        st.error("⚠ High Heart Rate Detected!")
    elif heart_rate < 60:
        st.warning("⚠ Low Heart Rate Detected!")
    else:
        st.success("✅ Heart Rate Normal")

    if bp > 140:
        st.error("⚠ High Blood Pressure!")
    else:
        st.success("✅ Blood Pressure Normal")

    if sugar > 180:
        st.error("⚠ High Sugar Level!")
    else:
        st.success("✅ Sugar Level Normal")


# ---------------- TRAVELLER MODE ----------------
elif mode == "✈ Traveller Mode":
    st.header("🌍 Traveller Mode - Health Safety Assistant")

    location = st.text_input("Enter Travel Location")
    weather = st.selectbox("Weather Condition", ["Hot", "Cold", "Humid", "Rainy"])
    activity = st.selectbox("Activity Type", ["Walking", "Trekking", "Business Travel", "Vacation"])

    st.subheader("🧳 AI Travel Health Advice")

    if weather == "Hot":
        st.info("💧 Stay hydrated. Drink at least 3-4 liters of water.")
    if weather == "Cold":
        st.info("🧥 Wear warm clothes and monitor blood pressure.")
    if activity == "Trekking":
        st.warning("⚠ Carry glucose & check oxygen levels if at high altitude.")
    if activity == "Business Travel":
        st.info("😴 Ensure proper sleep to avoid stress-related BP issues.")

    st.success("✅ Traveller Mode Activated for " + location)


# ---------------- MEDICINE REMINDER ----------------
elif mode == "💊 Medicine Reminder":
    st.header("⏰ Smart Medicine Reminder")

    med_name = st.text_input("Medicine Name")
    med_time = st.time_input("Select Reminder Time", datetime.time(9, 0))

    if st.button("Set Reminder"):
        st.success(f"Reminder set for {med_name} at {med_time}")

    st.subheader("🔔 Live Reminder Simulation")

    current_time = datetime.datetime.now().time()

    if current_time.hour == med_time.hour and current_time.minute == med_time.minute:
        st.error(f"💊 Time to take your medicine: {med_name}")
    else:
        st.info("Waiting for reminder time...")

        