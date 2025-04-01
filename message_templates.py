import random

def get_message(message_key, **kwargs):
    """
    Returns a randomly selected message variation with formatted parameters
    
    Args:
        message_key: The key for the desired message
        **kwargs: Parameters to format into the message
    """
    if message_key in messages:
        template = random.choice(messages[message_key])
        return template.format(**kwargs)
    return f'Message key "{message_key}" not found'

messages = {
    # Booking Flow Messages
    "booking_date_prompt": [
        "When would you like to schedule your appointment? Please provide a date in DD/MM/YYYY format, or say something like 'tomorrow' or 'next Thursday'.",
        "What date works best for you? You can use DD/MM/YYYY format or phrases like 'tomorrow' or 'next Thursday'.",
        "Let's find a purr-fect date for your visit! Please specify a date (DD/MM/YYYY) or use terms like 'tomorrow' or 'next Thursday'."
    ],
    
    "time_format_error": [
        "I couldn't understand the time format. Please provide the time as '5:30 PM' or '5.30 PM'. Let's get this right meow! 🕒",
        "Sorry, I didn't recognize that time format. Could you use '5:30 PM' or '5.30 PM' instead? I'm trying to be purr-cise about your scheduling!",
        "The time format seems incorrect. Please use '5:30 PM' or '5.30 PM' format. I'm pawsitive we'll get it right this time!"
    ],
    
    "date_format_error": [
        "Please provide a valid date such as 'tomorrow', 'next Thursday', or in DD/MM/YYYY format. Let's get your appointment scheduled right meow!",
        "I'm not sure about that date. Could you try 'tomorrow', 'next Thursday', or DD/MM/YYYY format? I'm pawsitively committed to getting this right for you!",
        "That date format wasn't clear to me. Please use 'tomorrow', 'next Thursday', or DD/MM/YYYY. Don't worry, I'm not kitten around - I'm here to help! 🐱"
    ],
    
    "booking_confirmation_prompt": [
        "I'll book a {treatment} for {name} on {date} at {time}. Your phone number ({number}) will be associated with this appointment. Is this correct? Please reply with 'yes' or 'no'. We're almost done, right meow! 🐱",
        "Would you like me to book your {treatment} appointment for {date} at {time} under the name {name}? Please confirm with 'yes' or 'no'. Just need your purr-mission to proceed!",
        "I'm ready to pounce on this booking! 📅 Your {treatment} on {date} at {time} with phone number {number}. Does this look correct? Please reply with 'yes' or 'no'."
    ],
    
    "booking_success": [
        "Paw-some! Your appointment for {treatment} has been successfully booked for {date} at {time}.\n\nThe appointment will last approximately {duration}.\n\nPlease arrive 10 minutes before your scheduled time. If you need to cancel or reschedule, please let me know at least 24 hours in advance. We're looking fur-ward to seeing you!",
        "Purr-fect! Your {treatment} appointment is confirmed for {date} at {time}.\n\nIt will take about {duration}.\n\nPlease come 10 minutes early. Need to change? Let me know 24 hours before. We're excited to see you soon!",
        "Meow-velous! Your {treatment} is all set for {date} at {time}! 🐱\n\nThe appointment will be approximately {duration} long.\n\n*Please note:* Arrive 10 minutes early and give us 24 hours notice for any changes. We're feline excited to see you soon!"
    ],

    
    "booking_error": [
        "I encountered a problem with booking: {error}. Please call our clinic directly at 87713358 for assistance.",
        "There was an issue while booking your appointment: {error}. Please contact our clinic at 87713358 for help.",
        "I'm having trouble completing your booking: {error}. Please reach out to our clinic at 87713358."
    ],
    
    # Appointment Management
    "no_appointments": [
        "You don't have any upcoming appointments scheduled. Would you like to book one now? Just let me know what purr-fect time works for you!",
        "I don't see any appointments under your number. Would you like to schedule one? What time would be paw-sible for you?",
        "You currently have no appointments with us. Would you like to book one? Just tell me what time would be paw-some for you!"
    ],
    
    "reschedule_success": [
        "Paw-some! Your appointment has been successfully rescheduled to {date} at {time}. We're looking fur-ward to seeing you then!",
        "Purr-fect! Your appointment is now set for {date} at {time}. We can't wait to see you!",
        "Your appointment has been meow-velously rescheduled! 📅 You're now booked for {date} at {time}. We're ex-purr-ts at flexibility and can't wait to see you at your new time!"
    ],
    
    "cancel_success": [
        "Your {treatment} appointment on {date} at {time} has been successfully canceled. Thanks for letting us know in advance - it's the purr-fect way to help us manage our schedule! 📅",
        "I've canceled your {treatment} appointment scheduled for {date} at {time}. No fur-ther action is needed from your side. Feel free to book again when you're ready!",
        "Your {treatment} appointment for {date} at {time} has been fur-gotten as requested. We hope to see you again soon for your beauty and wellness needs! 🐱"
    ],

    
    # Business Hours & Availability
    "public_holiday_closed": [
        "I encountered a problem with booking: The clinic is closed on public holidays. Please input another time. Let's find a more purr-fect day! 🗓️",
        "Oh no! That date is a public holiday, and our clinic will be closed. Could you please input another time? I'm pawsitive we can find a good alternative!",
        "I'm afraid we're closed on that date due to a public holiday. Would you mind inputting another time? Don't fur-get that we're closed on public holidays! 🐱"
    ],

    
    "outside_operating_hours": [
        "I'm sorry, but {time} is outside our operating hours. Our clinic is open from 11:00 AM to 8:00 PM Monday to Friday, and 11:00 AM to 10:00 PM on Saturday. Please choose a time within these hours for your booking.",
        "That time ({time}) won't work as it's outside our business hours. We're open from 11:00 AM to 8:00 PM Monday to Friday, and 11:00 AM to 10:00 PM on Saturday. Could you select a time during these hours?",
        "I need to paws you there - {time} is outside our operating hours! 🕒 Our clinic hours are:\n*Monday-Friday:* 11:00 AM to 8:00 PM\n*Saturday:* 11:00 AM to 10:00 PM\nCould you purr-haps choose a time within these hours?"
    ],
    
    "no_available_slots": [
        "I'm sorry, there are no available times on {date}. Please select another date. Let's find a more purr-fect time for you! 📅",
        "Unfortunately, we're fully booked on {date}. Could you try a different date? Our schedule is filling up fast, but I'm pawsitive we can find you a slot!",
        "All our slots are taken on {date}. Would you like to try another day? I'm not kitten around - we're quite busy but want to accommodate you! 🐱"
    ],
    
    "available_slots": [
        "Great! For your {treatment} on {date}, here are the available times:\n\n{times}\n\nPlease reply with your preferred time. I'm pawsitively excited to get you booked in! ⏰",
        "For your {treatment} on {date}, you can choose from these times:\n\n{times}\n\nWhich time works best for you? Let's find the purr-fect slot for your schedule!",
        "Here are the available slots for your {treatment} on {date}:\n\n{times}\n\nLet me know which one you prefer. I'm all ears... or should I say, all whiskers! 🐱"
    ],
    
    # Rate Limiting
    "rate_limit_exceeded": [
        "Whoa there, fur-get about spamming! You're sending messages too quickly. Please slow down and try again in a minute.",
        "Hold your paws! That's too many messages at once. Please wait a moment before trying again.",
        "Meow! You're typing faster than I can keep up! Please slow down and try again shortly."
    ],
    
    # Error Handling
    "api_error_fallback": [
        "I'm having trouble processing your request right meow. Please try again later or call our clinic directly at 87713358 during our operating hours (Mon-Fri: 11am-8pm, Sat: 11am-10pm). Purr-fectly yours, Meowkies 🐾",
        "Something seems to be wrong with my whiskers right now! Please try again soon or call our clinic at 87713358 during our hours (Mon-Fri: 11am-8pm, Sat: 11am-10pm). Purr-fectly yours, Meowkies 🐾",
        "My cat-pabilities seem to be limited at the moment. 🐱 For immediate assistance, please call our clinic at *87713358* during our operating hours:\n*Monday-Friday:* 11am-8pm\n*Saturday:* 11am-10pm\nI'll be back on my paws soon! Purr-fectly yours, Meowkies 🐾"
    ],
    
    "appointment_booking_format": [
        "I'd be happy to help you book an appointment! Please provide:\n1. The type of treatment you want (consultation, medical facial, laser treatment, botox, filler, or follow-up)\n2. Your preferred date (YYYY-MM-DD)\n3. Your preferred time\n4. Your name (if this is your first time)\n\nFor example: 'I'd like to book a consultation on 2025-03-20 at 2:00 PM'",
        "I'd love to book you in! Please tell me:\n1. What treatment you'd like (consultation, medical facial, laser treatment, botox, filler, or follow-up)\n2. Your preferred date\n3. Your preferred time\n4. Your name\n\nFor example: 'I want a consultation on 2025-03-20 at 2:00 PM'",
        "Let's get your purr-fect appointment scheduled! 📅 Please provide these details:\n\n1. *Treatment type*: consultation, medical facial, laser treatment, botox, filler, or follow-up\n2. *Date*: YYYY-MM-DD format\n3. *Time*: Your preferred time\n4. *Your name*\n\nFor example: 'I'd like a laser treatment on 2025-03-25 at 3:30 PM.'"
    ],
    
    "session_timeout": [
        "Your booking request has timed out. Please start again. Don't worry, I'm still here, ready to help you right meow! 🕒",
        "It looks like our conversation was idle for too long. Let's start the booking process again. I'm pawsitively ready when you are!",
        "Our booking session has expired due to inactivity. Please begin again when you're ready. I'm not kitten around - I'm here to assist whenever you want to continue! 🐱"
    ],

    "general_fallback": [
        "I'm not sure how to respond to that. Would you like to book an appointment, check your existing appointments, or learn more about our services? I'm here to help with anything clinic-related!",
        "I didn't quite catch that. Can I help you book an appointment, check your schedule, or answer questions about our treatments? Just let me know what you're looking for!",
        "Hmm, I'm not paw-sitive about what you're asking. Would you like to schedule an appointment, view your existing bookings, or ask about our services?"
    ],
    
    "booking_canceled": [
        "I've canceled the booking. Let's try again. What type of appointment would you like to schedule?",
        "Your booking has been canceled. Would you like to try booking a different appointment?",
        "The booking has been fur-gotten. Let me know if you'd like to schedule something else."
    ],
    
    "provide_reschedule_date": [
        "Please provide a new date for your appointment in DD/MM/YYYY format, or say something like 'tomorrow' or 'next Thursday'.",
        "When would you like to reschedule to? You can use a format like DD/MM/YYYY, or say 'tomorrow' or 'next Thursday'.",
        "What's a better date for you? You can specify a date like DD/MM/YYYY or use phrases like 'tomorrow' or 'next Thursday'."
    ],
    
    "invalid_appointment_number": [
        "Please enter a valid number between 1 and {max_appointments}.",
        "That number doesn't match any appointment. Please choose a number between 1 and {max_appointments}.",
        "I need a number between 1 and {max_appointments} to identify which appointment you mean."
    ],
    
    "enter_valid_number": [
        "Please enter a valid number for the appointment you want to reschedule.",
        "I need a numeric value to identify which appointment to reschedule.",
        "Could you provide the number of the appointment you'd like to change?"
    ],
    
    "past_date_error": [
        "Cannot reschedule appointments to past dates. Please select a future date.",
        "Oops! Time travel isn't possible yet. Please choose a date in the future.",
        "We need to book appointments for future dates. Please select an upcoming date."
    ],
    
    "clinic_closed": [
        "The clinic is closed on this date. Please select another date. Let's find a purr-fect alternative! 📅",
        "We're not open on that date. Could you choose a different day? I'm pawsitive we can find a time that works!",
        "Our clinic won't be open then. Please pick another date. Don't fur-get that we're closed on Sundays! 🐱"
    ],
    
    "booking_with_time_confirmation": [
        "I see you'd like to book a {treatment} at {time}. What date would you prefer? Please provide a date in DD/MM/YYYY format, or say something like 'tomorrow' or 'next Thursday'.",
        "Great choice! For your {treatment} at {time}, which date works best? You can use DD/MM/YYYY format or phrases like 'tomorrow' or 'next Thursday'.",
        "A {treatment} at {time} sounds purr-fect! Now I just need a date. You can specify DD/MM/YYYY or use terms like 'tomorrow' or 'next Thursday'."
    ],
    
    "no_appointments_to_reschedule": [
        "You don't have any upcoming appointments to reschedule. Would you like to book a new appointment instead?",
        "I don't see any scheduled appointments that can be rescheduled. Would you like to make a new booking?",
        "There are no upcoming appointments to change. Would you like to schedule a fresh appointment?"
    ],
    
    "selected_appointment_to_reschedule": [
        "You've selected to reschedule your {treatment} appointment on {date} at {time}. Please provide a new date in DD/MM/YYYY format, or say something like 'tomorrow' or 'next Thursday'.",
        "I'll help you reschedule your {treatment} appointment currently set for {date} at {time}. What new date would work better? Use DD/MM/YYYY format or phrases like 'tomorrow'.",
        "Let's change your {treatment} appointment from {date} at {time}. What date would you prefer instead? You can use DD/MM/YYYY format or terms like 'next Thursday'."
    ],
    
    "invalid_appointment_index": [
        "Invalid appointment number. You have {count} upcoming appointments.",
        "That appointment number doesn't exist. You currently have {count} appointments scheduled.",
        "Please choose a number between 1 and {count} to select an appointment."
    ],
    
    "no_appointments_to_cancel": [
        "You don't have any upcoming appointments to cancel.",
        "I don't see any scheduled appointments that can be canceled.",
        "There are no appointments in our system for your number."
    ],
    
    "generic_error": [
        "I'm sorry, I encountered an error: {error}. Our team is working to fix this right meow! 🛠️ Please try again later or call us directly.",
        "Something went wrong: {error}. Don't fur-get that you can always reach us by phone at *87713358* if this persists!",
        "There was a problem with your request: {error}. I'm pawsitively sorry about this inconvenience. Please try again or contact our clinic directly."
    ],
    
    "reschedule_error": [
        "I encountered a problem with rescheduling: {error}. Please try a different time or date, or call our clinic directly at 87713358 for assistance.",
        "There was an issue rescheduling your appointment: {error}. You could try another time/date or call us at 87713358 for help.",
        "I couldn't reschedule your appointment: {error}. Please select a different time or date, or reach our staff at 87713358."
    ],
    
    "which_appointment_to_reschedule": [
        "Which appointment would you like to reschedule? Please reply with the number:\n\n{appointment_list}",
        "Please select which appointment to reschedule by number:\n\n{appointment_list}",
        "Which of these appointments would you like to change? Reply with the number:\n\n{appointment_list}"
    ],

    "ask_name": [
        "Could you please provide your name so I can complete the booking? It's the purr-fect way to personalize your experience with us! 📋",
        "I just need your name to finalize this booking. What should I call you? I'm all ears... or should I say, all whiskers! 🐱",
        "What name would you like to use for this appointment? This helps us keep track of your visits and provide the most paw-sitive experience!"
    ],

    "availability_check_error": [
        "I encountered a problem checking availability: {error}. Please try a different date.",
        "There was an issue while checking available times: {error}. Could you select another date?",
        "I couldn't retrieve the available slots: {error}. Please try a different date."
    ],

    "alternative_times": [
        "I'm sorry, but the requested time ({time}) is not available on {date}. Here are the available times:\n\n{slots}\n\nWould you like to book one of these times instead?",
        "That time ({time}) is already booked on {date}. You could choose from these times instead:\n\n{slots}\n\nWhich one works for you?",
        "Unfortunately, {time} isn't available on {date}. Here are the times you can book:\n\n{slots}\n\nDo any of these work for you?"
    ],

    "view_appointments": [
        "Here are your upcoming appointments:\n\n{appointment_list}\n\nTo reschedule or cancel an appointment, just let me know which one by number or details.",
        "These are the appointments you have scheduled:\n\n{appointment_list}\n\nYou can reschedule or cancel by telling me which appointment number.",
        "I found these upcoming appointments for you:\n\n{appointment_list}\n\nLet me know if you'd like to modify any of them by number."
    ],

    "time_format_explanation": [
        "I couldn't understand the time format. Please provide the time in either 24-hour format (like 14:30) or 12-hour format (like 2:30 PM). Let's get this right meow! ⏰",
        "The time format wasn't clear to me. Please use either 24-hour format (e.g., 14:30) or 12-hour format (e.g., 2:30 PM). I'm pawsitively committed to booking you correctly!",
        "I didn't recognize that time format. Could you use either 24-hour time (14:30) or 12-hour time (2:30 PM)? I'm not kitten around about getting your appointment purr-fectly scheduled! 🕒"
    ],

    "ask_for_date": [
        "When would you like to book your {treatment}? Please provide a date in DD/MM/YYYY format, or say something like 'tomorrow' or 'next Thursday'. I'm paw-sitively excited to get you scheduled! 📅",
        "What date works for your {treatment}? You can specify DD/MM/YYYY or use phrases like 'tomorrow' or 'next Thursday'. Let's find the purr-fect time for you!",
        "When would you like to come in for your {treatment}? Please provide a date (DD/MM/YYYY) or use terms like 'tomorrow' or 'next Thursday'. I'm all ears... or should I say, all whiskers! 🐱"
    ],

    "ask_for_time": [
        "Paw-some! Now, what time would you like to book your {treatment} appointment on {date}?",
        "Purr-fect! What time works best for your {treatment} on {date}?",
        "Meow-velous! Let's pick a time for your {treatment} on {date}. What suits you?"
    ],

    "time_format_error": "I'm sorry, but I couldn't understand that time format. Please enter a time like '2:30 PM' or '14:30'.",


    "appointment_reminder": [
        "Reminder: You have a {treatment} appointment at Meow Aesthetic Clinic tomorrow at {time} on {date}. Please arrive 10 minutes early. Need to reschedule? Let us know at least 24 hours in advance. We're looking fur-ward to seeing you!",
        "Don't fur-get! Your {treatment} appointment at Meow Aesthetic Clinic is scheduled for {time} on {date}. Please arrive 10 minutes early. Need to cancel or reschedule? Please give us 24 hours notice. We're excited to see you soon!",
        "Meow there! This is a friendly reminder of your upcoming {treatment} appointment tomorrow at {time} on {date}. Please arrive 10 minutes early. We're purr-pared and ready to see you!"
    ],



}