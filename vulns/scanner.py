# vulns/scanner.py
# Orchestrates vulnerability lookup for a list of packages using OSV and EUVD.

from vulns.osv_client import query_osv
from vulns.euvd_client import query_euvd

SEVERITY_ORDER = {"CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "UNKNOWN": 4, "NONE": 5}


def scan_packages(packages: list) -> list:
    """
    For each package, query OSV and enrich with EUVD data.
    Returns findings sorted by severity.
    """
    findings = []

    for pkg in packages:
        name = pkg["name"]
        version = pkg["version"]
        ecosystem = pkg["ecosystem"]

        print(f"[INFO] Checking {name} {version}...")
        vulns = query_osv(name, version, ecosystem)

        if not vulns:
            findings.append({
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
            })
        else:
            for vuln in vulns:
                cve_id = vuln["id"]

                # extract plain CVE id for EUVD lookup
                plain_cve = cve_id
                if "CVE-" in cve_id:
                    plain_cve = "CVE-" + cve_id.split("CVE-")[1]

                # enrich with EUVD data
                euvd = query_euvd(plain_cve)

                findings.append({
                    "package": name,
                    "version": version,
                    "severity": vuln["severity"],
                    "cve": cve_id,
                    "fix": vuln["fixed"],
                    "command": vuln["command"],
                    "url": vuln["url"],
                    "euvd_id": euvd.get("euvd_id"),
                    "euvd_score": euvd.get("base_score"),
                    "euvd_url": euvd.get("url"),
                    "description": vuln["description"],
                })

    findings.sort(key=lambda x: SEVERITY_ORDER.get(x["severity"], 99))
    return findings
