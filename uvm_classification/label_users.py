#!/usr/bin/env python3
"""
Interactive labeling tool for uncertain GitHub users.

Opens each user's GitHub profile in the browser and prompts you to label them.
Progress is saved after each label so you can stop and resume anytime.

Labeling provenance:
  - Claude's automated labels live in Data/db/user_classification_claude.csv
  - Your manual labels are saved to Data/db/user_classification_manual.csv
  - Both files have a 'labeled_by' column ('claude' vs 'human')
  - Manual labels override Claude's when merging (see merge_labels.py)

Usage:
  python label_users.py
"""

import csv
import webbrowser
import os
from datetime import datetime

from pyprojroot.here import here

INPUT_CSV = here("Data/db/user_classification_claude.csv")
OUTPUT_CSV = here("Data/db/user_classification_manual.csv")

FIELDNAMES = ["login", "label", "reason", "labeled_by", "labeled_at"]

VALID_LABELS = {
    "y": "uvm_vermont",
    "n": "not_uvm",
    "m": "uvm_mexico",
    "v": "uvm_verification",
    "s": "skip",  # keep as uncertain
}


def load_claude_labels():
    with open(INPUT_CSV) as f:
        return list(csv.DictReader(f))


def load_manual_labels():
    if not os.path.exists(OUTPUT_CSV):
        return {}
    with open(OUTPUT_CSV) as f:
        return {r["login"]: r for r in csv.DictReader(f)}


def save_manual_labels(manual):
    rows = list(manual.values())
    if not rows:
        return
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main():
    claude_labels = load_claude_labels()
    manual = load_manual_labels()

    # Get uncertain users that haven't been manually labeled yet
    to_label = [
        r for r in claude_labels
        if r["label"] == "uncertain" and r["login"] not in manual
    ]

    already_done = len([r for r in claude_labels if r["label"] == "uncertain" and r["login"] in manual])

    print("=" * 60)
    print("  User labeling tool")
    print("  Claude pre-labeled users from profile metadata.")
    print("  You are now reviewing the ones Claude couldn't classify.")
    print("=" * 60)
    print()
    print(f"  Uncertain users remaining: {len(to_label)}")
    print(f"  Already manually labeled:  {already_done}")
    print()
    print("  For each user, their GitHub profile will open in your browser.")
    print("  Then enter a label:")
    print("    y = UVM Vermont")
    print("    n = not UVM")
    print("    m = UVM Mexico")
    print("    v = UVM verification methodology")
    print("    s = skip (keep uncertain)")
    print("    q = quit (progress is saved)")
    print()

    for i, row in enumerate(to_label):
        login = row["login"]
        url = f"https://github.com/{login}"

        print(f"[{already_done + i + 1}/{already_done + len(to_label)}] {login}")
        print(f"  {url}")
        webbrowser.open(url)

        while True:
            choice = input("  Label (y/n/m/v/s/q): ").strip().lower()
            if choice == "q":
                print(f"\nSaved {len(manual)} manual labels to {OUTPUT_CSV}")
                return
            if choice in VALID_LABELS:
                label = VALID_LABELS[choice]
                manual[login] = {
                    "login": login,
                    "label": label,
                    "reason": "manual review of GitHub profile",
                    "labeled_by": "human",
                    "labeled_at": datetime.now().isoformat(timespec="seconds"),
                }
                save_manual_labels(manual)
                break
            print("  Invalid choice. Use y/n/m/v/s/q")

    print(f"\nDone! All {len(manual)} manual labels saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
