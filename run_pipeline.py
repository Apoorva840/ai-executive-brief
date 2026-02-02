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

# Paths to critical data files used for the "Backup Check"
RAW_NEWS_PATH = os.path.join(BASE_DIR, "data", "raw_news.json")
BACKUP_QUEUE_PATH = os.path.join(BASE_DIR, "data", "backup_queue.json")
TOP_NEWS_PATH = os.path.join(BASE_DIR, "data", "top_news.json")
ENRICHED_PATH = os.path.join(BASE_DIR, "data", "enriched_summaries.json")

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

    # STEP 1: Always Fetch News First
    if not run_step("fetch_news.py"):
        sys.exit(1)

    # STEP 2: Check for new content
    has_new_content = False
    if os.path.exists(RAW_NEWS_PATH):
        with open(RAW_NEWS_PATH, "r", encoding="utf-8") as f:
            try:
                raw_data = json.load(f)
                if len(raw_data) > 0:
                    has_new_content = True
            except json.JSONDecodeError:
                has_new_content = False

    # STEP 3: The Fork in the Road
    if has_new_content:
        # PATH A: New news exists -> Run full AI process
        print(f">>> {len(raw_data)} new articles found. Executing full AI enhancement...")
        standard_flow = ["ai_deduplicate.py", "rank_news.py", "summarize.py", "enrich.py"]
        for script in standard_flow:
            if not run_step(script):
                sys.exit(1)
    else:
        # PATH B: 0 new news -> Try Archive/Backup
        print(">>> 0 new articles found. Switching to Archive Recovery Mode...")
        if os.path.exists(BACKUP_QUEUE_PATH):
            with open(BACKUP_QUEUE_PATH, "r", encoding="utf-8") as f:
                backup_data = json.load(f)
            
            if len(backup_data) > 0:
                print(f">>> Found {len(backup_data)} stories in backup queue. Using top 5.")
                # Save backup stories as top_news.json so format_brief.py can see them
                with open(TOP_NEWS_PATH, "w", encoding="utf-8") as f:
                    json.dump(backup_data[:5], f, indent=2, ensure_ascii=False)
                
                # Create a blank enriched file to avoid errors in the next steps
                with open(ENRICHED_PATH, "w", encoding="utf-8") as f:
                    json.dump([], f)
                
                print(">>> Archive articles loaded. Bypassing AI steps.")
            else:
                print(">>> Archive is also empty. Ending pipeline to avoid blank email.")
                sys.exit(0)
        else:
            print(">>> No backup_queue.json found. Ending pipeline.")
            sys.exit(0)

    # STEP 4: Always Format and Send (Works for both Path A and Path B)
    final_steps = ["format_brief.py", "send_email.py"]
    for script in final_steps:
        if not run_step(script):
            sys.exit(1)

    print("\n========================================")
    print("ALL TASKS COMPLETED SUCCESSFULLY")

if __name__ == "__main__":
    run_pipeline()