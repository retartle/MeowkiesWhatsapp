import os
import logging
import json
import requests
from datetime import datetime, timedelta
import pytz
from dotenv import load_dotenv
import message_templates

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# WhatsApp API configuration
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN")
WHATSAPP_API_URL = f"https://graph.facebook.com/v22.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
CLINIC_TIMEZONE = pytz.timezone("Asia/Singapore")  # Set timezone for the clinic

# File to store scheduled reminders
REMINDERS_FILE = "appointment_reminders.json"

def load_reminders():
    """Load the scheduled reminders from file"""
    try:
        if os.path.exists(REMINDERS_FILE):
            with open(REMINDERS_FILE, 'r') as file:
                return json.load(file)
        else:
            reminders = {"reminders": []}
            with open(REMINDERS_FILE, 'w') as file:
                json.dump(reminders, file, indent=4)
            return reminders
    except Exception as e:
        logger.error(f"Error loading reminders: {str(e)}")
        return {"reminders": []}

def save_reminders(reminders):
    """Save reminders to file"""
    try:
        with open(REMINDERS_FILE, 'w') as file:
            json.dump(reminders, file, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error saving reminders: {str(e)}")
        return False

def schedule_appointment_reminder(appointment_id, customer_name, customer_number, 
                                 treatment_type, appointment_time):
    """Schedule a reminder to be sent 1 hour before the appointment"""
    # Calculate time to send (1 hour before appointment)
    send_time = appointment_time - timedelta(hours=1)
    
    # Only schedule if the send time is in the future
    current_time = datetime.now(CLINIC_TIMEZONE)
    if send_time <= current_time:
        logger.warning(f"Not scheduling reminder for past time: {send_time}")
        return None
    
    # Create reminder object
    reminder = {
        "appointment_id": appointment_id,
        "customer_name": customer_name,
        "customer_number": customer_number,
        "treatment_type": treatment_type,
        "appointment_time": appointment_time.isoformat(),
        "send_time": send_time.isoformat(),
        "sent": False,
        "created_at": datetime.now(CLINIC_TIMEZONE).isoformat()
    }
    
    # Add to reminders file
    reminders = load_reminders()
    reminders["reminders"].append(reminder)
    save_reminders(reminders)
    
    logger.info(f"Scheduled appointment reminder for {customer_name} at {send_time}")
    return reminder

def send_appointment_reminder(reminder):
    """Send a reminder message via WhatsApp"""
    try:
        # Parse appointment time
        appointment_time = datetime.fromisoformat(reminder["appointment_time"])
        formatted_time = appointment_time.strftime("%I:%M %p").lstrip("0")
        formatted_date = appointment_time.strftime("%d/%m/%Y")
        
        # Prepare the message
        message = f"*Reminder:* Hi {reminder['customer_name']}! Just a friendly reminder that your {reminder['treatment_type']} appointment is scheduled for tomorrow at {formatted_time} on {formatted_date}. Please arrive 10 minutes early. We're looking fur-ward to seeing you! 🐱\n\nMeow Aesthetic Clinic\nWoods Square Tower 1, #05-62 S737715"
        
        # Send via WhatsApp API
        headers = {
            "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
            "Content-Type": "application/json",
        }
        
        message_data = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": reminder["customer_number"],
            "type": "text",
            "text": {
                "body": message
            }
        }
        
        # Send the request
        response = requests.post(
            WHATSAPP_API_URL,
            headers=headers,
            json=message_data,
            timeout=30
        )
        
        if response.status_code != 200:
            logger.error(f"WhatsApp API error: Status {response.status_code}, Response: {response.text}")
            return False
            
        logger.info(f"Successfully sent appointment reminder to {reminder['customer_number']}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending reminder: {str(e)}")
        return False

def check_and_send_reminders():
    """Check for reminders that need to be sent and send them"""
    reminders = load_reminders()
    current_time = datetime.now(CLINIC_TIMEZONE)
    
    for reminder in reminders["reminders"]:
        if reminder["sent"]:
            continue
            
        send_time = datetime.fromisoformat(reminder["send_time"])
        # Send if it's time (within the last minute)
        if send_time <= current_time:
            logger.info(f"Sending reminder for appointment {reminder['appointment_id']}")
            success = send_appointment_reminder(reminder)
            
            if success:
                # Mark as sent
                reminder["sent"] = True
                reminder["sent_at"] = current_time.isoformat()
    
    # Save updated reminders
    save_reminders(reminders)

def cleanup_old_reminders():
    """Remove reminders for appointments that have passed (older than 7 days)"""
    reminders = load_reminders()
    current_time = datetime.now(CLINIC_TIMEZONE)
    cutoff_time = current_time - timedelta(days=7)
    
    new_reminders = []
    for reminder in reminders["reminders"]:
        appointment_time = datetime.fromisoformat(reminder["appointment_time"])
        if appointment_time > cutoff_time:
            new_reminders.append(reminder)
    
    if len(new_reminders) < len(reminders["reminders"]):
        reminders["reminders"] = new_reminders
        save_reminders(reminders)
        logger.info(f"Cleaned up {len(reminders['reminders']) - len(new_reminders)} old reminders")
