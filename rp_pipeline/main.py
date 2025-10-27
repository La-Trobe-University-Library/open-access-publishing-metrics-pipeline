import argparse # argparse is used to parse command-line arguments
import sys # sys is used for system-specific parameters and functions like exiting
import logging # logging is used to log messages for debugging and tracking
from pathlib import Path # Path from pathlib is used to handle filesystem paths
from rp_pipeline.loaders import *   # Import all data loading functions from the loaders module
from rp_pipeline.measures import compute_measures   # Import the function to compute journal metrics and merge datasets

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')  # Configure the logging format and level
logger = logging.getLogger(__name__)   # Create a logger instance for this module

"""
Main function to run the R&P pipeline.
It loads datasets, computes metrics, and writes the final output.
"""
def main():
    logger.info(">>> Starting R&P pipeline...")
    ap = argparse.ArgumentParser(description="R&P pipeline (Power Query/DAX → Python)") # Create an argument parser for command-line inputs
    ap.add_argument("--input-root", type=Path, required=True, help="Root folder containing the data subfolders")  # Path to the root folder containing input data subfolders
    ap.add_argument("--out", type=Path, required=True, help="Output CSV path")  # Path to the output CSV file
    ap.add_argument("--sheet-name", type=str, default=None, help="Optional Excel sheet name to read from")  # Optional: specify a sheet name for Excel files
    ap.add_argument("--journal-list-year", type=int, help="Year for Journal List (CAUL)")  # Year for Journal List (CAUL) data
    ap.add_argument("--scimago-year", type=int, help="Year for SCImago (Scopus)")  # Year for SCImago (Scopus) data
    ap.add_argument("--jcr-year", type=int, help="Year for JCR")  # Year for Journal Citation Reports (JCR) data
    ap.add_argument("--citescore-year", type=int, help="Year for CiteScore (Elsevier)") # Year for CiteScore (Elsevier) data
    ap.add_argument("--caplink-year", type=int, help="Year for Cap and Link (CAUL)")  # Year for Cap and Link (CAUL) data
    args = ap.parse_args()  # Parse the command-line arguments

    journal_list_year = args.journal_list_year or int(input("Enter Journal List (CAUL) year: ")) # Prompt user for year if not provided via command-line
    SCImago_Scopus_year = args.scimago_year or int(input("Enter SCImago (Scopus) year: ")) # Prompt user for year if not provided via command-line
    JCR_year = args.jcr_year or int(input("Enter JCR year: ")) # Prompt user for year if not provided via command-line
    CiteScore_Elsevier_year = args.citescore_year or int(input("Enter CiteScore (Elsevier) year: ")) # Prompt user for year if not provided via command-line
    Cap_and_Link_CAUL_year = args.caplink_year or int(input("Enter Cap and Link (CAUL) year: ")) # Prompt user for year if not provided via command-line

    # Begin try block to catch and handle errors gracefully
    try:
        logger.info(f">>> Input root: {args.input_root}")
        logger.info(f">>> Output file: {args.out}")

        root = args.input_root
        # Check if the input root directory exists
        if not root.exists():
            logger.error(f"Input root not found: {root}")
            # Exit with error code 2 if input root is missing
            sys.exit(2)
        

        caul = load_caul_journals(root, args.sheet_name) # Load CAUL journal list data
        scim = load_scimago(root, args.sheet_name) # Load SCImago metrics data
        jcr = load_jcr(root, args.sheet_name) # Load Journal Citation Reports data
        cs = load_citescore(root, args.sheet_name) # Load CiteScore metrics data
        cap = load_cap_and_link(root, args.sheet_name)  # Load Cap and Link data
        
        logger.info(f">>> Loaded CAUL Journals: {len(caul)} rows")
        logger.info(f">>> Loaded SCImago: {len(scim)} rows")
        logger.info(f">>> Loaded JCR: {len(jcr)} rows")
        logger.info(f">>> Loaded CiteScore: {len(cs)} rows")
        if not cap.empty:
            logger.info(f">>> Loaded Cap & Link: {len(cap)} rows")

        # Merge datasets and compute journal-level metrics
        final = compute_measures(caul, scim, jcr, cs, cap, jcr_year=JCR_year, scimago_year=SCImago_Scopus_year, citescore_year=CiteScore_Elsevier_year)
        args.out.parent.mkdir(parents=True, exist_ok=True)
        final.to_csv(args.out, index=False) # Save the final merged dataset to CSV
        # Generate summary statistics for the output
        summary = {
            "Total Journals": len(final),
            "Unique Publishers": final["Publisher Name"].nunique() if "Publisher Name" in final.columns else "N/A",
            "Missing Impact Factor": final["JIF (JCR, 2024)"].isna().sum() if "JIF (JCR, 2024)" in final.columns else "N/A",
            "Missing CiteScore": final["CiteScore (Scopus, 2024)"].isna().sum() if "CiteScore (Scopus, 2024)" in final.columns else "N/A"
        }

        # Save summary report as Markdown
        summary_path = args.out.parent / "summary_report.md"
        # Write summary statistics to a Markdown file
        with open(summary_path, "w", encoding="utf-8") as f:
            f.write("# R&P Pipeline Summary Report\n\n")
            f.write("## Summary Statistics\n")
            for k, v in summary.items():
                f.write(f"- **{k}**: {v}\n")

        logger.info(f">>> Wrote: {args.out} ({len(final)} rows)")

    # Handle missing file errors
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        sys.exit(1)
    # Handle pandas parsing errors
    except pd.errors.ParserError as e:
        logger.error(f"Pandas parsing error: {e}")
        sys.exit(1)
    # Catch any other unexpected errors
    except Exception as e:
        logger.exception("Unexpected error occurred")
        sys.exit(1)

# Entry point for script execution
if __name__ == "__main__":
    logger.info(">>> Entering main()")
    main()