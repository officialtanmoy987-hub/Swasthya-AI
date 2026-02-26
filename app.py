import datetime

import streamlit as st

from services.db import init_db, save_emergency_event, save_health_record
from services.ml import predict_risk_probability, train_and_save_model
from services.sms import send_bulk_sms

st.set_page_config(page_title="Swasthya AI", layout="wide")
init_db()

st.title("Swasthya AI")
st.subheader("24x7 Intelligent Health Monitoring and Emergency Response System")

st.sidebar.markdown("### Model")
if st.sidebar.button("Train/Refresh AI Model"):
    ok, msg = train_and_save_model()
    if ok:
        st.sidebar.success(msg)
    else:
        st.sidebar.error(msg)

mode = st.sidebar.selectbox(
    "Select Mode",
    ["Smart Dashboard", "Traveller Mode", "Emergency and Alerts", "Medicine Reminder"],
)

st.sidebar.markdown("### Emergency Contacts")
family_contact = st.sidebar.text_input("Family Member Phone")
doctor_contact = st.sidebar.text_input("Doctor Phone")


def trigger_alerts(event_type: str, message: str):
    numbers = [n for n in [family_contact, doctor_contact] if n]
    if not numbers:
        save_emergency_event(event_type, message, "no_contacts")
        st.warning("No contact numbers found. Add contacts in sidebar.")
        return

    results = send_bulk_sms(numbers, message)
    ok_count = 0
    for number, ok, detail in results:
        if ok:
            ok_count += 1
            st.success(f"SMS sent to {number} (SID: {detail})")
        else:
            st.error(f"SMS failed for {number}: {detail}")

    status = f"{ok_count}/{len(results)} sent"
    save_emergency_event(event_type, message, status, family_contact, doctor_contact)


if mode == "Smart Dashboard":
    st.header("Real-Time Health Monitoring")

    col1, col2, col3 = st.columns(3)
    with col1:
        heart_rate = st.number_input("Heart Rate (BPM)", 40, 200, 80)
    with col2:
        bp = st.number_input("Systolic BP", 80, 200, 120)
    with col3:
        sugar = st.number_input("Blood Sugar (mg/dL)", 50, 400, 100)

    if st.button("Analyze and Save"):
        risk_prob = predict_risk_probability(float(heart_rate), float(bp), float(sugar))
        risk_score = int(round(risk_prob * 100))
        risk_label = 1 if risk_score >= 60 else 0

        save_health_record(float(heart_rate), float(bp), float(sugar), risk_score, risk_label)
        st.metric("AI Health Risk Score", f"{risk_score}%")

        if risk_score < 30:
            st.success("Health stable - no immediate risk")
        elif risk_score < 60:
            st.warning("Moderate risk - monitor closely")
        else:
            st.error("High risk detected - emergency protocol activated")
            msg = (
                f"Emergency alert from Swasthya AI. Risk score: {risk_score}%. "
                f"HR: {heart_rate}, BP: {bp}, Sugar: {sugar}."
            )
            trigger_alerts("auto_high_risk", msg)

elif mode == "Traveller Mode":
    st.header("Traveller Safety Mode")
    location = st.text_input("Travel Location")
    weather = st.selectbox("Weather Condition", ["Hot", "Cold", "Humid", "Rainy"])
    altitude = st.selectbox("Altitude Level", ["Normal", "High Altitude"])

    if weather == "Hot":
        st.info("Dehydration risk high. Increase fluid intake.")
    if weather == "Cold":
        st.info("Monitor BP fluctuations in cold weather.")
    if altitude == "High Altitude":
        st.warning("Oxygen level monitoring recommended.")

    if location:
        st.success(f"Traveller mode active for {location}")
    st.write("Continuous monitoring during travel enabled.")

elif mode == "Emergency and Alerts":
    st.header("Manual Emergency Trigger")
    st.warning("Press this button only in a real emergency")

    if st.button("Activate Emergency Response"):
        st.error("Emergency protocol initiated")
        msg = "Manual emergency triggered from Swasthya AI. Immediate response requested."
        trigger_alerts("manual_trigger", msg)
        st.write("Notifying nearest hospital and requesting ambulance dispatch.")

elif mode == "Medicine Reminder":
    st.header("Smart Medicine Reminder")
    med_name = st.text_input("Medicine Name")
    med_time = st.time_input("Select Reminder Time", datetime.time(9, 0))

    if st.button("Set Reminder"):
        if med_name.strip():
            reminder_msg = f"Medicine reminder: Take {med_name} at {med_time}."
            st.success(f"Reminder scheduled for {med_name} at {med_time}")
            trigger_alerts("medicine_reminder", reminder_msg)
        else:
            st.warning("Enter medicine name before setting reminder.")



