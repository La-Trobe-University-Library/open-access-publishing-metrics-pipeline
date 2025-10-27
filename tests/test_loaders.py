from rp_pipeline.loaders import load_caul_journals
from pathlib import Path
import pandas as pd

def test_load_caul_journals_empty(tmp_path):
    # Create empty folder
    folder = tmp_path / "Journal List (CAUL)"
    folder.mkdir()
    df = load_caul_journals(tmp_path, sheet_name=None)
    assert isinstance(df, pd.DataFrame)
    assert df.empty