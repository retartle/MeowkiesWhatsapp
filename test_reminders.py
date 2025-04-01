from appointment_reminders import schedule_appointment_reminder
from datetime import datetime, timedelta
import pytz

# Create an appointment that's 70 minutes from now
CLINIC_TIMEZONE = pytz.timezone("Asia/Singapore")
now = datetime.now(CLINIC_TIMEZONE)
test_time = now + timedelta(minutes=70)

schedule_appointment_reminder(
    appointment_id="test_123",
    customer_name="Test Customer",
    customer_number="your_actual_phone_number",  # Use your number for testing
    treatment_type="medical_facial",
    appointment_time=test_time
)

# Force check reminders (optional)
from appointment_reminders import check_and_send_reminders
print("Scheduled reminder, now checking if it's in the system...")
check_and_send_reminders()
