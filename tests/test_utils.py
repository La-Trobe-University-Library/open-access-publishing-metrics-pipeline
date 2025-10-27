import pandas as pd
from rp_pipeline.utils import (
    normalise_issn,
    clean_agreement_key,
    first_nonblank,
    clean_text_upper_alnum_space,
    ensure_numeric
)

def test_normalise_issn():
    assert normalise_issn("1234-567X") == "1234-567X"
    assert normalise_issn("1234567X") == "1234-567X"
    assert normalise_issn("1234 567X") == "1234-567X"
    assert normalise_issn("invalid") is None

def test_clean_agreement_key():
    assert clean_agreement_key("  Read & Publish ") == "READ&PUBLISH"

def test_first_nonblank():
    s = pd.Series(["", None, "Data", "More"])
    assert first_nonblank(s) == "Data"

def test_clean_text_upper_alnum_space():
    assert clean_text_upper_alnum_space("Journal of Biology!") == "JOURNAL OF BIOLOGY"

def test_ensure_numeric():
    s = pd.Series(["1,234", "567.89", "abc"])
    result = ensure_numeric(s)
    assert result[0] == 1.234
    assert pd.isna(result[2])