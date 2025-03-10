# Meowkies WhatsApp Customer Support Bot

This project implements a WhatsApp chatbot for Meow Aesthetic Clinic, powered by Gemini API. It provides customer support and information to users via WhatsApp.

## Prerequisites

Before you begin, ensure you have the following:

  * **Python 3.6+:** Python is required to run the Flask application.
  * **Meta Developer Account:** You'll need a Meta Developer account with a WhatsApp Business product linked to a verified WhatsApp Business Account.
  * **Gemini API Key:** Obtain a Gemini API key from the Google Cloud Platform.
  * **ngrok:** ngrok is used to expose your local Flask server to the internet.

## Setup

### 1\. Clone the Repository

Clone this repository to your local machine:

```bash
git clone <repository_url>
cd <repository_directory>
```

### 2\. Create a Virtual Environment (Recommended)

It's best practice to use a virtual environment to manage dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate  # On macOS/Linux
.venv\Scripts\activate  # On Windows
```

### 3\. Install Dependencies

Install the required Python packages:

```bash
pip install -r requirements.txt
```

(If you don't have a `requirements.txt` file, create one with `pip freeze > requirements.txt` after manually installing `flask requests python-dotenv` and `logging`)

### 4\. Configure Environment Variables

Create a `.env` file in the project root directory and add your API keys and tokens:

```
WHATSAPP_PHONE_NUMBER_ID=YOUR_WHATSAPP_PHONE_NUMBER_ID
WHATSAPP_API_TOKEN=YOUR_WHATSAPP_API_TOKEN
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
VERIFY_TOKEN=YOUR_VERIFY_TOKEN
```

Replace the placeholder values with your actual credentials.

### 5\. Run the Flask Application

Start the Flask application:

```bash
python app.py
```

The app will run on `http://127.0.0.1:5000` (or the port specified in your `.env` file).

### 6\. Set Up ngrok

1.  **Download ngrok:** Download ngrok from [ngrok.com](https://www.google.com/url?sa=E&source=gmail&q=https://ngrok.com/download).

2.  **Run ngrok:** Open a new terminal window and run:

    ```bash
    ngrok http 5000
    ```

    (Replace `5000` with your Flask app's port if necessary.)

3.  **Copy the HTTPS URL:** ngrok will provide a public HTTPS URL. Copy this URL.

### 7\. Configure Meta Developer Webhook

1.  **Go to Meta for Developers:** Log in to your Meta Developer account and navigate to your app.
2.  **WhatsApp Configuration:** Go to "WhatsApp" -\> "Configuration."
3.  **Webhook Settings:** In the "Webhook" section, click "Edit."
4.  **Callback URL:** Paste the ngrok HTTPS URL into the "Callback URL" field. Append `/webhook` to the end (e.g., `https://your-ngrok-url.ngrok-free.app/webhook`).
5.  **Verify Token:** Enter the `VERIFY_TOKEN` from your `.env` file.
6.  **Verify and Save:** Click "Verify and Save."
7.  **Subscribe to Fields:** Subscribe to the `messages` field.

### 8\. Test the Chatbot

1.  Send a message to your WhatsApp Business number.
2.  Observe the response from your chatbot.
3.  Check the Flask app's console for logs and potential errors.

## Important Notes

  * **Security:** Never commit your `.env` file to version control.
  * **Production:** For production, use a permanent access token and a proper web server.
  * **Error Handling:** The code includes error handling and logging. Monitor the logs for issues.
  * **Context:** The `MEOWKIES_CONTEXT` variable provides the chatbot with the necessary information about Meow Aesthetic Clinic.

## Health Check

To check the health of your service, you can use the `/health` endpoint. It will return a JSON object with the status of your service and the configuration of your WhatsApp and Gemini integrations.

```bash
curl http://127.0.0.1:5000/health
```

## Logging

The application uses Python's `logging` module to log important events and errors. Logs are output to the console.