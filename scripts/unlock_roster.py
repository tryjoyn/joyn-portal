#!/usr/bin/env python3
"""
unlock_roster.py — Joyn roster auto-unlock script
Runs via GitHub Actions on a weekly cron schedule.

Reads data/roster.json, checks unlockDate vs today.
If unlockDate <= today and status === "coming-soon", updates status to "live" and commits.

Usage:
  python scripts/unlock_roster.py

GitHub Actions workflow trigger:
  on:
    schedule:
      - cron: '0 6 * * 1'  # Monday 6am UTC
    workflow_dispatch:       # Manual trigger
"""

import json
import subprocess
import sys
from datetime import date
from pathlib import Path


ROSTER_PATH = Path(__file__).parent.parent / "data" / "roster.json"


def load_roster(path: Path) -> list:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_roster(path: Path, roster: list) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(roster, f, indent=2, ensure_ascii=False)
        f.write("\n")


def check_and_unlock(roster: list, today: date) -> tuple[list, list]:
    """Return (updated_roster, list_of_unlocked_names)."""
    unlocked = []
    for staff in roster:
        if staff.get("status") == "coming-soon" and staff.get("unlockDate"):
            unlock_date = date.fromisoformat(staff["unlockDate"])
            if unlock_date <= today:
                staff["status"] = "live"
                unlocked.append(staff["name"])
                print(f"  Unlocked: {staff['name']} (unlock date: {unlock_date})")
    return roster, unlocked


def git_commit(unlocked_names: list) -> None:
    names_str = ", ".join(unlocked_names)
    msg = f"Auto-unlock roster: {names_str}"
    try:
        subprocess.run(["git", "config", "user.name", "Joyn Roster Bot"], check=True)
        subprocess.run(["git", "config", "user.email", "bot@tryjoyn.me"], check=True)
        subprocess.run(["git", "add", str(ROSTER_PATH)], check=True)
        subprocess.run(["git", "commit", "-m", msg], check=True)
        print(f"  Committed: {msg}")
    except subprocess.CalledProcessError as e:
        print(f"  Git error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    today = date.today()
    print(f"Joyn roster unlock — checking against {today}")

    if not ROSTER_PATH.exists():
        print(f"ERROR: roster not found at {ROSTER_PATH}", file=sys.stderr)
        sys.exit(1)

    roster = load_roster(ROSTER_PATH)
    roster, unlocked = check_and_unlock(roster, today)

    if not unlocked:
        print("  No staff to unlock today.")
        return

    save_roster(ROSTER_PATH, roster)
    print(f"  {len(unlocked)} staff member(s) unlocked and roster saved.")
    git_commit(unlocked)


if __name__ == "__main__":
    main()
