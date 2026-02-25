import subprocess
import os
import sys
import json
from datetime import datetime

# ============================
# CONFIGURATION
# ============================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PYTHON_EXE = sys.executable

# Paths to critical data files
DATA_DIR = os.path.join(BASE_DIR, "data")
RAW_NEWS_PATH = os.path.join(DATA_DIR, "raw_news.json")
BACKUP_QUEUE_PATH = os.path.join(DATA_DIR, "backup_queue.json")
TOP_NEWS_PATH = os.path.join(DATA_DIR, "top_news.json")
ENRICHED_PATH = os.path.join(DATA_DIR, "enriched_summaries.json")

def run_step(script_name):
    """Utility to run individual scripts and print output"""
    script_path = os.path.join(BASE_DIR, script_name)
    print(f"\n>>> [RUNNING] {script_name}...")

    if not os.path.exists(script_path):
        print(f"ERROR: Script not found: {script_path}")
        return False

    try:
        result = subprocess.run(
            [PYTHON_EXE, script_path],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
        if result.stdout:
            print(result.stdout.strip())
        
        if result.returncode != 0:
            print(f"ERROR in {script_name}:\n{result.stderr.strip()}")
            return False
        return True
    except Exception as e:
        print(f"CRITICAL SYSTEM ERROR running {script_name}: {e}")
        return False

# ============================
# DYNAMIC PIPELINE RUNNER
# ============================

def run_pipeline():
    print("========== AI NEWS PIPELINE START ==========")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # PRE-STEP: Clear old session data to ensure fresh results
    for path in [RAW_NEWS_PATH, TOP_NEWS_PATH, ENRICHED_PATH]:
        if os.path.exists(path):
            os.remove(path)

    # STEP 1: Always Fetch News First
    if not run_step("fetch_news.py"):
        print("CRITICAL: Fetch stage failed.")
        sys.exit(1)

    # STEP 2: Check for content
    has_new_content = False
    raw_data = []
    if os.path.exists(RAW_NEWS_PATH):
        with open(RAW_NEWS_PATH, "r", encoding="utf-8") as f:
            try:
                raw_data = json.load(f)
                if len(raw_data) > 0:
                    has_new_content = True
            except json.JSONDecodeError:
                has_new_content = False

    # STEP 3: Content Processing
    if has_new_content:
        print(f">>> {len(raw_data)} new articles found. Executing AI enhancement...")
        
        standard_flow = [
            "ai_deduplicate.py", 
            "jargon_buster.py",     # Project B: Weekly Jargon (Handles Saturday logic inside)
            "process_lab_report.py", # Project C: (Disabled for now to fix errors first)
            "rank_news.py",         # Project A: Ranking & Selection
            "summarize.py", 
            "enrich.py"
        ]
        
        for script in standard_flow:
            if not run_step(script):
                print(f"Pipeline stopped at {script}")
                sys.exit(1)
    else:
        # PATH B: 0 new news -> Try Archive (Fixes Sunday Drought UI)
        print(">>> 0 new articles found. Switching to Archive Recovery Mode...")
        if os.path.exists(BACKUP_QUEUE_PATH):
            with open(BACKUP_QUEUE_PATH, "r", encoding="utf-8") as f:
                backup_data = json.load(f)
            
            if len(backup_data) > 0:
                print(f">>> Found {len(backup_data)} stories in backup. Filling Today's Brief.")
                with open(TOP_NEWS_PATH, "w", encoding="utf-8") as f:
                    json.dump(backup_data[:5], f, indent=2, ensure_ascii=False)
            else:
                print(">>> Archive empty. Pipeline cannot proceed.")
                sys.exit(0)

    # STEP 4: Always Format and Send
    #final_steps = ["format_brief.py", "send_email.py"]
    final_steps = ["format_brief.py"]
    for script in final_steps:
        if not run_step(script):
            sys.exit(1)

    print("\n========================================")
    print("ALL TASKS COMPLETED SUCCESSFULLY")

if __name__ == "__main__":
    run_pipeline()