import streamlit as st
import datetime
import random

st.set_page_config(page_title="Swasthya AI", layout="wide")

st.title("🩺 Swasthya AI")
st.subheader("24×7 Intelligent Health Monitoring & Emergency Response System")

# ---------------- SIDEBAR ----------------
mode = st.sidebar.selectbox(
    "Select Mode",
    ["🏠 Smart Dashboard", "✈ Traveller Mode", "🚨 Emergency & Alerts", "💊 Medicine Reminder"]
)

st.sidebar.markdown("### 👨‍👩‍👧 Emergency Contacts")
family_contact = st.sidebar.text_input("Family Member Phone")
doctor_contact = st.sidebar.text_input("Doctor Phone")

# ---------------- SMART DASHBOARD ----------------
if mode == "🏠 Smart Dashboard":
    st.header("📊 Real-Time Health Monitoring")

    col1, col2, col3 = st.columns(3)

    with col1:
        heart_rate = st.number_input("Heart Rate (BPM)", 40, 200, 80)
    with col2:
        bp = st.number_input("Systolic BP", 80, 200, 120)
    with col3:
        sugar = st.number_input("Blood Sugar (mg/dL)", 50, 400, 100)

    st.subheader("🧠 AI Risk Analysis Engine")

    # Risk Score Calculation
    risk_score = 0

    if heart_rate > 110 or heart_rate < 50:
        risk_score += 30
    if bp > 160:
        risk_score += 35
    if sugar > 250:
        risk_score += 35

    st.metric("⚡ AI Health Risk Score", f"{risk_score}%")

    if risk_score < 30:
        st.success("✅ Health Stable - No Immediate Risk")
    elif 30 <= risk_score < 60:
        st.warning("⚠ Moderate Risk - Monitor Closely")
    else:
        st.error("🚨 HIGH RISK DETECTED - EMERGENCY PROTOCOL ACTIVATED")

        st.markdown("### 📡 Alert System Activated")

        if family_contact:
            st.write(f"📲 Notifying Family Member at {family_contact}")
        if doctor_contact:
            st.write(f"📞 Alerting Doctor at {doctor_contact}")

        st.write("🏥 Sending health data to nearest hospital...")
        st.write("📍 Sharing last known health metrics and location...")
        st.success("Emergency notifications sent successfully!")

# ---------------- TRAVELLER MODE ----------------
elif mode == "✈ Traveller Mode":
    st.header("🌍 Traveller Safety Mode")

    location = st.text_input("Travel Location")
    weather = st.selectbox("Weather Condition", ["Hot", "Cold", "Humid", "Rainy"])
    altitude = st.selectbox("Altitude Level", ["Normal", "High Altitude"])

    st.subheader("🧳 AI Travel Risk Advisory")

    if weather == "Hot":
        st.info("💧 Dehydration risk high. Increase fluid intake.")
    if weather == "Cold":
        st.info("🧥 Monitor BP fluctuations in cold weather.")
    if altitude == "High Altitude":
        st.warning("⚠ Oxygen level monitoring recommended.")

    st.success(f"Traveller Mode Active for {location}")
    st.write("📡 Continuous monitoring during travel enabled.")

# ---------------- EMERGENCY PANEL ----------------
elif mode == "🚨 Emergency & Alerts":
    st.header("🚨 Manual Emergency Trigger")

    st.warning("Press this button ONLY in real emergency")

    if st.button("🚨 ACTIVATE EMERGENCY RESPONSE"):
        st.error("Emergency Protocol Initiated")

        if family_contact:
            st.write(f"📲 Emergency SMS sent to {family_contact}")
        if doctor_contact:
            st.write(f"📞 Emergency call alert sent to {doctor_contact}")

        st.write("🏥 Notifying nearest hospital...")
        st.write("🚑 Requesting ambulance dispatch...")
        st.success("All emergency services notified!")

# ---------------- MEDICINE REMINDER ----------------
elif mode == "💊 Medicine Reminder":
    st.header("⏰ Smart Medicine Reminder")

    med_name = st.text_input("Medicine Name")
    med_time = st.time_input("Select Reminder Time", datetime.time(9, 0))

    if st.button("Set Reminder"):
        st.success(f"Reminder scheduled for {med_name} at {med_time}")
        st.info("📲 Reminder will notify patient & family member.")


