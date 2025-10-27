"""
measures.py

This module computes journal-level metrics by merging CAUL journal data with SCImago, JCR, and CiteScore datasets.
It mimics DAX-like logic from Power BI and outputs a clean, deduplicated DataFrame.
"""

import pandas as pd
from rp_pipeline.utils import *
import logging

# Set up logger for this module
logger = logging.getLogger(__name__)

"""
    Compute journal-level metrics by merging CAUL journal list with SCImago, JCR, and CiteScore datasets.
    Performs grouping, aggregation, and fallback logic to ensure completeness.

    Parameters:
        caul_df (pd.DataFrame): CAUL journal list
        scimago_df (pd.DataFrame): SCImago metrics
        jcr_df (pd.DataFrame): JCR metrics
        cs_df (pd.DataFrame): CiteScore metrics
        cap (pd.DataFrame): Cap and Link metadata
        jcr_year (int): Year for JCR metrics
        scimago_year (int): Year for SCImago metrics
        citescore_year (int): Year for CiteScore metrics

    Returns:
        pd.DataFrame: Final enriched and deduplicated journal dataset
    """


def compute_measures(caul_df: pd.DataFrame, scimago_df: pd.DataFrame, jcr_df: pd.DataFrame, cs_df: pd.DataFrame, cap: pd.DataFrame, jcr_year: int, scimago_year: int, citescore_year: int) -> pd.DataFrame:
    """
    Join on ISSN/EISSN and compute DAX-like measures per journal.
    Output schema: one row per (Journal Name, ISSN/EISSN) with added metrics and safe fallbacks.
    """
    # Create a working copy of CAUL data and clean journal names
    base = caul_df.copy()
    base["JName clean"] = base["Journal Name"].apply(clean_text_upper_alnum_space)

    # Join with SCImago/JCR/CiteScore on ISSN/EISSN (left joins to preserve CAUL set)
    # Merge SCImago, JCR, and CiteScore metrics using ISSN/EISSN
    merged = base.merge(scimago_df, on="ISSN/EISSN", how="left", suffixes=("", "_SC"))
    merged = merged.merge(jcr_df, on="ISSN/EISSN", how="left", suffixes=("", "_JCR"))
    merged = merged.merge(cs_df, on="ISSN/EISSN", how="left", suffixes=("", "_CS"))

    # Group by cleaned journal name and concatenate all ISSNs
    # Concatenate all ISSNs grouped by cleaned journal name
    issn_concat_clean = (
        merged.groupby("JName clean")["ISSN/EISSN"]
        .apply(lambda s: ", ".join(sorted({
            x for x in s.dropna().astype(str).str.strip()
            if x and x.upper() != "NONE"
        })))
        .reset_index()
        .rename(columns={"ISSN/EISSN": "ISSNs by JName clean"})
    )

    # Group by Journal (using ISSN/EISSN + Journal Name to disambiguate) for FIRSTNONBLANK logic
    group_keys = ["Journal Name", "ISSN/EISSN"]

    # Helper function to mimic DAX FIRSTNONBLANK logic
    def pick(series):
        val = first_nonblank(series)
        return "N/A" if (val is None or (isinstance(val, str) and val.strip() == "")) else val

    # Aggregate metrics using FIRSTNONBLANK logic
    agg = merged.groupby(group_keys).agg({
        "5-year Impact Factor": pick,
        "Impact Factor": pick,
        "SJR": pick,
        "H index": pick,
        "SNIP": pick,
        "CiteScore": pick,
        "SJR Best Quartile": pick,
        "Categories": pick,
        "Journal Website": pick,
        "Field of Research": pick,
        "Publisher Name": pick,
        "Agreement": pick,
        "Agreement Key": pick
    }).reset_index()

    # Add cleaned journal name for grouping
    agg["JName clean"] = agg["Journal Name"].apply(clean_text_upper_alnum_space)

    # Merge concatenated ISSNs by cleaned journal name
    # Merge concatenated ISSNs into the final output
    out = agg.merge(issn_concat_clean, on="JName clean", how="left")

    # Ensure Agreement Key is cleaned consistently
    if "Agreement" in out.columns:
        out["Agreement Key"] = out["Agreement"].astype(str).str.replace(r"\s+", "", regex=True).str.upper()
    else:
        logger.info("⚠️ 'Agreement' column missing in `out`")

    if "Agreement" in cap.columns:
        cap["Agreement Key"] = cap["Agreement"].astype(str).str.replace(r"\s+", "", regex=True).str.upper()
    else:
        logger.info("⚠️ 'Agreement' column missing in `cap`")

    
    # Rename to match DAX measure labels
    agg = agg.rename(columns={
    "5-year Impact Factor": f"5-Year JIF (JCR, {jcr_year})",
    "Impact Factor": f"JIF (JCR, {jcr_year})",
    "CiteScore": f"CiteScore (Scopus, {citescore_year})",
    "SNIP": f"SNIP (Scopus, {citescore_year})",
    "SJR": f"SJR (SCImago, {scimago_year})",
    "SJR Best Quartile": f"Best SJR Quartile (SCImago, {scimago_year})",
    "H index": f"H-Index (SCImago, {scimago_year})",
    "Categories": f"Categories (SCImago, {scimago_year})",
    "Field of Research": "Field of Research (CAUL)"
    })


    # Categories \n substitution like DAX SUBSTITUTE("; ", UNICHAR(10))
    agg[f"Categories (SCImago, {scimago_year})"] = agg[f"Categories (SCImago, {scimago_year})"].apply(
        lambda x: "N/A" if (x == "N/A" or pd.isna(x)) else str(x).replace("; ", "\n")
    )

    # Merge concatenated ISSNs back into the output using cleaned journal name
    # Merge concatenated ISSNs into the final output
    out = agg.merge(issn_concat_clean, on="JName clean", how="left")

    # Journal Website fallback to Google if missing
    def site_fallback(row):
        site = row.get("Journal Website")
        jname = row.get("Journal Name")
        if pd.isna(site) or str(site).strip() == "" or str(site).strip().upper() == "N/A":
            return get_google_search_url(jname)
        return site
    # Fallback to Google search URL if Journal Website is missing
    out["Journal Website"] = out.apply(site_fallback, axis=1)

    # Merge Cap and Link data using Agreement Key
    if not cap.empty and "Agreement Key" in cap.columns:
        cap["Agreement Key"] = cap["Agreement"].astype(str).str.replace(r"\s+", "", regex=True).str.upper()
        cap_clean = cap[[
            "Agreement Key",
            "Agreement type",
            "Link",
            "Publisher data",
            "Capped agreement approval statistics"
        ]].drop_duplicates()

        # Merge Cap and Link metadata using Agreement Key
        if "Agreement Key" in out.columns:
            out = out.merge(cap_clean, on="Agreement Key", how="left")
        else:
            logger.info("⚠️ 'Agreement Key' missing in output — Cap & Link merge skipped.")
    else:
        logger.info("⚠️ Cap & Link data missing or malformed — merge skipped.")

    # Remove duplicates based on Journal Name and ISSNs by JName clean
    before = len(out)
    # Deduplicate final output based on Journal Name and ISSNs
    out = out.drop_duplicates(subset=["Journal Name", "ISSNs by JName clean"])
    after = len(out)
    logger.info(f">>> Deduplicated output: {before} → {after} rows")

    # Rename columns for final output
    out = out.rename(columns={
        "ISSNs by JName clean": "ISSN/s",
        "Link": "Agreement link"
    })

    # Define final column order for output
    final_columns = [
        "Journal Name",
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

    # Keep only columns that exist
    # Define final column order for output
    final_columns = [c for c in final_columns if c in out.columns]
    out = out[final_columns]

    return out