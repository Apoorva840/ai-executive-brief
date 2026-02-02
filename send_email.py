import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# =========================
# ENV VARIABLES (FROM GITHUB SECRETS)
# =========================
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")  # comma-separated

HTML_FILE = os.path.join("site", "index.html")

def send_email():
    if not EMAIL_USER or not EMAIL_PASS or not EMAIL_TO:
        raise ValueError("Missing EMAIL_USER / EMAIL_PASS / EMAIL_TO")

    if not os.path.exists(HTML_FILE):
        raise FileNotFoundError(f"{HTML_FILE} not found")

    recipients = [email.strip() for email in EMAIL_TO.split(",")]

    with open(HTML_FILE, "r", encoding="utf-8") as f:
        html_content = f.read()

    today = datetime.now().strftime("%d %b %Y")
    subject = f"Daily AI Executive Brief – {today}"

    msg = MIMEMultipart("alternative")
    msg["From"] = EMAIL_USER
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject

    msg.attach(MIMEText(html_content, "html"))

    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASS)
        server.send_message(msg)

    print(f"📧 Email sent to: {', '.join(recipients)}")

if __name__ == "__main__":
    send_email()
