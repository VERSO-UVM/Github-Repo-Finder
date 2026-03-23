#!/usr/bin/env python3
"""
Classify: Label repos as UVM (University of Vermont) related or not.

Reads from Data/db/githubrepo_metadata.json (produced by extract_metadata.py)
Writes to Data/db/githubrepo_classified.csv

Usage:
  python classify_repos.py
"""

import csv
import json
import sys
from collections import Counter

from pyprojroot.here import here

METADATA_JSON = here("Data/db/githubrepo_metadata.json")
OUTPUT_CSV = here("Data/db/githubrepo_classified.csv")


def classify(full_name, meta):
    """
    Classify whether a repo is related to the University of Vermont.

    Returns (label, confidence, reason) where:
      label: "uvm" | "not_uvm" | "uncertain"
      confidence: "high" | "medium" | "low"
      reason: short explanation
    """
    if meta is None:
        return "uncertain", "low", "repo not found or private"

    name_lower = full_name.lower()
    owner_lower = full_name.split("/")[0].lower()
    desc = (meta.get("description") or "").lower()
    topics = [t.lower() for t in (meta.get("topics") or [])]
    lang = (meta.get("language") or "").lower()
    bio = (meta.get("owner_bio") or "").lower()
    company = (meta.get("owner_company") or "").lower()
    location = (meta.get("owner_location") or "").lower()
    org_desc = (meta.get("owner_org_description") or "").lower()

    context_text = f"{desc} {' '.join(topics)} {bio} {company} {location} {org_desc}"
    all_text = f"{name_lower} {context_text}"

    # ── 1. Language-based: SystemVerilog/Verilog → verification methodology ──
    if lang in ("systemverilog", "verilog"):
        if _has_university_signal(context_text):
            return "uvm", "medium", f"lang={lang} but description/bio references University of Vermont"
        return "not_uvm", "high", f"lang={lang} → UVM Verification Methodology"

    # ── 2. Explicit University of Vermont references ──
    if _has_university_signal(all_text):
        return "uvm", "high", "explicitly references University of Vermont"

    # ── 3. Strong verification methodology signals ──
    verif_signal = _has_verification_signal(desc, topics)
    if verif_signal:
        return "not_uvm", "high", f"verification methodology: {verif_signal}"

    # ── 4. Owner location/company ──
    if any(kw in location for kw in ["vermont", "burlington", "vt"]):
        return "uvm", "medium", f"owner location: {meta.get('owner_location')}"
    if any(kw in company for kw in ["vermont", "uvm"]):
        return "uvm", "medium", f"owner company: {meta.get('owner_company')}"

    # ── 5. Repo/owner name contains 'uvm' ──
    if "uvm" in owner_lower or "uvm" in name_lower.split("/")[-1]:
        if any(kw in all_text for kw in ["uv map", "uvmap", "uv-map", "ultraviolet"]):
            return "not_uvm", "medium", "UV mapping / ultraviolet, not UVM"
        return "uvm", "medium", "name contains 'uvm', no verification signals"

    # ── 6. No clear signal ──
    return "uncertain", "low", "no UVM-related signals found"


def _has_university_signal(text):
    keywords = [
        "university of vermont", "univ. of vermont",
        "burlington, vt", "burlington vt", "burlington, vermont",
        "vermont",
    ]
    return any(kw in text for kw in keywords)


def _has_verification_signal(desc, topics):
    verif_keywords = [
        "verification methodology", "testbench", "test bench",
        "uvm framework", "uvm methodology", "uvm base class",
        "uvm sequence", "uvm driver", "uvm monitor", "uvm agent",
        "uvm scoreboard", "uvm environment", "uvm register",
        "constrained random", "coverage driven", "functional verification",
        "verification ip", "chip verification", "asic verification",
        "rtl verification", "design verification", "soc verification",
        "uvm_component", "uvm_object", "uvm_sequence_item",
    ]
    for kw in verif_keywords:
        if kw in desc:
            return kw
    verif_topics = [
        "systemverilog", "verilog", "uvm", "verification",
        "testbench", "fpga-verification", "asic",
    ]
    topic_hits = [t for t in topics if t in verif_topics]
    if len(topic_hits) >= 2:
        return f"topics: {', '.join(topic_hits)}"
    if "systemverilog" in topics or "verilog" in topics:
        return f"topic: {topics}"
    return None


def main():
    with open(METADATA_JSON) as f:
        all_meta = json.load(f)

    print(f"Classifying {len(all_meta)} repos...", file=sys.stderr)

    results = []
    for full_name, meta in all_meta.items():
        label, conf, reason = classify(full_name, meta)
        results.append({
            "full_name": full_name,
            "label": label,
            "confidence": conf,
            "reason": reason,
            "description": (meta or {}).get("description") or "",
            "language": (meta or {}).get("language") or "",
            "topics": ";".join((meta or {}).get("topics") or []),
            "owner_bio": (meta or {}).get("owner_bio") or "",
            "owner_company": (meta or {}).get("owner_company") or "",
            "owner_location": (meta or {}).get("owner_location") or "",
            "stars": (meta or {}).get("stars", 0),
            "is_archived": (meta or {}).get("is_archived", False),
            "is_fork": (meta or {}).get("is_fork", False),
        })

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    labels = Counter(r["label"] for r in results)
    print(f"\nResults written to {OUTPUT_CSV}", file=sys.stderr)
    for label, count in labels.most_common():
        print(f"  {label}: {count}", file=sys.stderr)


if __name__ == "__main__":
    main()
