#!/usr/bin/env python3
"""
Extract: Fetch GitHub repo metadata via GraphQL and save as raw JSON.

Reads repo names from Data/db/githubrepo_name.csv
Writes metadata to Data/db/githubrepo_metadata.json

Usage:
  python extract_metadata.py
"""

import csv
import json
import subprocess
import sys
import time

from pyprojroot.here import here

BATCH_SIZE = 30
INPUT_CSV = here("Data/db/githubrepo_name.csv")
METADATA_JSON = here("Data/db/githubrepo_metadata.json")

REPO_FRAGMENT = """
    description
    repositoryTopics(first: 10) { nodes { topic { name } } }
    primaryLanguage { name }
    owner {
      login
      ... on User { bio company location }
      ... on Organization { description organizationBillingEmail: email }
    }
    homepageUrl
    isArchived
    isFork
    stargazerCount
    forkCount
    createdAt
    updatedAt
    licenseInfo { spdxId }
"""


def build_query(batch):
    parts = []
    for alias, owner, name in batch:
        parts.append(f'  {alias}: repository(owner: "{owner}", name: "{name}") {{{REPO_FRAGMENT}  }}')
    return "query {\n" + "\n".join(parts) + "\n}"


def fetch_batch(batch, retries=2):
    query = build_query(batch)
    result = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={query}"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        stderr = result.stderr
        if ("rate limit" in stderr.lower() or "abuse" in stderr.lower()) and retries > 0:
            print("  Rate limited, waiting 60s...", file=sys.stderr)
            time.sleep(60)
            return fetch_batch(batch, retries - 1)
        print(f"  GraphQL error: {stderr[:200]}", file=sys.stderr)
        return {}
    try:
        resp = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"  JSON decode error: {result.stdout[:200]}", file=sys.stderr)
        return {}
    if "errors" in resp and "data" not in resp:
        print(f"  Query errors: {resp['errors'][0].get('message', '')}", file=sys.stderr)
        return {}
    return resp.get("data", {})


def flatten_meta(raw):
    """Flatten nested GraphQL response into a cleaner dict."""
    if raw is None:
        return None
    topics = []
    if raw.get("repositoryTopics") and raw["repositoryTopics"].get("nodes"):
        topics = [n["topic"]["name"] for n in raw["repositoryTopics"]["nodes"]]
    return {
        "description": raw.get("description"),
        "topics": topics,
        "language": (raw["primaryLanguage"]["name"] if raw.get("primaryLanguage") else None),
        "owner_login": raw.get("owner", {}).get("login"),
        "owner_bio": raw.get("owner", {}).get("bio"),
        "owner_company": raw.get("owner", {}).get("company"),
        "owner_location": raw.get("owner", {}).get("location"),
        "owner_org_description": raw.get("owner", {}).get("description"),
        "homepage_url": raw.get("homepageUrl"),
        "is_archived": raw.get("isArchived"),
        "is_fork": raw.get("isFork"),
        "stars": raw.get("stargazerCount"),
        "forks": raw.get("forkCount"),
        "created_at": raw.get("createdAt"),
        "updated_at": raw.get("updatedAt"),
        "license": raw.get("licenseInfo", {}).get("spdxId") if raw.get("licenseInfo") else None,
    }


def main():
    with open(INPUT_CSV) as f:
        repos = [row["full_name"] for row in csv.DictReader(f)]

    print(f"Fetching metadata for {len(repos)} repos in batches of {BATCH_SIZE}...", file=sys.stderr)

    # Prepare batches
    batches = []
    alias_map = {}
    for i, full_name in enumerate(repos):
        parts = full_name.split("/", 1)
        if len(parts) != 2:
            continue
        owner, name = parts
        alias = f"repo_{i}"
        alias_map[alias] = full_name
        if not batches or len(batches[-1]) >= BATCH_SIZE:
            batches.append([])
        batches[-1].append((alias, owner, name))

    all_meta = {}
    for bi, batch in enumerate(batches):
        if bi % 10 == 0:
            pct = (bi / len(batches)) * 100
            print(f"  Batch {bi+1}/{len(batches)} ({pct:.0f}%)...", file=sys.stderr)
        data = fetch_batch(batch)
        for alias, owner, name in batch:
            raw = data.get(alias)
            all_meta[alias_map[alias]] = flatten_meta(raw)
        time.sleep(0.2)

    with open(METADATA_JSON, "w") as f:
        json.dump(all_meta, f, indent=2)

    found = sum(1 for v in all_meta.values() if v is not None)
    missing = sum(1 for v in all_meta.values() if v is None)
    print(f"\nSaved to {METADATA_JSON}", file=sys.stderr)
    print(f"  Found: {found}, Missing/private: {missing}", file=sys.stderr)


if __name__ == "__main__":
    main()
