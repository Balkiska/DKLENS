from cve.cpe import enrich_packages


def pkg(name, version, ecosystem):
    return {"name": name, "version": version, "ecosystem": ecosystem}


# AC 1: known package uses lookup table → correct vendor/product in CPE
def test_known_package_uses_lookup_table():
    packages = [pkg("openssl", "1.1.1f", "Debian")]
    result = enrich_packages(packages)
    assert result[0]["cpe"] == "cpe:2.3:a:openssl:openssl:1.1.1f:*:*:*:*:*:*:*"


# AC 2: package not in table → heuristic (name:name) applied
def test_unknown_package_uses_heuristic():
    packages = [pkg("mycustompkg", "2.0.0", "Debian")]
    result = enrich_packages(packages)
    assert result[0]["cpe"] == "cpe:2.3:a:mycustompkg:mycustompkg:2.0.0:*:*:*:*:*:*:*"


# AC 3: package with no version → cpe = None; package still present in result
def test_no_version_yields_none_cpe():
    packages = [{"name": "brokenlib", "ecosystem": "Alpine"}]
    result = enrich_packages(packages)
    assert len(result) == 1
    assert result[0]["cpe"] is None


# AC 4: lookup table absent → heuristic for all; no exception raised
def test_missing_lookup_file_falls_back_to_heuristic(monkeypatch):
    monkeypatch.setattr("cve.cpe.LOOKUP_TABLE", {})
    packages = [pkg("curl", "7.68.0", "Debian")]
    result = enrich_packages(packages)
    assert result[0]["cpe"] == "cpe:2.3:a:curl:curl:7.68.0:*:*:*:*:*:*:*"


# Original dict must not be mutated
def test_original_dict_not_mutated():
    original = pkg("openssl", "1.1.1f", "Debian")
    enrich_packages([original])
    assert "cpe" not in original


# Enriched dict must carry all original fields
def test_enriched_dict_preserves_original_fields():
    packages = [pkg("openssl", "1.1.1f", "Debian")]
    result = enrich_packages(packages)
    assert result[0]["name"] == "openssl"
    assert result[0]["version"] == "1.1.1f"
    assert result[0]["ecosystem"] == "Debian"
