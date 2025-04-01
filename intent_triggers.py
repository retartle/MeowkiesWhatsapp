# intent_triggers.py

# Treatment types with expanded variations and abbreviations
# Treatment types with expanded variations and abbreviations
TREATMENT_TYPES = {
    "nails": [
        # Original terms
        "nails", "nail", "manicure", "pedicure", "nail art", "nail treatment", "nail polish", 
        "gel nails", "acrylic nails", "nail extension", "nail spa",
        # Misspellings
        "nailes", "nale", "nailz", "nale polish", "gel nailes", "nayl", "neils",
        # Broken English
        "finger paint", "finger color", "toe color", "hand nail", "toe nail", "nail hand", 
        "color nail", "make nail", "pretty nail", "beauty nail"
    ],
    
    "lashes": [
        # Original terms
        "lashes", "eyelashes", "lash extensions", "lash extension", "eyelash extensions",
        "volume lashes", "lash lift", "lash volume", "full lashes",
        # Misspellings
        "lashs", "lashis", "lashees", "lashess", "lash extention", "eye lash", "eylash",
        # Broken English
        "eye hair long", "eye hair pretty", "make eye long", "eye beauty", "eye curl",
        "big lash", "long lash", "pretty eye hair", "fake lash", "eye fake hair"
    ],
    
    "lashes_touchup": [
        # Original terms
        "lashes touchup", "lash touchup", "lash touch up", "lashes touch up", "touchup lashes",
        "touch up lashes", "eyelash refill", "lash refill", "lash fill", "lashes fill",
        # Misspellings
        "lash touch-up", "lashes tuch up", "lash tuchup", "lash refil", "lash re-fill",
        # Broken English
        "fix lash", "repair lash", "add more lash", "more lash", "lash again", "continue lash",
        "small lash fix", "quick lash", "eye hair fix", "eye touch"
    ],
    
    "medical_facial": [
        # Original terms
        "facial", "med facial", "medical facial", "face treatment", "skin facial", "med fc", "face", "fcial",
        "medic facial", "medi facial", "deep facial", "skin treatment", "complexion treatment",
        # Misspellings
        "facil", "fasial", "fecial", "medikal facial", "medical face", "medicl facil", "medic facel",
        "faycial", "faical", "medic fayshal", "fascial", "face treetment", "facial treetment", "skin treat",
        # Broken English
        "face clean", "clean face", "face deep clean", "face doctor clean", "doctor face", "clinic face",
        "face good skin", "face wash doctor", "face clinic", "face nice", "face care", "medic face",
        # Concatenated/phonetic
        "medfacial", "facetx", "facialtx", "medface", "skintx", "facetreat", "skintreat", "cleanface"
    ],
    
    "ipl": [
        # Original terms
        "ipl", "intense pulsed light", "ipl treatment", "ipl facial", "ipl therapy",
        "photorejuvenation", "photo facial", "photofacial", "light therapy", "light treatment",
        # Misspellings
        "ipeel", "i.p.l", "i p l", "intence pulse light", "intense pulse lite", "foto facial",
        # Broken English
        "light face", "flash face", "light skin make good", "face light machine", "skin light treatment",
        "special light", "bright light face", "light make skin nice", "flash treatment", "face flash"
    ],
    
    "slimming": [
        # Original terms
        "slimming", "body contour", "body contouring", "weight loss", "fat reduction", 
        "body sculpting", "slim treatment", "fat removal", "body shaping", "figure treatment",
        # Misspellings
        "sliming", "slimming", "slim tratment", "boddy contour", "weight loose", "fat reduce",
        # Broken English
        "make body small", "less fat", "thin body", "small body make", "remove fat", 
        "body thin", "make slim", "no more fat", "good body shape", "make body nice"
    ]
}



# Booking intent phrases - require these for booking flow
BOOKING_INTENT_PHRASES = [
    # Original terms
    "book", "schedule", "make appointment", "get appointment", "reserve", "set up",
    "appointment for", "booking for", "set appointment", "create appointment",
    "arrange", "organize", "plan", "book in", "sign up for", "register for",
    "want appointment", "need appointment", "like to come in for", "arrange appointment",
    "slot", "time slot", "visit", "confirm appointment", "secure appointment",
    # Misspellings
    "boook", "buk", "schedual", "skedule", "skhedule", "schedual", "scedule", "shadul", 
    "apointment", "apoiment", "apointmant", "apptment", "appt", "appt for", "apoint",
    "reserv", "reserf", "arrang", "aranje", "orginize", "organizze", "plan for", 
    # Broken English
    "make time", "get time", "doctor when", "when doctor", "fix time", "put time", 
    "doctor see me", "come clinic", "come when", "i come when", "time book", "time fix", 
    "me come", "i come", "want come", "me want time", "clinic when", "clinic time",
    # Shortened/Concatenated
    "booktime", "bookdr", "bookdoc", "gettime", "getslot", "makeappt", "fixappt", 
    "whenvisit", "whencome", "bookin", "appttime", "bookvisit", "visittime"
]

# Intent expression phrases - require one of these for genuine intent
INTENT_EXPRESSION_PHRASES = [
    # Original terms
    "i want", "i need", "i would like", "i'd like", "can i", "could i",
    "looking to", "trying to", "hoping to", "wish to", "interested in",
    "planning to", "thinking about", "considering", "wondering if", "may i",
    "please book", "please schedule", "help me book", "help me schedule",
    "i am looking", "i am hoping", "i'm interested", "i'm planning",
    # Misspellings
    "i wnat", "i ned", "i woud like", "i'd liek", "can i", "culd i", "cud i",
    "lukng to", "tryng to", "hopng to", "interestd in", "intrested", "planng to",
    # Broken English
    "me want", "want to", "need to", "like to", "me need", "me like", "me hope",
    "me try", "me book", "me schedule", "i try", "me interest", "me thinking",
    "please help", "want book", "need book", "want schedule", "need schedule",
    # Shortened/Casual
    "wanna", "gonna", "gotta", "need2", "want2", "like2", "tryna", "lemme", 
    "pls", "plz", "hlp me", "i'd lv", "i wnt", "i nd"
]


# Phrases that indicate a question rather than booking intent
NON_BOOKING_PHRASES = [
    # Original terms
    "how much", "cost", "price", "pricing", "fee", "fees",
    "how much is", "how much are", "price of", "cost of", "fees for", 
    "pricing for", "what is the price", "what is the cost",
    "what are the prices", "what are the costs", "charge", "charges",
    "information about", "info on", "tell me about",
    "what is", "what's", "what are", "how is", "how are",
    "explain", "describe", "details on", "learn about",
    "do you offer", "do you have", "do you provide",
    "wondering about", "curious about", "interested in learning",
    "can you tell me if", "discount", "promotion", "special offer",
    "package price", "compare", "versus", "vs", "better",
    # Misspellings
    "hw much", "howmuch", "kost", "prise", "pricing", "priceing", "fe", "fes",
    "informasion", "info abt", "tel me about", "wat is", "wats", "wat r", "hw is",
    "explaine", "explan", "detales", "lern about", "lern abt",
    # Broken English
    "money how", "pay how", "how pay", "cost how", "price how", "tell price", 
    "tell cost", "money need", "pay need", "info give", "tell about", "say about",
    "what mean", "how work", "clinic have", "clinic give", "you have", "you give",
    # Question forms
    "how do", "can you", "would you", "is there", "are there", "do i need",
    "should i", "when is", "where is", "which is", "why is", "who is"
]

# Reschedule intent phrases
RESCHEDULE_INTENT_PHRASES = [
    # Original terms
    "reschedule", "change appointment", "modify appointment", "move appointment",
    "adjust appointment", "switch appointment", "update appointment", "postpone",
    "change the date", "change the time", "different date", "different time",
    "need to change", "want to change", "would like to reschedule", "need to reschedule",
    "shift appointment", "need new time", "can't make it", "alternative time",
    "move to another day", "different day", "delay appointment", "bring forward",
    # Misspellings
    "reshedule", "reskhedule", "reshudule", "chaneg appointment", "chang appt", 
    "modifie appt", "moove appt", "ajust appt", "swithc appt", "updaet appt", 
    "postponn", "diferent date", "diferent time", "deferent day",
    # Broken English
    "change time", "new time", "other time", "move time", "no this time", 
    "time no good", "date no good", "change day", "move day", "other day",
    "later time", "early time", "not come this time", "come other time",
    # Shortened/Concatenated
    "movappt", "changetime", "newtime", "otherday", "othertime", "notthisday", 
    "reschedul", "resch", "moveappt", "changeappt", "switchtime", "diffday"
]


# View appointments intent phrases 
VIEW_APPOINTMENTS_INTENT_PHRASES = [
    # Original terms
    "can i view my appointments", "can i see my appointments",
    "view appointment", "see appointment", "check appointment", "my appointment",
    "view bookings", "see bookings", "check bookings", "my bookings",
    "view schedule", "see schedule", "check schedule", "my schedule",
    "list appointment", "show appointment", "upcoming appointment",
    "appointment status", "booking status",
    "when is my next", "what appointments do I have", "appointment details",
    "show my schedule", "display appointments", "what have I booked",
    # Misspellings
    "veiw appointment", "veiw appt", "se appt", "chek appt", "mi appt",
    "veiw booking", "se booking", "chek booking", "mi booking",
    "veiw skedule", "se schedule", "chek skedule", "mi schedule",
    "upcoming appt", "appt status", "booking statuts", "wen is my next",
    # Broken English
    "my time when", "when my time", "i come when", "my day what", "what day i come",
    "i book what", "what i book", "see my book", "my booking what", "tell my time",
    "what time i have", "i have what time", "show time", "show booking", "show what i book",
    # Shortened/Concatenated
    "myappt", "mybook", "myappts", "myappttime", "whencome", "whatbooked", 
    "nextappt", "scheduleview", "viewappt", "seeappt", "checkappt"
]


CANCEL_INTENT_PHRASES = [
    # Original terms
    "cancel", "delete", "remove", "cancel appointment", "delete appointment",
    "cancel my appointment", "delete my appointment", "remove my appointment",
    "no longer need", "don't need", "can't attend", "unable to attend",
    "want to cancel", "would like to cancel", "need to cancel",
    "stop appointment", "terminate appointment", "want to skip", "no longer want",
    "withdraw booking", "drop my appointment", "forget about my appointment",
    # Misspellings
    "cancle", "cancell", "delet", "deleet", "cansel", "cancl", "canc", "dlete",
    "remov", "remuv", "cancl appt", "delet appt", "remov appt", "cancl my appt",
    "dont need", "dont ned", "cant attend", "can't atend", "unabl to atend",
    # Broken English
    "no come", "not come", "stop come", "no want come", "no need appointment",
    "appointment no", "no appointment", "remove time", "time remove", "no want time",
    "cancel time", "stop time", "finish appointment", "end appointment", "appointment end",
    # Shortened/Concatenated
    "cancelappt", "delappt", "removappt", "notcoming", "stopappt", "endappt",
    "notneed", "notattend", "noshow", "cancelbook", "deletebook", "byeappt"
]


def get_treatment_code(text):
    """Returns the standardized treatment code for mentioned treatment."""
    text_lower = text.lower()
    for treatment_code, variations in TREATMENT_TYPES.items():
        for variation in variations:
            if variation in text_lower:
                return treatment_code
    return None

def has_booking_intent(text):
    """
    Determines if text has a genuine booking intent, requiring:
    1. A booking intent phrase
    2. An intent expression phrase ("I want to", "Can I", etc.)
    3. NOT containing non-booking phrases (questions, info requests)
    """
    text_lower = text.lower()
    
    # First check if any non-booking phrase is present - exit early if found
    is_question = any(phrase in text_lower for phrase in NON_BOOKING_PHRASES)
    if is_question:
        return False
        
    # Check if any booking intent phrase is present
    has_intent_phrase = any(phrase in text_lower for phrase in BOOKING_INTENT_PHRASES)
    
    # Check if any intent expression is present
    has_expression = any(expr in text_lower for expr in INTENT_EXPRESSION_PHRASES)
    
    # Return True only if it has booking intent phrase AND intent expression
    return has_intent_phrase and has_expression


def is_price_inquiry(text):
    """Determines if text is asking about prices"""
    text_lower = text.lower()
    price_terms = ["price", "cost", "fee", "how much", "charges", "pricing"]
    return any(term in text_lower for term in price_terms)


def has_reschedule_intent(text):
    """Determines if text has a reschedule intent"""
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in RESCHEDULE_INTENT_PHRASES)

def has_view_appointments_intent(text):
    """Determines if text has a view appointments intent"""
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in VIEW_APPOINTMENTS_INTENT_PHRASES)

def has_cancel_intent(text):
    """Determines if text has a cancel intent"""
    text_lower = text.lower()
    return any(phrase in text_lower for phrase in CANCEL_INTENT_PHRASES)

def extract_intent(text):
    """
    Extracts the primary intent from the message
    Returns a tuple of (intent_type, treatment_code)
    """
    text_lower = text.lower()
    
    # Extract treatment code if present
    treatment_code = get_treatment_code(text_lower)
    
    # First check if it's a price inquiry
    if is_price_inquiry(text_lower):
        return "info", treatment_code
        
    # Check for various intents
    if has_booking_intent(text_lower) and treatment_code:
        return "booking", treatment_code
    elif has_reschedule_intent(text_lower):
        return "reschedule", None
    elif has_view_appointments_intent(text_lower):
        return "view", None
    elif has_cancel_intent(text_lower):
        return "cancel", None
    elif treatment_code:
        # Treatment mentioned but no booking intent
        return "info", treatment_code
    else:
        return None, None
