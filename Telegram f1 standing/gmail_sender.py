import os
import yagmail

def send_email(subject, content):
    try:
        gmail_user = os.getenv('GMAIL_USER')
        gmail_password = os.getenv('GMAIL_APP_PASSWORD')
        recipient = os.getenv('RECIPIENT_EMAIL')
        
        yag = yagmail.SMTP(gmail_user, gmail_password)
        yag.send(
            to=recipient,
            subject=subject,
            contents=content
        )
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False