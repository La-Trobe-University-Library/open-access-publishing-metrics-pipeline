import pandas as pd
from rp_pipeline.measures import compute_measures

def test_compute_measures_basic():
    caul = pd.DataFrame({
        "Journal Name": ["Test Journal"],
        "ISSN/EISSN": ["1234-567X"],
        "Agreement": ["Read & Publish"],
        "Agreement Key": ["READ&PUBLISH"],
        "Publisher Name": ["Test Publisher"],
        "Journal Website": ["http://testjournal.com"],
        "Field of Research": ["Library Science"]
    })

    scimago = pd.DataFrame({
        "ISSN/EISSN": ["1234-567X"],
        "SJR": [1.5],
        "H index": [42],
        "SJR Best Quartile": ["Q1"],
        "Categories": ["Education; Library Science"]
    })

    jcr = pd.DataFrame({
        "ISSN/EISSN": ["1234-567X"],
        "Impact Factor": [2.0],
        "5-year Impact Factor": [2.5]
    })

    citescore = pd.DataFrame({
        "ISSN/EISSN": ["1234-567X"],
        "CiteScore": [3.0],
        "SNIP": [1.2]
    })

    cap = pd.DataFrame({
        "Agreement": ["Read & Publish"],
        "Agreement Key": ["READ&PUBLISH"],
        "Agreement type": ["Transformative"],
        "Link": ["http://example.com"],
        "Publisher data": ["Some data"],
        "Capped agreement approval statistics": ["Approved"]
    })

    result = compute_measures(caul, scimago, jcr, citescore, cap, 2024, 2024, 2024)

    assert isinstance(result, pd.DataFrame)
    assert not result.empty
    assert "Journal Name" in result.columns