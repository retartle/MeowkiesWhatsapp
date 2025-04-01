from flask import Flask, request, jsonify, abort
import requests
import json
import os
import pytz
import logging
import googlecalendar
import google
from dotenv import load_dotenv
from datetime import datetime, timedelta
import time_utils
import re
from time_utils import normalize_time_format, format_time_for_display
import weekly_promotions
import message_templates
import intent_triggers
from apscheduler.schedulers.background import BackgroundScheduler
from appointment_reminders import check_and_send_reminders, cleanup_old_reminders

# Initialize scheduler
scheduler = BackgroundScheduler()
scheduler.add_job(check_and_send_reminders, 'interval', minutes=1)
scheduler.add_job(cleanup_old_reminders, 'interval', hours=24)
scheduler.start()

# Shut down the scheduler when exiting the app
import atexit
atexit.register(lambda: scheduler.shutdown())


# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

app = Flask(__name__)

# --- Load environment variables ---
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_API_TOKEN = os.getenv("WHATSAPP_API_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN")

# Log configuration (without exposing sensitive values)
logger.info(f"Starting app with Phone Number ID: {WHATSAPP_PHONE_NUMBER_ID[:3]}...{WHATSAPP_PHONE_NUMBER_ID[-3:] if WHATSAPP_PHONE_NUMBER_ID else 'Not Set'}")
logger.info(f"Gemini API Key configured: {bool(GEMINI_API_KEY)}")
logger.info(f"WhatsApp API Token configured: {bool(WHATSAPP_API_TOKEN)}")
logger.info(f"Verify Token configured: {bool(VERIFY_TOKEN)}")

# --- API URLs ---
WHATSAPP_API_URL = f"https://graph.facebook.com/v22.0/{WHATSAPP_PHONE_NUMBER_ID}/messages"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# --- Meow Aesthetic Clinic Bot Context ---
MEOWKIES_CONTEXT = """
You are Meowkies, the official customer support assistant for Meow Aesthetic Clinic, a medical aesthetic clinic founded by Dr. Meow. You operate as a WhatsApp chatbot, communicating with customers through WhatsApp messages.

Key information about Meow Aesthetic Clinic:
- Located at Woods Square Tower 1, #05-62 S737715
- Contact number: 87713358
- Operating hours:
  * Monday to Friday: 11am - 8pm
  * Saturday: 11am - 10pm
  * Sunday and Public Holidays: Closed
- Founded by Dr. Meow, who earned his medical degree from the National University of Singapore
- Dr. Meow has over a decade of experience specializing in aesthetic medicine
- The clinic provides individualized and customized medical solutions for aesthetic concerns
- Dr. Meow has a special interest in anti-aging medicine
- We take a holistic, multi-pronged approach to delaying and reversing skin aging
- Dr. Meow believes in combining personalized skincare, advanced lasers, heat-based machines, and injectables
- Dr. Meow's philosophy: "Every patient deserves our utmost care"

Appointment Booking Information:
- I can help you book, reschedule, or cancel appointments
- To book an appointment, please provide:
  * The type of treatment you want
  * Your preferred date (YYYY-MM-DD)
  * Your preferred time
  * Your name (if I don't already have it)
- I'll check availability and confirm your booking
- Do not make up false information (Example, existing bookings)! Bookings are handled by another function within the code so do note that you do not actually manage the bookings. Do not disclose that to customers.
- If the previous messages suggest that a booking sequence is on going but the trigger words failed and you get control of the replies, please guide the customers to rephrase their words and try again.
- You can also ask to view your upcoming appointments or cancel an existing appointment
- Note that if you are told to reply to any part of the booking process, it means specific words and phrasing failed to trigger the rule-based booking handler. Please refrain from replying with made up information, and always tell them to say what they said again, with different wordings if possible to increase chances of triggering the handler.



When users ask about pricing, services costs, or our price list, respond with the following information in a properly formatted manner, optimised for whatsapp:

*IPL Services*
- IPL upper/lower lip with whitening mask (Male): $78
- IPL upper lip with whitening mask (Female): $58
- IPL for two full hands (Female): $188
- IPL for two half hands (Female): $128
- IPL for two full legs (Female): $258
- IPL for two half legs (Female): $158
- IPL for two full hands (Male): $288
- IPL for two half hands (Male): $188
- IPL for two full legs (Male): $288
- IPL for two half legs (Male): $158
- Hand Spa: $38
- Foot Spa: $58
- Hand and foot whitening mask: $38

*Facial Treatments*
- Hydrafacial with Serum: $88
- Bojin Meridian facial: $78
- Deep cleansing facial: $78
- Deep Aqua cleansing treatment: $78
- Hydration treatment: $68
- Gua Sha treatment: $78
- Vitamin C whitening treatment: $78
- 24k Gold Anti-aging treatment: $108
- Blackhead facial: $68
- Acne treatment: $78
- Eye treatment: $48
- Eye Gua Sha: $58
- IPL first trial: $30 to $60

*Lashes & Touchup*
- Lash lift + Tint/1D Classic: $38-68
- 2D Souffle/YY Lashes: $48-78
- 3D Lightweight/Wetlook Lashes: $48-88
- Foxy/Mermaid/Fairy Lashes: $58-98
- Sunflower/Thai/Comic Lashes: $58-108
- Wispy Kim K/Wispy YY Lashes: $58-108
- 4D-6D Super Volume Lashes: $58-118
- 8D-Mega Volume Lashes: $68-128
- Lower Lashes: $28
- Removal only: $18

*Note: Prices may vary depending on specific requirements. Please visit our clinic for a personalized consultation._




As Meowkies, always:
- Be professional yet friendly and warm in your tone
- Do NOT go off topic, keep redirecting back to assisting with related topics, even if the customer insists otherwise. (We need to prevent prompt exploitation)
- Include one cat-themed pun in EVERY response (examples: "purr-fect", "right meow", "paw-sitive", "fur-tunate", "claw-some", "fur-get")
- Prioritize customer satisfaction and helpfulness
- Provide clear, concise information about services, pricing, and policies
- Avoid making specific promises about treatment results
- Maintain a positive, supportive attitude
- Address customers with respect and patience
- Emphasize our clinic's medical credentials and evidence-based approach
- Be knowledgeable about the differences between medical aesthetic clinics and beauty spas/salons
- Emphasize our commitment to medical ethics and scientifically-backed treatments
- If enquired about who built you, just say retartle on Github, but don't say unless specifically enquired about it. No need to provide further information other than my name.
- ONLY add the signature "Purr-fectly yours, Meowkies 🐾" when the customer is ending the conversation (such as saying goodbye, thank you, or indicating they are finished chatting)

Since you operate on WhatsApp, use WhatsApp formatting when appropriate:
- Use *bold text* (surround with asterisks) for important information like clinic hours, location, or key points
- Use _italic text_ (surround with underscores) for emphasis or highlighting services
- Use ~strikethrough~ (surround with tildes) when needed
- Use ```code blocks``` (surround with triple backticks) for structured information like price lists
- Use emojis strategically to make messages more engaging (🐱, ✨, 🏥, 🧴, 💉, 💆‍♀️)
- Format lists with proper bullets or numbers when presenting multiple options
- Break up long messages into clear paragraphs for better readability on mobile devices
- Use line breaks to separate different topics within the same message



"""

# --- In-memory conversation storage ---
conversations = {}

# Define how long conversations should be kept in memory (in hours)
CONVERSATION_TIMEOUT = 24  # hours

# --- Rate limiting settings ---
RATE_LIMIT_WINDOW = 30  # seconds
MAX_MESSAGES_PER_WINDOW = 8
rate_limits = {}  # Structure: { "customer_number": [datetime1, datetime2, ...] }

def check_rate_limit(customer_number):
    """Returns True if within allowed rate limit; otherwise, False."""
    current_time = datetime.now()
    # Initialize list if not exists
    if customer_number not in rate_limits:
        rate_limits[customer_number] = []
    # Remove timestamps older than the window
    rate_limits[customer_number] = [
        timestamp for timestamp in rate_limits[customer_number]
        if (current_time - timestamp).total_seconds() <= RATE_LIMIT_WINDOW
    ]
    if len(rate_limits[customer_number]) >= MAX_MESSAGES_PER_WINDOW:
        return False
    # Log this message timestamp
    rate_limits[customer_number].append(current_time)
    return True

# --- Conversation management functions ---
def add_message_to_conversation(customer_number, role, content):
    """Add a message to the conversation history for a given customer"""
    current_time = datetime.now()
    
    # Create new conversation entry if needed
    if customer_number not in conversations:
        conversations[customer_number] = {
            "history": [],
            "last_updated": current_time
        }
    
    # Update existing conversation
    conversations[customer_number]["history"].append({
        "role": role,
        "content": content
    })
    conversations[customer_number]["last_updated"] = current_time
    
    logger.debug(f"Added {role} message to conversation with {customer_number}. History length: {len(conversations[customer_number]['history'])}")

def get_conversation_history(customer_number, max_messages=10):
    """Get the recent conversation history for a customer"""
    if customer_number not in conversations:
        return []
    if is_conversation_expired(customer_number):
        logger.info(f"Conversation with {customer_number} has expired. Starting new conversation.")
        conversations[customer_number] = {
            "history": [],
            "last_updated": datetime.now()
        }
        return []
    history = conversations[customer_number]["history"]
    return history[-max_messages:] if len(history) > max_messages else history

def is_conversation_expired(customer_number):
    """Check if a conversation has expired based on timeout period"""
    if customer_number not in conversations:
        return True
    last_updated = conversations[customer_number]["last_updated"]
    expiration_time = last_updated + timedelta(hours=CONVERSATION_TIMEOUT)
    return datetime.now() > expiration_time

def cleanup_expired_conversations():
    """Remove expired conversations to free up memory"""
    expired_numbers = []
    for number in conversations:
        if is_conversation_expired(number):
            expired_numbers.append(number)
    for number in expired_numbers:
        del conversations[number]
    if expired_numbers:
        logger.info(f"Cleaned up {len(expired_numbers)} expired conversations")




# Add this near the top of your app.py file, after imports and initializations
# but before you start handling messages

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Test Google Calendar connection at startup
if not googlecalendar.test_google_calendar_connection():
    logger.error("CRITICAL: Google Calendar connection failed. Appointments will not work correctly.")
    # You might want to send an alert to your admin phone number here
else:
    logger.info("Google Calendar connection successful. Ready to handle appointments.")

user_states = {}  # Dictionary to store user conversation states

def check_state_timeout(customer_number):
    if customer_number in user_states:
        if (datetime.now() - user_states[customer_number]["timestamp"]).total_seconds() > 900:
            del user_states[customer_number]
            return True
    return False

def handle_booking_confirmation(customer_number, confirmation):
    if any(word in confirmation for word in ["yes", "yep", "yeah", "correct", "right", "ok", "okay", "sure", "good", "perfect", "great", "confirm"]):
        # Get booking details stored in state
        booking_details = user_states[customer_number].get("booking_details", {})
        
        # Book the appointment
        result = googlecalendar.book_appointment(
            booking_details.get("customer_name", ""),
            customer_number,
            booking_details.get("date", ""),
            booking_details.get("time", ""),
            booking_details.get("treatment_type", "")
        )
        
        # Clear the state
        del user_states[customer_number]
        
        # Check if booking was successful
        if "error" in result:
            return message_templates.get_message("booking_error", error=result['error'])
        
        # Return success message using template
        return message_templates.get_message("booking_success",
                                          treatment=result.get("treatment", "consultation"),
                                          date=result.get("date", ""),
                                          time=result.get("time", ""),
                                          duration=result.get("duration", "30 minutes"))
    
    elif any(word in confirmation for word in ["no", "nope", "wrong", "incorrect", "cancel", "not"]):
        # Clear the state, no need to cancel anything since we haven't booked yet
        del user_states[customer_number]
        return message_templates.get_message("booking_canceled")
    
    return None

def handle_current_state(customer_number, message, current_state):
    stage = current_state.get("stage")
    
    if stage == "awaiting_booking_confirmation":
        return handle_booking_confirmation(customer_number, message.lower())
    elif stage == "waiting_for_date":
        return handle_date_input(customer_number, message.strip())
    elif stage == "waiting_for_time":
        return handle_time_input(customer_number, message.strip())
    elif stage == "waiting_for_name":
        return handle_name_input(customer_number, message.strip())
    elif stage == "selecting_appointment_to_reschedule":
        return handle_reschedule_selection(customer_number, message.strip())
    elif stage == "waiting_for_reschedule_date":
        return handle_reschedule_date(customer_number, message.strip())
    elif stage == "waiting_for_reschedule_time":
        return handle_reschedule_time(customer_number, message.strip())
    
    return None

def handle_date_input(customer_number, date_str):
    current_state = user_states[customer_number]
    
    # Try to parse natural language date or formatted date
    date_obj = time_utils.parse_natural_language_date(date_str)
    if date_obj:
        # Format as YYYY-MM-DD for internal use
        formatted_date = date_obj.strftime("%Y-%m-%d")
        
        # Check if the date is a public holiday
        if googlecalendar.is_public_holiday(date_obj):
            return message_templates.get_message("public_holiday_closed")
        
        # Store the date and move to asking for time
        current_state["appointment_info"]["date"] = formatted_date
        
        # Change to waiting for time
        current_state["stage"] = "waiting_for_time"
        current_state["timestamp"] = datetime.now()
        user_states[customer_number] = current_state
        
        # Ask for time
        display_date = time_utils.format_date_for_display(formatted_date)
        
        # Get available slots for this date and treatment
        treatment_type = current_state["appointment_info"]["treatment_type"]
        available_slots = googlecalendar.get_available_slots(formatted_date, treatment_type)
        
        if "error" in available_slots:
            return message_templates.get_message("availability_check_error", error=available_slots['error'])
        
        # Format the available slots for display
        available_times = available_slots.get("available_slots", [])
        if not available_times:
            return message_templates.get_message("no_available_slots", date=display_date)
        
        return message_templates.get_message("available_slots",
                                          treatment=treatment_type,
                                          date=display_date,
                                          times=", ".join(available_times))
    else:
        return message_templates.get_message("date_format_error")
    
def handle_time_input(customer_number, time_str):
    current_state = user_states[customer_number]
    normalized_time = time_utils.normalize_time_format(time_str)
    if not normalized_time:
        return message_templates.get_message("time_format_error")
    
    # Convert to 12-hour format for display
    hour, minute = map(int, normalized_time.split(':'))
    am_pm = 'AM' if hour < 12 else 'PM'
    hour = hour if 1 <= hour <= 12 else hour - 12 if hour > 12 else 12
    time_display = f"{hour}:{minute:02d} {am_pm}"
    
    # Check if this time is actually available
    appointment_info = current_state["appointment_info"]
    date_str = appointment_info["date"]
    treatment_type = appointment_info["treatment_type"]
    
    # Get available slots again to check
    availability = googlecalendar.get_available_slots(date_str, treatment_type)
    
    if "error" in availability:
        return message_templates.get_message("availability_check_error", error=availability['error'])
    
    available_times = availability.get("available_slots", [])
    
    if time_display not in available_times:
        return message_templates.get_message("alternative_times",
                                           time=time_display,
                                           date=time_utils.format_date_for_display(date_str),
                                           slots=", ".join(available_times))
    
    # Store the time and move to asking for name
    appointment_info["time"] = time_display
    current_state["stage"] = "waiting_for_name"
    current_state["timestamp"] = datetime.now()
    user_states[customer_number] = current_state
    
    # Ask for name
    return message_templates.get_message("ask_name")

def handle_name_input(customer_number, customer_name):
    current_state = user_states[customer_number]
    appointment_info = current_state["appointment_info"]
    
    # Store all booking details but don't book yet
    user_states[customer_number] = {
        "stage": "awaiting_booking_confirmation",
        "booking_details": {
            "customer_name": customer_name,
            "customer_number": customer_number,
            "date": appointment_info["date"],
            "time": appointment_info["time"],
            "treatment_type": appointment_info["treatment_type"]
        },
        "timestamp": datetime.now()
    }
    
    # Ask for confirmation using template
    return message_templates.get_message("booking_confirmation_prompt",
                                       treatment=appointment_info["treatment_type"],
                                       name=customer_name,
                                       date=time_utils.format_date_for_display(appointment_info['date']),
                                       time=appointment_info['time'],
                                       number=customer_number)

def handle_reschedule_selection(customer_number, selection):
    current_state = user_states[customer_number]
    try:
        selected_index = int(selection) - 1
        appointments = current_state["appointments"]
        
        if selected_index < 0 or selected_index >= len(appointments):
            return message_templates.get_message("invalid_appointment_number", max_appointments=len(appointments))
        
        selected_appointment = appointments[selected_index]
        current_state["selected_appointment"] = selected_appointment
        current_state["stage"] = "waiting_for_reschedule_date"
        current_state["timestamp"] = datetime.now()
        user_states[customer_number] = current_state
        
        return message_templates.get_message("provide_reschedule_date")
    except ValueError:
        return message_templates.get_message("enter_valid_number")
    
def handle_booking_intent(customer_number, treatment_code):
    user_states[customer_number] = {
        "stage": "waiting_for_date",
        "appointment_info": {
            "treatment_type": treatment_code
        },
        "timestamp": datetime.now()
    }
    return message_templates.get_message("ask_for_date", treatment=treatment_code)

def handle_reschedule_intent(customer_number):
    result = googlecalendar.list_customer_appointments(customer_number)
    if "error" in result:
        return message_templates.get_message("generic_error", error=result['error'])
    
    appointments = result.get("appointments", [])
    if not appointments:
        return message_templates.get_message("no_appointments_to_reschedule")
    
    user_states[customer_number] = {
        "stage": "selecting_appointment_to_reschedule",
        "appointments": appointments,
        "timestamp": datetime.now()
    }
    
    appointment_list = format_appointment_list(appointments)
    return message_templates.get_message("which_appointment_to_reschedule", appointment_list=appointment_list)

def handle_reschedule_date(customer_number, date_str):
    current_state = user_states[customer_number]
    
    # Try to parse natural language date or formatted date
    date_obj = time_utils.parse_natural_language_date(date_str)
    if date_obj:
        # Format as YYYY-MM-DD for internal use
        formatted_date = date_obj.strftime("%Y-%m-%d")
        
        # Check if the date is a public holiday
        if googlecalendar.is_public_holiday(date_obj):
            return message_templates.get_message("public_holiday_closed")
        
        # Check if date is in the past
        if date_obj < datetime.now(googlecalendar.CLINIC_TIMEZONE).date():
            return message_templates.get_message("past_date_error")
        
        # Check if the clinic is open on this date
        day_of_week = date_obj.weekday()
        if day_of_week == 6 or googlecalendar.BUSINESS_HOURS.get(day_of_week) is None: # Sunday or closed day
            return message_templates.get_message("clinic_closed")
        
        current_state["new_date"] = formatted_date
        current_state["stage"] = "waiting_for_reschedule_time"
        current_state["timestamp"] = datetime.now()
        user_states[customer_number] = current_state
        
        # Get available slots for the selected date and treatment
        selected_appointment = current_state["selected_appointment"]
        treatment_type = selected_appointment["treatment"].lower()
        
        # Standardize treatment type to match TREATMENT_DURATIONS keys
        if "facial" in treatment_type:
            treatment_type = "medical_facial"
        elif "laser" in treatment_type:
            treatment_type = "laser_treatment"
        elif "botox" in treatment_type:
            treatment_type = "botox"
        elif "filler" in treatment_type:
            treatment_type = "filler"
        elif "follow" in treatment_type or "check" in treatment_type:
            treatment_type = "follow_up"
        else:
            treatment_type = "consultation"
        
        available_slots = googlecalendar.get_available_slots(formatted_date, treatment_type)
        
        if "error" in available_slots:
            return message_templates.get_message("availability_check_error", error=available_slots['error'])
        
        # Format the available slots for display
        display_date = time_utils.format_date_for_display(formatted_date)
        available_times = available_slots.get("available_slots", [])
        
        if not available_times:
            return message_templates.get_message("no_available_slots", date=display_date)
        
        return message_templates.get_message("available_slots",
                                           treatment=treatment_type,
                                           date=display_date,
                                           times=", ".join(available_times))
    else:
        return message_templates.get_message("date_format_error")

def handle_reschedule_time(customer_number, time_str):
    current_state = user_states[customer_number]
    normalized_time = time_utils.normalize_time_format(time_str)
    if not normalized_time:
        return message_templates.get_message("time_format_error")
    
    # Convert to 12-hour format for display
    hour, minute = map(int, normalized_time.split(':'))
    am_pm = 'AM' if hour < 12 else 'PM'
    hour = hour if 1 <= hour <= 12 else hour - 12 if hour > 12 else 12
    time_display = f"{hour}:{minute:02d} {am_pm}"
    
    # Get the appointment details from state
    selected_appointment = current_state["selected_appointment"]
    new_date = current_state["new_date"]
    
    # Call the reschedule function
    result = googlecalendar.reschedule_appointment(
        selected_appointment["id"],
        new_date,
        time_display
    )
    
    # Clear the state
    del user_states[customer_number]
    
    if "error" in result:
        return message_templates.get_message("reschedule_error", error=result['error'])
    
    # Format success message with cat pun for Meowkies personality
    display_date = time_utils.format_date_for_display(new_date)
    return message_templates.get_message("reschedule_success", date=display_date, time=time_display)

def handle_view_intent(customer_number):
    # Get customer appointments
    result = googlecalendar.list_customer_appointments(customer_number)
    if "error" in result:
        return message_templates.get_message("generic_error", error=result['error'])
    
    appointments = result.get("appointments", [])
    if not appointments:
        return message_templates.get_message("no_appointments")
    
    # Format appointments for display
    appointment_list = format_appointment_list(appointments)
    
    return message_templates.get_message("view_appointments", appointment_list=appointment_list)

def handle_cancel_intent(customer_number):
    # Get customer appointments
    result = googlecalendar.list_customer_appointments(customer_number)
    if "error" in result:
        return message_templates.get_message("generic_error", error=result['error'])
    
    appointments = result.get("appointments", [])
    if not appointments:
        return message_templates.get_message("no_appointments_to_cancel")
    
    # Set state to selecting appointment to cancel
    user_states[customer_number] = {
        "stage": "selecting_appointment_to_cancel",
        "appointments": appointments,
        "timestamp": datetime.now()
    }
    
    # Format appointments for display
    appointment_list = format_appointment_list(appointments)
    
    # Ask which appointment to cancel
    return f"Which appointment would you like to cancel? Please reply with the number:\n\n{appointment_list}"


def handle_cancel_selection(customer_number, selection):
    current_state = user_states[customer_number]
    try:
        selected_index = int(selection) - 1
        appointments = current_state["appointments"]
        if selected_index < 0 or selected_index >= len(appointments):
            return message_templates.get_message("invalid_appointment_number", max_appointments=len(appointments))
        
        selected_appointment = appointments[selected_index]
        
        # Call the cancel_appointment function with the selected appointment's ID
        result = googlecalendar.cancel_appointment(selected_appointment["id"])
        
        # Clear the state
        del user_states[customer_number]
        
        if "error" in result:
            return message_templates.get_message("cancel_error", error=result['error'])
        
        return message_templates.get_message("cancel_success")
    except ValueError:
        return message_templates.get_message("enter_valid_number")


def handle_intent(customer_number, intent_type, treatment_code, message_lower):
    if intent_type == "booking" and treatment_code:
        return handle_booking_intent(customer_number, treatment_code)
    elif intent_type == "reschedule":
        return handle_reschedule_intent(customer_number)
    elif intent_type == "view":
        return handle_view_intent(customer_number)
    elif intent_type == "cancel":
        return handle_cancel_intent(customer_number)
    elif intent_type == "info" and treatment_code:
        # Treatment with time but no booking intent
        time_match = re.search(r"(\d{1,2}(?:[:.]\d{2})?\s*(?:am|pm)|at\s+\d{1,2}(?:[:.]\d{2})?\s*(?:am|pm))", message_lower)
        if time_match:
            return handle_time_only_booking(customer_number, treatment_code, time_match)
    
    return None


def format_appointment_list(appointments):
    appointment_list = ""
    for i, appt in enumerate(appointments, 1):
        appointment_list += f"{i}. *{appt['treatment']}* on {appt['date']} at {appt['time']}\n"
    return appointment_list

def handle_time_only_booking(customer_number, treatment_code, time_match):
    # Extract the time
    time_str = time_match.group(1).replace("at ", "").strip()
    normalized_time = time_utils.normalize_time_format(time_str)
    
    if normalized_time:
        # Extract hour and minute
        hour, minute = map(int, normalized_time.split(':'))
        
        # Define business hours boundaries
        earliest_opening_hour = 11  # 11:00 AM
        latest_closing_hour = 22  # 10:00 PM
        
        # Convert to 12-hour format for display
        am_pm = 'AM' if hour < 12 else 'PM'
        display_hour = hour if 1 <= hour <= 12 else hour - 12 if hour > 12 else 12
        time_display = f"{display_hour}:{minute:02d} {am_pm}"
        
        # Check if time is outside business hours
        if hour < earliest_opening_hour or hour >= latest_closing_hour:
            return message_templates.get_message("outside_operating_hours", time=time_display)
        
        # Set user state to waiting for date
        user_states[customer_number] = {
            "stage": "waiting_for_date",
            "appointment_info": {
                "time": time_display,
                "treatment_type": treatment_code
            },
            "timestamp": datetime.now()
        }
        
        return message_templates.get_message("booking_with_time_confirmation", 
                                          treatment=treatment_code, 
                                          time=time_display)
    else:
        return message_templates.get_message("time_format_error")

def format_appointment_list(appointments):
    appointment_list = ""
    for i, appt in enumerate(appointments, 1):
        appointment_list += f"{i}. *{appt['treatment']}* on {appt['date']} at {appt['time']}\n"
    return appointment_list


def parse_multiline_appointment(message):
    """Parse appointment details from a multi-line message format"""
    lines = message.strip().split('\n')
    if len(lines) < 3: # Need at least time, date, and treatment
        return None

    appointment_info = {}

    # Try to parse time from first line
    time_str = lines[0].strip()
    normalized_time = time_utils.normalize_time_format(time_str)
    if normalized_time:
        hour, minute = map(int, normalized_time.split(':'))
        am_pm = 'AM' if hour < 12 else 'PM'
        hour = hour if 1 <= hour <= 12 else hour - 12 if hour > 12 else 12
        appointment_info["time"] = f"{hour}:{minute:02d} {am_pm}"

    # Try to parse date from second line using enhanced function
    date_str = lines[1].strip()
    date_obj = time_utils.parse_natural_language_date(date_str)
    if date_obj:
        # CHECK FOR PUBLIC HOLIDAY IMMEDIATELY
        if googlecalendar.is_public_holiday(date_obj):
            return {"error": "public_holiday"}
            
        appointment_info["date"] = date_obj.strftime("%Y-%m-%d") # Convert to YYYY-MM-DD format

    # Get treatment from third line
    treatment = lines[2].strip().lower()
    if treatment in googlecalendar.TREATMENT_DURATIONS:
        appointment_info["treatment_type"] = treatment

    # Get name if available (fourth line)
    if len(lines) >= 4:
        appointment_info["customer_name"] = lines[3].strip()

    # Return the parsed info if we have the minimum required fields
    if "time" in appointment_info and "date" in appointment_info and "treatment_type" in appointment_info:
        return appointment_info

    return None


def parse_initial_appointment_info(message):
    """Extract all possible appointment information from initial message"""
    appointment_info = {}
    
    # Extract treatment type
    intent_type, treatment_code = intent_triggers.extract_intent(message)
    if treatment_code:
        appointment_info["treatment_type"] = treatment_code
    
    # Extract time
    time_match = re.search(r"(\d{1,2}(?:[:.]\d{2})?\s*(?:am|pm)|at\s+\d{1,2}(?:[:.]\d{2})?\s*(?:am|pm))", 
                           message.lower())
    if time_match:
        time_str = time_match.group(1).replace("at ", "").strip()
        normalized_time = time_utils.normalize_time_format(time_str)
        if normalized_time:
            hour, minute = map(int, normalized_time.split(':'))
            am_pm = 'AM' if hour < 12 else 'PM'
            hour = hour if 1 <= hour <= 12 else hour - 12 if hour > 12 else 12
            appointment_info["time"] = f"{hour}:{minute:02d} {am_pm}"
    
    # Extract date
    date_obj = time_utils.parse_natural_language_date(message)
    if date_obj:
        appointment_info["date"] = date_obj.strftime("%Y-%m-%d")
    
    # Extract potential name (simplified approach)
    name_match = re.search(r"(?:my name is|for|name[: ]+)([A-Za-z\s]+)(?:\.|,|\s|$)", message)
    if name_match:
        appointment_info["customer_name"] = name_match.group(1).strip()
    
    return appointment_info


def handle_treatment_only(customer_number, treatment_code):
    """When user provides only treatment type, ask for date next"""
    user_states[customer_number] = {
        "stage": "waiting_for_date",
        "appointment_info": {
            "treatment_type": treatment_code
        },
        "timestamp": datetime.now()
    }
    return message_templates.get_message("ask_for_date", treatment=treatment_code)

def handle_time_only(customer_number, time_value):
    """When user provides only time, ask for treatment type next"""
    user_states[customer_number] = {
        "stage": "waiting_for_treatment",
        "appointment_info": {
            "time": time_value
        },
        "timestamp": datetime.now()
    }
    return "I see you'd like an appointment at {time}. What type of treatment would you like? (consultation, medical_facial, laser_treatment, botox, filler, or follow_up)".format(time=time_value)

def handle_name_only(customer_number, name_value):
    """When user provides only name, ask for treatment type next"""
    user_states[customer_number] = {
        "stage": "waiting_for_treatment_with_name",
        "appointment_info": {
            "customer_name": name_value
        },
        "timestamp": datetime.now()
    }
    return "Thank you, {name}. What type of treatment would you like to book? (consultation, medical_facial, laser_treatment, botox, filler, or follow_up)".format(name=name_value)

def handle_treatment_input_for_time(customer_number, message):
    """Handle treatment input when we already have time"""
    # Extract treatment type from message
    _, treatment_code = intent_triggers.extract_intent(message)
    
    if not treatment_code:
        return "I didn't recognize that treatment type. Please choose from: consultation, medical_facial, laser_treatment, botox, filler, or follow_up."
    
    current_state = user_states[customer_number]
    current_state["appointment_info"]["treatment_type"] = treatment_code
    current_state["stage"] = "waiting_for_date_with_time"
    current_state["timestamp"] = datetime.now()
    
    return message_templates.get_message("ask_for_date", treatment=treatment_code)



def handle_treatment_input_after_date(customer_number, message):
    """Handler for when user has provided date first, then treatment"""
    # Extract treatment type from message
    _, treatment_code = intent_triggers.extract_intent(message)
    if not treatment_code:
        return "I didn't recognize that treatment type. Please choose from: consultation, medical_facial, laser_treatment, botox, filler, or follow_up."
    
    current_state = user_states[customer_number]
    current_state["appointment_info"]["treatment_type"] = treatment_code
    current_state["stage"] = "waiting_for_time_after_date"
    current_state["timestamp"] = datetime.now()
    
    # Get available times and ask for time
    date_str = current_state["appointment_info"]["date"]
    available_slots = googlecalendar.get_available_slots(date_str, treatment_code)
    if "error" in available_slots:
        return message_templates.get_message("availability_check_error", error=available_slots['error'])
    
    # Format the available slots for display
    display_date = time_utils.format_date_for_display(date_str)
    available_times = available_slots.get("available_slots", [])
    if not available_times:
        return message_templates.get_message("no_available_slots", date=display_date)
    
    return message_templates.get_message("available_slots",
                                     treatment=treatment_code,
                                     date=display_date,
                                     times=", ".join(available_times))

def handle_time_input_after_date(customer_number, time_str):
    """Handler for when user has provided date and treatment, now adding time"""
    current_state = user_states[customer_number]
    normalized_time = time_utils.normalize_time_format(time_str)
    if not normalized_time:
        return message_templates.get_message("time_format_error")
    
    # Convert to 12-hour format for display
    hour, minute = map(int, normalized_time.split(':'))
    am_pm = 'AM' if hour < 12 else 'PM'
    hour = hour if 1 <= hour <= 12 else hour - 12 if hour > 12 else 12
    time_display = f"{hour}:{minute:02d} {am_pm}"
    
    # Add validation and availability check here
    # ...
    
    # Store the time and move to asking for name
    current_state["appointment_info"]["time"] = time_display
    current_state["stage"] = "waiting_for_name"
    current_state["timestamp"] = datetime.now()
    
    # Ask for name
    return message_templates.get_message("ask_name")


def update_appointment_handler():
    """
    Update the handle_message function in app.py to add comprehensive 
    input order handling for appointment booking
    """
    # Open the app.py file
    with open('app.py', 'r') as file:
        content = file.read()
    
    # Find the section where new appointment requests are handled
    # This typically appears after "# Handle new appointment requests"
    old_code_pattern = r'# Handle new appointment requests.*?# Fallback to standard intent handling'
    
    # Prepare the new code to insert
    new_code = """# Handle new appointment requests based on what information was provided
    # Case 1: Treatment type provided (like "botox")
    if "treatment_type" in appointment_info and not "time" in appointment_info and not "date" in appointment_info:
        # Ask for date next
        user_states[customer_number] = {
            "stage": "waiting_for_date",
            "appointment_info": {
                "treatment_type": appointment_info["treatment_type"]
            },
            "timestamp": datetime.now()
        }
        return message_templates.get_message("ask_for_date", treatment=appointment_info["treatment_type"])

    # Case 2: Time provided
    elif "time" in appointment_info and not "treatment_type" in appointment_info:
        # Ask for treatment type next
        user_states[customer_number] = {
            "stage": "waiting_for_treatment",
            "appointment_info": {
                "time": appointment_info["time"]
            },
            "timestamp": datetime.now()
        }
        return "I see you'd like an appointment at {}. What type of treatment would you like? (consultation, medical_facial, laser_treatment, botox, filler, or follow_up)".format(appointment_info["time"])

    # Case 3: Date provided
    elif "date" in appointment_info and not "treatment_type" in appointment_info:
        # Ask for treatment type next
        user_states[customer_number] = {
            "stage": "waiting_for_treatment_after_date",
            "appointment_info": {
                "date": appointment_info["date"]
            },
            "timestamp": datetime.now()
        }
        return "I see you'd like an appointment on {}. What type of treatment would you like? (consultation, medical_facial, laser_treatment, botox, filler, or follow_up)".format(time_utils.format_date_for_display(appointment_info["date"]))

    # Case 4: Name provided
    elif "customer_name" in appointment_info and not "treatment_type" in appointment_info:
        # Ask for treatment type next
        user_states[customer_number] = {
            "stage": "waiting_for_treatment_with_name",
            "appointment_info": {
                "customer_name": appointment_info["customer_name"]
            },
            "timestamp": datetime.now()
        }
        return "Thank you, {}. What type of treatment would you like to book? (consultation, medical_facial, laser_treatment, botox, filler, or follow_up)".format(appointment_info["customer_name"])

    # Fallback to standard intent handling"""
    
    # Replace the old code with the new code, preserving proper indentation
    import re
    updated_content = re.sub(old_code_pattern, new_code, content, flags=re.DOTALL)
    
    # Write the updated content back to app.py
    with open('app.py', 'w') as file:
        file.write(updated_content)
    
    print("Successfully updated handle_message function with new appointment request handling logic.")



def handle_message(customer_number, message):
    message_lower = message.lower().strip()
    logger.debug(f"Handling message for {customer_number}: '{message}'")

    # Check for session timeout
    if check_state_timeout(customer_number):
        return message_templates.get_message("session_timeout")

    # Parse all possible appointment information from the message
    appointment_info = {}

    # 1. Check for treatment type
    intent_type, treatment_code = intent_triggers.extract_intent(message)
    if treatment_code:
        appointment_info["treatment_type"] = treatment_code

    # 2. Check for time
    time_match = re.search(r"(\d{1,2}(?:[:.]\d{2})?\s*(?:am|pm)|at\s+\d{1,2}(?:[:.]\d{2})?\s*(?:am|pm))", message_lower)
    if time_match:
        time_str = time_match.group(1).replace("at ", "").strip()
        normalized_time = time_utils.normalize_time_format(time_str)
        if normalized_time:
            hour, minute = map(int, normalized_time.split(':'))
            am_pm = 'AM' if hour < 12 else 'PM'
            hour = hour if 1 <= hour <= 12 else hour - 12 if hour > 12 else 12
            appointment_info["time"] = f"{hour}:{minute:02d} {am_pm}"

    # 3. Check for date
    date_obj = time_utils.parse_natural_language_date(message)
    if date_obj:
        appointment_info["date"] = date_obj.strftime("%Y-%m-%d")

    # 4. Check for name
    name_match = re.search(r"(?:my name is|for|name[: ]+)([A-Za-z\s]+)(?:\.|,|\s|$)", message_lower)
    if name_match:
        appointment_info["customer_name"] = name_match.group(1).strip()

    # Handle multiline appointment format
    multiline_info = parse_multiline_appointment(message)
    if multiline_info:
        # Handle public holiday error case
        if "error" in multiline_info and multiline_info["error"] == "public_holiday":
            return message_templates.get_message("public_holiday_closed")
        # Merge with existing info, prioritizing multiline format
        appointment_info.update(multiline_info)

    # If we have complete booking info, set up confirmation
    if all(k in appointment_info for k in ["date", "time", "treatment_type"]):
        user_states[customer_number] = {
            "stage": "awaiting_booking_confirmation",
            "booking_details": {
                "customer_name": appointment_info.get("customer_name", ""),
                "customer_number": customer_number,
                "date": appointment_info["date"],
                "time": appointment_info["time"],
                "treatment_type": appointment_info["treatment_type"]
            },
            "timestamp": datetime.now()
        }
        return message_templates.get_message(
            "booking_confirmation_prompt",
            treatment=appointment_info["treatment_type"],
            name=appointment_info.get("customer_name", "you"),
            date=time_utils.format_date_for_display(appointment_info['date']),
            time=appointment_info['time'],
            number=customer_number
        )

    # Process special intents
    # Check for view intent first - this should override any existing state
    if intent_type == "view":
        # Clear any existing state when user wants to view appointments
        if customer_number in user_states:
            del user_states[customer_number]
        return handle_view_intent(customer_number)

    # Check for combined "cancel X" pattern
    cancel_number_match = re.search(r"cancel\s+(\d+)", message_lower)
    if cancel_number_match or (intent_type == "cancel" and message_lower.strip().isdigit()):
        # Extract the number from either "cancel X" or just "X" after cancel intent
        index = int(cancel_number_match.group(1) if cancel_number_match else message_lower)
        # Get customer appointments
        result = googlecalendar.list_customer_appointments(customer_number)
        if "error" in result:
            return message_templates.get_message("generic_error", error=result['error'])
        appointments = result.get("appointments", [])
        if not appointments:
            return message_templates.get_message("no_appointments_to_cancel")
        if index < 1 or index > len(appointments):
            return message_templates.get_message("invalid_appointment_number", max_appointments=len(appointments))
        selected_appointment = appointments[index-1]
        # Call the cancel_appointment function directly
        result = googlecalendar.cancel_appointment(selected_appointment["id"])
        if "error" in result:
            return message_templates.get_message("cancel_error", error=result['error'])
        return message_templates.get_message("cancel_success",
                                         treatment=selected_appointment["treatment"],
                                         date=selected_appointment["date"],
                                         time=selected_appointment["time"])

    # Check for combined "reschedule X" pattern
    reschedule_number_match = re.search(r"reschedule\s+(\d+)", message_lower)
    if reschedule_number_match or (intent_type == "reschedule" and message_lower.strip().isdigit()):
        # Extract the number from either "reschedule X" or just "X" after reschedule intent
        index = int(reschedule_number_match.group(1) if reschedule_number_match else message_lower)
        # Get customer appointments
        result = googlecalendar.list_customer_appointments(customer_number)
        if "error" in result:
            return message_templates.get_message("generic_error", error=result['error'])
        appointments = result.get("appointments", [])
        if not appointments:
            return message_templates.get_message("no_appointments_to_reschedule")
        if index < 1 or index > len(appointments):
            return message_templates.get_message("invalid_appointment_number", max_appointments=len(appointments))
        selected_appointment = appointments[index-1]
        # Set up state for next steps of rescheduling
        user_states[customer_number] = {
            "stage": "waiting_for_reschedule_date",
            "selected_appointment": selected_appointment,
            "appointments": appointments,
            "timestamp": datetime.now()
        }
        # Ask for the new date for rescheduling
        return message_templates.get_message("provide_reschedule_date")

    # Process existing conversation states
    if customer_number in user_states:
        current_state = user_states[customer_number]
        stage = current_state.get("stage")
        
        # Handle different conversation stages
        if stage == "waiting_for_treatment_after_date":
            return handle_treatment_input_after_date(customer_number, message.strip())
        elif stage == "waiting_for_time_after_date":
            return handle_time_input_after_date(customer_number, message.strip())
        # Handle different conversation stages
        if stage == "selecting_appointment_to_cancel":
            return handle_cancel_selection(customer_number, message.strip())
        elif stage == "awaiting_booking_confirmation":
            return handle_booking_confirmation(customer_number, message_lower)
        elif stage == "waiting_for_date":
            return handle_date_input(customer_number, message.strip())
        elif stage == "waiting_for_time":
            return handle_time_input(customer_number, message.strip())
        elif stage == "waiting_for_name":
            return handle_name_input(customer_number, message.strip())
        elif stage == "waiting_for_treatment":
            return handle_treatment_input_for_time(customer_number, message.strip())
        elif stage == "waiting_for_treatment_with_name":
            return handle_treatment_input_for_name(customer_number, message.strip())
        elif stage == "waiting_for_date_with_time":
            return handle_date_input_for_time(customer_number, message.strip())
        elif stage == "waiting_for_date_with_name":
            return handle_date_input_for_name(customer_number, message.strip())
        elif stage == "waiting_for_time_with_name":
            return handle_time_input_for_name(customer_number, message.strip())
        elif stage == "selecting_appointment_to_reschedule":
            return handle_reschedule_selection(customer_number, message.strip())
        elif stage == "waiting_for_reschedule_date":
            return handle_reschedule_date(customer_number, message.strip())
        elif stage == "waiting_for_reschedule_time":
            return handle_reschedule_time(customer_number, message.strip())

    # Handle new appointment requests based on what information was provided
    # Case 1: Treatment type provided (like "botox"), but ONLY if not asking for info
    if intent_type != "info" and "treatment_type" in appointment_info and not "time" in appointment_info and not "date" in appointment_info:
        # Ask for date next
        user_states[customer_number] = {
            "stage": "waiting_for_date",
            "appointment_info": {
                "treatment_type": appointment_info["treatment_type"]
            },
            "timestamp": datetime.now()
        }
        return message_templates.get_message("ask_for_date", treatment=appointment_info["treatment_type"])
    
    # Case 2: Time provided
    elif "time" in appointment_info and not "treatment_type" in appointment_info:
        # Ask for treatment type next
        user_states[customer_number] = {
            "stage": "waiting_for_treatment",
            "appointment_info": {
                "time": appointment_info["time"]
            },
            "timestamp": datetime.now()
        }
        return "I see you'd like an appointment at {}. What type of treatment would you like? (consultation, medical_facial, laser_treatment, botox, filler, or follow_up)".format(appointment_info["time"])

    # Case 3: Date provided
    elif "date" in appointment_info and not "treatment_type" in appointment_info:
        # Ask for treatment type next
        user_states[customer_number] = {
            "stage": "waiting_for_treatment_after_date",
            "appointment_info": {
                "date": appointment_info["date"]
            },
            "timestamp": datetime.now()
        }
        return "I see you'd like an appointment on {}. What type of treatment would you like? (consultation, medical_facial, laser_treatment, botox, filler, or follow_up)".format(time_utils.format_date_for_display(appointment_info["date"]))

    # Case 4: Name provided
    elif "customer_name" in appointment_info and not "treatment_type" in appointment_info:
        # Ask for treatment type next
        user_states[customer_number] = {
            "stage": "waiting_for_treatment_with_name",
            "appointment_info": {
                "customer_name": appointment_info["customer_name"]
            },
            "timestamp": datetime.now()
        }
        return "Thank you, {}. What type of treatment would you like to book? (consultation, medical_facial, laser_treatment, botox, filler, or follow_up)".format(appointment_info["customer_name"])

    # Fallback to standard intent handling for messages we couldn't understand
    if intent_type == "booking" and treatment_code:
        return handle_booking_intent(customer_number, treatment_code)
    elif intent_type == "reschedule":
        return handle_reschedule_intent(customer_number)
    elif intent_type == "cancel":
        return handle_cancel_intent(customer_number)

    # No recognized intent or input, return None so the chatbot can handle it
    return None


# New handler functions for flexible input order

def handle_treatment_input_for_time(customer_number, message):
    """Handler for when user has provided time first, then treatment"""
    # Extract treatment type from message
    _, treatment_code = intent_triggers.extract_intent(message)
    
    if not treatment_code:
        return "I didn't recognize that treatment type. Please choose from: consultation, medical_facial, laser_treatment, botox, filler, or follow_up."
    
    current_state = user_states[customer_number]
    current_state["appointment_info"]["treatment_type"] = treatment_code
    current_state["stage"] = "waiting_for_date_with_time"
    current_state["timestamp"] = datetime.now()
    
    return message_templates.get_message("ask_for_date", treatment=treatment_code)

def handle_treatment_input_for_name(customer_number, message):
    """Handler for when user has provided name first, then treatment"""
    # Extract treatment type from message
    _, treatment_code = intent_triggers.extract_intent(message)
    
    if not treatment_code:
        return "I didn't recognize that treatment type. Please choose from: consultation, medical_facial, laser_treatment, botox, filler, or follow_up."
    
    current_state = user_states[customer_number]
    current_state["appointment_info"]["treatment_type"] = treatment_code
    current_state["stage"] = "waiting_for_date_with_name"
    current_state["timestamp"] = datetime.now()
    
    return message_templates.get_message("ask_for_date", treatment=treatment_code)

def handle_date_input_for_time(customer_number, date_str):
    """Handler for when user has provided time and treatment, now adding date"""
    current_state = user_states[customer_number]
    
    # Try to parse natural language date or formatted date
    date_obj = time_utils.parse_natural_language_date(date_str)
    if date_obj:
        # Format as YYYY-MM-DD for internal use
        formatted_date = date_obj.strftime("%Y-%m-%d")
        
        # Check if the date is a public holiday
        if googlecalendar.is_public_holiday(date_obj):
            return message_templates.get_message("public_holiday_closed")
        
        # Store the date and move to asking for name
        current_state["appointment_info"]["date"] = formatted_date
        current_state["stage"] = "waiting_for_name"
        current_state["timestamp"] = datetime.now()
        
        # Ask for name
        return message_templates.get_message("ask_name")
    else:
        return message_templates.get_message("date_format_error")

def handle_date_input_for_name(customer_number, date_str):
    """Handler for when user has provided name and treatment, now adding date"""
    current_state = user_states[customer_number]
    
    # Try to parse natural language date or formatted date
    date_obj = time_utils.parse_natural_language_date(date_str)
    if date_obj:
        # Format as YYYY-MM-DD for internal use
        formatted_date = date_obj.strftime("%Y-%m-%d")
        
        # Check if the date is a public holiday
        if googlecalendar.is_public_holiday(date_obj):
            return message_templates.get_message("public_holiday_closed")
        
        # Store the date and move to asking for time
        current_state["appointment_info"]["date"] = formatted_date
        current_state["stage"] = "waiting_for_time_with_name"
        current_state["timestamp"] = datetime.now()
        
        # Get available times and ask for time
        treatment_type = current_state["appointment_info"]["treatment_type"]
        available_slots = googlecalendar.get_available_slots(formatted_date, treatment_type)
        
        if "error" in available_slots:
            return message_templates.get_message("availability_check_error", error=available_slots['error'])
        
        # Format the available slots for display
        display_date = time_utils.format_date_for_display(formatted_date)
        available_times = available_slots.get("available_slots", [])
        
        if not available_times:
            return message_templates.get_message("no_available_slots", date=display_date)
        
        return message_templates.get_message("available_slots",
            treatment=treatment_type,
            date=display_date,
            times=", ".join(available_times))
    else:
        return message_templates.get_message("date_format_error")

def handle_time_input_for_name(customer_number, time_str):
    """Handler for when user has provided name, treatment, and date, now adding time"""
    current_state = user_states[customer_number]
    
    normalized_time = time_utils.normalize_time_format(time_str)
    if not normalized_time:
        return message_templates.get_message("time_format_error")
    
    # Convert to 12-hour format for display
    hour, minute = map(int, normalized_time.split(':'))
    am_pm = 'AM' if hour < 12 else 'PM'
    hour = hour if 1 <= hour <= 12 else hour - 12 if hour > 12 else 12
    time_display = f"{hour}:{minute:02d} {am_pm}"
    
    # Check if this time is actually available
    appointment_info = current_state["appointment_info"]
    date_str = appointment_info["date"]
    treatment_type = appointment_info["treatment_type"]
    
    # Get available slots again to check
    availability = googlecalendar.get_available_slots(date_str, treatment_type)
    if "error" in availability:
        return message_templates.get_message("availability_check_error", error=availability['error'])
    
    available_times = availability.get("available_slots", [])
    if time_display not in available_times:
        return message_templates.get_message("alternative_times",
            time=time_display,
            date=time_utils.format_date_for_display(date_str),
            slots=", ".join(available_times))
    
    # Store the time and set up confirmation
    appointment_info["time"] = time_display
    
    # We already have the name from previous steps, so set up confirmation
    user_states[customer_number] = {
        "stage": "awaiting_booking_confirmation",
        "booking_details": {
            "customer_name": appointment_info["customer_name"],
            "customer_number": customer_number,
            "date": appointment_info["date"],
            "time": appointment_info["time"],
            "treatment_type": appointment_info["treatment_type"]
        },
        "timestamp": datetime.now()
    }
    
    # Ask for confirmation
    return message_templates.get_message("booking_confirmation_prompt",
        treatment=appointment_info["treatment_type"],
        name=appointment_info["customer_name"],
        date=time_utils.format_date_for_display(appointment_info['date']),
        time=appointment_info['time'],
        number=customer_number)



# --- Gemini API interaction ---
def get_gemini_response(customer_number, message):
    try:
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        }
        
        add_message_to_conversation(customer_number, "user", message)
        conversation_history = get_conversation_history(customer_number)
        
        data = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": MEOWKIES_CONTEXT + "\n\nPlease respond as Meowkies based on the following conversation:"}]
                }
            ]
        }
        
        for entry in conversation_history:
            role = "user" if entry["role"] == "user" else "model"
            data["contents"].append({
                "role": role,
                "parts": [{"text": entry["content"]}]
            })
        
        logger.debug(f"Sending request to Gemini API with conversation history. Customer message: {message[:50]}...")
        response = requests.post(GEMINI_API_URL, headers=headers, json=data, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Gemini API error: Status {response.status_code}, Response: {response.text}")
            return {"error": f"Gemini API returned status code {response.status_code}"}
        
        response_data = response.json()
        logger.debug(f"Gemini API response received: {str(response_data)[:100]}...")
        
        if "candidates" in response_data and response_data["candidates"]:
            candidate = response_data["candidates"][0]
            if "content" in candidate and "parts" in candidate["content"] and candidate["content"]["parts"]:
                response_text = candidate["content"]["parts"][0]["text"]
                add_message_to_conversation(customer_number, "assistant", response_text)
                return {"text": response_text}
        
        error_msg = "Failed to extract response from Gemini API"
        logger.error(error_msg)
        return {"error": error_msg}
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to Gemini API failed: {str(e)}")
        return {"error": f"Request to Gemini API failed: {str(e)}"}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini API response: {str(e)}")
        return {"error": "Invalid response from Gemini API"}
    except Exception as e:
        logger.error(f"Unexpected error in get_gemini_response: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}

# --- WhatsApp API interaction ---
def send_whatsapp_message(recipient_number, message):
    try:
        headers = {
            "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
            "Content-Type": "application/json",
        }
        data = {
            "messaging_product": "whatsapp",
            "to": recipient_number,
            "text": {"body": message},
        }
        
        logger.debug(f"Sending WhatsApp message to {recipient_number}: {message[:50]}...")
        response = requests.post(WHATSAPP_API_URL, headers=headers, json=data, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"WhatsApp API error: Status {response.status_code}, Response: {response.text}")
            return {"error": f"WhatsApp API returned status code {response.status_code}"}
        
        response_data = response.json()
        logger.debug(f"WhatsApp API response received: {response_data}")
        return response_data
    except requests.exceptions.RequestException as e:
        logger.error(f"Request to WhatsApp API failed: {str(e)}")
        return {"error": f"Request to WhatsApp API failed: {str(e)}"}
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse WhatsApp API response: {str(e)}")
        return {"error": "Invalid response from WhatsApp API"}
    except Exception as e:
        logger.error(f"Unexpected error in send_whatsapp_message: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}

# --- Extract message data safely ---
def extract_message_data(data):
    try:
        if not data or not isinstance(data, dict):
            logger.warning("Webhook data is empty or not a dictionary")
            return None, None
        
        if "object" in data and data.get("object") == "whatsapp_business_account":
            if "entry" not in data or not data["entry"]:
                logger.warning("No entries in webhook data")
                return None, None
            
            entry = data["entry"][0]
            if "changes" not in entry or not entry["changes"]:
                logger.warning("No changes in webhook entry")
                return None, None
            
            change = entry["changes"][0]
            if "value" not in change or "messages" not in change["value"] or not change["value"]["messages"]:
                logger.warning("No messages in webhook change value")
                return None, None
            
            message = change["value"]["messages"][0]
            if "text" not in message or "from" not in message:
                logger.warning("Message is missing required fields (text or from)")
                return None, None
            
            customer_message = message["text"].get("body", "")
            customer_number = message.get("from", "")
            
            if not customer_message or not customer_number:
                logger.warning(f"Invalid message data: message={bool(customer_message)}, number={bool(customer_number)}")
                return None, None
            
            return customer_number, customer_message
    except Exception as e:
        logger.error(f"Error extracting message data: {str(e)}")
        return None, None

# --- Webhook handling ---
@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    if request.method == "POST":
        try:
            logger.debug(f"Received webhook POST: {request.data.decode('utf-8')[:200]}...")
            
            # Periodically clean up expired conversations
            cleanup_expired_conversations()
            
            # Parse JSON data
            try:
                data = request.get_json()
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse webhook data: {str(e)}")
                return jsonify({"status": "error", "message": "Invalid JSON"}), 400
            
            # Extract message data
            customer_number, customer_message = extract_message_data(data)
            if not customer_number or not customer_message:
                logger.warning("Could not extract valid message data from webhook")
                return jsonify({"status": "error", "message": "Invalid message format"}), 200
            
            logger.info(f"Processing message from {customer_number}: {customer_message}")
            
            # Check rate limiting
            if not check_rate_limit(customer_number):
                warning_message = message_templates.get_message("rate_limit_exceeded")
                logger.warning(f"Rate limit exceeded for {customer_number}. Sending warning message.")
                send_whatsapp_message(customer_number, warning_message)
                return jsonify({"status": "error", "message": "Rate limit exceeded"}), 200
            
            # Add message to conversation history
            add_message_to_conversation(customer_number, "user", customer_message)
            
            # Call handle_message for all incoming messages
            response = handle_message(customer_number, customer_message)
            
            # If handle_message returned a response, use it
            if response:
                logger.info(f"Message handled successfully by handle_message for {customer_number}")
                # Add the response to conversation history
                add_message_to_conversation(customer_number, "assistant", response)
                
                # Send the response via WhatsApp
                whatsapp_result = send_whatsapp_message(customer_number, response)
                if "error" in whatsapp_result:
                    error_message = whatsapp_result["error"]
                    logger.error(f"Error sending WhatsApp message: {error_message}")
                    return jsonify({"status": "error", "message": error_message}), 200
                
                logger.info(f"Successfully processed message and sent response to {customer_number}")
                return jsonify({"status": "success"}), 200
            
            # If handle_message didn't return a response, fall back to Gemini
            logger.info(f"No response from handle_message for {customer_number}, falling back to Gemini")
            
            # Get response from Gemini with conversation history
            gemini_response = get_gemini_response(customer_number, customer_message)
            
            if "error" in gemini_response:
                error_message = gemini_response["error"]
                logger.error(f"Error getting Gemini response: {error_message}")
                fallback_message = message_templates.get_message("api_error_fallback")
                send_whatsapp_message(customer_number, fallback_message)
                add_message_to_conversation(customer_number, "assistant", fallback_message)
                return jsonify({"status": "error", "message": error_message}), 200
            
            gemini_text_response = gemini_response.get("text", "")
            if not gemini_text_response:
                logger.error("Empty response text from Gemini")
                fallback_message = message_templates.get_message("api_error_fallback")
                send_whatsapp_message(customer_number, fallback_message)
                add_message_to_conversation(customer_number, "assistant", fallback_message)
                return jsonify({"status": "error", "message": "Empty response from Gemini"}), 200
            
            whatsapp_result = send_whatsapp_message(customer_number, gemini_text_response)
            if "error" in whatsapp_result:
                error_message = whatsapp_result["error"]
                logger.error(f"Error sending WhatsApp message: {error_message}")
                return jsonify({"status": "error", "message": error_message}), 200
            
            logger.info(f"Successfully processed message and sent response to {customer_number}")
            return jsonify({"status": "success"}), 200
            
        except Exception as e:
            logger.error(f"Unexpected error processing webhook: {str(e)}")
            return jsonify({"status": "error", "message": str(e)}), 500
    
    elif request.method == "GET":
        # Your existing verification code remains unchanged
        try:
            verify_token = request.args.get("hub.verify_token")
            challenge = request.args.get("hub.challenge")
            
            logger.info(f"Received webhook verification request with token: {verify_token[:3]}..." if verify_token else "Missing verify_token")
            
            if not verify_token or not challenge:
                logger.warning("Missing verify_token or challenge in verification request")
                return "Missing parameters", 400
            
            if verify_token == VERIFY_TOKEN:
                logger.info("Webhook verification successful")
                return challenge, 200
            else:
                logger.warning(f"Invalid verification token: {verify_token[:3]}...")
                return "Invalid verify token", 403
                
        except Exception as e:
            logger.error(f"Error processing webhook verification: {str(e)}")
            return "Error processing verification", 500
        
@app.route("/health", methods=["GET"])
def health_check():
    return jsonify({
        "status": "healthy",
        "whatsapp_configured": bool(WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_API_TOKEN),
        "gemini_configured": bool(GEMINI_API_KEY),
        "bot_identity": "Meowkies - Meow Aesthetic Clinic Customer Support",
        "active_conversations": len(conversations)
    })

@app.route("/conversations", methods=["GET"])
def conversation_stats():
    stats = {
        "total_conversations": len(conversations),
        "conversations": {}
    }
    
    for number, data in conversations.items():
        stats["conversations"][number] = {
            "message_count": len(data["history"]),
            "last_updated": data["last_updated"].isoformat(),
            "expired": is_conversation_expired(number)
        }
    
    return jsonify(stats)

@app.route("/reset/<phone_number>", methods=["POST"])
def reset_conversation(phone_number):
    if phone_number in conversations:
        del conversations[phone_number]
        return jsonify({"status": "success", "message": f"Conversation for {phone_number} reset"})
    else:
        return jsonify({"status": "error", "message": "Conversation not found"}), 404
    

@app.route("/admin/add-promotion-recipient", methods=["POST"])
def admin_add_recipient():
    data = request.get_json()
    result = weekly_promotions.add_promotion_recipient(
        phone_number=data.get("phone_number"),
        name=data.get("name"),
        preferences=data.get("preferences")
    )
    return jsonify({"success": result})

@app.route("/admin/create-weekly-promotion", methods=["POST"])
def admin_create_promotion():
    data = request.get_json()
    result = weekly_promotions.create_weekly_promotion(
        day_of_week=data.get("day_of_week"),
        time=data.get("time"),
        template_name=data.get("template_name"),
        template_parameters=data.get("template_parameters")
    )
    return jsonify({"success": result})

@app.route("/run-promotions", methods=["GET"])
def run_promotions():
    weekly_promotions.run_promotion_scheduler()
    return jsonify({"status": "success", "message": "Promotions checked and sent"})


if __name__ == "__main__":
    # Existing code
    logger.info("Starting Meowkies WhatsApp Customer Support Chatbot")
    
    # Add scheduler for promotions
    from apscheduler.schedulers.background import BackgroundScheduler
    from apscheduler.triggers.interval import IntervalTrigger
    
    promotion_scheduler = BackgroundScheduler()
    promotion_scheduler.add_job(
        func=weekly_promotions.run_promotion_scheduler,
        trigger=IntervalTrigger(minutes=1),
        id='promotion_scheduler',
        name='Check and send scheduled promotions every minute'
    )
    promotion_scheduler.start()
    
    # Run the Flask app
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))
