# vulns/scanner.py
# Orchestrates vulnerability lookup for a list of packages using OSV and EUVD.

from cache.repository import CacheRepository
from config.settings import get_cache
from vulns.osv_client import query_osv
from vulns.euvd_client import query_euvd

SEVERITY_ORDER = {
    "CRITICAL": 0,
    "HIGH": 1,
    "MEDIUM": 2,
    "LOW": 3,
    "UNKNOWN": 4,
    "NONE": 5,
}


def _empty_finding(name: str, version: str | None) -> dict:
    """Finding for a package with no known vulnerability."""
    return {
        "package": name,
        "version": version,
        "severity": "NONE",
        "cve": None,
        "fix": None,
        "command": None,
        "url": None,
        "euvd_id": None,
        "euvd_score": None,
        "euvd_url": None,
        "description": None,
    }


def _cached_lookup(cache: CacheRepository, key: str, source: str, fetch):
    """Return the cached value for (key, source), or fetch it once and store it."""
    result = cache.get(key, source)
    if result is None:
        result = fetch()
        cache.set(key, source, result)
    return result


def scan_packages(packages: list, no_cache: bool = False) -> list:
    """
    For each package, query OSV and enrich with EUVD data.
    Results are cached locally (SQLite) to avoid repeated API calls.
    Returns findings sorted by severity.
    """
    cache = get_cache(no_cache)
    findings = []

    for pkg in packages:
        name = pkg["name"]
        version = pkg.get("version")
        ecosystem = pkg["ecosystem"]

        if not version:
            findings.append(_empty_finding(name, None))
            continue

        print(f"[INFO] Checking {name} {version}...")
        package_key = f"{ecosystem}:{name}:{version}"
        vulns = _cached_lookup(
            cache, package_key, "osv", lambda: query_osv(name, version, ecosystem)
        )

        if not vulns:
            findings.append(_empty_finding(name, version))
            continue

        for vuln in vulns:
            cve_id = vuln["id"]

            # extract plain CVE id for EUVD lookup
            plain_cve = cve_id
            if "CVE-" in cve_id:
                plain_cve = "CVE-" + cve_id.split("CVE-")[1]

            euvd = _cached_lookup(
                cache, plain_cve, "euvd", lambda: query_euvd(plain_cve)
            )

            findings.append(
                {
                    "package": name,
                    "version": version,
                    "cpe": pkg.get("cpe"),
                    "severity": vuln["severity"],
                    "cve": cve_id,
                    "fix": vuln["fixed"],
                    "command": vuln["command"],
                    "url": vuln["url"],
                    "advisory_url": vuln.get("advisory_url"),
                    "euvd_id": euvd.get("euvd_id"),
                    "euvd_score": euvd.get("base_score"),
                    "euvd_url": euvd.get("url"),
                    "description": vuln["description"],
                }
            )

    findings.sort(key=lambda x: SEVERITY_ORDER.get(x["severity"], 99))
    return findings
