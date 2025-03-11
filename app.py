from flask import Flask, request, jsonify, abort
import requests
import json
import os
import logging
from dotenv import load_dotenv
from datetime import datetime, timedelta

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
- We offer a full suite of treatments including:
  * Medical facials
  * Machine-based treatments like lasers
  * Injectables such as Botox and fillers
  * Scientifically proven, evidence-based protocols
- Dr. Meow has a special interest in anti-aging medicine
- We take a holistic, multi-pronged approach to delaying and reversing skin aging
- Dr. Meow believes in combining personalized skincare, advanced lasers, heat-based machines, and injectables
- Dr. Meow's philosophy: "Every patient deserves our utmost care"

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
RATE_LIMIT_WINDOW = 60  # seconds
MAX_MESSAGES_PER_WINDOW = 5
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
                warning_message = ("Whoa there, fur-get about spamming! "
                                   "You're sending messages too quickly. Please slow down and try again in a minute.")
                logger.warning(f"Rate limit exceeded for {customer_number}. Sending warning message.")
                send_whatsapp_message(customer_number, warning_message)
                return jsonify({"status": "error", "message": "Rate limit exceeded"}), 200
            
            # Get response from Gemini with conversation history
            gemini_response = get_gemini_response(customer_number, customer_message)
            
            if "error" in gemini_response:
                error_message = gemini_response["error"]
                logger.error(f"Error getting Gemini response: {error_message}")
                fallback_message = ("I'm having trouble processing your request right meow. "
                                    "Please try again later or call our clinic directly at 87713358 during our operating hours (Mon-Fri: 11am-8pm, Sat: 11am-10pm). "
                                    "Purr-fectly yours, Meowkies 🐾")
                send_whatsapp_message(customer_number, fallback_message)
                add_message_to_conversation(customer_number, "assistant", fallback_message)
                return jsonify({"status": "error", "message": error_message}), 200
            
            gemini_text_response = gemini_response.get("text", "")
            if not gemini_text_response:
                logger.error("Empty response text from Gemini")
                fallback_message = ("I apologize for the inconvenience, but I'm having trouble responding to your message right meow. "
                                    "Please try again later or contact our clinic directly at 87713358 during our operating hours (Mon-Fri: 11am-8pm, Sat: 11am-10pm). "
                                    "Purr-fectly yours, Meowkies 🐾")
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

if __name__ == "__main__":
    logger.info("Starting Meowkies WhatsApp Customer Support Chatbot")
    app.run(debug=False, host="0.0.0.0", port=int(os.getenv("PORT", 8080)))