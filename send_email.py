import os
import json
import smtplib
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

# ============================
# CONFIGURATION & PATHS
# ============================
PROJECT_ROOT = Path(__file__).resolve().parent
JSON_INPUT = PROJECT_ROOT / "docs" / "data" / "daily_brief.json"

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")  # Expected: "email1@me.com, email2@me.com"

# ============================
# HTML GENERATOR
# ============================

def build_html_body(data):
    """Converts JSON brief data into a clean HTML email."""
    date_str = data.get("date", datetime.now().strftime("%B %d, %Y"))
    stories = data.get("top_stories", [])
    
    html = f"""
    <html>
    <body style="font-family: Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: auto;">
        <h2 style="color: #2c3e50; border-bottom: 2px solid #eee; padding-bottom: 10px;">
            Daily AI Executive Brief
        </h2>
        <p style="color: #7f8c8d; font-size: 0.9em;">{date_str}</p>
    """
    
    for item in stories:
        html += f"""
        <div style="margin-bottom: 30px; padding: 15px; border-left: 4px solid #3498db; background: #f9f9f9;">
            <h3 style="margin-top: 0; color: #2980b9;">{item.get('rank', '•')}. {item['title']}</h3>
            <p><strong>Summary:</strong> {item['summary']}</p>
            <p><strong>Technical Takeaway:</strong> {item['technical_takeaway']}</p>
            <p style="color: #c0392b;"><strong>Primary Risk:</strong> {item['primary_risk']}</p>
            <p style="color: #27ae60;"><strong>Opportunity:</strong> {item['primary_opportunity']}</p>
            <p><a href="{item['url']}" style="color: #3498db; text-decoration: none;">Read source article ({item['source']}) &rarr;</a></p>
        </div>
        """
    
    html += """
        <footer style="margin-top: 20px; font-size: 0.8em; color: #bdc3c7; text-align: center;">
            Sent via Automated AI Pipeline
        </footer>
    </body>
    </html>
    """
    return html

# ============================
# MAIN SENDER
# ============================

def send_email():
    if not EMAIL_USER or not EMAIL_PASS or not EMAIL_TO:
        print(" ERROR: Missing EMAIL_USER / EMAIL_PASS / EMAIL_TO environment variables.")
        return

    if not JSON_INPUT.exists():
        print(f" ERROR: {JSON_INPUT} not found. Run format_brief.py first.")
        return

    # Load the JSON data
    with open(JSON_INPUT, "r", encoding="utf-8") as f:
        brief_data = json.load(f)

    # RECIPIENT HANDLING: Split the comma-separated string into a clean list
    recipients = [email.strip() for email in EMAIL_TO.split(",")]
    
    subject = f"Daily AI Executive Brief – {brief_data.get('date')}"
    html_content = build_html_body(brief_data)

    msg = MIMEMultipart("alternative")
    msg["From"] = f"AI Briefing Service <{EMAIL_USER}>"
    # The 'To' header expects a single string of comma-separated emails
    msg["To"] = ", ".join(recipients) 
    msg["Subject"] = subject

    msg.attach(MIMEText(html_content, "html"))

    try:
        # Using SMTP_SSL for enhanced security on port 465
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            # Use to_addrs to ensure the server delivers to the full list
            server.send_message(msg, to_addrs=recipients)
        print(f"📧 Success: Email sent to {len(recipients)} recipients.")
    except Exception as e:
        print(f" Failed to send email: {e}")

if __name__ == "__main__":
    send_email()