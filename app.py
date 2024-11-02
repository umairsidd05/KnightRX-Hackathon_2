import os
import smtplib
import ssl
from email.message import EmailMessage
import streamlit as st
from datetime import datetime, date, timedelta
import pandas as pd
import plotly.express as px
from apscheduler.schedulers.background import BackgroundScheduler
from models import SessionLocal, Medication, MedicationLog, ReminderSetting, HealthCheckIn

# Set page configuration - this must be the first Streamlit command
st.set_page_config(page_title="KnightRX", layout="wide")

# Hardcoded Gmail account credentials (for testing purposes)
SENDER_EMAIL = "umairsiddiqui2005@gmail.com"  # Your Gmail account
SENDER_PASSWORD = "qzwsqmwzdtqwgmqy"  # Your Gmail App Password (generated from your Gmail account settings)

# Initialize database session
db = SessionLocal()
scheduler = BackgroundScheduler()

# Custom CSS for a vibrant UI
st.markdown(
    """
    <style>
    body {
        background: linear-gradient(to right, #ff7eb3, #ff758c, #ff6a5c);
        color: #333333;
        font-family: 'Arial', sans-serif;
    }
    .stButton button {
        background-color: #ff477e;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
        transition: background-color 0.3s, transform 0.3s;
    }
    .stButton button:hover {
        background-color: #ff96ad;
        color: #333333;
        transform: translateY(-3px);
    }
    .sidebar .sidebar-content {
        background-color: #fff3f8;
        border-radius: 15px;
        padding: 25px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    .stHeader {
        color: #ff477e;
        font-size: 28px;
        font-weight: bold;
    }
    .stSubheader {
        color: #ff6a5c;
        font-size: 22px;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Function to send email
def send_email(to_email, subject, body):
    # Create the email message
    em = EmailMessage()
    em['From'] = SENDER_EMAIL
    em['To'] = to_email
    em['Subject'] = subject
    em.set_content(body)
    
    # Create an SSL context
    context = ssl.create_default_context()

    # Send the email using Gmail SMTP
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as smtp:
            smtp.login(SENDER_EMAIL, SENDER_PASSWORD)
            smtp.sendmail(SENDER_EMAIL, to_email, em.as_string())
        print("Email sent successfully")
    except Exception as e:
        print("Error sending email:", e)

# Function to send email reminders
def send_email_reminder(to_email, medication_name, dosage, reminder_time):
    subject = "KnightRX Medication Reminder"
    body = f"""
    Hi there,

    This is a reminder to take your medication:

    - Medication: {medication_name}
    - Dosage: {dosage}
    - Time: {reminder_time.strftime('%I:%M %p')}

    Please make sure to take your medication as prescribed.

    Stay healthy,
    KnightRX
    """
    send_email(to_email, subject, body)

# Function to send low stock email alert
def send_low_stock_alert(to_email, medication_name, remaining_quantity):
    subject = "KnightRX Low Medication Stock Alert"
    body = f"""
    Hi there,

    This is an alert that your medication '{medication_name}' is running low.

    - Remaining Quantity: {remaining_quantity}

    Please make sure to refill your medication to avoid missing any doses.

    Stay healthy,
    KnightRX
    """
    send_email(to_email, subject, body)

# Function to schedule email reminders
def schedule_reminders():
    meds = db.query(Medication).all()
    reminder_setting = db.query(ReminderSetting).first()
    
    if reminder_setting:
        to_email = reminder_setting.contact_info
        for med in meds:
            reminder_time = datetime.combine(datetime.now().date(), med.reminder_time)
            if med.frequency == "Daily":
                scheduler.add_job(send_email_reminder, 'interval', days=1, start_date=reminder_time, 
                                  args=[to_email, med.med_name, med.dosage, med.reminder_time])
            elif med.frequency == "Weekly":
                scheduler.add_job(send_email_reminder, 'interval', weeks=1, start_date=reminder_time, 
                                  args=[to_email, med.med_name, med.dosage, med.reminder_time])

# Start the scheduler
scheduler.start()

# Initialize session state for navigation if not already set
if "page" not in st.session_state:
    st.session_state.page = "Medication Input"

# Sidebar Buttons for Navigation
st.sidebar.title("🔍 Navigation")
if st.sidebar.button("💊 Medication Input"):
    st.session_state.page = "Medication Input"
if st.sidebar.button("📋 Medication Log"):
    st.session_state.page = "Medication Log"
if st.sidebar.button("🔔 Refill Alerts"):
    st.session_state.page = "Refill Alerts"
if st.sidebar.button("📝 Health Check-In"):
    st.session_state.page = "Health Check-In"
if st.sidebar.button("⚙️ Settings"):
    st.session_state.page = "Settings"
if st.sidebar.button("📊 Dashboard"):
    st.session_state.page = "Dashboard"

# Use the session state to determine the current page
choice = st.session_state.page

# Medication Input Page
if choice == "Medication Input":
    st.header("💊 Add New Medication")
    med_name = st.text_input("Medication Name")
    dosage = st.text_input("Dosage")
    total_quantity = st.number_input("Total Quantity", min_value=1)  # New field for refill alerts
    frequency = st.selectbox("Frequency", ["Daily", "Weekly"])
    reminder_time = st.time_input("Reminder Time")

    if st.button("Save Medication"):
        new_med = Medication(
            med_name=med_name,
            dosage=dosage,
            total_quantity=total_quantity,  # Store total quantity
            frequency=frequency,
            reminder_time=reminder_time
        )
        db.add(new_med)
        db.commit()
        st.success(f"✅ Medication '{med_name}' added successfully!")
        schedule_reminders()

# Medication Log Page
elif choice == "Medication Log":
    st.header("📋 Log Medication Intake")
    meds = db.query(Medication).all()
    selected_med = st.selectbox("Select Medication", meds, format_func=lambda med: med.med_name)
    status = st.selectbox("Status", ["Taken on Time", "Taken Late", "Missed"])
    log_time = st.time_input("Time Taken", datetime.now().time())
    
    if st.button("Log Medication"):
        # Update total quantity for refill alerts
        selected_med.total_quantity -= 1
        if selected_med.total_quantity < 5:  # Alert when quantity is low
            st.warning(f"⚠️ Low stock alert: Only {selected_med.total_quantity} doses left for {selected_med.med_name}!")
            reminder_setting = db.query(ReminderSetting).first()
            if reminder_setting:
                send_low_stock_alert(reminder_setting.contact_info, selected_med.med_name, selected_med.total_quantity)

        new_log = MedicationLog(
            medication_id=selected_med.medication_id,
            date=datetime.now().date(),
            time=log_time,
            status=status
        )
        db.add(new_log)
        db.commit()
        st.success(f"📝 Medication log for '{selected_med.med_name}' added successfully!")

# Refill Alerts Page
elif choice == "Refill Alerts":
    st.header("🔔 Medication Refill Alerts")
    meds = db.query(Medication).filter(Medication.total_quantity < 5).all()
    if meds:
        for med in meds:
            st.warning(f"⚠️ {med.med_name} is running low with only {med.total_quantity} doses left!")
    else:
        st.info("🎉 All medications have sufficient stock!")

# Health Check-In Page
elif choice == "Health Check-In":
    st.header("📝 Daily Health Check-In")
    today = date.today()
    symptoms = st.text_area("How are you feeling today? Any symptoms or side effects?")
    
    if st.button("Save Check-In"):
        new_check_in = HealthCheckIn(
            date=today,
            symptoms=symptoms
        )
        db.add(new_check_in)
        db.commit()
        st.success("✅ Health check-in saved successfully!")

# Settings Page
elif choice == "Settings":
    st.header("⚙️ Reminder Settings")
    email = st.text_input("Enter your Email for Notifications")

    if st.button("Save Preferences"):
        existing_setting = db.query(ReminderSetting).first()
        if existing_setting:
            existing_setting.contact_info = email
        else:
            new_setting = ReminderSetting(contact_info=email)
            db.add(new_setting)
        db.commit()
        st.success("✅ Email settings saved successfully!")
        send_email_reminder(email, "Test Medication", "1 pill", datetime.now())
        st.info("📧 Test email sent successfully! Please check your inbox.")

# Dashboard Page
elif choice == "Dashboard":
    st.header("📊 Medication Schedule and Adherence")
    
    # Adherence Streak Calculation
    logs = db.query(MedicationLog).filter(MedicationLog.status == "Taken on Time").all()
    streak = len(logs)  # Simplified streak calculation
    if streak >= 7:
        st.balloons()
        st.success(f"🎉 Congratulations! You've maintained a {streak}-day adherence streak!")

    # Weekly Summary and Visualizations
    st.subheader("📅 Weekly Adherence Summary")
    log_data = [{
        "Date": log.date,
        "Time": log.time,
        "Status": log.status
    } for log in db.query(MedicationLog).all()]
    df = pd.DataFrame(log_data)
    if not df.empty:
        # Line Graph
        line_fig = px.line(df, x="Date", y="Status", title="Medication Adherence Over Time")
        st.plotly_chart(line_fig)

        # Pie Chart
        pie_fig = px.pie(df, names="Status", title="Adherence Status Distribution")
        st.plotly_chart(pie_fig)

        # Calendar View
        calendar_fig = px.density_heatmap(df, x="Date", y="Status", title="Medication Adherence Calendar")
        st.plotly_chart(calendar_fig)

    st.subheader("📋 Medication Logs")
    st.write(df)
