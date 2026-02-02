import subprocess
import os
import sys
from datetime import datetime

# ============================
# CONFIGURATION
# ============================

# Automatically detect the folder where this script resides
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Full path to Python executable (adjust if needed)
#PYTHON_EXE = r"C:\Python313\python.exe"
PYTHON_EXE = sys.executable

print("Using Python executable:", PYTHON_EXE)


# Scripts to run in order
SCRIPTS = [
    "fetch_news.py",
    "ai_deduplicate.py",
    "rank_news.py",
    "summarize.py",   
    "enrich.py",      
    "format_brief.py",
    "send_email.py"
]

# ============================
# PIPELINE RUNNER
# ============================

def run_pipeline():
    print("========== AI NEWS PIPELINE START ==========")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    for script in SCRIPTS:
        script_path = os.path.join(BASE_DIR, script)
        print(f"\n>>> [RUNNING] {script}...")

        if not os.path.exists(script_path):
            print(f"\nERROR: Script not found: {script_path}")
            sys.exit(1)

        try:
            result = subprocess.run(
                [PYTHON_EXE, script_path],
                cwd=BASE_DIR,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"  # Prevent encoding errors
            )

            if result.stdout:
                print(result.stdout.strip())

            if result.returncode != 0:
                print(f"\nERROR in {script}:")
                print(result.stderr.strip())
                sys.exit(1)

        except Exception as e:
            print(f"\nCRITICAL SYSTEM ERROR running {script}: {e}")
            sys.exit(1)

    print("\n========================================")
    print("ALL TASKS COMPLETED SUCCESSFULLY")


# ============================
if __name__ == "__main__":
    run_pipeline()
