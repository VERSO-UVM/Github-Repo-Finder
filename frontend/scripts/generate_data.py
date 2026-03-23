#!/usr/bin/env python3
"""
Generate static JSON data for the SvelteKit dashboard.

Reads from the SQLite database and classification CSV,
writes to frontend/static/data/dashboard.json.

Usage:
  python frontend/scripts/generate_data.py
"""

import json
import os
import sqlite3
from pathlib import Path

import pandas as pd

# This script lives in frontend/scripts/, project root is two levels up
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "Data/db/repository_data_UVM_database.db"
CLASSIFICATION_CSV = PROJECT_ROOT / "Data/db/repo_classification_claude.csv"
OUTPUT_JSON = Path(__file__).resolve().parent.parent / "static/data/dashboard.json"

FEATURES = [
    ("readme", "README"),
    ("license", "License"),
    ("code_of_conduct_file", "Code of Conduct"),
    ("contributing", "Contributing Guide"),
    ("security_policy", "Security Policy"),
    ("issue_templates", "Issue Templates"),
    ("pull_request_template", "PR Template"),
]


def bool_col(series):
    """Return a boolean Series: True when the field has a meaningful value."""
    num = pd.to_numeric(series, errors="coerce")
    has_num = num.notna() & (num != 0)
    has_str = series.astype(str).str.strip().replace({"nan": "", "None": "", "0": ""}) != ""
    return has_num | has_str


def load_data():
    conn = sqlite3.connect(str(DB_PATH))
    repo_df = pd.read_sql_query("SELECT * FROM repositories", conn)

    # Filter to UVM Vermont repos
    if os.path.exists(str(CLASSIFICATION_CSV)):
        class_df = pd.read_csv(str(CLASSIFICATION_CSV))
        uvm_repos = set(class_df[class_df["label"] == "uvm_vermont"]["full_name"])
        repo_df = repo_df[repo_df["full_name"].isin(uvm_repos)]
        print(f"  Filtered to {len(repo_df)} UVM Vermont repos")

    # Merge contributor counts
    try:
        contrib_df = pd.read_sql_query(
            "SELECT repository_name, COUNT(contributor_login) AS contributor_count "
            "FROM contributions GROUP BY repository_name",
            conn,
        )
        repo_df = repo_df.merge(
            contrib_df, how="left", left_on="full_name", right_on="repository_name"
        )
        if "repository_name" in repo_df.columns:
            repo_df.drop(columns=["repository_name"], inplace=True)
    except Exception:
        repo_df["contributor_count"] = 0

    conn.close()

    for col in [
        "stargazers_count", "forks_count", "open_issues_count",
        "subscribers_count", "release_downloads", "size", "contributor_count",
    ]:
        if col in repo_df.columns:
            repo_df[col] = pd.to_numeric(repo_df[col], errors="coerce").fillna(0).astype(int)

    return repo_df


def compute_stats(df):
    total = len(df)
    total_stars = int(df["stargazers_count"].sum()) if "stargazers_count" in df.columns else 0
    total_forks = int(df["forks_count"].sum()) if "forks_count" in df.columns else 0

    # Language distribution
    lang_counts = {}
    if "language" in df.columns:
        lang_series = df["language"].replace("Jupyter Notebook", "Jupyter").dropna()
        lang_series = lang_series[lang_series.astype(str).str.strip() != ""]
        vc = lang_series.value_counts()
        threshold = 0.03 * len(lang_series)
        major = vc[vc >= threshold]
        other = int(vc[vc < threshold].sum())
        lang_counts = major.to_dict()
        if other > 0:
            lang_counts["Other"] = other

    # License distribution
    license_counts = {}
    if "license" in df.columns:
        lic = df["license"].dropna()
        lic = lic[lic.astype(str).str.strip().replace({"nan": "", "None": ""}) != ""]
        vc = lic.value_counts()
        threshold = 0.03 * len(df)
        major = vc[vc >= threshold]
        other = int(vc[vc < threshold].sum())
        no_license = int(
            (df["license"].isna() | df["license"].astype(str).str.strip().isin(["", "nan", "None"])).sum()
        )
        license_counts = major.to_dict()
        if other > 0:
            license_counts["Other"] = other
        if no_license > 0:
            license_counts["None"] = no_license

    # Feature adoption
    feature_stats = []
    for col, label in FEATURES:
        if col in df.columns:
            pct = round(100 * bool_col(df[col]).sum() / total, 1) if total > 0 else 0.0
            feature_stats.append({"label": label, "pct": pct})

    # Stars histogram
    star_buckets = {}
    if "stargazers_count" in df.columns:
        bins = [0, 1, 5, 10, 50, 100, 500, 1000, float("inf")]
        labels = ["0", "1-4", "5-9", "10-49", "50-99", "100-499", "500-999", "1000+"]
        stars = df["stargazers_count"]
        for i in range(len(labels)):
            count = int(((stars >= bins[i]) & (stars < bins[i + 1])).sum())
            star_buckets[labels[i]] = count

    # Top repos table (top 500 by stars)
    cols = [
        "full_name", "language", "license", "stargazers_count", "forks_count",
        "open_issues_count", "contributor_count", "created_at", "pushed_at", "description",
    ]
    available = [c for c in cols if c in df.columns]
    top = df[available].copy()
    if "stargazers_count" in top.columns:
        top = top.sort_values("stargazers_count", ascending=False)
    top = top.head(500)

    # Feature flags for table
    for col, label in FEATURES:
        if col in df.columns:
            top[f"has_{col}"] = bool_col(df.loc[top.index, col]).values

    # URL
    if "html_url" in df.columns:
        top["html_url"] = df.loc[top.index, "html_url"].values
    elif "url" in df.columns:
        top["html_url"] = df.loc[top.index, "url"].values

    top = top.fillna("").astype(str)
    repos_list = top.to_dict(orient="records")

    unique_langs = int(df["language"].nunique()) if "language" in df.columns else 0

    return {
        "acronym": "UVM",
        "total": total,
        "total_stars": total_stars,
        "total_forks": total_forks,
        "unique_langs": unique_langs,
        "lang_counts": lang_counts,
        "license_counts": license_counts,
        "feature_stats": feature_stats,
        "star_buckets": star_buckets,
        "repos": repos_list,
    }


def main():
    print("Generating dashboard data...")
    df = load_data()
    stats = compute_stats(df)

    os.makedirs(os.path.dirname(str(OUTPUT_JSON)), exist_ok=True)
    with open(str(OUTPUT_JSON), "w") as f:
        json.dump(stats, f, default=str)

    print(f"Wrote {OUTPUT_JSON} ({len(stats['repos'])} repos)")


if __name__ == "__main__":
    main()
