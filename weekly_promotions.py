import os
import logging
import json
import requests
from datetime import datetime, timedelta
import pytz
import time_utils
from dotenv import load_dotenv

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

class WeeklyPromotionScheduler:
    def __init__(self):
        self.recipients_file = "promotion_recipients.json"
        self.schedule_file = "promotion_schedule.json"
        self.sent_log_file = "sent_promotions.json"
        
        # Load recipient list, schedule, and sent log
        self.recipients = self._load_json(self.recipients_file, {"recipients": []})
        self.schedule = self._load_json(self.schedule_file, {"weekly_promotions": []})
        self.sent_log = self._load_json(self.sent_log_file, {"sent_promotions": []})

    def _load_json(self, filename, default_data):
        """Load data from JSON file, creating it if it doesn't exist"""
        try:
            if os.path.exists(filename):
                with open(filename, 'r') as file:
                    return json.load(file)
            else:
                with open(filename, 'w') as file:
                    json.dump(default_data, file, indent=4)
                return default_data
        except Exception as e:
            logger.error(f"Error loading {filename}: {str(e)}")
            return default_data

    def _save_json(self, filename, data):
        """Save data to JSON file"""
        try:
            with open(filename, 'w') as file:
                json.dump(data, file, indent=4)
            return True
        except Exception as e:
            logger.error(f"Error saving to {filename}: {str(e)}")
            return False

    def add_recipient(self, phone_number, name, preferences=None):
        """Add a new recipient to the promotion list"""
        if not preferences:
            preferences = {"opt_in": True, "categories": ["all"]}
        
        # Check if recipient already exists
        for recipient in self.recipients["recipients"]:
            if recipient["phone_number"] == phone_number:
                logger.info(f"Recipient {phone_number} already exists, updating information")
                recipient["name"] = name
                recipient["preferences"] = preferences
                recipient["updated_at"] = datetime.now(CLINIC_TIMEZONE).isoformat()
                self._save_json(self.recipients_file, self.recipients)
                return True
        
        # Add new recipient
        new_recipient = {
            "phone_number": phone_number,
            "name": name,
            "preferences": preferences,
            "created_at": datetime.now(CLINIC_TIMEZONE).isoformat(),
            "updated_at": datetime.now(CLINIC_TIMEZONE).isoformat()
        }
        self.recipients["recipients"].append(new_recipient)
        self._save_json(self.recipients_file, self.recipients)
        logger.info(f"Added new recipient: {phone_number} - {name}")
        return True

    def schedule_weekly_promotion(self, day_of_week, time, template_name, template_parameters):
        """
        Schedule a weekly promotion
        
        Args:
            day_of_week (int): Day of the week (0-6, where 0 is Monday)
            time (str): Time in format "HH:MM" or "H:MM AM/PM"
            template_name (str): Name of the approved WhatsApp template
            template_parameters (dict): Parameters for the template
        
        Returns:
            bool: Success or failure
        """
        if day_of_week < 0 or day_of_week > 6:
            logger.error(f"Invalid day of week: {day_of_week}. Must be 0-6.")
            return False
            
        # Normalize time format
        normalized_time = time_utils.normalize_time_format(time)
        if not normalized_time:
            logger.error(f"Invalid time format: {time}")
            return False
        
        # Create new schedule entry
        new_promotion = {
            "id": f"promo_{datetime.now().timestamp()}",
            "day_of_week": day_of_week,
            "time": normalized_time,
            "template_name": template_name,
            "template_parameters": template_parameters,
            "active": True,
            "created_at": datetime.now(CLINIC_TIMEZONE).isoformat()
        }
        
        self.schedule["weekly_promotions"].append(new_promotion)
        self._save_json(self.schedule_file, self.schedule)
        
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        logger.info(f"Scheduled weekly promotion for {day_names[day_of_week]} at {normalized_time} using template '{template_name}'")
        return True
    
    def check_and_send_promotions(self):
        """Check scheduled promotions and send if it's time"""
        current_time = datetime.now(CLINIC_TIMEZONE)
        current_day_of_week = current_time.weekday()  # 0-6 (Monday-Sunday)
        current_hour = current_time.hour
        current_minute = current_time.minute
        
        logger.info(f"Checking promotions for {current_time.strftime('%A %H:%M')}")
        
        for promo in self.schedule["weekly_promotions"]:
            if not promo.get("active", True):
                continue
                
            promo_day = promo["day_of_week"]
            promo_time_parts = promo["time"].split(":")
            promo_hour = int(promo_time_parts[0])
            promo_minute = int(promo_time_parts[1])
            
            # Check if it's time to send this promotion
            if (promo_day == current_day_of_week and 
                promo_hour == current_hour and 
                promo_minute == current_minute):
                
                logger.info(f"It's time to send promotion: {promo['id']}")
                
                # Send promotion to all eligible recipients
                for recipient in self.recipients["recipients"]:
                    if recipient.get("preferences", {}).get("opt_in", True):
                        self._send_promotion_to_recipient(promo, recipient)
                    
                # Log that we sent this promotion
                self._log_sent_promotion(promo, len(self.recipients["recipients"]))
    
    def _send_promotion_to_recipient(self, promotion, recipient):
        """Send a promotion to a specific recipient"""
        try:
            template_name = promotion["template_name"]
            template_parameters = promotion.get("template_parameters", {})
            
            # Prepare parameters list for WhatsApp API
            components = []
            
            # Add body parameters if any
            if "body_parameters" in template_parameters:
                body_params = []
                for param in template_parameters["body_parameters"]:
                    # Replace {{name}} with actual recipient name
                    if param == "{{name}}":
                        param = recipient.get("name", "Valued Customer")
                    
                    body_params.append({
                        "type": "text",
                        "text": param
                    })
                
                if body_params:
                    components.append({
                        "type": "body",
                        "parameters": body_params
                    })
            
            # Add header parameters if any
            if "header_parameters" in template_parameters:
                header_type = template_parameters.get("header_type", "text")
                header_param = {
                    "type": header_type
                }
                
                if header_type == "image":
                    header_param["image"] = {
                        "link": template_parameters["header_parameters"]
                    }
                elif header_type == "text":
                    header_param["text"] = template_parameters["header_parameters"]
                
                components.append({
                    "type": "header",
                    "parameters": [header_param]
                })
            
            # Send message via WhatsApp API
            headers = {
                "Authorization": f"Bearer {WHATSAPP_API_TOKEN}",
                "Content-Type": "application/json",
            }
            
            message_data = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": recipient["phone_number"],
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {
                        "code": "en_US"
                    }
                }
            }
            
            # Add components if present
            if components:
                message_data["template"]["components"] = components
            
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
            
            logger.info(f"Successfully sent promotion to {recipient['phone_number']}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending promotion: {str(e)}")
            return False
    
    def _log_sent_promotion(self, promotion, recipient_count):
        """Log a sent promotion"""
        sent_log_entry = {
            "promotion_id": promotion["id"],
            "template_name": promotion["template_name"],
            "sent_at": datetime.now(CLINIC_TIMEZONE).isoformat(),
            "recipient_count": recipient_count
        }
        
        self.sent_log["sent_promotions"].append(sent_log_entry)
        self._save_json(self.sent_log_file, self.sent_log)

def run_promotion_scheduler():
    """
    Run the promotion scheduler to check and send promotions.
    This function should be scheduled to run every minute.
    """
    scheduler = WeeklyPromotionScheduler()
    scheduler.check_and_send_promotions()

def create_weekly_promotion(day_of_week, time, template_name, template_parameters):
    """
    Create a new weekly promotion schedule
    
    Args:
        day_of_week (int): Day of the week (0-6, where 0 is Monday)
        time (str): Time in format "HH:MM" or "H:MM AM/PM"
        template_name (str): Name of the approved WhatsApp template
        template_parameters (dict): Parameters for the template
    
    Returns:
        bool: Success or failure
    """
    scheduler = WeeklyPromotionScheduler()
    return scheduler.schedule_weekly_promotion(
        day_of_week, time, template_name, template_parameters
    )

def add_promotion_recipient(phone_number, name, preferences=None):
    """
    Add a recipient to the promotion list
    
    Args:
        phone_number (str): The recipient's phone number
        name (str): The recipient's name
        preferences (dict): The recipient's preferences
    
    Returns:
        bool: Success or failure
    """
    scheduler = WeeklyPromotionScheduler()
    return scheduler.add_recipient(phone_number, name, preferences)

# Example of how to use this module
if __name__ == "__main__":
    # Example: Create a weekly promotion for Mondays at 10:00 AM
    create_weekly_promotion(
        day_of_week=0,  # Monday
        time="10:00 AM",
        template_name="weekly_special_offer",  # This should be an approved template name in WhatsApp
        template_parameters={
            "body_parameters": [
                "{{name}}",  # Will be replaced with recipient's name
                "20% off all facial treatments",
                "This week only"
            ],
            "header_type": "image",
            "header_parameters": "https://example.com/promotion-image.jpg"
        }
    )
    
    # Example: Add a recipient
    add_promotion_recipient(
        phone_number="6512345678",
        name="John Doe",
        preferences={
            "opt_in": True,
            "categories": ["facial", "botox"]
        }
    )
    
    # To run the scheduler (should be called by a cron job every minute)
    # run_promotion_scheduler()
