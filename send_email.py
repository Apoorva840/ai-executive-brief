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
LAB_INPUT = PROJECT_ROOT / "docs" / "data" / "lab_report.json"
TOOLBOX_INPUT = PROJECT_ROOT / "docs" / "data" / "toolbox.json" 

EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
EMAIL_TO = os.getenv("EMAIL_TO")

# ============================
# HTML GENERATOR
# ============================
def build_html_body(data, jargon_data, lab_data, toolbox_data):
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

    # --- JARGON SECTION (Updated for Business Value & Analogies) ---
    if jargon_data and jargon_data.get("terms"):
        html += f"""
        <div style="margin: 25px 0; padding: 20px; background-color: #f5f3ff; border: 1px solid #8b5cf6; border-radius: 12px;">
            <h3 style="margin-top: 0; color: #7c3aed; font-size: 1.1em;">🎓 Jargon Decoder</h3>
            <p style="font-size: 0.85em; color: #5b21b6; margin-bottom: 15px;">Mastering technical concepts.</p>
        """
        for item in jargon_data.get("terms", []):
            html += f"""
            <div style="margin-bottom: 15px; border-bottom: 1px solid #e9d5ff; padding-bottom: 10px;">
                <p style="margin: 0; font-weight: bold; color: #1e1b4b; font-size: 1.05em;">{item['term']}</p>
                <p style="margin: 5px 0; font-size: 0.9em; color: #374151;">{item.get('definition', '')}</p>
                <p style="margin: 5px 0; font-size: 0.85em; color: #6b21a8; font-style: italic;"><strong>💡 Analogy:</strong> {item.get('analogy', 'N/A')}</p>
                <p style="margin: 5px 0; font-size: 0.85em; color: #1e1b4b;"><strong>📊 Business Value:</strong> {item.get('business_value', 'N/A')}</p>
            </div>
            """
        html += "</div>"

    # --- DAILY STORIES SECTION ---
    for item in stories:
        html += f"""
        <div style="margin-bottom: 30px; padding: 25px; border-radius: 12px; border: 1px solid #e5e7eb; background: #ffffff;">
            <h3 style="margin-top: 0; color: #1e40af; font-size: 1.25em;">{item.get('rank', '•')}. {item['title']}</h3>
            <p style="font-size: 0.95em; color: #374151;">{item.get('summary', '')}</p>
            
            <div style="background-color: #f8fafc; padding: 15px; border-radius: 8px; border-left: 4px solid #0f172a; margin: 15px 0;">
                <p style="margin: 5px 0; font-size: 0.9em;"><strong style="color: #0f172a;">💡 Takeaway:</strong> {item.get('technical_takeaway', '')}</p>
                <p style="margin: 5px 0; font-size: 0.9em;"><strong style="color: #b91c1c;">⚖️ Risk:</strong> {item.get('primary_risk', 'N/A')}</p>
                <p style="margin: 5px 0; font-size: 0.9em;"><strong style="color: #15803d;">🚀 Opportunity:</strong> {item.get('primary_opportunity', 'N/A')}</p>
            </div>
            <p style="margin-top: 20px;"><a href="{item['url']}" style="background-color: #2563eb; color: white; padding: 10px 18px; text-decoration: none; border-radius: 6px; font-size: 0.85em; font-weight: bold; display: inline-block;">Read Source &rarr;</a></p>
        </div>
        """

    # --- TOOLBOX SECTION (Optimized for Visibility) ---
    if toolbox_data and (toolbox_data.get("tools") or isinstance(toolbox_data, list)):
        # Normalize data if it's a raw list
        tools_list = toolbox_data if isinstance(toolbox_data, list) else toolbox_data.get("tools", [])
        
        if tools_list:
            html += f"""
            <div style="margin: 30px 0; padding: 25px; background-color: #ecfdf5; border: 1px solid #10b981; border-radius: 12px;">
                <h3 style="margin-top: 0; color: #065f46; font-size: 1.1em;">🛠️ AI Dev Toolbox (Trending)</h3>
                <p style="font-size: 0.85em; color: #065f46; margin-bottom: 15px;">New libraries and repositories for your stack.</p>
            """
            for tool in tools_list[:3]: # Keep email concise with top 3
                html += f"""
                <div style="margin-bottom: 15px; padding: 12px; background: #ffffff; border-radius: 8px; border: 1px solid #d1fae5;">
                    <span style="font-size: 0.7em; font-weight: bold; background: #d1fae5; color: #065f46; padding: 2px 6px; border-radius: 4px; text-transform: uppercase;">{tool.get('Category', 'Tool')}</span>
                    <p style="margin: 5px 0; font-weight: bold; color: #064e3b; font-size: 1em;">{tool.get('Name', 'Unknown Tool')}</p>
                    <p style="margin: 5px 0; font-size: 0.85em; color: #374151;">{tool.get('Description', '')}</p>
                    <p style="margin: 5px 0; font-size: 0.8em; color: #64748b;"><strong>Use Case:</strong> {tool.get('Use_Case', 'N/A')}</p>
                    <a href="{tool.get('URL', '#')}" style="color: #10b981; font-size: 0.8em; font-weight: bold; text-decoration: none;">GitHub Repo &rarr;</a>
                </div>
                """
            html += "</div>"

    # --- LAB REPORT SECTION ---
    if lab_data and lab_data.get("papers"):
        html += f"""
        <div style="margin: 30px 0; padding: 25px; background-color: #f0f4ff; border: 1px solid #6366f1; border-radius: 12px;">
            <h3 style="margin-top: 0; color: #4338ca; font-size: 1.1em;">🔬 The Lab Report (Research)</h3>
            <p style="font-size: 0.85em; color: #4338ca; margin-bottom: 15px;">Deep-tech breakthroughs.</p>
        """
        for paper in lab_data.get("papers", []):
            html += f"""
            <div style="margin-bottom: 20px; padding-bottom: 10px; border-bottom: 1px solid #c7d2fe;">
                <p style="margin: 0; font-weight: bold; color: #1e1b4b; font-size: 1em;">{paper['title']}</p>
                <p style="margin: 8px 0; font-size: 0.85em; color: #374151;"><strong>Innovation:</strong> {paper['innovation']}</p>
                <a href="{paper['url']}" style="color: #6366f1; font-size: 0.8em; font-weight: bold; text-decoration: none;">View Paper &rarr;</a>
            </div>
            """
        html += "</div>"
    
    html += f"""
        <div style="margin-top: 40px; padding: 30px; text-align: center; background-color: #0f172a; border-radius: 12px; color: #ffffff;">
            <a href="{microsite_url}" style="background-color: #ffffff; color: #0f172a; padding: 12px 25px; text-decoration: none; border-radius: 6px; font-weight: bold; display: inline-block;">Full Web Archive</a>
            <p style="margin-top: 25px; font-size: 0.7em; opacity: 0.6;">© 2026 AI Executive Brief</p>
        </div>
    </body>
    </html>
    """
    return html

def send_email():
    # Ensure environment variables are loaded
    if not all([EMAIL_USER, EMAIL_PASS, EMAIL_TO]):
        print("❌ ERROR: Missing EMAIL environment variables.")
        return

    # Load Data Sources with error handling
    try:
        with open(JSON_INPUT, "r", encoding="utf-8") as f:
            brief_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Error: {JSON_INPUT} not found.")
        return

    # Optional verticals
    def safe_load(path):
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

    jargon_data = safe_load(JARGON_INPUT)
    lab_data = safe_load(LAB_INPUT)
    toolbox_data = safe_load(TOOLBOX_INPUT)

    recipients = [e.strip() for e in EMAIL_TO.split(",")]
    subject = f"AI Daily & Jargon Decoder: {brief_data.get('date', datetime.now().strftime('%B %d, %Y'))}"
    html_content = build_html_body(brief_data, jargon_data, lab_data, toolbox_data)

    msg = MIMEMultipart("alternative")
    msg["From"] = f"AI Briefing <{EMAIL_USER}>"
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.attach(MIMEText(html_content, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)
        print(f"📧 Success: Email sent to {len(recipients)} recipient(s).")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")

if __name__ == "__main__":
    send_email()