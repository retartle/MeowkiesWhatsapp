# survey_message.py
from datetime import datetime, timedelta

def schedule_survey_message(appointment_time, message_template, owner_number):
    """
    Schedules a survey or review message to be sent 1 hour after the appointment.
    """
    # Calculate time to send (1 hour after appointment)
    send_time = appointment_time + timedelta(hours=1)
    
    # Format the message with the scheduled time
    message = message_template.format(time=send_time.strftime('%Y-%m-%d %H:%M:%S'))
    
    # Return the scheduled message details
    return {
        "send_time": send_time,
        "message": message,
        "forward_to": owner_number
    }

def forward_message(scheduled_message):
    """
    Forwards the scheduled message to the owner's number.
    """
    confirmation = f"Message: '{scheduled_message['message']}' has been forwarded to {scheduled_message['forward_to']} at {scheduled_message['send_time']}"
    return confirmation
