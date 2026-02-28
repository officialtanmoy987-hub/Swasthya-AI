import datetime
import io
import secrets
import streamlit as st
import pandas as pd
import joblib
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from services.fitbit_auth import (
    build_authorize_url,
    exchange_code_for_tokens,
    generate_pkce_pair,
    load_tokens,
    refresh_access_token,
    save_tokens,
    token_is_expired,
)
from services.db import init_db, save_emergency_event, save_health_record
from services.ml import predict_risk_probability, train_and_save_model
from services.sms import send_bulk_sms
from services.wearable_connectors import sync_fitbit_once, sync_google_fit_once

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
    [
        "Smart Dashboard",
        "Traveller Mode",
        "Emergency and Alerts",
        "Medicine Reminder",
        "Model Trainer (CSV)",
        "Wearable Connectors",
    ],
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

elif mode == "Model Trainer (CSV)":
    st.header("Train AI Model with scikit-learn")
    st.write("Upload a CSV file, choose feature columns and target column, then train.")

    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded is not None:
        raw = uploaded.read()
        df = pd.read_csv(io.BytesIO(raw))
        st.write("Preview")
        st.dataframe(df.head())

        if df.shape[1] < 2:
            st.error("CSV must have at least 2 columns.")
        else:
            all_cols = list(df.columns)
            target_col = st.selectbox("Target Column (label)", all_cols)
            feature_cols = st.multiselect(
                "Feature Columns (inputs)",
                [c for c in all_cols if c != target_col],
                default=[c for c in all_cols if c != target_col][:3],
            )
            model_path = st.text_input("Model Save Path (.joblib)", "trained_model.joblib")

            if st.button("Train scikit-learn Model"):
                if not feature_cols:
                    st.warning("Select at least one feature column.")
                else:
                    x = df[feature_cols]
                    y = df[target_col]

                    x = x.apply(pd.to_numeric, errors="coerce")
                    y = pd.to_numeric(y, errors="coerce")
                    clean = pd.concat([x, y], axis=1).dropna()

                    x_clean = clean[feature_cols]
                    y_clean = clean[target_col].astype(int)

                    if y_clean.nunique() < 2:
                        st.error("Target needs at least 2 classes.")
                    elif len(clean) < 10:
                        st.error("Not enough valid rows after cleanup. Need at least 10.")
                    else:
                        x_train, x_test, y_train, y_test = train_test_split(
                            x_clean, y_clean, test_size=0.2, random_state=42
                        )
                        model = LogisticRegression(max_iter=1000)
                        model.fit(x_train, y_train)
                        y_pred = model.predict(x_test)
                        acc = accuracy_score(y_test, y_pred)

                        st.success("Model trained successfully.")
                        st.metric("Accuracy", f"{acc:.2%}")
                        joblib.dump(
                            {
                                "model": model,
                                "feature_columns": feature_cols,
                                "target_column": target_col,
                            },
                            model_path,
                        )
                        st.success(f"Model saved: {model_path}")

elif mode == "Wearable Connectors":
    st.header("Wearable Connectors (Fitbit / Google Fit)")
    st.write("Fetch heart-rate from provider APIs and push to auto-analysis gateway.")
    st.caption(
        "Most watches do not expose direct Bluetooth to Python apps. "
        "Production flow is watch -> provider cloud -> this connector -> gateway."
    )

    provider = st.selectbox("Provider", ["fitbit", "googlefit"])
    access_token = st.text_input("Access Token (optional if using OAuth)", type="password")
    gateway_url = st.text_input("Gateway URL", "http://127.0.0.1:8080")
    fallback_bp = st.number_input("Fallback Systolic BP", min_value=80, max_value=220, value=120)
    fallback_sugar = st.number_input("Fallback Blood Sugar", min_value=50, max_value=450, value=100)

    if provider == "fitbit":
        st.subheader("Fitbit OAuth Setup")
        client_id = st.text_input("Fitbit Client ID")
        client_secret = st.text_input("Fitbit Client Secret (if required)", type="password")
        redirect_uri = st.text_input("Redirect URI", "http://127.0.0.1:8765/callback")
        scope = st.text_input("Scope", "heartrate")
        auth_code = st.text_input("Authorization Code")

        col_auth, col_exchange, col_refresh = st.columns(3)
        with col_auth:
            if st.button("Generate Login URL"):
                if not client_id.strip():
                    st.error("Client ID is required.")
                else:
                    code_verifier, code_challenge = generate_pkce_pair()
                    state = secrets.token_urlsafe(24)
                    st.session_state["fitbit_code_verifier"] = code_verifier
                    st.session_state["fitbit_state"] = state
                    url = build_authorize_url(
                        client_id=client_id.strip(),
                        redirect_uri=redirect_uri.strip(),
                        scope=scope.strip(),
                        state=state,
                        code_challenge=code_challenge,
                    )
                    st.session_state["fitbit_auth_url"] = url
                    st.info("Open Fitbit login URL below, then paste returned code.")

        if st.session_state.get("fitbit_auth_url"):
            st.markdown(f"[Open Fitbit Authorization URL]({st.session_state['fitbit_auth_url']})")

        with col_exchange:
            if st.button("Exchange Code"):
                verifier = st.session_state.get("fitbit_code_verifier")
                if not client_id.strip():
                    st.error("Client ID is required.")
                elif not auth_code.strip():
                    st.error("Authorization code is required.")
                elif not verifier:
                    st.error("Generate Login URL first in this session.")
                else:
                    ok, payload = exchange_code_for_tokens(
                        client_id=client_id.strip(),
                        code=auth_code.strip(),
                        redirect_uri=redirect_uri.strip(),
                        code_verifier=verifier,
                        client_secret=client_secret.strip() or None,
                    )
                    if ok:
                        save_tokens(payload)
                        st.success("Fitbit tokens saved to fitbit_tokens.json")
                    else:
                        st.error(str(payload))

        with col_refresh:
            if st.button("Refresh Saved Token"):
                saved = load_tokens()
                if not saved:
                    st.error("No saved tokens found.")
                elif not client_id.strip():
                    st.error("Client ID is required to refresh.")
                elif not saved.get("refresh_token"):
                    st.error("Saved token does not contain refresh_token.")
                else:
                    ok, payload = refresh_access_token(
                        client_id=client_id.strip(),
                        refresh_token=str(saved["refresh_token"]),
                        client_secret=client_secret.strip() or None,
                    )
                    if ok:
                        save_tokens(payload)
                        st.success("Token refreshed and saved.")
                    else:
                        st.error(str(payload))

        saved = load_tokens()
        if saved:
            st.caption(f"Saved token loaded. Expires at unix time: {int(saved.get('expires_at', 0))}")

    if st.button("Sync Now"):
        if provider == "fitbit":
            token_to_use = access_token.strip()
            saved = load_tokens() if not token_to_use else None
            if not token_to_use and saved:
                if token_is_expired(saved):
                    if not client_id.strip():
                        st.error("Saved Fitbit token expired. Enter Client ID to auto-refresh.")
                        st.stop()
                    if not saved.get("refresh_token"):
                        st.error("Saved Fitbit token expired and no refresh_token was found.")
                        st.stop()
                    ok_refresh, refreshed = refresh_access_token(
                        client_id=client_id.strip(),
                        refresh_token=str(saved["refresh_token"]),
                        client_secret=client_secret.strip() or None,
                    )
                    if not ok_refresh:
                        st.error(f"Auto-refresh failed: {refreshed}")
                        st.stop()
                    save_tokens(refreshed)
                    token_to_use = str(refreshed.get("access_token", ""))
                else:
                    token_to_use = str(saved.get("access_token", ""))

            if not token_to_use:
                st.error("No usable Fitbit access token. Paste token or complete OAuth setup.")
            else:
                ok, msg = sync_fitbit_once(
                    access_token=token_to_use,
                    gateway_url=gateway_url.strip(),
                    systolic_bp=float(fallback_bp),
                    blood_sugar=float(fallback_sugar),
                    family_contact=family_contact.strip() or None,
                    doctor_contact=doctor_contact.strip() or None,
                )
                if ok:
                    st.success("Sync successful.")
                    st.code(msg)
                else:
                    st.error(msg)
        else:
            if not access_token.strip():
                st.error("Access token is required.")
                st.stop()

            ok, msg = sync_google_fit_once(
                access_token=access_token.strip(),
                gateway_url=gateway_url.strip(),
                systolic_bp=float(fallback_bp),
                blood_sugar=float(fallback_sugar),
                family_contact=family_contact.strip() or None,
                doctor_contact=doctor_contact.strip() or None,
            )

            if ok:
                st.success("Sync successful.")
                st.code(msg)
            else:
                st.error(msg)





