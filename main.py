from flask import Flask, request, jsonify
import requests
import json
import os
import logging
from dotenv import load_dotenv

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
You are Meowkies, the official customer support assistant for Meow Aesthetic Clinic, a medical aesthetic clinic founded by Dr. Meow.

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
- Use occasional cat-themed puns when appropriate, but don't overdo it (limit to one pun per message)
- Prioritize customer satisfaction and helpfulness
- Provide clear, concise information about services, pricing, and policies
- Avoid making specific promises about treatment results
- Maintain a positive, supportive attitude
- Address customers with respect and patience
- Emphasize our clinic's medical credentials and evidence-based approach
- Be knowledgeable about the differences between medical aesthetic clinics and beauty spas/salons
- Emphasize our commitment to medical ethics and scientifically-backed treatments
- Sign off with "Purr-fectly yours, Meowkies 🐾" when concluding a conversation (When the customer says bye, not every message)

If you don't know something specific or if the customer has a detailed medical question, suggest they contact the clinic directly at 87713358 to speak with our staff or schedule a consultation with Dr. Meow. Always be helpful but remember you cannot diagnose conditions or recommend specific treatments without a proper consultation.
"""

# --- Gemini API interaction ---
def get_gemini_response(message):
    try:
        headers = {
            "Content-Type": "application/json",
            "x-goog-api-key": GEMINI_API_KEY
        }
        
        # Create the full prompt with context
        contextual_prompt = f"{MEOWKIES_CONTEXT}\n\nCustomer message: {message}\n\nYour response as Meowkies:"
        
        data = {
            "contents": [{"parts": [{"text": contextual_prompt}]}]
        }
        
        logger.debug(f"Sending request to Gemini API with Meowkies context. Customer message: {message[:50]}...")
        response = requests.post(GEMINI_API_URL, headers=headers, json=data, timeout=30)
        
        if response.status_code != 200:
            logger.error(f"Gemini API error: Status {response.status_code}, Response: {response.text}")
            return {"error": f"Gemini API returned status code {response.status_code}"}
        
        response_data = response.json()
        logger.debug(f"Gemini API response received: {str(response_data)[:100]}...")
        return response_data
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
        
        # Check for Meta's challenge response
        if "object" in data and data.get("object") == "whatsapp_business_account":
            # Process entry array
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
            
            # Get response from Gemini
            gemini_response = get_gemini_response(customer_message)
            
            # Check for errors in Gemini response
            if "error" in gemini_response:
                error_message = gemini_response["error"]
                logger.error(f"Error getting Gemini response: {error_message}")
                
                # Send error message to user (optional)
                fallback_message = "I'm having trouble processing your request right meow. Please try again later or call our clinic directly at 87713358 during our operating hours (Mon-Fri: 11am-8pm, Sat: 11am-10pm). Purr-fectly yours, Meowkies 🐾"
                send_whatsapp_message(customer_number, fallback_message)
                
                return jsonify({"status": "error", "message": error_message}), 200
            
            # Extract text from Gemini response
            try:
                if "candidates" in gemini_response and gemini_response["candidates"]:
                    candidate = gemini_response["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"] and candidate["content"]["parts"]:
                        gemini_text_response = candidate["content"]["parts"][0]["text"]
                    else:
                        logger.error(f"Invalid Gemini response structure: {gemini_response}")
                        gemini_text_response = "I apologize for the inconvenience, but I'm having trouble responding to your message right meow. Please try again later or contact our clinic directly at 87713358 during our operating hours (Mon-Fri: 11am-8pm, Sat: 11am-10pm). Purr-fectly yours, Meowkies 🐾"
                else:
                    logger.error(f"No candidates in Gemini response: {gemini_response}")
                    gemini_text_response = "I apologize for the inconvenience, but I'm having trouble responding to your message right meow. Please try again later or contact our clinic directly at 87713358 during our operating hours (Mon-Fri: 11am-8pm, Sat: 11am-10pm). Purr-fectly yours, Meowkies 🐾"
            except Exception as e:
                logger.error(f"Error extracting text from Gemini response: {str(e)}")
                gemini_text_response = "I apologize for the inconvenience, but I'm having trouble responding to your message right meow. Please try again later or contact our clinic directly at 87713358 during our operating hours (Mon-Fri: 11am-8pm, Sat: 11am-10pm). Purr-fectly yours, Meowkies 🐾"
            
            # Send response via WhatsApp
            whatsapp_result = send_whatsapp_message(customer_number, gemini_text_response)
            
            # Check for errors in WhatsApp API response
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
            # Webhook verification
            verify_token = request.args.get("hub.verify_token")
            challenge = request.args.get("hub.challenge")
            
            logger.info(f"Received webhook verification request with token: {verify_token[:3]}...")
            
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
    """Simple endpoint to check if the service is running"""
    return jsonify({
        "status": "healthy",
        "whatsapp_configured": bool(WHATSAPP_PHONE_NUMBER_ID and WHATSAPP_API_TOKEN),
        "gemini_configured": bool(GEMINI_API_KEY),
        "bot_identity": "Meowkies - Meow Aesthetic Clinic Customer Support"
    })

if __name__ == "__main__":
    logger.info("Starting Meowkies WhatsApp Customer Support for Meow Aesthetic Clinic")
    app.run(debug=True, host="0.0.0.0", port=int(os.getenv("PORT", 5000)))