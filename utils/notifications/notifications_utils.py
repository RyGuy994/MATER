#src/utils/notifcations/notifcations_utils.py
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import current_app
from twilio.rest import Client

def send_email_notification(to_email, subject, message_body):
    """
    Send an email notification using SMTP.
    """
    try:
        smtp_server = os.getenv("SMTP_SERVER")
        smtp_port = int(os.getenv("SMTP_PORT", 587))
        smtp_user = os.getenv("SMTP_USER")
        smtp_password = os.getenv("SMTP_PASSWORD")
        from_email = os.getenv("SMTP_FROM_EMAIL")

        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = from_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message_body, 'plain'))

        # Connect to the SMTP server and send the email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Secure the connection
            server.login(smtp_user, smtp_password)
            server.send_message(msg)

        return True
    except Exception as e:
        current_app.logger.error(f"Error sending email: {e}")
        return False

def send_sms_notification(to_number, message_body):
    """
    Send an SMS notification using Twilio.
    """
    try:
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        from_number = os.getenv("TWILIO_FROM_NUMBER")

        client = Client(account_sid, auth_token)
        message = client.messages.create(
            body=message_body,
            from_=from_number,
            to=to_number
        )

        return message.sid
    except Exception as e:
        current_app.logger.error(f"Error sending SMS: {e}")
        return None

def format_notification_message(template, **kwargs):
    """
    Format a notification message using a template.
    """
    try:
        return template.format(**kwargs)
    except KeyError as e:
        current_app.logger.error(f"Missing template key: {e}")
        return None

def send_user_mfa_notification(user, mfa_method):
    """
    Send a notification to the user about their MFA setup or verification.
    """
    message_body = f"Your {mfa_method} method has been updated successfully."
    if user.email:
        send_email_notification(user.email, "MFA Update", message_body)
    if user.phone_number:
        send_sms_notification(user.phone_number, message_body)
