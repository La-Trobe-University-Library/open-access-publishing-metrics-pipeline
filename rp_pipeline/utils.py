"""
utils.py

This module provides a collection of utility functions used throughout the R&P pipeline.
These functions support data normalization, cleaning, and ingestion from various file formats.

Included utilities:
- ISSN normalization to standard format (NNNN-NNNN)
- Text cleaning for consistent journal name matching
- Robust numeric parsing (locale-safe)
- Reading CSV and Excel files with automatic delimiter detection
- Concatenating multiple files from a folder into a single DataFrame
- Unpivoting multiple ISSN columns into a normalized structure
- Fallback logic for missing journal websites using Google search

These helpers are designed to be modular, reusable, and robust to common data inconsistencies.
"""

from typing import Optional
from typing import List, Tuple
import re
import pandas as pd
import csv
import unicodedata
from pathlib import Path
import logging
from tqdm import tqdm

# Logging setup
logger = logging.getLogger(__name__)

# Regex
ISSN_RE = re.compile(r'^\s*(\d{4})-?(\d{3}[\dxX])\s*$')

def normalise_issn(value: str) -> Optional[str]:
    """Return ISSN in NNNN-NNNN format where possible; otherwise None."""
    if value is None:
        return None
    s = str(value).strip()
    if not s or s == "-":
        return None
    m = ISSN_RE.match(s)
    if m:
        return f"{m.group(1)}-{m.group(2)}".upper()
    # sometimes ISSNs are stored like '12345678' or '1234 5678'
    digits = re.sub(r'[^0-9Xx]', '', s)
    if len(digits) == 8:
        return f"{digits[:4]}-{digits[4:]}".upper()
    return None


# ✏️ CUSTOMIZATION: Add helper functions for new data sources if needed
# Example: def clean_doaj_field(value): ...
# Extend read_any() for DOAJ quirks
# Example: handle semicolon-delimited CSV
# ✏️ CUSTOMIZATION: Add DOAJ-specific cleaning
#def clean_doaj_field(value: str) -> str:
#    return str(value).strip().title()


def clean_agreement_key(s: str) -> str:
    if pd.isna(s):
        return ""
    # Normalize Unicode, remove all whitespace and control characters
    s = unicodedata.normalize("NFKC", str(s))
    s = re.sub(r"\s+", "", s)  # Remove all whitespace
    s = ''.join(c for c in s if unicodedata.category(c)[0] != 'C')  # Remove control chars
    return s.upper()

# ✏️ CUSTOMIZATION: Change fallback URL logic
# Current behavior: returns a Google search URL for the journal name
# Examples:
# - Use DOAJ lookup: return f"https://doaj.org/search/journals?q={journal_name}"
# - Use institutional resolver: return f"https://resolver.myuniversity.edu/?q={journal_name}"
def get_google_search_url(journal_name: str) -> str:
    return f"https://www.google.com/search?q=Journal+{journal_name}"


def first_nonblank(series: pd.Series):
    """DAX-like FIRSTNONBLANK: first value that is not NaN/empty string."""
    for v in series:
        if pd.notna(v) and str(v).strip() != "":
            return v
    return None

def clean_text_upper_alnum_space(s: str) -> str:
    """Mimics the JName clean: upper, trim/clean, only A-Z 0-9 space."""
    if pd.isna(s):
        return ""
    s = str(s).upper().strip()
    s = re.sub(r'[^A-Z0-9 ]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def ensure_numeric(series: pd.Series) -> pd.Series:
    """Parse numbers robustly (comma/locale safe)."""
    return pd.to_numeric(series.astype(str).str.replace(",", "."), errors="coerce")


def read_any(path, sheet_name=None):
    if path.suffix.lower() in {".csv", ".txt"}:
        with open(path, "r", encoding="utf-8") as f:
            sample = f.read(2048)
            try:
                dialect = csv.Sniffer().sniff(sample)
                sep = dialect.delimiter
            except csv.Error:
                sep = ","  # fallback to comma
        return pd.read_csv(path, sep=sep, encoding="utf-8")
    if path.suffix.lower() in {".xlsx", ".xls"}:
        try:
            if sheet_name is None:
                # Read all sheets and pick the first one
                xls = pd.read_excel(path, sheet_name=None, engine="openpyxl" if path.suffix.lower() == ".xlsx" else "xlrd")
                first_sheet = next(iter(xls.values()))
                return first_sheet
            else:
                return pd.read_excel(path, sheet_name=sheet_name, engine="openpyxl" if path.suffix.lower() == ".xlsx" else "xlrd")
        except (ValueError, FileNotFoundError, pd.errors.ExcelFileError) as e:
            logger.error(f"Error reading Excel file {path.name}: {e}")
            raise
    raise ValueError(f"Unsupported file type: {path}")

"""Concatenate all CSV/Excel files in a folder (non-recursive)."""
def concat_folder(folder: Path, sheet_name: Optional[str] = None) -> pd.DataFrame:
    parts = []
    for p in tqdm(sorted(folder.glob("*")), desc=f"Reading files from {folder.name}"):
        if p.is_file() and p.suffix.lower() in {".csv", ".xlsx", ".xls"}:
            try:
                df = read_any(p, sheet_name=sheet_name).copy()
                df["Source"] = p.stem
                parts.append(df)
            except Exception as e:
                logger.warning(f"Skipping {p.name} due to error: {e}")
    if not parts:
        logger.info(f"No valid files found in folder: {folder}")
        return pd.DataFrame()
    logger.info(f"Loaded {len(parts)} file(s) from {folder.name}")
    return pd.concat(parts, ignore_index=True)


def unpivot_issns(df: pd.DataFrame) -> pd.DataFrame:
    # Find all columns that look like ISSNs
    issn_cols = [c for c in df.columns if "issn" in c.lower()]
    if not issn_cols:
        df["ISSN/EISSN"] = pd.NA
        return df

    # Separate metadata columns
    meta_cols = [c for c in df.columns if c not in issn_cols]

    # Stack all ISSN columns into one
    parts = []
    for c in issn_cols:
        tmp = df[meta_cols + [c]].rename(columns={c: "ISSN/EISSN"})
        parts.append(tmp)

    df = pd.concat(parts, ignore_index=True)

    # Handle comma-separated ISSNs
    df["ISSN/EISSN"] = df["ISSN/EISSN"].astype(str).str.split(",")
    df = df.explode("ISSN/EISSN", ignore_index=True)

    # Normalize
    df["ISSN/EISSN"] = df["ISSN/EISSN"].apply(normalise_issn)

    return df