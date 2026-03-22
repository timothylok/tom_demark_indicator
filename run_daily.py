"""Entry point for the Windows Task Scheduler cron job.

Runs the full STOCK_LIST signal engine and writes output to output/.
Any unhandled exception is caught, printed, and sent to Discord.
"""

import sys
import traceback
from pathlib import Path

# Ensure the project root is on the path regardless of working directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tom_demark_indicator.signals import run_daily_signals
from tom_demark_indicator.discord_notifier import send_error_alert

if __name__ == "__main__":
    try:
        run_daily_signals(save_charts=True, write_output=True)
    except Exception:
        detail = traceback.format_exc()
        print(f"[FATAL] Daily job crashed:\n{detail}", file=sys.stderr)
        send_error_alert("Daily Job Crashed", detail)
        sys.exit(1)
