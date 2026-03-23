# Repository Finder

## Overview
Repository Finder is a tool that identifies and analyzes open-source repositories affiliated with universities using GitHub metadata and contributor analysis. The pipeline is split into four modular scripts:

- **main_scraping.py**: Fetches and stores raw repository, organization, and contributor data.

- **main_filtering.py**: Filters repositories based on affiliation with a specific university.

- **main_analysis.py**: Analyzes and visualizes filtered repository data, including license usage, language distribution, and community practices.

- **main_analysis_combined.py**: Analyzes and visualizes aggregated repository data by type. We use this script to analyze the data of the 10 University of California campuses.

## Installation
1. **Clone the repository:**
   ```sh
   git clone <repository-url>
   cd <repository-folder>
   ```
2. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```
3. **Set up GitHub API access:**
   - Create a `.env` file in the root directory and add:
     ```
     GITHUB_TOKEN=your_personal_access_token
     OPENAI_API_KEY=your_openai_token  # Optional: only needed for LLM-based models
     ```

## Scraping 

This step collects raw data from GitHub, including repositories, organizations, contributor activity, and extended metadata (e.g., README, license, templates). All data is stored in a structured SQLite database located in:
```
Data/db/repository_data_{ACRONYM}_database.db
```

There are already configuration files available for ten universities from the University of California System:
- UCB (University of California, Berkeley)  
- UCD (University of California, Davis)  
- UCI (University of California, Irvine)  
- UCLA (University of California, Los Angeles)  
- UCM (University of California, Merced)  
- UCR (University of California, Riverside)  
- UCSD (University of California, San Diego)  
- UCSB (University of California, Santa Barbara)  
- UCSC (University of California, Santa Cruz)  
- UCSF (University of California, San Francisco)

For a simple test case, replace `university_acronyms = ['UCSD']` in `repofinder/main_scraping.py` with the acronym of the university you would like to collect data from.

For any other university, create a configuration file inside the config folder and update the path accordingly.


Run the scraping script:
```sh
python repofinder/main_scraping.py
```


It will execute the following steps:
1. **Repository Finder:** Generates a JSON file with repositories based on a configuration file.
2. **Database Creation:** Reads the JSON file and creates a database.
3. **Organization Data Collection:** Gathers organization metadata.
4. **Repository Collection from Organizations:** Finds repositories owned by discovered organizations.
5. **User Data Collection:** Identifies users affiliated with the university.
6. **Repository Collection from Users:** Finds repositories owned by discovered users.
7. **Extra Features Extraction:** Retrieves extra features that are not collected by default (includes release downloads, readme, code of conduct, contributing, security policy, issue templates, pull request template, subscribers count).
8. **Contributor Data Collection:** Fetches contributor details for repositories.

Note: Execution times vary based on the number of repositories and API rate limits. You can selectively comment out steps in `main_scraping.py` to run only specific parts of the pipeline.

## Filtering
This step filters repositories in two stages: (1) identifying whether a repository is affiliated with a university and (2) classifying the type of project (DEV, EDU, DATA, DOCS, WEB, OTHER). Both tasks are handled in the `main_filtering.py` script.

1. Score-based classification, which applies a set of heuristic rules over repository and contributor metadata.
2. Supervised machine learning models using embedding models.
3. Large Language Model (LLM) classification using OpenAI models (e.g., GPT-4o, GPT-5-mini, and GPT-3.5-turbo).

There are manual labels and test sets for UCSB, UCSC and UCSD so you can use all classification methods for these three universities.

If you want to classify repositories for another university, provide a file named `{ACRONYM}_Random200.csv` with the columns `html_url` and `manual_label` in the following directory: 
     ```
  Data/manual_labels/{ACRONYM}_Random200.csv
     ```

Additionally, for ROC curve generation, you will need to provide a test set under:
     ```
  Data/test_data/test_set_{ACRONYM}.csv
     ```

For the type classification pipeline, we only use language models so no manual labels are required. However, to compute the accuracy of the classification, you will need to provide a test set under:
     ```
  Data/test_data/type_test_set_{ACRONYM}.csv
     ```

Project type test sets are provided for UCSB, UCSC and UCSD. 

Run the filtering script:
```sh
python repofinder/main_filtering.py
```

You can selectively comment out models in `main_filtering.py` to run only specific methods. This script generates prediction CSV files for each method (score-based, machine learning, and LLMs) in the `results/{ACRONYM}/` folder.

## Analysis
This step generates visual summaries and evaluation metrics based on the filtered repository data per university. It includes:

1. Language distribution 
2. License usage patterns
3. Adoption of best-practice repository features (e.g., README, security policy, issue templates)


Run the analysis script:
```sh
python repofinder/main_analysis.py
```

All plots are saved in the `plots/combined/` directory.

## Combined Type Analysis
This step generates visual summaries and evaluation metrics using filtered aggregated repository data. The script focuses on analyzing project characteristics by type and popularity.

It includes:

1. **Language distribution by project type**
2. **License usage patterns by project type**
3. **Adoption of best-practice repository features** (e.g., README, license, citation, issue templates)
4. **Project type distribution** across all affiliated repositories
5. **Feature heatmap by star buckets for DEV projects** — shows the presence of best practices in projects grouped by their GitHub star count
6. **Scatterplot of feature presence by stars** — visualizes how feature usage varies across individual projects based on their popularity

Run the combined analysis script:
```sh
python repofinder/main_analysis_combined.py
```

All plots are saved in the `plots/combined/` directory.

## Local Web Dashboard

A self-contained HTML dashboard can be generated from any scraped database. It requires no server — the output is a single HTML file that opens directly in your browser.

Run the dashboard generator after scraping:
```sh
python dashboard.py [ACRONYM]
```

For example:
```sh
python dashboard.py UVM
```

This reads `Data/db/repository_data_{ACRONYM}_database.db`, generates `dashboard_{ACRONYM}.html`, and opens it automatically in your browser.

The dashboard includes:
- **Summary stats** — total repositories, stars, forks, and unique languages
- **Language distribution** — doughnut chart of primary languages used
- **License distribution** — doughnut chart of license types
- **Community feature adoption** — horizontal bar chart showing the percentage of repositories with a README, license, code of conduct, contributing guide, security policy, issue templates, and PR template
- **Star count histogram** — distribution of repositories by star count
- **Repository explorer** — searchable, sortable table of up to 500 repositories with per-repo feature badges

## UVM Classification (March 2025)

The existing scraping pipeline (`main_scraping.py`) searches GitHub for "UVM" across repos, orgs, and users. This produces a large candidate set, but "UVM" is ambiguous — it matches the University of Vermont, Universidad del Valle de Mexico, and the UVM Verification Methodology (SystemVerilog). Below documents the additional classification work done to disambiguate these.

### Data produced by the scraping pipeline

The scraper uses three search strategies, all driven by `config/config_uvm.json`:

| File | Records | How collected |
|------|---------|---------------|
| `Data/json/repository_data_UVM.json` | 5,178 | GitHub repo search for "UVM" / "University of Vermont" / "uvm.edu" in name, description, readme, tags |
| `Data/json/organization_data_UVM.json` | 410 (124 unique) | GitHub user search (type:Organization) for "UVM" in name, login, description, company |
| `Data/json/repository_data_org_scraping_UVM.json` | 1,471 (403 unique) | **All** repos from matched orgs (not just UVM-related ones) |
| `Data/json/user_data_UVM.json` | 2,078 (900 unique) | GitHub user search for "UVM" in name, login, bio, company |
| `Data/json/repository_data_user_scraping_UVM.json` | 9,602 (4,540 unique) | **All** repos from matched users |
| `Data/db/githubrepo_name.csv` | 7,853 | Deduplicated union of the three repo sources above |

Key issue: the org/user scraping fetches **all** repos from anyone matching "UVM", not just their UVM-related work. A UVM professor's personal cooking repo ends up in the dataset. And "UVM" itself matches three different things.

### Classification approach

We classified bottom-up: orgs first, then users, then propagated to repos.

**Step 1: Enrich profiles via GraphQL** (`extract_metadata.py`)

Fetched full profiles (bio, company, location, description) for all 124 orgs and 900 users via the GitHub GraphQL API. Saved to:
- `Data/db/org_profiles.json` — 124 org profiles
- `Data/db/user_profiles.json` — 900 user profiles
- `Data/db/githubrepo_metadata.json` — 7,853 repo metadata (description, topics, language, owner info, stars, forks, license, dates)

**Step 2: Classify orgs** (124 unique)

Claude reviewed each org's profile (name, description, location, email, blog) and classified them. Labels: `uvm_vermont` (88), `not_uvm` (24, including 14 inactive/empty), `uvm_mexico` (9), `uvm_verification` (3).

Output: `Data/db/org_classification_claude.csv` (`labeled_by=claude`)

**Step 3: Classify users** (900 unique)

- Claude auto-classified using profile keywords: 225 `uvm_vermont` (strong Vermont signals like "University of Vermont" in bio), 297 `not_uvm` (verification engineers), 172 `not_uvm` (no repos = inactive).
- Remaining 206 uncertain users (had repos but ambiguous profiles): human (JSO) reviewed a sample of 50 via `label_users.py` — found zero UVM Vermont positives. All 206 marked `not_uvm`.

Output:
- `Data/db/user_classification_claude.csv` (`labeled_by=claude`)
- `Data/db/user_classification_manual.csv` (`labeled_by=human`, with timestamps)

**Step 4: Propagate to repos** (7,853)

Labels propagated by owner, with fallback to repo metadata:
1. Owner is a classified org → use org label
2. Owner is a classified user → use user label (manual overrides claude)
3. Neither → fall back to repo-level metadata (language=SystemVerilog → `not_uvm`, description mentions "University of Vermont" → `uvm_vermont`)

Output: `Data/db/repo_classification_claude.csv`

**Step 5: README-based reclassification**

After manual annotation revealed additional signals in README content, we applied keyword heuristics using the README and description stored in the SQLite database:

1. **"uvm.edu" → `uvm_vermont`** (421 repos): Repos whose README mentions "uvm.edu" were reclassified as Vermont-affiliated. Only 2 out of 4,035 `not_uvm` repos had this signal, confirming high precision.
2. **"verification" → `not_uvm`** (165 repos): Since "UVM" is also the Universal Verification Methodology (SystemVerilog), repos whose README or description mentions "verification" were reclassified as not UVM Vermont. 27 already-labeled `uvm_vermont` repos also contain this word incidentally, but those were already classified via org/user ownership and were not affected.
3. **"University of Vermont" → `uvm_vermont`** (336 repos): Repos whose README explicitly mentions "University of Vermont" were reclassified as Vermont-affiliated.
4. **Spanish keywords → `uvm_mexico`** (35 repos): Since "UVM" also refers to Universidad del Valle de México, repos with Spanish-language signals (e.g., "tarea", "proyecto", "actividad", "programación") in their README or description were reclassified as UVM Mexico. Strong signals like "uvm.edu.mx" or "campus uvm" triggered immediately; weaker signals required 2+ keywords plus "uvm" in the repo name or description.
5. **Non-Latin characters → `not_uvm`** (56 repos): Repos whose README or description contains CJK (Chinese, Japanese, Korean), Cyrillic, Arabic, Devanagari, or Thai characters were reclassified as not UVM Vermont, since UVM Vermont repos are expected to be in English.
6. **Virtual machine keywords → `not_uvm`** (35 repos): Repos mentioning "virtual machine", "bytecode", "opcode", "stack machine", or "instruction set" were reclassified, as these refer to VM projects unrelated to any university.
7. **NVIDIA/GPU/CUDA keywords → `not_uvm`** (88 repos): "UVM" in the NVIDIA ecosystem refers to Unified Virtual Memory (`nvidia_uvm` kernel module). Repos mentioning `nvidia_uvm`, `nvidia-uvm`, `cuda`, `gpu passthrough`, or `nvidia-drm` were reclassified.
8. **Underwater vehicle keywords → `not_uvm`** (7 repos): "UVMS" also stands for Underwater Vehicle-Manipulator System. Repos mentioning "underwater vehicle", "underwater manipulator", "underwater robot", or "subsea" were reclassified.
9. **Language detection → `uvm_mexico` / `not_uvm`** (64 repos): Used `langdetect` library to detect the language of each remaining uncertain repo's README+description. Spanish-detected repos (14) were reclassified as `uvm_mexico`; other non-English repos (50) as `not_uvm`.
10. **UVM university signals → `uvm_vermont`** (36 repos): Repos whose text contains university-context signals like "at UVM", "UVM CS", "uvm.edu", "UVM homework", "UVM hackathon", etc. were reclassified as Vermont-affiliated, excluding repos that also contain verification keywords (SystemVerilog, testbench, etc.).
11. **Vessel monitoring systems → `not_uvm`** (16 repos): Repos from UnionVMS and FocusFish organizations (Union Vessel Monitoring System) were reclassified.
12. **Repos named exactly "UVM"/"uvm" → `not_uvm`** (106 repos): Repos where the repository name (not owner) is exactly "UVM" or "uvm" were almost universally unrelated to the University of Vermont — they are version managers, virtual machines, verification libraries, or empty repos. One exception (`ospanoff/UVM`, grad assignments) was manually labeled as `uvm_vermont`.
13. **UV mapping / 3D graphics → `not_uvm`** (5 repos): Repos related to UV mapping (3D texture coordinates) were reclassified based on keywords like "uv map", "uv unwrap", "uvmap" in repo names or text.
14. **Verilog/HDL keywords → `not_uvm`** (44 repos): Repos mentioning Verilog, SystemVerilog, testbench, HDL, cocotb, verilator, or Accellera in their README/description, or using SystemVerilog/Verilog/VHDL as primary language, were reclassified. This catches verification-related repos that slipped through the earlier "verification" keyword check.
15. **Uveal melanoma / cancer keywords → `not_uvm`** (2 repos): "UVM" in the biomedical literature refers to Uveal Melanoma (a type of eye cancer). Repos mentioning "uveal melanoma", "tumor", "carcinoma", etc. were reclassified.
16. **Owner location/company not Vermont → `not_uvm`** (22 repos): Repos whose owner has a GitHub profile location or company clearly outside Vermont (e.g., Shanghai, Indonesia, Berlin, Wenzhou Medical University) were reclassified.
17. **Manual inspection of final 144 repos** (144 repos): The remaining repos were individually inspected based on repo name, description, and owner context. Classified as 27 `uvm_vermont`, 22 `uvm_mexico`, and 95 `not_uvm` (verification tools, version managers, UV sensors, microVMs, unrelated projects).

**Step 6: Manual org additions and owner propagation**

Some UVM Vermont orgs were missed by the original scraping pipeline because their GitHub profiles lacked explicit UVM metadata. We manually added orgs whose repos clearly showed UVM affiliation: CIROH-UVM (hydrology project at UVM), Vermont-Complex-Systems, VERSO-UVM, UVM-Wireless-Lab, and PIP-UVM. We also propagated labels from owners who already had `uvm_vermont` repos — if an owner had at least one Vermont-labeled repo, their remaining uncertain repos were reclassified as `uvm_vermont` (23 repos).

### Final classification results

| Label | Count | Description |
|-------|-------|-------------|
| `uvm_vermont` | 2,937 | University of Vermont affiliated |
| `not_uvm` | 4,785 | Not UVM Vermont (verification, VM, UV, Mexico, unrelated) |
| `uvm_mexico` | 128 | Universidad del Valle de Mexico |
| `uvm_verification` | 3 | UVM Verification Methodology orgs |

All 7,853 repos have been classified. Zero remain uncertain.

### Labeling tools

Interactive browser-based labeling scripts for manual review:

```sh
python uvm_classification/label_users.py          # label uncertain users (opens GitHub profiles)
python uvm_classification/label_repos.py          # label uncertain repos (random sample of 50)
python uvm_classification/label_repos.py -n 100   # label 100 repos
python uvm_classification/label_repos.py --all    # label all uncertain repos
```

Both scripts save after every label, track `labeled_by` (human vs claude) and `labeled_at` timestamps, and can be stopped/resumed freely.






