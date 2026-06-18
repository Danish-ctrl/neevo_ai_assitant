import smtplib
from email.message import EmailMessage
import sys
import os

# Add the parent directory to the path so we can import config.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import GMAIL_ADDRESS, GMAIL_APP_PASSWORD

def send_email(to_email: str, subject: str, body: str) -> str:
    """Sends an email securely using Gmail's SMTP server."""
    if not GMAIL_ADDRESS or not GMAIL_APP_PASSWORD:
        return "Error: Gmail credentials are missing in config.py."

    try:
        # Construct the email message
        msg = EmailMessage()
        msg.set_content(body)
        msg['Subject'] = subject
        msg['From'] = GMAIL_ADDRESS
        msg['To'] = to_email

        # Connect to Gmail's secure outgoing server
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        
        # Send and close
        server.send_message(msg)
        server.quit()

        return f"Success: Email sent to {to_email} with subject '{subject}'."

    except smtplib.SMTPAuthenticationError:
        return "Error: Gmail Authentication failed. Check your App Password."
    except Exception as e:
        return f"Error: Failed to send email. Details: {e}"

# Quick Testing Routine
if __name__ == "__main__":
    print("Testing Gmail Tool...")
    # Put your own email address here to test sending an email to yourself!
    test_recipient = "mohammeddanish.reza1@gmail.com" 
    
    result = send_email(
        to_email=test_recipient,
        subject="Agent Hub Initialization",
        body="Hello! This is a test message from your new AI Voice Hub. The Gmail Tool is fully operational."
    )
    print(result)