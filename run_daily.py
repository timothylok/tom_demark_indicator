"""Entry point for the Windows Task Scheduler cron job.

Runs the full STOCK_LIST signal engine and writes output to output/.
"""

import sys
from pathlib import Path

# Ensure the project root is on the path regardless of working directory
sys.path.insert(0, str(Path(__file__).resolve().parent))

from tom_demark_indicator.signals import run_daily_signals

if __name__ == "__main__":
    run_daily_signals(save_charts=True, write_output=True)
