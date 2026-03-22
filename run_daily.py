"""Entry point for the Windows Task Scheduler cron job.

Daily sequence
--------------
1. Run TD Sequential signals for every ticker in STOCK_LIST.
   Saves charts (images/), data JSONs (data/), and a text report (output/).
   Sends Discord embeds.

2. Export Next.js data files (NextJS/data/*.json + index.json).
   Only runs if step 1 completed without a fatal crash.

3. Rebuild the Next.js static site (npm run build inside NextJS/).
   Only runs if at least one ticker was exported successfully in step 2.
   A build failure sends a Discord alert but does NOT abort the job —
   the previous build stays live until the next successful rebuild.

Error handling
--------------
- Step 1 fatal crash  → Discord alert, exit(1).
- Step 2 failure      → Discord alert, step 3 skipped, exit(0)
                         (signals already ran; don't hide that success).
- Step 3 build failure→ Discord alert, exit(0).
"""

import subprocess
import sys
import traceback
from pathlib import Path

# Ensure the project root is on the path regardless of working directory
_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_ROOT))

from tom_demark_indicator.signals import run_daily_signals, get_stock_list
from tom_demark_indicator.discord_notifier import send_error_alert
from export_for_nextjs import run_export

_NEXTJS_DIR = _ROOT / "NextJS"
_NPM = "npm.cmd" if sys.platform == "win32" else "npm"


# ── Step 3: Next.js static rebuild ───────────────────────────────────────────

def _build_nextjs() -> bool:
    """Run `npm run build` in NextJS/. Returns True on success."""
    print("\n[NextJS Build] Running npm run build ...")
    result = subprocess.run(
        [_NPM, "run", "build"],
        cwd=_NEXTJS_DIR,
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("[NextJS Build] Build succeeded.")
        return True

    # Trim stderr to last 3000 chars so Discord embed stays readable
    stderr_tail = result.stderr[-3000:] if result.stderr else "(no stderr)"
    msg = f"Exit code {result.returncode}.\n\n{stderr_tail}"
    print(f"[NextJS Build] FAILED:\n{stderr_tail}", file=sys.stderr)
    send_error_alert("NextJS Build Failed", msg)
    return False


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # ── Step 1: TD Sequential signals ────────────────────────────────────────
    try:
        run_daily_signals(save_charts=True, write_output=True)
    except Exception:
        detail = traceback.format_exc()
        print(f"[FATAL] Daily signals job crashed:\n{detail}", file=sys.stderr)
        send_error_alert("Daily Job Crashed", detail)
        sys.exit(1)

    # ── Step 2: Export Next.js JSON data ─────────────────────────────────────
    try:
        tickers = get_stock_list()
        entries = run_export(tickers)
    except Exception:
        detail = traceback.format_exc()
        print(f"[NextJS Export] FAILED:\n{detail}", file=sys.stderr)
        send_error_alert("NextJS Export Failed", detail)
        sys.exit(0)  # signals succeeded — don't report as a full job failure

    if not entries:
        print("[NextJS Export] No tickers exported; skipping build.")
        sys.exit(0)

    # ── Step 3: Rebuild Next.js static site ──────────────────────────────────
    _build_nextjs()
