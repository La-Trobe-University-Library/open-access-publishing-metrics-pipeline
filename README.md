# Copyright
Other than any prior works of which it is a derivative, the copyright in this work is owned by La Trobe University.

# Licenses
Rights of use and distribution are granted under the terms of the GNU Affero General Public License version 3 (AGPL-3.0). You should find a copy of this license in the root of the repository.

# Acknowledgements
La Trobe University Library is grateful to all who have contributed to this prooject. You can see who they are are at [ACKNOWLEDGEMENTS.md](ACKNOWLEDGEMENTS.md)

This repository does not include any external datasets. It provides a pathway to integrate the following sources, assuming appropriate access:

SCImago Journal Rank (SJR) — Publicly available at scimagojr.com
Journal Citation Reports (JCR) — Accessed via La Trobe University's institutional subscription
CiteScore and SNIP — Accessed via La Trobe University's institutional subscription

# Contact
The maintainer of this repository is Mitch Lawton, who can be contacted at m.lawton@latrobe.edu.au


# 📊 Open Access Publishing and Metrics Pipeline
This repository provides a modular Python pipeline for processing and enriching journal metadata from La Trobe University's CAUL Read & Publish agreements. It integrates external metrics from SCImago, Journal Citation Reports (JCR), and CiteScore to support researcher publishing decisions.

The project replicates and extends a Power BI (DAX) workflow using Python and pandas, enabling reproducible and scalable analysis of journal coverage, impact, and eligibility.

## 🚀 Features
- Load and clean CAUL journal lists with La Trobe eligibility filtering
- Integrate SCImago (SJR, H-index, Quartile, Categories)
- Integrate JCR (Impact Factor, 5-Year Impact Factor)
- Integrate CiteScore and SNIP metrics
- Optional integration of APC cap and agreement metadata
- Deduplicated journal output with fallback links
- Summary report generation in Markdown
- Unit tests for loaders, measures, and utilities

## 📁 Folder Structure
```bash
open-access-publishing-and-metrics-pipeline/
├── data/                  # Optional: sample input files
│   ├── Cap and Link (CAUL)/
│   ├── CiteScore (Elsevier)/
│   ├── Journal Citation Reports (JCR)/
│   ├── Journal List (CAUL)/
│   ├── SCImago (Scopus)/
├── output/                # Optional: generated outputs
├── rp_pipeline/
│   ├── __init__.py
│   ├── utils.py
│   ├── loaders.py
│   ├── measures.py
│   └── main.py
├── tests/                 # Unit tests for each module
│   ├── test_utils.py
│   ├── test_loaders.py
│   ├── test_measures.py
├── samples/
│   ├── Cap and Link (CAUL)/
│       ├──CAUL_2025_Cap_Link_SAMPLE_FUN.xlsx
│   ├── CiteScore (Elsevier)/
│       ├──CiteScore_2025_SAMPLE_FUN.csv
│   ├── Journal Citation Reports (JCR)/
│       ├──JCR_2025_SAMPLE_FUN.csv
│   ├── Journal List (CAUL)/
│       ├──CAUL_2025_Title_List_SAMPLE_FUN.xlsx
│   ├── SCImago (Scopus)/
│       ├──SCImago_2024_SAMPLE_FUN.csv
├── ACKNOWLEDGEMENTS.md
├── LICENSE
├── requirements.txt
├── README.md
└── .gitignore
└── setup.py
```


## ⚙️ Installation

### 1. Create and activate a virtual environment
```pwsh
python -m venv venv
```
#### 1.1 Activate On Windows:
```pwsh
venv\Scripts\activate
```
#### 1.2 Activate On macOS/Linux:
```pwsh
source venv/bin/activate
```
### 2. Install the package in editable mode
```pwsh
pip install -e .
```
### 3. Install dependencies to the environement
```pwsh
pip install -r requirements.txt
```

## 🚀 Running the Pipeline
```pwsh
python rp_pipeline/main.py --input-root "data" --out "output/final_rp.csv"
```

## 🧪 Testing
```pwsh
pytest tests/
```

# 🧪 Running with Sample Data

This repository includes a sample input file (CAUL_2025_Title_List_SAMPLE_FUN.xlsx) located in the data/ folder. This file mimics vendor-supplied journal metadata but uses humorous and fictional journal titles for testing and demonstration purposes.

To run the pipeline using this sample:
```pwsh
python rp_pipeline/main.py --input-root "samples" --out "output/sample_output.csv"

```
The output will be saved in the output/ directory as sample_output.csv.


# ✏️ Pipeline Customisation Guide
This section explains how to customize the pipeline for your needs. Look for `# ✏️ CUSTOMIZATION` comments in the code for quick entry points.

**Key files to edit:**
- `rp_pipeline/measures.py` → For aggregation, deduplication, fallback logic.
- `rp_pipeline/loaders.py` → For adding new data sources.
- `README.md` → For documentation updates.

#### ✏️ Updating Tests After Customisation
When you add new fields or metrics to the pipeline (e.g., `Journal Type`, `Journal Citation Indicator`), you must also update the unit tests to reflect the new schema.

**Where to edit:**
- `tests/test_measures.py` → Update the mock CAUL DataFrame in `test_compute_measures_basic()` to include the new column(s).
- Add assertions for any new metrics or fields in the output DataFrame.

**Example:**
```pwsh
caul = pd.DataFrame({
    "Journal Name": ["Test Journal"],
    "ISSN/EISSN": ["1234-567X"],
    "Agreement": ["Read & Publish"],
    "Agreement Key": ["READ&PUBLISH"],
    "Publisher Name": ["Test Publisher"],
    "Journal Website": ["http://testjournal.com"],
    "Field of Research": ["Library Science"],
    "Journal Type": ["Hybrid"]  # ✏️ Newly added field
})

```
If you add new metrics:
- Include them in the aggregation dictionary in compute_measures().
- Add rename mappings and include them in final_columns.
- Update tests to assert these columns exist in the output.
Tip: Search for test_compute_measures_basic and modify the mock data and assertions accordingly.


##  ✏️ Adding and removing Fields to the Output
**Where to edit:**
- `compute_measures()` in `rp_pipeline/measures.py` → Add fields to `agg` and `final_columns`.

The pipeline uses DAX-like logic to aggregate journal metadata. If you want to include additional fields (e.g., Journal Type, Notes, or any other column from CAUL or other sources) in the final output:

### 1. Add the field to the aggregation step in compute_measures():
```pwsh
agg = merged.groupby(group_keys).agg({
    "Journal Type": pick,  # ✅ Use FIRSTNONBLANK logic
    "Publisher Name": pick,
    "Agreement": pick,
    # Add other fields here

```

The helper pick() function mimics Power BI’s FIRSTNONBLANK:
```pwsh
def pick(series):
    val = first_nonblank(series)
    return "N/A" if (val is None or (isinstance(val, str) and val.strip() == "")) else val

```

### 2. Add the field to the final column order so it appears in the CSV:
```pwsh
final_columns = [
    "Journal Name",
    "Journal Type",  # ✏️ Newly added field
    "Journal Website",
    "ISSN/s",
    "Publisher Name",
    "Agreement link",
    "Agreement type",
    "Field of Research (CAUL)",
    f"JIF (JCR, {jcr_year})",
    f"5-Year JIF (JCR, {jcr_year})",
    f"CiteScore (Scopus, {citescore_year})",
    f"SNIP (Scopus, {citescore_year})",
    f"SJR (SCImago, {scimago_year})",
    f"Best SJR Quartile (SCImago, {scimago_year})",
    f"H-Index (SCImago, {scimago_year})",
    f"Categories (SCImago, {scimago_year})"
]

```
### 3. When to use pick() vs. other logic:
- ✅ Use pick() for descriptive fields (e.g., Journal Type, Publisher Name).
- ➕ Use numeric aggregation (e.g., mean, sum) for metrics if needed.
- 🔗 Use concatenation for multi-valued fields (e.g., ISSNs, categories).


## ✏️ Changing Deduplication Logic
**Where to edit:**
- `compute_measures()` in `rp_pipeline/measures.py` → Modify `drop_duplicates()` subset.

Currently, compute_measures() deduplicates on:
```pwsh
out = out.drop_duplicates(subset=["Journal Name", "ISSNs by JName clean"])

```
### This means:
- Journals with the same name and the same set of ISSNs are considered duplicates.
- If a journal has multiple ISSNs, they are concatenated into ISSNs by JName clean before deduplication.

### Why you might change this
- If you want one row per Journal Name only, regardless of ISSNs.
- If you want to include Publisher Name or other fields in the uniqueness check.
- If you want to keep all rows (no deduplication).

### How to change it
Edit the subset argument in drop_duplicates() inside compute_measures():

Example 1: Deduplicate by Journal Name only
```pwsh
out = out.drop_duplicates(subset=["Journal Name"])

```

Example 2: Deduplicate by Journal Name + Publisher Name
```pwsh
out = out.drop_duplicates(subset=["Journal Name", "Publisher Name"])

```

Example 3: Keep all rows (disable deduplication)
```pwsh
# Comment out or remove the drop_duplicates line
# out = out.drop_duplicates(subset=["Journal Name", "ISSNs by JName clean"])

```

### Things to consider
- Deduplication happens after merging all metrics, so changing this may increase row count.
- If you remove deduplication, journals with multiple ISSNs will appear multiple times.
- If you deduplicate too aggressively (e.g., by Journal Name only), you might lose ISSN-specific metrics.

## Adding New Metrics
**Where to edit:**
- `compute_measures()` in `rp_pipeline/measures.py` → Add metric to `agg`, rename mapping, and `final_columns`.

The pipeline dynamically renames and outputs metrics from SCImago, JCR, and CiteScore. If you want to add a new metric (e.g., Journal Citation Indicator, Eigenfactor, or any custom metric), follow these steps:

### 1. Add the metric to the aggregation step
Locate the agg dictionary in compute_measures():
```pwsh
agg = merged.groupby(group_keys).agg({
    "Impact Factor": pick,
    "5-year Impact Factor": pick,
    "SJR": pick,
    "H index": pick,
    "SNIP": pick,
    "CiteScore": pick,
    "SJR Best Quartile": pick,
    "Categories": pick,
    # ✏️ Add your new metric here
    "Journal Citation Indicator": pick,  # Example
}).reset_index()

```
Use pick() for descriptive or single-value metrics to mimic Power BI’s FIRSTNONBLANK logic.

### 2. Rename the metric for clarity
After aggregation, metrics are renamed with year labels:
```pwsh
agg = agg.rename(columns={
    "Impact Factor": f"JIF (JCR, {jcr_year})",
    "5-year Impact Factor": f"5-Year JIF (JCR, {jcr_year})",
    "CiteScore": f"CiteScore (Scopus, {citescore_year})",
    "SNIP": f"SNIP (Scopus, {citescore_year})",
    "SJR": f"SJR (SCImago, {scimago_year})",
    "SJR Best Quartile": f"Best SJR Quartile (SCImago, {scimago_year})",
    "H index": f"H-Index (SCImago, {scimago_year})",
    "Categories": f"Categories (SCImago, {scimago_year})",
    # ✏️ Add rename for your new metric
    "Journal Citation Indicator": f"JCI (JCR, {jcr_year})"
})

```

### 3. Add the metric to the final output columns
Ensure the metric appears in the CSV by adding it to final_columns:
```pwsh
final_columns = [
    "Journal Name",
    "Journal Type",
    "Journal Website",
    "ISSN/s",
    "Publisher Name",
    "Agreement link",
    "Agreement type",
    "Field of Research (CAUL)",
    f"JIF (JCR, {jcr_year})",
    f"5-Year JIF (JCR, {jcr_year})",
    f"CiteScore (Scopus, {citescore_year})",
    f"SNIP (Scopus, {citescore_year})",
    f"SJR (SCImago, {scimago_year})",
    f"Best SJR Quartile (SCImago, {scimago_year})",
    f"H-Index (SCImago, {scimago_year})",
    f"Categories (SCImago, {scimago_year})",
    f"JCI (JCR, {jcr_year})"  # ✏️ Newly added metric
]

```

### 4. Things to consider
- If the metric is numeric, you can use pick() or apply an aggregation like mean or max if multiple values exist.
- Ensure the metric exists in the merged DataFrame before adding it to agg.
- If the metric comes from a new data source, you’ll need to:
    - Add it in the loader function (e.g., load_jcr()).
    - Normalize ISSNs using unpivot_issns() for proper joins.


## ✏️ Changing Fallback Logic for Journal Website
**Where to edit:**
- `compute_measures()` in `rp_pipeline/measures.py` → Modify `site_fallback()` function.

The pipeline ensures that every journal has a valid website link. If the Journal Website field is missing or blank, it falls back to a Google search URL for the journal name.

This logic is implemented in compute_measures():
```pwsh
def site_fallback(row):
    site = row.get("Journal Website")
    jname = row.get("Journal Name")
    if pd.isna(site) or str(site).strip() == "" or str(site).strip().upper() == "N/A":
        return get_google_search_url(jname)  # Default fallback
    return site

out["Journal Website"] = out.apply(site_fallback, axis=1)

```

### Why you might change this
- You want to use the publisher homepage instead of Google search.
- You want to use a custom institutional resolver or Open Access lookup.
- You want to leave the field blank instead of adding a fallback.

### How to customize it
Edit the site_fallback() function:

#### Example 1: Leave blank if missing
```pwsh
def site_fallback(row):
    site = row.get("Journal Website")
    return site if pd.notna(site) and str(site).strip() != "" else ""

```

#### Example 2: Use publisher homepage if available
```pwsh
def site_fallback(row):
    site = row.get("Journal Website")
    publisher = row.get("Publisher Name")
    if pd.isna(site) or str(site).strip() == "":
        return f"https://www.{publisher.replace(' ', '').lower()}.com"
    return site

```

#### Example 3: Use an Open Access lookup service
```pwsh
def site_fallback(row):
    site = row.get("Journal Website")
    jname = row.get("Journal Name")
    if pd.isna(site) or str(site).strip() == "":
        return f"https://doaj.org/search/journals?ref=homepage&q={jname}"
    return site

```

### Things to consider
- Fallback logic runs after all merges, so it applies to the final dataset.
- If you use external services (e.g., DOAJ), ensure URLs are properly encoded.
- If you remove fallback entirely, some journals will have blank links in the output.


## ✏️ Adding New Data Sources
**Where to edit:**
- `rp_pipeline/loaders.py` → Create new loader function.
- `main.py` → Load the new dataset.
- `compute_measures()` in `rp_pipeline/measures.py` → Merge and aggregate new fields.

The pipeline is modular, so you can integrate additional datasets (e.g., DOAJ, Crossref, Unpaywall, or custom publisher lists**) by following these steps:

### 1. Create a Loader Function
Add a new function in loaders.py similar to existing ones (load_scimago(), load_jcr()):

Example: load_doaj()
```pwsh
def load_doaj(root: Path, sheet_name: Optional[str]) -> pd.DataFrame:
    """
    Load DOAJ data and normalize ISSNs.
    Expected columns: Journal Name, ISSN, eISSN, Open Access status, etc.
    """
    folder = root / "DOAJ"
    df = concat_folder(folder, sheet_name)
    if df.empty:
        return df

    # Normalize ISSNs
    df = unpivot_issns(df)

    # Ensure expected columns exist
    for col in ["Journal Name", "Open Access", "Publisher"]:
        if col not in df.columns:
            df[col] = pd.NA

    # Keep relevant columns
    keep = ["Source", "ISSN/EISSN", "Journal Name", "Open Access", "Publisher"]
    return df[[c for c in keep if c in df.columns]].dropna(subset=["ISSN/EISSN"]).drop_duplicates()

```
Key points:
- Use concat_folder() to read all files in the folder.
- Use unpivot_issns() to normalize ISSNs for joining.
- Add missing columns with pd.NA for consistency.


### 2. Add the Loader to main.py
In main.py, load the new dataset:
```pwsh
doaj = load_doaj(root, args.sheet_name)
logger.info(f">>> Loaded DOAJ: {len(doaj)} rows")

```

### 3. Merge in compute_measures()
Update compute_measures() to join the new dataset:
```pwsh
merged = merged.merge(doaj, on="ISSN/EISSN", how="left", suffixes=("", "_DOAJ"))

```

### 4. Aggregate New Fields
Add fields from the new source to the aggregation step:
```pwsh
agg = merged.groupby(group_keys).agg({
    "Open Access": pick,  # From DOAJ
    "Publisher": pick,     # From DOAJ
    # Existing fields...
}).reset_index()

```

### 5. Rename and Add to Output
Rename the new fields for clarity:
```pwsh
agg = agg.rename(columns={
    "Open Access": "Open Access (DOAJ)",
    "Publisher": "Publisher (DOAJ)"
})

```

Add them to final_columns:
```pwsh
final_columns += ["Open Access (DOAJ)", "Publisher (DOAJ)"]

```

### 6. Folder Structure
Create a folder for the new source under data/:
```bash
data/
├── DOAJ/
│   ├── doaj_2025.csv
```

### 7. Things to Consider
- ISSN Normalization: Always use unpivot_issns() for consistent joins.
- Column Naming: Keep names descriptive and avoid collisions.
- Performance: Large datasets may require optimization (e.g., chunked reading).
- Testing: Add a unit test in tests/test_loaders.py for your new loader.

### Example: Adding DOAJ
After following these steps, your pipeline will enrich journals with Open Access status from DOAJ.




# 📊 Sample Data: CAUL year Title List
This repository includes a sample input file for testing the pipeline:
📁 File sample Location:
```pwsh
samples/Journal List (CAUL)/CAUL_2025_Title_List_SAMPLE_FUN.xlsx
```

📁 Your File Location: (any name on the file as it uses the folder)
```pwsh
data/Journal List (CAUL)/CAUL_2025_Title _List.xlsx
```

### 🧾 Description

This file mimics the structure of vendor-supplied journal metadata from CAUL Read & Publish agreements. It includes fictional journal titles and metadata, designed for testing and demonstration purposes without using real or sensitive data. You can download the XLSX from here: https://caul.libguides.com/read-and-publish/title-list#s-lg-box-22923575


### 🧱 Structure (Key Columns)

The following table describes the key columns found in the sample CAUL title list:

| Column Name                   | Description                                                                 |
|------------------------------|-----------------------------------------------------------------------------|
| `Journal Name`               | Full title of the journal.                                                  |
| `Journal Type`               | Indicates whether the journal is Hybrid, Fully Open Access, or Subscription.|
| `Journal Abbreviation`       | Shortened or acronym version of the journal name.                           |
| `ISSN`                       | International Standard Serial Number for the print version.                 |
| `eISSN`                      | International Standard Serial Number for the electronic version.            |
| `Journal Website`            | URL to the journal's homepage or publisher page.                            |
| `Publisher Name`             | Name of the publishing company or organization.                             |
| `Imprint Name`               | Sub-brand or imprint under the main publisher.                              |
| `Notes`                      | Additional comments or metadata about the journal.                          |
| `Eligible`                   | Comma-separated list of institutions eligible for Read & Publish agreement. |
| `Not eligible`               | Comma-separated list of institutions not eligible for the agreement.        |
| `Discount`                   | Comma-separated list of institutions receiving a discount.                  |
| `Agreement`                  | Name of the agreement or consortium (e.g., Springer, CUP).                  |
| `Field of Research`          | Disciplinary classification or research field of the journal.               |
| `Participating Institutions` | Summary count of institutions participating in the agreement (e.g., 55/60). |

This structure is designed to match vendor-supplied metadata and is used as input to the R&P pipeline.

### 🧪 Example Row

| Journal Name               | Journal Type | ISSN      | eISSN     | Journal Website                         | Publisher Name        | Field of Research     | La Trobe University |
|---------------------------|--------------|-----------|-----------|------------------------------------------|------------------------|------------------------|----------------------|
| Journal of Overdue Theories | Hybrid       | 12345678  | 87654321  | https://overdue.theories.example.com     | Procrastination Press | Library Philosophy     | Y                    |



# 📊 Sample Data: CiteScore year
This repository includes a sample input file for testing the pipeline:
📁 File sample Location:
```pwsh
samples/CiteScore (Elsevier)/CiteScore_2024_sample.csv
```

📁 Your File Location: (any name on the file as it uses the folder)
```pwsh
data/CiteScore (Elsevier)/CiteScore_2024.csv
```

## 🧾 Description
This file mimics the structure of vendor-supplied journal metrics from Scopus. It includes real journal titles and associated CiteScore metrics, designed for testing and demonstration purposes. Each row represents a journal-subject area combination.


### 🧱 Structure (Key Columns)

The following table describes the key columns found in the CiteScore sample file:

| Column Name                             | Description                                                                 |
|----------------------------------------|-----------------------------------------------------------------------------|
| `Scopus Source ID`                     | Unique identifier for the journal in the Scopus database.                   |
| `Title`                                | Full title of the journal.                                                  |
| `Citation Count`                       | Total number of citations received in the CiteScore calculation window.     |
| `Scholarly Output`                     | Number of documents published in the CiteScore window.                      |
| `Percent Cited`                        | Percentage of documents that received at least one citation.                |
| `CiteScore`                            | CiteScore metric (citations per document over 4 years).                     |
| `SNIP`                                 | Source Normalized Impact per Paper — field-normalized citation impact.      |
| `SJR`                                  | SCImago Journal Rank — prestige-weighted citation metric.                   |
| `Scopus ASJC Code (Sub-subject Area)` | All Science Journal Classification (ASJC) code for the subject area.       |
| `Scopus Sub-Subject Area`              | Name of the sub-discipline (e.g., Clinical Psychology, History).            |
| `Percentile`                           | Percentile ranking of the journal in its subject area.                      |
| `RANK`                                 | Journal’s rank within its subject area.                                     |
| `Rank Out Of`                          | Total number of journals in the subject area.                               |
| `Publisher`                            | Name of the publishing imprint.                                             |
| `Main Publisher`                       | Parent publishing company.                                                  |
| `Type`                                 | Publication type (e.g., journal, book series).                              |
| `Open Access`                          | Indicates whether the journal is open access.                               |
| `Quartile`                             | Quartile ranking (1 = Q1, 4 = Q4) within the subject area.                  |
| `Top 10% (CiteScore Percentile)`       | Whether the journal is in the top 10% of its subject area.                 |
| `URL Scopus Source ID`                 | Link to the journal’s Scopus profile.                                       |
| `Print ISSN`                           | Print ISSN of the journal.                                                  |
| `E-ISSN`                               | Electronic ISSN of the journal.                                             |


### 🧪 Example Row

| Scopus Source ID | Title                       | Citation Count | Scholarly Output | Percent Cited | CiteScore | SNIP | SJR | Scopus ASJC Code (Sub-subject Area) | Scopus Sub-Subject Area | Percentile | RANK | Rank Out Of | Publisher             | Main Publisher | Type | Open Access | Quartile | Top 10% (CiteScore Percentile) | URL Scopus Source ID | Print ISSN | E-ISSN   |
|------------------|-----------------------------|----------------|------------------|----------------|-----------|------|-----|--------------------------------------|--------------------------|------------|------|--------------|------------------------|----------------|------|--------------|----------|-------------------------------|------------------------|-------------|----------|
| xxxxx            | Journal of Overdue Theories | 11111          | 2222             | 33             | 4.2       | 1.1  | 0.9 | 4444                                 | Library Philosophy       | 55         | 66   | 7777         | Procrastination Press | xxxxxx         | x    | xx           | 8        | xxxxx                        | xxxxxxxx              | 12345678    | 87654321 |


# 📊 Sample Data: JCR year
This repository includes a sample input file for testing the pipeline:
📁 File sample Location:
```pwsh
samples/Journal Citation Report (JCR)/JCR_2025_SAMPLE_FUN.csv
```

📁 Your File Location: (any name on the file as it uses the folder)
```pwsh
data/Journal Citation Report (JCR)/JCR, 2024.csv
```

## 🧾 Description
This file mimics the structure of vendor-supplied Journal Citation Reports (JCR) data. It includes fictional journal titles and metrics such as Impact Factor, Journal Citation Indicator (JCI), and quartile rankings. Each row represents a journal-subject area combination, designed for testing and demonstration purposes.

### 🧱 Structure (Key Columns)

The following table describes the key columns found in the JCR sample file:

| Column Name                     | Description                                                                 |
|--------------------------------|-----------------------------------------------------------------------------|
| `ID`                           | Internal identifier for the journal entry.                                  |
| `ISSN`                         | International Standard Serial Number.                                       |
| `Impact Factor`                | The 2-year Journal Impact Factor.                                           |
| `5-year Impact Factor`         | The 5-year Journal Impact Factor.                                           |
| `Title`                        | Full title of the journal.                                                  |
| `Title20`                      | Alternate or shortened title.                                               |
| `ISO Abbreviation`             | Abbreviated journal title.                                                  |
| `JIF Without Self-Citations`   | Impact Factor excluding journal self-citations.                             |
| `Average JIF Percentile`       | Average percentile across all categories.                                   |
| `Best JIF Category`            | Subject category with the best JIF ranking.                                 |
| `Best JIF Percentile`          | Percentile in the best JIF category.                                        |
| `Best JIF Quartile`            | Quartile in the best JIF category (Q1–Q4).                                  |
| `Best JIF Rank`                | Rank in the best JIF category.                                              |
| `Best JIF Rank (Text)`         | Formatted rank in the best JIF category.                                    |
| `Journal Citation Indicator`   | JCI score for the journal.                                                  |
| `Best JCI Category`            | Subject category with the best JCI ranking.                                 |
| `Best JCI Percentile`          | Percentile in the best JCI category.                                        |
| `Best JCI Quartile`            | Quartile in the best JCI category.                                          |
| `Best JCI Rank`                | Rank in the best JCI category.                                              |
| `Best JCI Rank (Text)`         | Formatted rank in the best JCI category.                                    |
| `Article Citation Median`      | Median number of citations per article.                                     |
| `Articles`                     | Number of articles published.                                               |
| `Reviews`                      | Number of review articles published.                                        |
| `Other`                        | Number of other document types published.                                   |
| `Times Cited`                  | Total number of citations received.                                         |
| `Unlinked Citations`           | Citations not linked to specific documents.                                 |
| `Article Influence Score`      | Average influence of each article.                                          |
| `Eigenfactor Score`            | Total importance to the scientific community.                               |
| `Normalized Eigenfactor`       | Field-normalized Eigenfactor score.                                         |
| `Immediacy Index`              | Average citations in the year of publication.                               |
| `Total Cites`                  | Total citations received by the journal.                                    |
| `Citable Items`                | Number of articles and reviews considered citable.                          |
| `Cited Half-Life`              | Median age of articles cited.                                               |
| `Citing Half-Life`             | Median age of articles cited by the journal.                                |
| `Publication Source Country/Region` | Country or region of the journal’s publisher.                        |
| `Publisher`                    | Name of the publishing company.                                             |
| `WoS Categories`               | Web of Science subject categories.                                          |


### 🧪 Example Row

| Title                        | Impact Factor | 5-year Impact Factor | Best JIF Category         | Best JIF Quartile | Publisher     | Publication Source Country/Region |
|-----------------------------|----------------|------------------------|----------------------------|--------------------|----------------|------------------------------------|
| Journal of Overdue Theories | 3.9            | 3.7                    | Library Anxiety Studies    | Q4                 | Late Press     | USA                                |


# 📊 Sample Data: SCImago year
This repository includes a sample input file for testing the pipeline:
📁 File sample Location:
```pwsh
samples/SCImago (Scopus)/SCImago_2024_SAMPLE_FUN.csv
```

📁 Your File Location: (any name on the file as it uses the folder)
```pwsh
data/SCImago (Scopus)/SCImago_2024.csv
```

## 🧾 Description
This file mimics the structure of SCImago Journal Rank (SJR) data. It includes fictional journal titles and metrics such as SJR score, quartile rankings, citation counts, and subject classifications. Each row represents a journal and its associated metrics, designed for testing and demonstration purposes.

### 🧱 Structure (Key Columns)

The following table describes the key columns found in the SCImago sample file:

| Column Name                   | Description                                                                 |
|------------------------------|-----------------------------------------------------------------------------|
| `Rank`                       | Journal's rank in the SCImago database.                                     |
| `Sourceid`                   | Unique identifier for the journal.                                          |
| `Title`                      | Full title of the journal.                                                  |
| `Type`                       | Type of source (e.g., journal, conference).                                 |
| `Issn`                       | ISSN(s) of the journal (print and/or electronic).                           |
| `SJR`                        | SCImago Journal Rank — prestige-weighted citation metric.                   |
| `SJR Best Quartile`          | Best quartile ranking (Q1–Q4) across subject categories.                    |
| `H index`                    | H-index of the journal.                                                     |
| `Total Docs. (2024)`         | Number of documents published in 2024.                                      |
| `Total Docs. (3years)`       | Number of documents published in the last 3 years.                          |
| `Total Refs.`                | Total number of references in the journal.                                  |
| `Total Citations (3years)`   | Total citations received in the last 3 years.                               |
| `Citable Docs. (3years)`     | Number of citable documents in the last 3 years.                            |
| `Citations / Doc. (2years)`  | Average citations per document over the last 2 years.                       |
| `Ref. / Doc.`                | Average number of references per document.                                  |
| `%Female`                    | Percentage of female authors (if available).                                |
| `Overton`                    | Overton policy citation count (if available).                               |
| `SDG`                        | Sustainable Development Goal alignment (if available).                      |
| `Country`                    | Country of the journal's publisher.                                         |
| `Region`                     | Geographic region of the publisher.                                         |
| `Publisher`                  | Name of the publishing company.                                             |
| `Coverage`                   | Coverage code or range (e.g., years).                                       |
| `Categories`                 | SCImago subject categories with quartile rankings.                          |
| `Areas`                      | Broader subject areas (e.g., Medicine, Social Sciences).                    |
``

### 🧪 Example Row

| Title                      | SJR   | SJR Best Quartile | H index | Country       | Publisher     | Categories                                                                 | Areas                                               |
|---------------------------|-------|-------------------|---------|----------------|----------------|------------------------------------------------------------------------------|-----------------------------------------------------|
| Journal of Overdue Theories | 34,054 | Q1                | 111     | United States | Late Press     | Library and Information Sciences (Q2); Metadata Philosophy (Q1); Archival Anxiety (Q3); Dewey Decimal Dynamics (Q2); Cataloguing Confusion (Q4) | Library and Information Science; Philosophy of Knowledge; Metadata Studies |
``

# 📊 Sample Data: CAUL Agreement Cap & Link
This file tracks whether each CAUL Read & Publish agreement is capped or uncapped, and includes links to:
- The public agreement page
- The publisher data submission form
- The approval statistics dashboard

📁 File sample Location:
```pwsh
samples/SCImago (Scopus)/SCImago_2024_SAMPLE_FUN.csv
```

📁 Your File Location: (any name on the file as it uses the folder)
```pwsh
data/SCImago (Scopus)/SCImago_2024.csv
```

## 🧾 Description
This spreadsheet is manually compiled by visiting the CAUL Read & Publish Agreements website. For each agreement, it records:

Whether the agreement is capped (i.e., has a publishing limit) or uncapped
- A link to the public-facing agreement page
- A link to the publisher data submission form (e.g., Airtable)
- A link to the approval statistics dashboard (e.g., Airtable or Power BI)

This data is used to enrich reporting pipelines and dashboards with contextual information about each publisher agreement.

### 🧱 Structure (Key Columns)

The following table describes the key columns found in the CAUL Cap & Link file:

| Column Name                          | Description                                                                 |
|-------------------------------------|-----------------------------------------------------------------------------|
| `Agreement`                         | Short name or code for the agreement (e.g., SHUSH, MARC).                   |
| `Agreement type`                    | Indicates whether the agreement is capped or uncapped.                      |
| `Link`                              | URL to the public-facing agreement page on the CAUL or institutional site. |
| `Publisher data`                    | Link to the publisher's data submission form (e.g., Airtable).              |
| `Capped agreement approval statistics` | Link to the approval statistics dashboard for capped agreements.         |
