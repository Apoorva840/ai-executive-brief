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
JARGON_INPUT = PROJECT_ROOT / "docs" / "data" / "jargon_buster.json"

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")

# ============================
# HTML GENERATOR
# ============================
def build_html_body(data, jargon_data):
    date_str = data.get("date", datetime.now().strftime("%B %d, %Y"))
    stories = data.get("top_stories", [])
    microsite_url = "https://Apoorva840.github.io/ai-executive-brief/"
    
    html = f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; color: #333; line-height: 1.6; max-width: 600px; margin: auto; padding: 20px; background-color: #f9fafb;">
        <h2 style="color: #0f172a; border-bottom: 3px solid #3498db; padding-bottom: 10px; margin-bottom: 0;">
            Daily AI Executive Brief
        </h2>
        <p style="color: #64748b; font-size: 0.9em; margin-top: 5px;">{date_str} | <a href="{microsite_url}" style="color: #3498db; text-decoration: none;">View Archive Online</a></p>
    """

    # --- JARGON SECTION: ONLY RENDERS ON SATURDAY (OR IF ACTIVE) ---
    if jargon_data and jargon_data.get("is_weekly_active") is True:
        html += f"""
        <div style="margin: 25px 0; padding: 20px; background-color: #f5f3ff; border: 1px solid #8b5cf6; border-radius: 12px;">
            <h3 style="margin-top: 0; color: #7c3aed; font-size: 1.1em;">🎓 Weekly Jargon Decoder</h3>
            <p style="font-size: 0.85em; color: #5b21b6; margin-bottom: 15px;">Mastering this week's technical AI concepts.</p>
        """
        for item in jargon_data.get("terms", []):
            html += f"""
            <div style="margin-bottom: 15px; border-bottom: 1px solid #ddd; padding-bottom: 10px;">
                <p style="margin: 0; font-weight: bold; color: #1e1b4b;">{item['term']}</p>
                <p style="margin: 5px 0; font-size: 0.9em; color: #374151;">{item['definition']}</p>
                <p style="margin: 0; font-size: 0.85em; font-style: italic; color: #6b7280;">🚗 Analogy: {item['analogy']}</p>
            </div>
            """
        html += "</div>"

    # --- DAILY STORIES SECTION ---
    for item in stories:
        audience_tags = ""
        if item.get("who_should_care"):
            roles = ", ".join(item["who_should_care"])
            audience_tags = f"<p style='font-size: 0.8em; color: #7c3aed; margin-top: 10px;'><strong>Relevant for:</strong> {roles}</p>"

        summary_display = item.get('summary', 'Review the technical source for full details.')

        html += f"""
        <div style="margin-bottom: 30px; padding: 25px; border-radius: 12px; border: 1px solid #e5e7eb; background: #ffffff; box-shadow: 0 2px 4px rgba(0,0,0,0.02);">
            <h3 style="margin-top: 0; color: #1e40af; font-size: 1.25em;">{item.get('rank', '•')}. {item['title']}</h3>
            <p style="font-size: 0.95em; color: #374151;">{summary_display}</p>
            
            <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #0f172a; margin: 15px 0;">
                <p style="margin: 5px 0; font-size: 0.9em;"><strong style="color: #0f172a;">💡 Technical Takeaway:</strong> {item.get('technical_takeaway', 'See archive for analysis.')}</p>
                <p style="margin: 5px 0; font-size: 0.9em;"><strong style="color: #b91c1c;">⚖️ Primary Risk:</strong> {item.get('primary_risk', 'Standard risks apply.')}</p>
                <p style="margin: 5px 0; font-size: 0.9em;"><strong style="color: #15803d;">🚀 Opportunity:</strong> {item.get('primary_opportunity', 'Incremental gains.')}</p>
            </div>
            {audience_tags}
            <p style="margin-top: 20px;"><a href="{item['url']}" style="background-color: #2563eb; color: white; padding: 10px 18px; text-decoration: none; border-radius: 6px; font-size: 0.85em; font-weight: bold; display: inline-block;">Read Source ({item.get('source', 'Link')}) &rarr;</a></p>
        </div>
        """
    
    html += f"""
        <div style="margin-top: 40px; padding: 30px; text-align: center; background-color: #0f172a; border-radius: 12px; color: #ffffff;">
            <p style="margin-bottom: 15px; font-weight: bold;">Deepen your AI strategy online</p>
            <a href="{microsite_url}" style="background-color: #ffffff; color: #0f172a; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">
                Full Web Archive
            </a>
            <p style="margin-top: 25px; font-size: 0.7em; opacity: 0.6; border-top: 1px solid rgba(255,255,255,0.1); padding-top: 15px;">
                Generated by Gemini AI Pipeline • Internship Project A<br>
                © 2026 AI Executive Brief
            </p>
        </div>
    </body>
    </html>
    """
    return html

def send_email():
    if not EMAIL_USER or not EMAIL_PASS or not EMAIL_TO:
        print(" ERROR: Missing EMAIL environment variables.")
        return

    # Load Daily Brief Data
    if not JSON_INPUT.exists():
        print(f" ERROR: {JSON_INPUT} not found.")
        return
    with open(JSON_INPUT, "r", encoding="utf-8") as f:
        brief_data = json.load(f)

    # Load Jargon Data (Handles the Saturday logic)
    jargon_data = None
    if JARGON_INPUT.exists():
        with open(JARGON_INPUT, "r", encoding="utf-8") as f:
            jargon_data = json.load(f)

    recipients = [e.strip() for e in EMAIL_TO.split(",")]
    subject = f"AI Executive Brief: {len(brief_data.get('top_stories', []))} Insights for {brief_data.get('date')}"
    html_content = build_html_body(brief_data, jargon_data)

    msg = MIMEMultipart("alternative")
    msg["From"] = f"AI Briefing <{EMAIL_USER}>"
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print(f"📧 Success: Email sent to {len(recipients)} recipients.")
    except Exception as e:
        print(f" Failed to send email: {e}")

if __name__ == "__main__":
    send_email()