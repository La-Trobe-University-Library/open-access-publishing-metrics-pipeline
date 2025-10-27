from pathlib import Path # Import Path for handling filesystem paths
import pandas as pd # Import pandas for data manipulation
from rp_pipeline.utils import *  # Import utility functions from the pipeline

# Function to load and clean CAUL journal list data
def load_caul_journals(root: Path, sheet_name: Optional[str]) -> pd.DataFrame:
    """
    Approximate the CAUL Journal List expansion from M.
    Key outputs: Journal Name, Journal Type, Journal Website, Publisher Name,
    Agreement, Field of Research, 'ISSN/EISSN', and 'JName clean'.
    """
    folder = root / "Journal List (CAUL)"
    df = concat_folder(folder, sheet_name)
    if df.empty:
        return df

    # Try to pick standard column names used in the M script
    # (Robust to slight header differences).
    colmap = {
        "Journal Name": "Journal Name",
        "Journal Type": "Journal Type",
        "Journal Website": "Journal Website",
        "Publisher Name": "Publisher Name",
        "Agreement": "Agreement",
        "Field of Research": "Field of Research",
        "ISSN": "ISSN",
        "eISSN": "eISSN",
        "La Trobe University": "La Trobe University"
    }
    # Ensure missing expected columns exist
    for k in colmap:
        if k not in df.columns:
            df[k] = pd.NA

    # Combine ISSN/eISSN into a single column where present
    # The original M did a more complex unpivot; here we prefer explicit columns
    # and later join on either ISSN or eISSN forms.
    df = unpivot_issns(df)

    # Agreement Key(s): uppercase remove spaces
    df["Agreement Key"] = df["Agreement"].apply(clean_agreement_key)

    # Filter La Trobe eligibility (D or Y)
    df["La Trobe University"] = df["La Trobe University"].astype(str).str.strip().str.upper()
    df = df[df["La Trobe University"] == "Y"].copy()

    # Clean journal name
    df["JName clean"] = df["Journal Name"].apply(clean_text_upper_alnum_space)

    # Trim/clean
    for c in ["Agreement", "Journal Name", "ISSN/EISSN"]:
        df[c] = df[c].astype(str).str.strip()

    # Keep a sane set of columns
    keep = [
        "Source", "Journal Name", "Journal Type", "Journal Website",
        "Publisher Name", "Agreement", "Field of Research",
        "ISSN", "eISSN", "ISSN/EISSN", "Agreement Key", "Agreement Keys",
        "La Trobe University", "JName clean"
    ]
    return df[[c for c in keep if c in df.columns]].drop_duplicates()

# Function to load SCImago metrics and normalize ISSNs
def load_scimago(root: Path, sheet_name: Optional[str]) -> pd.DataFrame:
    """Load SCImago and explode ISSNs; keep SJR, H index, Best Quartile, Categories."""
    folder = root / "SCImago (Scopus)"
    df = concat_folder(folder, sheet_name)
    if df.empty:
        return df

    # Standardise expected columns
    # Source, SJR, SJR Best Quartile, H index, Issn, Categories
    for col in ["SJR", "SJR Best Quartile", "H index", "Issn", "Categories"]:
        if col not in df.columns:
            df[col] = pd.NA

    df = unpivot_issns(df)

    # Clean numeric
    df["SJR"] = ensure_numeric(df["SJR"])

    # Keep selected columns
    df = df[["Source", "ISSN/EISSN", "SJR", "SJR Best Quartile", "H index", "Categories"]].dropna(subset=["ISSN/EISSN"]).drop_duplicates()
    return df

# Function to load Journal Citation Reports (JCR) metrics
def load_jcr(root: Path, sheet_name: Optional[str]) -> pd.DataFrame:
    """Load JCR minimal set: ISSN, Impact Factor, 5-year Impact Factor."""
    folder = root / "Journal Citation Reports (JCR)"
    df = concat_folder(folder, sheet_name)
    if df.empty:
        return df
    for col in ["ISSN", "Impact Factor", "5-year Impact Factor"]:
        if col not in df.columns:
            df[col] = pd.NA
    df = unpivot_issns(df)
    df["Impact Factor"] = ensure_numeric(df["Impact Factor"])
    df["5-year Impact Factor"] = ensure_numeric(df["5-year Impact Factor"])
    keep = ["Source", "ISSN/EISSN", "Impact Factor", "5-year Impact Factor"]
    return df[[c for c in keep if c in df.columns]].dropna(subset=["ISSN/EISSN"]).drop_duplicates()

# Function to load CiteScore and SNIP metrics from Elsevier
def load_citescore(root: Path, sheet_name: Optional[str]) -> pd.DataFrame:
    """
    Load CiteScore-like export.
    The M script unpivots ISSN columns; here we accept that an "ISSN/EISSN" column exists,
    or we attempt to find any column with 'issn' in its name.
    """
    folder = root / "CiteScore (Elsevier)"
    df = concat_folder(folder, sheet_name)
    if df.empty:
        return df

    df = unpivot_issns(df)

    # Keep metrics of interest: CiteScore, SNIP (and optional SJR if present)
    for col in ["CiteScore", "SNIP", "SJR", "Title", "Open Access"]:
        if col not in df.columns:
            df[col] = pd.NA
    df["CiteScore"] = ensure_numeric(df["CiteScore"])
    df["SNIP"] = ensure_numeric(df["SNIP"])

    keep = ["Source", "ISSN/EISSN", "CiteScore", "SNIP", "Title", "Open Access"]
    return df[[c for c in keep if c in df.columns]].dropna(subset=["ISSN/EISSN"]).drop_duplicates()

# Function to load Cap and Link metadata for inspection
def load_cap_and_link(root: Path, sheet_name: Optional[str]) -> pd.DataFrame:
    """Optional: load 'Cap and Link (CAUL)' Table1 if present; returned for inspection only."""
    folder = root / "Cap and Link (CAUL)"
    df_all = []
    for p in sorted(folder.glob("*")):
        if p.suffix.lower() in {".xlsx", ".xls"}:
            try:
                xls = pd.read_excel(p, sheet_name=None)
                first_name = next(iter(xls.keys()))
                df = xls[first_name]
            except Exception:
                df = pd.read_excel(p, sheet_name=sheet_name)
    
            df["Source"] = p.stem
            df["Agreement Key"] = df["Agreement"].apply(clean_agreement_key)
            df_all.append(df)
        elif p.suffix.lower() == ".csv":
            df = pd.read_csv(p)
            df["Source"] = p.stem
            df_all.append(df)
            df["Agreement Key"] = df["Agreement"].apply(clean_agreement_key)
    if not df_all:
        return pd.DataFrame()
    return pd.concat(df_all, ignore_index=True)