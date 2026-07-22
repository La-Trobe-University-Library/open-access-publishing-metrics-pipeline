import pandas as pd
from rp_pipeline.measures import compute_measures

def test_compute_measures_basic():
    caul = pd.DataFrame({
        "Journal Name": ["Test Journal"],
        "ISSN/EISSN": ["1234-567X"],
        "Agreement": ["Read & Publish"],
        "Agreement Key": ["READ&PUBLISH"],
        "Journal Type": ["Hybrid"],
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


def test_cap_link_blank_jt_only_applies_when_jt_missing():
    caul = pd.DataFrame({
        "Journal Name": ["Wiley Hybrid", "Wiley MissingJT"],
        "ISSN/EISSN": ["1111-1111", "2222-2222"],
        "Agreement": ["Wiley", "Wiley"],
        "Agreement Key": ["WILEY", "WILEY"],
        "Journal Type": ["Hybrid", pd.NA],   # second row missing JT
        "Publisher Name": ["Wiley", "Wiley"],
        "Journal Website": ["http://a", "http://b"],
        "Field of Research": ["X", "Y"],
        "Institution": ["La Trobe University", "La Trobe University"],
    })

    scimago = pd.DataFrame({"ISSN/EISSN": ["1111-1111", "2222-2222"]})
    jcr = pd.DataFrame({"ISSN/EISSN": ["1111-1111", "2222-2222"]})
    citescore = pd.DataFrame({"ISSN/EISSN": ["1111-1111", "2222-2222"]})

    cap = pd.DataFrame({
        "Agreement": ["Wiley", "Wiley"],
        "Journal Type": ["Hybrid", ""],  # blank JT row is NOT wildcard; only for missing JT
        "Agreement type": ["Uncapped", "FallbackType"],
        "Link": ["http://hybrid", "http://fallback"],
    })

    result = compute_measures(caul, scimago, jcr, citescore, cap, 2024, 2024, 2024)

    hybrid = result[result["Journal Name"] == "Wiley Hybrid"].iloc[0]
    missing = result[result["Journal Name"] == "Wiley MissingJT"].iloc[0]

    assert hybrid["Agreement type"] == "Uncapped"
    assert hybrid["Agreement link"] == "http://hybrid"

    assert missing["Agreement type"] == "FallbackType"
    assert missing["Agreement link"] == "http://fallback"