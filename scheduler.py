"""
Scheduler
─────────
Runs the email pipeline automatically every N minutes.
Start this alongside the FastAPI server.

Usage:
    python scheduler.py

It will poll Gmail every POLL_INTERVAL_SECONDS (set in .env).
"""
import time
import schedule
from app.config import get_settings
from app.services.pipeline import run_pipeline
from app.database import init_db

def job():
    print("\n⏰ Scheduled pipeline run triggered")
    run_pipeline()

if __name__ == "__main__":
    init_db()
    settings = get_settings()
    interval = settings.poll_interval_seconds

    print(f"🕐 Scheduler started — running pipeline every {interval} seconds")
    print("   Press Ctrl+C to stop\n")

    # Run once immediately on startup
    job()

    # Then schedule recurring runs
    schedule.every(interval).seconds.do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
