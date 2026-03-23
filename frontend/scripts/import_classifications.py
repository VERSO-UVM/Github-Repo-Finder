#!/usr/bin/env python3
"""
Import classification CSVs into the SQLite database.

This makes the DB the single source of truth for both raw repo data
and classification labels. The CSVs were produced by the classification
pipeline documented in the README (Steps 1-6).

Usage:
  python frontend/scripts/import_classifications.py
"""

import csv
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / "Data/db/repository_data_UVM_database.db"

TABLES = {
    "repo_classifications": {
        "csv": PROJECT_ROOT / "Data/db/repo_classification_claude.csv",
        "schema": """
            CREATE TABLE IF NOT EXISTS repo_classifications (
                full_name TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                method TEXT,
                labeled_by TEXT,
                source TEXT
            )
        """,
    },
    "org_classifications": {
        "csv": PROJECT_ROOT / "Data/db/org_classification_claude.csv",
        "schema": """
            CREATE TABLE IF NOT EXISTS org_classifications (
                login TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                reason TEXT,
                labeled_by TEXT
            )
        """,
    },
    "user_classifications": {
        "csv": PROJECT_ROOT / "Data/db/user_classification_claude.csv",
        "schema": """
            CREATE TABLE IF NOT EXISTS user_classifications (
                login TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                reason TEXT,
                labeled_by TEXT
            )
        """,
    },
}


def import_table(conn, name, config):
    csv_path = config["csv"]
    if not csv_path.exists():
        print(f"  SKIP {name}: {csv_path} not found")
        return

    conn.execute(f"DROP TABLE IF EXISTS {name}")
    conn.execute(config["schema"])

    with open(csv_path) as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        placeholders = ", ".join(["?"] * len(columns))
        col_names = ", ".join(columns)
        rows = [tuple(row[c] for c in columns) for row in reader]

    conn.executemany(f"INSERT INTO {name} ({col_names}) VALUES ({placeholders})", rows)
    print(f"  {name}: {len(rows)} rows imported from {csv_path.name}")


def main():
    print(f"Importing classifications into {DB_PATH}")
    conn = sqlite3.connect(str(DB_PATH))

    for name, config in TABLES.items():
        import_table(conn, name, config)

    conn.commit()

    # Verify
    for name in TABLES:
        count = conn.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        labels = conn.execute(
            f"SELECT label, COUNT(*) FROM {name} GROUP BY label ORDER BY COUNT(*) DESC"
        ).fetchall()
        print(f"\n  {name} ({count} rows):")
        for label, n in labels:
            print(f"    {label}: {n}")

    conn.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
