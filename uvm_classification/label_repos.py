#!/usr/bin/env python3
"""
Interactive labeling tool for uncertain GitHub repos.

Opens each repo's GitHub page in the browser and prompts you to label them.
Progress is saved after each label so you can stop and resume anytime.

Labels a random sample of uncertain repos from repo_classification_claude.csv.
Results saved to Data/db/repo_classification_manual.csv with labeled_by=human.

Usage:
  python label_repos.py           # label from random sample (default 50)
  python label_repos.py --all     # label all uncertain repos
  python label_repos.py -n 100    # label random sample of 100
"""

import argparse
import csv
import os
import random
import webbrowser
from datetime import datetime

from pyprojroot.here import here

CLASSIFICATION_CSV = here("Data/db/repo_classification_claude.csv")
OUTPUT_CSV = here("Data/db/repo_classification_manual.csv")

FIELDNAMES = ["full_name", "label", "reason", "labeled_by", "labeled_at"]

VALID_LABELS = {
    "y": "uvm_vermont",
    "n": "not_uvm",
    "m": "uvm_mexico",
    "v": "uvm_verification",
    "s": "skip",  # keep as uncertain
}


def load_uncertain_repos():
    with open(CLASSIFICATION_CSV) as f:
        return [r for r in csv.DictReader(f) if r["label"] == "uncertain"]


def load_manual_labels():
    if not os.path.exists(OUTPUT_CSV):
        return {}
    with open(OUTPUT_CSV) as f:
        return {r["full_name"]: r for r in csv.DictReader(f)}


def save_manual_labels(manual):
    rows = list(manual.values())
    if not rows:
        return
    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-n", type=int, default=50, help="sample size (default 50)")
    parser.add_argument("--all", action="store_true", help="label all uncertain repos")
    args = parser.parse_args()

    uncertain = load_uncertain_repos()
    manual = load_manual_labels()

    # Filter out already-labeled
    to_label = [r for r in uncertain if r["full_name"] not in manual]

    if not args.all:
        random.seed(42)
        to_label = random.sample(to_label, min(args.n, len(to_label)))

    already_done = len(manual)

    print("=" * 60)
    print("  Repo labeling tool")
    print("  Claude pre-classified repos from owner + metadata.")
    print("  You are now reviewing the ones that remain uncertain.")
    print("=" * 60)
    print()
    print(f"  Total uncertain:          {len(uncertain)}")
    print(f"  Already manually labeled: {already_done}")
    print(f"  To label this session:    {len(to_label)}")
    print()
    print("  For each repo, its GitHub page will open in your browser.")
    print("  Then enter a label:")
    print("    y = UVM Vermont")
    print("    n = not UVM")
    print("    m = UVM Mexico")
    print("    v = UVM verification methodology")
    print("    s = skip (keep uncertain)")
    print("    q = quit (progress is saved)")
    print()

    for i, row in enumerate(to_label):
        full_name = row["full_name"]
        url = f"https://github.com/{full_name}"

        print(f"[{already_done + i + 1}/{already_done + len(to_label)}] {full_name}")
        print(f"  {url}")
        webbrowser.open(url)

        while True:
            choice = input("  Label (y/n/m/v/s/q): ").strip().lower()
            if choice == "q":
                print(f"\nSaved {len(manual)} manual labels to {OUTPUT_CSV}")
                return
            if choice in VALID_LABELS:
                label = VALID_LABELS[choice]
                manual[full_name] = {
                    "full_name": full_name,
                    "label": label,
                    "reason": "manual review of GitHub repo",
                    "labeled_by": "human",
                    "labeled_at": datetime.now().isoformat(timespec="seconds"),
                }
                save_manual_labels(manual)
                break
            print("  Invalid choice. Use y/n/m/v/s/q")

    print(f"\nDone! {len(manual)} manual labels saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
