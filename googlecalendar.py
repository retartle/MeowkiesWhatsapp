import os
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pytz
import re
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time_utils
import googlecalendar
import message_templates

# Add this to the top section of googlecalendar.py after your imports
PUBLIC_HOLIDAYS_2025 = [
    datetime(2025, 1, 1).date(),   # New Year's Day
    datetime(2025, 1, 29).date(),  # Chinese New Year Day 1
    datetime(2025, 1, 30).date(),  # Chinese New Year Day 2
    datetime(2025, 3, 31).date(),  # Hari Raya Puasa
    datetime(2025, 4, 18).date(),  # Good Friday
    datetime(2025, 5, 1).date(),   # Labour Day
    datetime(2025, 5, 12).date(),  # Vesak Day
    datetime(2025, 6, 7).date(),   # Hari Raya Haji
    datetime(2025, 8, 9).date(),   # National Day
    datetime(2025, 10, 20).date(), # Deepavali
    datetime(2025, 12, 25).date(), # Christmas Day
]

def is_public_holiday(date_obj):
    """
    Check if a given date is a Singapore public holiday.
    
    Args:
        date_obj (datetime.date): The date to check
        
    Returns:
        bool: True if the date is a public holiday, False otherwise
    """
    return date_obj in PUBLIC_HOLIDAYS_2025




# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# --- Load Google Calendar API credentials ---
GOOGLE_CALENDAR_CREDENTIALS = os.getenv("GOOGLE_CALENDAR_CREDENTIALS")
CALENDAR_ID = os.getenv("CALENDAR_ID")
CLINIC_TIMEZONE = pytz.timezone("Asia/Singapore")  # Set timezone for the clinic

# After (Aware)
now = datetime.now(CLINIC_TIMEZONE)

BUSINESS_HOURS = {
    0: {"start": "11:00 AM", "end": "8:00 PM"},  # Monday
    1: {"start": "11:00 AM", "end": "8:00 PM"},  # Tuesday
    2: {"start": "11:00 AM", "end": "8:00 PM"},  # Wednesday
    3: {"start": "11:00 AM", "end": "8:00 PM"},  # Thursday
    4: {"start": "11:00 AM", "end": "8:00 PM"},  # Friday
    5: {"start": "11:00 AM", "end": "10:00 PM"},  # Saturday
    6: None,  # Sunday (closed)
}


# Treatment duration configuration (in minutes)
# Treatment duration configuration (in minutes)
TREATMENT_DURATIONS = {
    "nails": 180,  # 3 hours
    "lashes": 120,  # 2 hours
    "lashes_touchup": 60,  # 1 hour
    "medical_facial": 90,  # 1.5 hours
    "ipl": 30,  # 30 minutes
    "slimming": 60  # 1 hour
}


def get_google_calendar_service():
    """Create and return a Google Calendar API service object"""
    try:
        logger.info("Attempting to create Google Calendar service")
        
        if not GOOGLE_CALENDAR_CREDENTIALS:
            logger.error("Google Calendar credentials not configured")
            return None
        
        # Log credential info (safely)
        cred_info = json.loads(GOOGLE_CALENDAR_CREDENTIALS)
        logger.info(f"Using service account: {cred_info.get('client_email', 'Not found')}")
        logger.info(f"Calendar ID being used: {CALENDAR_ID}")
        
        # Create credentials
        credentials = service_account.Credentials.from_service_account_info(
            cred_info,
            scopes=['https://www.googleapis.com/auth/calendar']
        )
        
        # Build the service
        service = build('calendar', 'v3', credentials=credentials)
        
        # Test the connection with a simple API call
        try:
            calendar_info = service.calendars().get(calendarId=CALENDAR_ID).execute()
            logger.info(f"Successfully connected to calendar: {calendar_info.get('summary', 'Unknown')}")
        except HttpError as e:
            logger.error(f"Failed to access calendar with ID {CALENDAR_ID}: {str(e)}")
            return None
            
        return service
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in GOOGLE_CALENDAR_CREDENTIALS environment variable")
        return None
    except Exception as e:
        logger.error(f"Error creating Google Calendar service: {str(e)}")
        return None

def convert_12h_to_24h(time_str):
    """Convert 12-hour time format to 24-hour format for internal use"""
    if not time_str:
        logger.error("Empty time string provided.")
        return None
    try:
        return datetime.strptime(time_str, "%I:%M %p").strftime("%H:%M")
    except ValueError:
        logger.error(f"Invalid 12-hour time format: {time_str}. Expected format: 'h:MM AM/PM'")
        return None

def convert_24h_to_12h(time_str):
    """Convert 24-hour time format to 12-hour format for display"""
    if not time_str:
        logger.error("Empty time string provided.")
        return None
    try:
        return datetime.strptime(time_str, "%H:%M").strftime("%I:%M %p").lstrip("0")
    except ValueError:
        logger.error(f"Invalid 24-hour time format: {time_str}. Expected format: 'HH:MM'")
        return None

def get_available_slots(date_str, treatment_type, requested_time_str=None):
    try:
        # Existing code for date validation
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            date_obj_tz = CLINIC_TIMEZONE.localize(datetime.combine(date_obj, datetime.min.time()))
        except ValueError:
            logger.error(f"Invalid date format: {date_str}")
            return {"error": "Invalid date format. Please use YYYY-MM-DD format."}
            
        # Add this new check after the existing date validation checks
        # Check if the date is a public holiday
        # Check if the date is a public holiday
        if is_public_holiday(date_obj):
            logger.info(f"Attempted to book on public holiday: {date_str}")
            return {"error": "The clinic is closed on public holidays. Please input another time."}

            
        # Rest of your existing code...


        # Check if date is in the past
        if date_obj < datetime.now(CLINIC_TIMEZONE).date():
            return {"error": "Cannot book appointments for past dates."}

        # Check if date is too far in the future (e.g., more than 3 months)
        max_future_date = datetime.now(CLINIC_TIMEZONE).date() + timedelta(days=90)
        if date_obj > max_future_date:
            return {"error": "Cannot book appointments more than 3 months in advance."}

        # Check if the clinic is open on this date (check day of week)
        day_of_week = date_obj_tz.weekday()
        if day_of_week == 6 or BUSINESS_HOURS.get(day_of_week) is None:  # Sunday or holiday
            return {"error": "The clinic is closed on this date."}

        # Check if treatment type is valid
        treatment_duration = TREATMENT_DURATIONS.get(treatment_type.lower())
        if not treatment_duration:
            return {"error": f"Unknown treatment type: {treatment_type}. Please select from: {', '.join(TREATMENT_DURATIONS.keys())}"}

        # Get business hours for this day
        business_hour = BUSINESS_HOURS.get(day_of_week)
        # Convert 12-hour format to 24-hour for internal processing
        start_time_24h = convert_12h_to_24h(business_hour["start"])
        end_time_24h = convert_12h_to_24h(business_hour["end"])
        start_time = datetime.strptime(start_time_24h, "%H:%M").time()
        end_time = datetime.strptime(end_time_24h, "%H:%M").time()

        # Create calendar service
        service = get_google_calendar_service()
        if not service:
            return {"error": "Unable to connect to calendar service."}

        time_min = CLINIC_TIMEZONE.localize(datetime.combine(date_obj, start_time)).isoformat()
        time_max = CLINIC_TIMEZONE.localize(datetime.combine(date_obj, end_time)).isoformat()

        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=time_min,
            timeMax=time_max,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        # Generate all possible time slots based on treatment duration
        all_slots = []
        current_time = CLINIC_TIMEZONE.localize(datetime.combine(date_obj, start_time))
        end_datetime = CLINIC_TIMEZONE.localize(datetime.combine(date_obj, end_time))

        while current_time + timedelta(minutes=treatment_duration) <= end_datetime:
            all_slots.append(current_time)
            current_time += timedelta(minutes=30)  # 30-minute intervals

        # Filter out booked slots
        available_slots = []
        for slot in all_slots:
            slot_end = slot + timedelta(minutes=treatment_duration)
            is_available = True

            for event in events:
                # CORRECTED: Ensure event times are timezone-aware
                event_start_str = event['start'].get('dateTime', event['start'].get('date'))
                event_end_str = event['end'].get('dateTime', event['end'].get('date'))

                # Check if it's a date-only event
                if 'date' in event['start']:
                    event_start = CLINIC_TIMEZONE.localize(datetime.strptime(event_start_str, "%Y-%m-%d")).replace(hour=0, minute=0, second=0)
                    event_end = CLINIC_TIMEZONE.localize(datetime.strptime(event_end_str, "%Y-%m-%d")).replace(hour=23, minute=59, second=59)
                else:
                    event_start = datetime.fromisoformat(event_start_str).astimezone(CLINIC_TIMEZONE)
                    event_end = datetime.fromisoformat(event_end_str).astimezone(CLINIC_TIMEZONE)

                # CORRECTED: Compare timezone-aware datetimes directly
                if not (slot_end <= event_start or slot >= event_end):
                    is_available = False
                    break

            if is_available:
                # Append the datetime object, not a string
                available_slots.append(slot)

        available_slots_12h = [slot.strftime("%I:%M %p").lstrip("0") for slot in available_slots]

        if requested_time_str:
            # Convert requested time to datetime object with timezone
            try:
                requested_time_obj = datetime.strptime(requested_time_str, "%H:%M").time()
                requested_datetime_obj = CLINIC_TIMEZONE.localize(datetime.combine(date_obj, requested_time_obj))

                requested_time_12h = requested_datetime_obj.strftime("%I:%M %p").lstrip("0")

            except ValueError:
                logger.error(f"Invalid requested time format: {requested_time_str}")
                return {"error": f"Invalid requested time format: {requested_time_str}"}

            if requested_time_12h not in available_slots_12h:
                return {
                    "unavailable_time": requested_time_12h,
                    "available_slots": available_slots_12h
                }

        return {"available_slots": available_slots_12h}

    except HttpError as e:
        logger.error(f"Google Calendar API error: {str(e)}")
        return {"error": "Error accessing calendar. Please try again later."}
    except Exception as e:
        logger.error(f"Error getting available slots: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}

logger = logging.getLogger(__name__)



def book_appointment(customer_name, customer_number, date_str, time_str, treatment_type, additional_notes=""):
    # Add validation for the phone number
    if not customer_number:
        logger.error("BOOKING: Missing customer phone number")
        return {"error": "Phone number is required for booking"}
        
    # NEW CODE: Check if the user already has 3 appointments
    existing_appointments = list_customer_appointments(customer_number, future_only=True)
    
    if "error" not in existing_appointments:
        if len(existing_appointments.get("appointments", [])) >= 3:
            logger.info(f"BOOKING: User {customer_name} has reached the maximum of 3 appointments")
            return {"error": "You already have 3 appointments scheduled. Please complete or cancel one of your existing appointments before booking a new one."}
        
    # Continue with existing code

    try:
        logger.info(f"BOOKING: Starting appointment booking process for {customer_name}")
        logger.info(f"BOOKING: Date={date_str}, Time={time_str}, Treatment={treatment_type}")

        service = get_google_calendar_service()
        if not service:
            logger.error("BOOKING: Failed to get Google Calendar Service")
            return {"error": "Calendar service connection failed"}
        logger.info("BOOKING: Successfully got Google Calendar service")

        # Log input values before parsing
        logger.info(f"BOOKING: date_str: '{date_str}', time_str: '{time_str}'")

        try:
            # After extracting the date but before setting up the confirmation
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            if googlecalendar.is_public_holiday(date_obj):
                return message_templates.get_message("public_holiday_closed")

            time_obj = datetime.strptime(time_str, "%I:%M %p").time()
            logger.info(f"BOOKING: Date/time validation successful: {date_obj} at {time_obj}")
        except ValueError as e:
            logger.error(f"BOOKING: Date/time validation failed: {str(e)}")
            return {"error": "Invalid date or time format. Use YYYY-MM-DD for date and 'h:MM AM/PM' for time."}

        logger.info(f"BOOKING: Validating treatment type: {treatment_type}")
        treatment_duration = TREATMENT_DURATIONS.get(treatment_type.lower())
        if not treatment_duration:
            logger.error(f"BOOKING: Unknown treatment type: {treatment_type}")
            return {"error": f"Unknown treatment type: {treatment_type}. Please select from: {', '.join(TREATMENT_DURATIONS.keys())}"}
        logger.info(f"BOOKING: Treatment validation successful, duration: {treatment_duration} minutes")

        appointment_datetime = CLINIC_TIMEZONE.localize(datetime.combine(date_obj, time_obj))
        now_datetime = CLINIC_TIMEZONE.localize(datetime.now())
        logger.info(f"BOOKING: Appointment time: {appointment_datetime}, Current time: {now_datetime}")
        if appointment_datetime < now_datetime:
            logger.error(f"BOOKING: Attempted to book past appointment: {date_str} {time_str}")
            return {"error": "Cannot book appointments in the past."}

        logger.info(f"BOOKING: Checking availability for {date_str} at {time_str}")

        time_24h = time_obj.strftime("%H:%M")
        availability_result = get_available_slots(date_str, treatment_type, time_24h)
        logger.info(f"BOOKING: Availability check result: {availability_result}")

        if "error" in availability_result:
            logger.error(f"BOOKING: Availability check failed: {availability_result['error']}")
            return availability_result
        elif "unavailable_time" in availability_result:
            unavailable_time = availability_result["unavailable_time"]
            available_times = ", ".join(availability_result["available_slots"])
            logger.error(f"BOOKING: Requested time ({unavailable_time}) is not available")
            return {
                "error": f"I'm sorry, but the requested time ({unavailable_time}) is not available on {date_str}. Here are the available times:\n\n{available_times}\n\nWould you like to book one of these times instead?"
            }

        if time_24h not in [datetime.strptime(slot, "%I:%M %p").strftime("%H:%M") for slot in availability_result.get("available_slots", [])]:
            logger.warning(f"BOOKING: Time slot {time_str} is no longer available")
            return {"error": "This time slot is no longer available. Please choose another time."}
        logger.info(f"BOOKING: Time slot {time_str} is available for booking")

        end_datetime = appointment_datetime + timedelta(minutes=treatment_duration)
        logger.info(f"BOOKING: Calculated end time: {end_datetime}")

        event = {
            'summary': f"Appointment: {treatment_type.title()} - {customer_name}",
            'description': f"Treatment: {treatment_type}\nCustomer: {customer_name}\nPhone: {customer_number}\nAdditional Notes: {additional_notes}",
            'start': {
                'dateTime': appointment_datetime.isoformat(),
                'timeZone': 'Asia/Singapore',
            },
            'end': {
                'dateTime': end_datetime.isoformat(),
                'timeZone': 'Asia/Singapore',
            },
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 60},
                ],
            },
        }
        logger.info(f"BOOKING: Event object created: {json.dumps(event)}")

        logger.info("BOOKING: Submitting event to Google Calendar API")
        try:
            event_result = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()
            logger.info(f"BOOKING: Event created successfully with ID: {event_result.get('id')}")
            # Inside book_appointment function in googlecalendar.py
            # After this line: event_result = service.events().insert(calendarId=CALENDAR_ID, body=event).execute()

            try:
                from appointment_reminders import schedule_appointment_reminder
                
                # Schedule a reminder for the appointment
                schedule_appointment_reminder(
                    appointment_id=event_result.get('id'),
                    customer_name=customer_name,
                    customer_number=customer_number,
                    treatment_type=treatment_type,
                    appointment_time=appointment_datetime
                )
                logger.info(f"BOOKING: Scheduled appointment reminder for {customer_name}")
            except Exception as e:
                logger.error(f"BOOKING: Failed to schedule appointment reminder: {str(e)}")
                # Continue with booking confirmation (don't fail if reminder scheduling fails)

        except HttpError as e:
            error_reason = e.reason if hasattr(e, 'reason') else str(e)
            error_code = e.status_code if hasattr(e, 'status_code') else 'unknown'
            logger.error(f"BOOKING: Google Calendar API error ({error_code}): {error_reason}")
            if hasattr(e, 'content'):
                try:
                    error_content = json.loads(e.content.decode('utf-8'))
                    logger.error(f"BOOKING: Detailed error: {json.dumps(error_content)}")
                except:
                    logger.error(f"BOOKING: Raw error content: {e.content}")
            return {"error": f"Error booking appointment: {error_reason}. Please try again later."}
        except Exception as e:
            logger.error(f"BOOKING: Failed to create event: {str(e)}")
            return {"error": f"Failed to create calendar event: {str(e)}"}

        logger.info(f"BOOKING SUCCESS: Appointment successfully added to calendar - ID: {event_result.get('id')}")
        logger.info(f"BOOKING: Appointment details: {treatment_type} for {customer_name} on {date_str} at {time_str}")
        logger.info(f"BOOKING: Calendar link: {event_result.get('htmlLink')}")

        confirmation = {
            "success": True,
            "appointment_id": event_result.get('id'),
            "customer_name": customer_name,
            "treatment": treatment_type,
            "date": time_utils.format_date_for_display(date_str),  # Convert to DD/MM/YYYY
            "time": time_str,
            "duration": f"{treatment_duration} minutes",
            "confirmation_link": event_result.get('htmlLink')
        }

        return confirmation

    except HttpError as e:
        error_reason = e.reason if hasattr(e, 'reason') else str(e)
        error_code = e.status_code if hasattr(e, 'status_code') else 'unknown'
        logger.error(f"BOOKING: Google Calendar API error ({error_code}): {error_reason}")
        return {"error": "Error booking appointment. Please try again later."}
    except Exception as e:
        logger.error(f"BOOKING: Error booking appointment: {str(e)}", exc_info=True)
        return {"error": f"Unexpected error: {str(e)}"}

def cancel_appointment(appointment_id):
    """
    Cancel an appointment by ID
    
   Args:
    appointment_id (str): Google Calendar event ID

    Returns:
        dict: Result of cancellation operation
    """
    try:
        # Create calendar service
        service = get_google_calendar_service()
        if not service:
            return {"error": "Unable to connect to calendar service."}

        # Delete the event
        service.events().delete(calendarId=CALENDAR_ID, eventId=appointment_id).execute()

        logger.info(f"Appointment {appointment_id} cancelled successfully")

        return {
            "success": True,
            "message": "Appointment cancelled successfully."
        }

    except HttpError as e:
        logger.error(f"Google Calendar API error: {str(e)}")
        return {"error": "Error cancelling appointment. Please try again later."}
    except Exception as e:
        logger.error(f"Error cancelling appointment: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}

def list_customer_appointments(customer_number, future_only=True):
    """
    List all appointments for a specific customer
    
    Args:
    customer_number (str): WhatsApp number of the customer
    future_only (bool): If True, return only future appointments

    Returns:
        dict: List of customer's appointments
    """
    try:
        # Create calendar service
        service = get_google_calendar_service()
        if not service:
            return {"error": "Unable to connect to calendar service."}

        # Set time range
        time_min = CLINIC_TIMEZONE.localize(datetime.now()).isoformat() if future_only else None

        # Get all events
        events_result = service.events().list(
            calendarId=CALENDAR_ID,
            timeMin=time_min,
            singleEvents=True,
            orderBy='startTime'
        ).execute()

        events = events_result.get('items', [])

        # Filter events for this customer
        customer_appointments = []
        for event in events:
            description = event.get('description', '')
            if f"Phone: {customer_number}" in description:
                # **CORRECTED: Handle date-only and datetime events**
                start_time_str = event['start'].get('dateTime', event['start'].get('date'))
                if 'date' in event['start']:
                    start_time = CLINIC_TIMEZONE.localize(datetime.strptime(start_time_str, "%Y-%m-%d")).replace(hour=0, minute=0, second=0)
                else:
                    start_time = datetime.fromisoformat(start_time_str).astimezone(CLINIC_TIMEZONE)

                # Extract treatment type from event summary
                summary = event.get('summary', '')
                treatment_type = "Unknown"
                if ":" in summary:
                    treatment_type = summary.split(":")[1].split("-")[0].strip()

                appointment = {
                    "id": event.get('id'),
                    "treatment": treatment_type,
                    "date": time_utils.format_date_for_display(start_time.strftime("%Y-%m-%d")),
                    "time": start_time.strftime("%I:%M %p").lstrip("0"),
                    "link": event.get('htmlLink')
                }


                customer_appointments.append(appointment)

        return {
            "appointments": customer_appointments
        }
        
    except HttpError as e:
        logger.error(f"Google Calendar API error: {str(e)}")
        return {"error": "Error retrieving appointments. Please try again later."}
    except Exception as e:
        logger.error(f"Error listing appointments: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}

def reschedule_appointment(appointment_id, new_date_str, new_time_str):
    """
    Reschedule an existing appointment
    
    Args:
    appointment_id (str): Google Calendar event ID
    new_date_str (str): New date in format 'YYYY-MM-DD'
    new_time_str (str): New time in 12-hour format (e.g., '2:00 PM')

    Returns:
        dict: Result of rescheduling operation
    """
    try:
        # Validate inputs
        try:
            new_date_obj = datetime.strptime(new_date_str, "%Y-%m-%d").date()
            # Convert 12-hour time to 24-hour for internal processing
            new_time_24h = datetime.strptime(new_time_str, "%I:%M %p").strftime("%H:%M")
            new_time_obj = datetime.strptime(new_time_24h, "%H:%M").time()
        except ValueError:
            return {"error": "Invalid date or time format. Useтрибут-MM-DD for date and 'h:MM AM/PM' for time."}

        # Create calendar service
        service = get_google_calendar_service()
        if not service:
            return {"error": "Unable to connect to calendar service."}

        # Get the existing event
        # ✅ Correct: Retrieve existing event before modifying
        event = service.events().get(calendarId=CALENDAR_ID, eventId=appointment_id).execute()



        # Extract treatment type from event summary
        summary = event.get('summary', '')
        treatment_type = "consultation"  # Default
        if ":" in summary:
            treatment_type = summary.split(":")[1].split("-")[0].strip().lower()

        # Get treatment duration
        treatment_duration = TREATMENT_DURATIONS.get(treatment_type, 30)  # Default to 30 minutes

        # Calculate new start and end time
        new_start_datetime = datetime.combine(new_date_obj, new_time_obj)
        new_end_datetime = new_start_datetime + timedelta(minutes=treatment_duration)

        # Check if the new slot is available
        availability = get_available_slots(new_date_str, treatment_type)
        if "error" in availability:
            return availability

        if new_time_str not in availability.get("available_slots", []):
            return {"error": "This time slot is not available. Please choose another time."}

        # Update the event
        event['start']['dateTime'] = new_start_datetime.isoformat()
        event['end']['dateTime'] = new_end_datetime.isoformat()

        updated_event = service.events().update(
            calendarId=CALENDAR_ID,
            eventId=appointment_id,
            body=event
        ).execute()

        logger.info(f"Appointment rescheduled: {updated_event.get('htmlLink')}")

        # Format the confirmation details
        confirmation = {
            "success": True,
            "appointment_id": updated_event.get('id'),
            "new_date": new_date_str,
            "new_time": new_time_str,
            "duration": f"{treatment_duration} minutes",
            "confirmation_link": updated_event.get('htmlLink')
        }

        return confirmation

    except HttpError as e:
        logger.error(f"Google Calendar API error: {str(e)}")
        return {"error": "Error rescheduling appointment. Please try again later."}
    except Exception as e:
        logger.error(f"Error rescheduling appointment: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}

logger = logging.getLogger(__name__)

def parse_appointment_request(message):
    """
    Parse appointment details from a user message.

    Args:
        message (str): The user message

    Returns:
        dict: Extracted appointment details or None if not enough information
    """
    try:
        appointment_info = {}

        # Extract date
        date_formats = [
            r"(\d{4}-\d{2}-\d{2})",  #лефон-MM-DD
            r"(\d{2}/\d{2}/\d{4})",  # DD/MM/YYYY
            r"(\d{2}-\d{2}-\d{4})"   # DD-MM-YYYY
        ]

        for date_format in date_formats:
            date_match = re.search(date_format, message)
            if date_match:
                date_str = date_match.group(1)
                # Convert toлефон-MM-DD if needed
                if "/" in date_str or (date_str[2] == "-" and date_str[5] == "-"):
                    parts = re.split(r"[-/]", date_str)
                    if len(parts) == 3:
                        if len(parts[0]) == 4:  #лефон-MM-DD
                            appointment_info["date"] = date_str
                        else:  # DD/MM/YYYY or DD-MM-YYYY
                            appointment_info["date"] = f"{parts[2]}-{parts[1]}-{parts[0]}"
                else:
                    appointment_info["date"] = date_str
                break

        # Extract time with improved patterns
        full_time_pattern = r"(\d{1,2}[:\.]\d{1,2}\s*(?:AM|PM|am|pm))"
        full_time_match = re.search(full_time_pattern, message, re.IGNORECASE)

        if full_time_match:
            time_str = full_time_match.group(1)
            normalized_time = time_utils.normalize_time_format(time_str)
            if normalized_time:
                try:
                    # Convert to 12-hour AM/PM format
                    hour, minute = map(int, normalized_time.split(':'))
                    am_pm = 'AM' if hour < 12 else 'PM'
                    hour = hour if 1 <= hour <= 12 else hour - 12 if hour > 12 else 12
                    converted_time = f"{hour:02d}:{minute:02d} {am_pm}"
                    appointment_info["time"] = converted_time  # Store converted time
                except ValueError as e:
                    logger.error(f"Error converting time: {e}")
                    return None
        else:
            hour_ampm_pattern = r"(\d{1,2}\s*(?:AM|PM|am|pm))"
            hour_ampm_match = re.search(hour_ampm_pattern, message, re.IGNORECASE)

            if hour_ampm_match:
                time_str = hour_ampm_match.group(1)
                normalized_time = time_utils.normalize_time_format(time_str)
                if normalized_time:
                    try:
                        # Convert to 12-hour AM/PM format
                        hour, minute = map(int, normalized_time.split(':'))
                        am_pm = 'AM' if hour < 12 else 'PM'
                        hour = hour if 1 <= hour <= 12 else hour - 12 if hour > 12 else 12
                        converted_time = f"{hour:02d}:{minute:02d} {am_pm}"
                        appointment_info["time"] = converted_time  # Store converted time
                    except ValueError as e:
                        logger.error(f"Error converting time: {e}")
                        return None
            else:
                hour_24_pattern = r"(\d{1,2}[:\.]\d{1,2})"
                hour_24_match = re.search(hour_24_pattern, message)

                if hour_24_match:
                    time_str = hour_24_match.group(1)
                    normalized_time = time_utils.normalize_time_format(time_str)
                    if normalized_time:
                        try:
                            # Convert to 12-hour AM/PM format
                            hour, minute = map(int, normalized_time.split(':'))
                            am_pm = 'AM' if hour < 12 else 'PM'
                            hour = hour if 1 <= hour <= 12 else hour - 12 if hour > 12 else 12
                            converted_time = f"{hour:02d}:{minute:02d} {am_pm}"
                            appointment_info["time"] = converted_time  # Store converted time
                        except ValueError as e:
                            logger.error(f"Error converting time: {e}")
                            return None
                else:
                    hour_only_pattern = r"(?<!\d)(\d{1,2})(?!\d)"
                    hour_only_match = re.search(hour_only_pattern, message)

                    if hour_only_match:
                        time_str = hour_only_match.group(1)
                        normalized_time = time_utils.normalize_time_format(time_str)
                        if normalized_time:
                            try:
                                # Convert to 12-hour AM/PM format
                                hour, minute = map(int, normalized_time.split(':'))
                                am_pm = 'AM' if hour < 12 else 'PM'
                                hour = hour if 1 <= hour <= 12 else hour - 12 if hour > 12 else 12
                                converted_time = f"{hour:02d}:{minute:02d} {am_pm}"
                                appointment_info["time"] = converted_time  # Store converted time
                            except ValueError as e:
                                logger.error(f"Error converting time: {e}")
                                return None

        # Extract treatment type
        treatment_keywords = {
            "consultation": ["consult", "consultation"],
            "medical_facial": ["facial", "med facial", "medical facial"],
            "laser_treatment": ["laser", "laser treatment"],
            "botox": ["botox", "toxin", "anti-wrinkle"],
            "filler": ["filler", "fillers", "dermal filler"],
            "follow_up": ["follow up", "follow-up", "checkup", "check up"]
        }

        message_lower = message.lower()
        for treatment, keywords in treatment_keywords.items():
            for keyword in keywords:
                if keyword in message_lower:
                    appointment_info["treatment_type"] = treatment
                    break
            if "treatment_type" in appointment_info:
                break

        # If we have at least date and time, return the information
        if "date" in appointment_info and "time" in appointment_info:
            # Set default treatment type if not found
            if "treatment_type" not in appointment_info:
                appointment_info["treatment_type"] = "consultation"

            # Log the extracted information
            logger.debug(f"Extracted appointment info: {appointment_info}")
            return appointment_info

        # Log what's missing
        missing = []
        if "date" not in appointment_info:
            missing.append("date")
        if "time" not in appointment_info:
            missing.append("time")
        logger.debug(f"Incomplete appointment info - missing: {', '.join(missing)}")

        return None

    except Exception as e:
        logger.error(f"Error parsing appointment request: {str(e)}")
        return None
    
def test_google_calendar_connection():
    """Test if we can connect to the Google Calendar API"""
    try:
        logger.info("Testing Google Calendar API connection")
        
        # Check if credentials are configured
        if not GOOGLE_CALENDAR_CREDENTIALS:
            logger.error("Google Calendar credentials not configured")
            return False
            
        # Check if calendar ID is configured
        if not CALENDAR_ID:
            logger.error("Calendar ID not configured")
            return False
            
        # Try to parse credentials
        try:
            cred_info = json.loads(GOOGLE_CALENDAR_CREDENTIALS)
            logger.info(f"Using service account: {cred_info.get('client_email', 'Not found')}")
        except json.JSONDecodeError:
            logger.error("Invalid JSON in GOOGLE_CALENDAR_CREDENTIALS")
            return False
            
        # Create service
        service = get_google_calendar_service()
        if not service:
            logger.error("Failed to create Google Calendar service")
            return False
            
        # Test access to the calendar
        try:
            calendar_info = service.calendars().get(calendarId=CALENDAR_ID).execute()
            logger.info(f"Successfully connected to calendar: {calendar_info.get('summary', 'Unknown')}")
            return True
        except HttpError as e:
            logger.error(f"Failed to access calendar with ID {CALENDAR_ID}: {e.reason}")
            return False
            
    except Exception as e:
        logger.error(f"Calendar connection test failed: {str(e)}")
        return False