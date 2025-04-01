import logging
from datetime import datetime, timedelta
import re

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def normalize_time_format(time_str):
    """
    Normalize time strings to a standard 24-hour format (HH:MM)
    
    Args:
        time_str (str): Time string in various formats (e.g., "2:30 PM", "14:30", "2:00", "4.30pm")
        
    Returns:
        str: Normalized time in "HH:MM" format, or None if parsing fails
    """
    if not time_str:
        return None
        
    time_str = time_str.strip().upper()
    logger.debug(f"Normalizing time string: {time_str}")
    
    # Handle 24-hour format with colon (14:30)
    if ":" in time_str and ("AM" not in time_str) and ("PM" not in time_str):
        try:
            hour_str, minute_str = time_str.split(":")
            hour = int(hour_str)
            minute = int(minute_str)
            
            # Validate hour and minute
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return f"{hour:02d}:{minute:02d}"
            else:
                logger.warning(f"Invalid hour or minute values in 24-hour time: {time_str}")
                return None
        except ValueError:
            logger.warning(f"Failed to parse 24-hour time with colon: {time_str}")
            # Continue to other patterns
    
    # Handle 24-hour format with period (14.30)
    if "." in time_str and ("AM" not in time_str) and ("PM" not in time_str):
        try:
            hour_str, minute_str = time_str.split(".")
            hour = int(hour_str)
            minute = int(minute_str)
            
            # Validate hour and minute
            if 0 <= hour <= 23 and 0 <= minute <= 59:
                return f"{hour:02d}:{minute:02d}"
            else:
                logger.warning(f"Invalid hour or minute values in 24-hour time with period: {time_str}")
                return None
        except ValueError:
            logger.warning(f"Failed to parse 24-hour time with period: {time_str}")
            # Continue to other patterns

    # Handle 12-hour format with AM/PM
    # In the 12-hour format with AM/PM section of normalize_time_format()
    try:
        import re
        
        # Modified pattern using character class for simpler matching
        # This explicitly matches both period and colon as separators
        pattern = r"(\d{1,2})[:\.](\d{1,2})(?:\s*)([AaPp][Mm])"
        match = re.search(pattern, time_str)
        
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            am_pm = match.group(3).upper()
            
            # Validate hour and minute
            if not (1 <= hour <= 12 and 0 <= minute <= 59):
                logger.warning(f"Invalid hour or minute values in 12-hour time: {time_str}")
                return None
            
            # Convert to 24-hour format
            if am_pm == "PM" and hour < 12:
                hour += 12
            elif am_pm == "AM" and hour == 12:
                hour = 0
                
            return f"{hour:02d}:{minute:02d}"

            
        # Match just hours with AM/PM (like 4PM, 4 PM)
        pattern = r"(\d{1,2})(?:\s*)([AaPp][Mm])"
        match = re.search(pattern, time_str)
        
        if match:
            hour = int(match.group(1))
            am_pm = match.group(2).upper()
            
            # Validate hour
            if not (1 <= hour <= 12):
                logger.warning(f"Invalid hour value in 12-hour time without minutes: {time_str}")
                return None
                
            # Convert to 24-hour format
            if am_pm == "PM" and hour < 12:
                hour += 12
            elif am_pm == "AM" and hour == 12:
                hour = 0
            
            return f"{hour:02d}:00"
    except Exception as e:
        logger.warning(f"Failed to parse 12-hour time: {time_str}, Error: {str(e)}")
        # Continue to other patterns

    # Handle simple hour formats without AM/PM (assume during business hours)
    try:
        import re
        # Match patterns like: "2", "14"
        pattern = r"^(\d{1,2})$"
        match = re.search(pattern, time_str)
        
        if match:
            hour = int(match.group(1))
            
            # Validate and interpret the hour
            if 0 <= hour <= 23:
                return f"{hour:02d}:00"
            else:
                logger.warning(f"Invalid hour value in simple time: {time_str}")
                return None
    except Exception as e:
        logger.warning(f"Failed to parse simple hour: {time_str}, Error: {str(e)}")
        
    logger.warning(f"Failed to parse time: {time_str} - no patterns matched")
    return None

def format_time_for_display(time_str):
    """
    Format time strings for display to users in a user-friendly format
    
    Args:
        time_str (str): Time string in various formats
        
    Returns:
        str: Time formatted as "h:MM AM/PM"
    """
    # First normalize to 24-hour format
    normalized = normalize_time_format(time_str)
    if not normalized:
        return time_str
    
    try:
        # Parse the normalized time (should be in HH:MM format)
        hour, minute = map(int, normalized.split(":"))
        
        # Convert to 12-hour format
        am_pm = "AM" if hour < 12 else "PM"
        hour = hour if 1 <= hour <= 12 else hour - 12 if hour > 12 else 12
        
        return f"{hour}:{minute:02d} {am_pm}"
    except Exception as e:
        logger.warning(f"Failed to format time for display: {time_str}, Error: {str(e)}")
    return time_str

def parse_natural_language_date(date_str):
    """
    Parse natural language date expressions into a datetime.date object.
    Supports multiple date formats and natural language expressions.
    
    Args:
        date_str (str): Natural language date like "tomorrow", "next Monday", etc.
                        or formatted date in various formats
    Returns:
        datetime.date or None: The parsed date or None if parsing failed
    """
    if not date_str:
        return None
        
    date_str = date_str.lower().strip()
    today = datetime.now().date()
    
    # Handle common natural language expressions
    natural_language_mapping = {
        "today": today,
        "tomorrow": today + timedelta(days=1),
        "day after tomorrow": today + timedelta(days=2),
        "the day after tomorrow": today + timedelta(days=2),
        "next week": today + timedelta(days=7),
    }
    
    if date_str in natural_language_mapping:
        return natural_language_mapping[date_str]
    
    # Try various date formats
    date_formats = [
        "%d-%m-%Y",  # DD-MM-YYYY (prioritize this format)
        "%Y-%m-%d",  # YYYY-MM-DD
        "%d/%m/%Y",  # DD/MM/YYYY
        "%m/%d/%Y",  # MM/DD/YYYY (US format)
        "%d.%m.%Y",  # DD.MM.YYYY
        "%Y.%m.%d",  # YYYY.MM.DD
    ]
    
    for fmt in date_formats:
        try:
            parsed_date = datetime.strptime(date_str, fmt).date()
            return parsed_date
        except ValueError:
            continue
    
    # Could not parse with any format
    logger.debug(f"Could not parse date: {date_str}")
    return None


def format_date_for_display(date_str):
    """
    Format a date string from YYYY-MM-DD to DD/MM/YYYY for display
    
    Args:
        date_str (str): Date in YYYY-MM-DD format
        
    Returns:
        str: Date in DD/MM/YYYY format
    """
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        return date_obj.strftime("%d/%m/%Y")
    except ValueError:
        return date_str  # Return as-is if parsing fails
