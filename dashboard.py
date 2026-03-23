#!/usr/bin/env python3
"""
Generate a self-contained HTML dashboard from a repofinder SQLite database.

Usage:
    python dashboard.py [ACRONYM]

If ACRONYM is omitted, defaults to UVM.
"""

import sys
import os
import json
import sqlite3
import webbrowser
from pathlib import Path

import pandas as pd

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

ACRONYM = sys.argv[1].upper() if len(sys.argv) > 1 else "UVM"
DB_PATH = f"Data/db/repository_data_{ACRONYM}_database.db"
OUTPUT_HTML = f"dashboard_{ACRONYM}.html"

FEATURES = [
    ("readme",               "README"),
    ("license",              "License"),
    ("code_of_conduct_file", "Code of Conduct"),
    ("contributing",         "Contributing Guide"),
    ("security_policy",      "Security Policy"),
    ("issue_templates",      "Issue Templates"),
    ("pull_request_template","PR Template"),
]

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

def load_data(db_path):
    if not os.path.exists(db_path):
        print(f"[ERROR] Database not found: {db_path}")
        print("Run main_scraping.py first to collect data.")
        sys.exit(1)

    conn = sqlite3.connect(db_path)
    repo_df = pd.read_sql_query("SELECT * FROM repositories", conn)

    # Filter to classified UVM Vermont repos if classification exists
    classification_csv = f"Data/db/repo_classification_claude.csv"
    if os.path.exists(classification_csv):
        class_df = pd.read_csv(classification_csv)
        uvm_repos = set(class_df[class_df["label"] == "uvm_vermont"]["full_name"])
        before = len(repo_df)
        repo_df = repo_df[repo_df["full_name"].isin(uvm_repos)]
        print(f"  Filtered to {len(repo_df)} UVM Vermont repos (from {before} total)")

    try:
        org_df = pd.read_sql_query(
            "SELECT login, url AS org_url, email AS org_email FROM organizations", conn
        )
        repo_df = repo_df.merge(org_df, how="left", left_on="owner", right_on="login")
        if "login" in repo_df.columns:
            repo_df.drop(columns=["login"], inplace=True)
    except Exception:
        pass

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

    # Numeric coercions
    for col in ["stargazers_count", "forks_count", "open_issues_count",
                "subscribers_count", "release_downloads", "size", "contributor_count"]:
        if col in repo_df.columns:
            repo_df[col] = pd.to_numeric(repo_df[col], errors="coerce").fillna(0).astype(int)

    return repo_df


def bool_col(series):
    """Return a boolean Series: True when the field has a meaningful value."""
    num = pd.to_numeric(series, errors="coerce")
    has_num = num.notna() & (num != 0)
    has_str = series.astype(str).str.strip().replace({"nan": "", "None": "", "0": ""}) != ""
    return has_num | has_str


# ---------------------------------------------------------------------------
# Compute aggregates
# ---------------------------------------------------------------------------

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
        no_license = int((df["license"].isna() | (df["license"].astype(str).str.strip().isin(["", "nan", "None"]))).sum())
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

    # Stars histogram buckets
    star_buckets = {}
    if "stargazers_count" in df.columns:
        bins = [0, 1, 5, 10, 50, 100, 500, 1000, float("inf")]
        labels = ["0", "1–4", "5–9", "10–49", "50–99", "100–499", "500–999", "1000+"]
        stars = df["stargazers_count"]
        for i in range(len(labels)):
            count = int(((stars >= bins[i]) & (stars < bins[i + 1])).sum())
            star_buckets[labels[i]] = count

    # Top repos table
    cols = ["full_name", "language", "license", "stargazers_count", "forks_count",
            "open_issues_count", "contributor_count", "created_at", "pushed_at", "description"]
    available = [c for c in cols if c in df.columns]
    top = df[available].copy()
    if "stargazers_count" in top.columns:
        top = top.sort_values("stargazers_count", ascending=False)
    top = top.head(500)

    # Add feature flags for table
    for col, label in FEATURES:
        if col in df.columns:
            top[f"has_{col}"] = bool_col(df.loc[top.index, col]).values

    # Add html_url if available
    if "html_url" in df.columns:
        top["html_url"] = df.loc[top.index, "html_url"].values
    elif "url" in df.columns:
        top["html_url"] = df.loc[top.index, "url"].values

    top = top.fillna("").astype(str)
    repos_list = top.to_dict(orient="records")

    # Org counts
    org_count = 0
    if "owner" in df.columns and "organization" in df.columns:
        org_count = int((df["organization"].astype(str).str.lower().isin(["1", "true"])).sum())

    unique_langs = int(df["language"].nunique()) if "language" in df.columns else 0

    return {
        "acronym": ACRONYM,
        "total": total,
        "total_stars": total_stars,
        "total_forks": total_forks,
        "org_count": org_count,
        "unique_langs": unique_langs,
        "lang_counts": lang_counts,
        "license_counts": license_counts,
        "feature_stats": feature_stats,
        "star_buckets": star_buckets,
        "repos": repos_list,
    }


# ---------------------------------------------------------------------------
# HTML template
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0"/>
<title>{acronym} Repository Dashboard</title>
<script src="https://cdn.tailwindcss.com"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3/dist/chart.umd.min.js"></script>
<style>
  body {{ font-family: system-ui, sans-serif; background: #f8fafc; }}
  .card {{ background: white; border-radius: 0.75rem; box-shadow: 0 1px 4px rgba(0,0,0,.08); padding: 1.25rem; }}
  th {{ cursor: pointer; user-select: none; }}
  th:hover {{ background: #e2e8f0; }}
  tr:hover td {{ background: #f1f5f9; }}
  .badge {{ display:inline-block; padding:1px 7px; border-radius:999px; font-size:.7rem; font-weight:600; }}
  .badge-yes {{ background:#dcfce7; color:#166534; }}
  .badge-no  {{ background:#fee2e2; color:#991b1b; }}
</style>
</head>
<body class="p-6">

<h1 class="text-3xl font-bold text-slate-800 mb-1">{acronym} Open-Source Repository Dashboard</h1>
<p class="text-slate-500 mb-6">Data from GitHub scraping via repofinder</p>

<!-- Stat cards -->
<div class="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6" id="stat-cards"></div>

<!-- Charts row -->
<div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
  <div class="card"><h2 class="font-semibold text-slate-700 mb-3">Language Distribution</h2><canvas id="langChart"></canvas></div>
  <div class="card"><h2 class="font-semibold text-slate-700 mb-3">License Distribution</h2><canvas id="licenseChart"></canvas></div>
  <div class="card"><h2 class="font-semibold text-slate-700 mb-3">Community Features Adoption</h2><canvas id="featureChart"></canvas></div>
</div>

<!-- Stars histogram -->
<div class="card mb-6">
  <h2 class="font-semibold text-slate-700 mb-3">Star Count Distribution</h2>
  <canvas id="starChart" style="max-height:220px"></canvas>
</div>

<!-- Repository table -->
<div class="card">
  <div class="flex items-center justify-between mb-3">
    <h2 class="font-semibold text-slate-700">Repositories (top 500 by stars)</h2>
    <input id="tableSearch" type="text" placeholder="Search…"
           class="border rounded px-3 py-1 text-sm w-56 focus:outline-none focus:ring-2 focus:ring-blue-300"/>
  </div>
  <div class="overflow-x-auto">
    <table class="w-full text-sm text-left" id="repoTable">
      <thead class="text-xs uppercase text-slate-500 border-b">
        <tr>
          <th class="py-2 pr-3" data-col="full_name">Repository</th>
          <th class="py-2 pr-3" data-col="language">Language</th>
          <th class="py-2 pr-3" data-col="license">License</th>
          <th class="py-2 pr-3 text-right" data-col="stargazers_count">Stars</th>
          <th class="py-2 pr-3 text-right" data-col="forks_count">Forks</th>
          <th class="py-2 pr-3 text-right" data-col="contributor_count">Contribs</th>
          <th class="py-2 pr-3">Features</th>
          <th class="py-2 pr-3" data-col="pushed_at">Last Push</th>
        </tr>
      </thead>
      <tbody id="tableBody"></tbody>
    </table>
    <div id="tablePager" class="flex gap-2 mt-3 items-center text-sm text-slate-500"></div>
  </div>
</div>

<script>
const DATA = {data_json};

// ── Palette ──────────────────────────────────────────────────────────────────
const PALETTE = [
  '#3b82f6','#10b981','#f59e0b','#ef4444','#8b5cf6',
  '#06b6d4','#f97316','#84cc16','#ec4899','#6366f1',
  '#14b8a6','#eab308','#64748b','#a855f7','#22c55e',
];

// ── Stat cards ────────────────────────────────────────────────────────────────
const cards = [
  {{ label: 'Repositories', value: DATA.total.toLocaleString(), icon: '📦' }},
  {{ label: 'Total Stars',  value: DATA.total_stars.toLocaleString(), icon: '⭐' }},
  {{ label: 'Total Forks',  value: DATA.total_forks.toLocaleString(), icon: '🍴' }},
  {{ label: 'Languages',    value: DATA.unique_langs.toLocaleString(), icon: '💻' }},
];
const cardEl = document.getElementById('stat-cards');
cards.forEach(c => {{
  cardEl.innerHTML += `<div class="card text-center">
    <div class="text-3xl mb-1">${{c.icon}}</div>
    <div class="text-2xl font-bold text-slate-800">${{c.value}}</div>
    <div class="text-sm text-slate-500">${{c.label}}</div>
  </div>`;
}});

// ── Chart helpers ─────────────────────────────────────────────────────────────
function doughnut(id, labels, values) {{
  new Chart(document.getElementById(id), {{
    type: 'doughnut',
    data: {{
      labels,
      datasets: [{{ data: values, backgroundColor: PALETTE, borderWidth: 1 }}]
    }},
    options: {{
      plugins: {{
        legend: {{ position: 'right', labels: {{ font: {{ size: 11 }}, boxWidth: 12 }} }}
      }}
    }}
  }});
}}

function hbar(id, labels, values, color) {{
  new Chart(document.getElementById(id), {{
    type: 'bar',
    data: {{
      labels,
      datasets: [{{ data: values, backgroundColor: color || '#3b82f6', borderRadius: 4 }}]
    }},
    options: {{
      indexAxis: 'y',
      plugins: {{ legend: {{ display: false }} }},
      scales: {{
        x: {{ max: 100, ticks: {{ callback: v => v + '%' }} }},
        y: {{ ticks: {{ font: {{ size: 11 }} }} }}
      }}
    }}
  }});
}}

// Language chart
doughnut('langChart',
  Object.keys(DATA.lang_counts),
  Object.values(DATA.lang_counts)
);

// License chart
doughnut('licenseChart',
  Object.keys(DATA.license_counts),
  Object.values(DATA.license_counts)
);

// Feature chart
hbar('featureChart',
  DATA.feature_stats.map(f => f.label),
  DATA.feature_stats.map(f => f.pct),
  '#10b981'
);

// Stars histogram
new Chart(document.getElementById('starChart'), {{
  type: 'bar',
  data: {{
    labels: Object.keys(DATA.star_buckets),
    datasets: [{{
      label: 'Repositories',
      data: Object.values(DATA.star_buckets),
      backgroundColor: '#6366f1',
      borderRadius: 4,
    }}]
  }},
  options: {{
    plugins: {{ legend: {{ display: false }} }},
    scales: {{ y: {{ beginAtZero: true }} }}
  }}
}});

// ── Repository table ──────────────────────────────────────────────────────────
const FEATURE_COLS = [
  ['has_readme','README'],['has_license','License'],
  ['has_code_of_conduct_file','CoC'],['has_contributing','Contrib'],
  ['has_security_policy','Security'],['has_issue_templates','Issues'],
  ['has_pull_request_template','PR Tmpl'],
];

let sortCol = 'stargazers_count', sortDir = -1;
let page = 0;
const PAGE_SIZE = 25;
let filtered = DATA.repos.slice();

function renderTable() {{
  const body = document.getElementById('tableBody');
  body.innerHTML = '';
  const start = page * PAGE_SIZE;
  const slice = filtered.slice(start, start + PAGE_SIZE);
  slice.forEach(r => {{
    const name = r.full_name || '';
    const url  = r.html_url || '#';
    const stars = parseInt(r.stargazers_count) || 0;
    const forks = parseInt(r.forks_count) || 0;
    const contribs = parseInt(r.contributor_count) || 0;
    const pushed = r.pushed_at ? r.pushed_at.slice(0,10) : '';
    const featureBadges = FEATURE_COLS.map(([col, lbl]) =>
      `<span class="badge ${{r[col]==='True'?'badge-yes':'badge-no'}}">${{lbl}}</span>`
    ).join(' ');
    body.innerHTML += `<tr class="border-b border-slate-100">
      <td class="py-2 pr-3 font-medium"><a href="${{url}}" target="_blank" class="text-blue-600 hover:underline">${{name}}</a></td>
      <td class="py-2 pr-3 text-slate-600">${{r.language || ''}}</td>
      <td class="py-2 pr-3 text-slate-600">${{r.license || ''}}</td>
      <td class="py-2 pr-3 text-right">${{stars.toLocaleString()}}</td>
      <td class="py-2 pr-3 text-right">${{forks.toLocaleString()}}</td>
      <td class="py-2 pr-3 text-right">${{contribs.toLocaleString()}}</td>
      <td class="py-2 pr-3 whitespace-nowrap">${{featureBadges}}</td>
      <td class="py-2 pr-3 text-slate-500">${{pushed}}</td>
    </tr>`;
  }});
  renderPager();
}}

function renderPager() {{
  const pager = document.getElementById('tablePager');
  const total = filtered.length;
  const pages = Math.ceil(total / PAGE_SIZE);
  pager.innerHTML = `
    <button onclick="changePage(-1)" class="px-2 py-1 border rounded disabled:opacity-40" ${{page===0?'disabled':''}}>‹ Prev</button>
    <span>Page ${{page+1}} / ${{pages}} &nbsp;(${{total}} repos)</span>
    <button onclick="changePage(1)"  class="px-2 py-1 border rounded disabled:opacity-40" ${{page>=pages-1?'disabled':''}}>Next ›</button>`;
}}

function changePage(d) {{
  page = Math.max(0, page + d);
  renderTable();
}}

// Sort
document.querySelectorAll('#repoTable th[data-col]').forEach(th => {{
  th.addEventListener('click', () => {{
    const col = th.dataset.col;
    if (sortCol === col) sortDir *= -1; else {{ sortCol = col; sortDir = -1; }}
    const isNum = ['stargazers_count','forks_count','contributor_count'].includes(col);
    filtered.sort((a,b) => {{
      const av = isNum ? (parseInt(a[col])||0) : (a[col]||'').toLowerCase();
      const bv = isNum ? (parseInt(b[col])||0) : (b[col]||'').toLowerCase();
      return av < bv ? sortDir : av > bv ? -sortDir : 0;
    }});
    page = 0;
    renderTable();
  }});
}});

// Search
document.getElementById('tableSearch').addEventListener('input', e => {{
  const q = e.target.value.toLowerCase();
  filtered = DATA.repos.filter(r =>
    (r.full_name||'').toLowerCase().includes(q) ||
    (r.language||'').toLowerCase().includes(q) ||
    (r.description||'').toLowerCase().includes(q)
  );
  page = 0;
  renderTable();
}});

renderTable();
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print(f"Loading database: {DB_PATH}")
    df = load_data(DB_PATH)
    print(f"  {len(df)} repositories loaded.")

    stats = compute_stats(df)
    data_json = json.dumps(stats, default=str)

    html = HTML_TEMPLATE.format(
        acronym=ACRONYM,
        data_json=data_json,
    )

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    abs_path = Path(OUTPUT_HTML).resolve()
    print(f"Dashboard saved: {abs_path}")
    webbrowser.open(abs_path.as_uri())


if __name__ == "__main__":
    main()
