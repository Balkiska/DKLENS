# vulns/osv_client.py
# Queries the OSV API to find known vulnerabilities for a list of packages.

import httpx

OSV_API_URL = "https://api.osv.dev/v1/query"


def parse_cvss_severity(score_string: str) -> str:
    if not score_string:
        return "UNKNOWN"
    impact_map = {"N": 0.0, "L": 0.22, "H": 0.56}
    try:
        parts = {}
        for part in score_string.split("/"):
            if ":" in part:
                key, val = part.split(":", 1)
                parts[key] = val
        c = impact_map.get(parts.get("C", "N"), 0.0)
        i = impact_map.get(parts.get("I", "N"), 0.0)
        a = impact_map.get(parts.get("A", "N"), 0.0)
        score = (c + i + a) * 10 / 1.68
    except Exception:
        return "UNKNOWN"
    if score >= 9.0:
        return "CRITICAL"
    elif score >= 7.0:
        return "HIGH"
    elif score >= 4.0:
        return "MEDIUM"
    elif score > 0.0:
        return "LOW"
    else:
        return "NONE"


def get_advisory_url(vuln_id: str) -> str:
    if "CVE-" in vuln_id:
        cve_id = "CVE-" + vuln_id.split("CVE-", 1)[1]
        return f"https://www.cve.org/CVERecord?id={cve_id}"
    return f"https://osv.dev/vulnerability/{vuln_id}"


def get_fix_command(package_name: str, fixed_version: str, ecosystem: str) -> str:
    if not fixed_version:
        return "No fix available yet."
    if ecosystem == "Alpine":
        return f"apk add {package_name}={fixed_version}"
    elif ecosystem in ("Debian", "Ubuntu"):
        return f"apt-get install {package_name}={fixed_version}"
    else:
        return f"Update {package_name} to version {fixed_version}"


def query_osv(package_name: str, version: str, ecosystem: str) -> list:
    """
    Query OSV API for vulnerabilities affecting a specific package version.
    Returns a list of dicts with id, description, fixed, severity, command, url.
    """
    payload = {
        "package": {"name": package_name, "ecosystem": ecosystem},
        "version": version,
    }

    response = httpx.post(OSV_API_URL, json=payload, timeout=10)
    if response.status_code != 200:
        return []

    data = response.json()
    vulns = data.get("vulns", [])

    results = []
    for vuln in vulns:
        vuln_id = vuln.get("id", "UNKNOWN")
        description = vuln.get("details", "No description available.")

        fixed = None
        for affected in vuln.get("affected", []):
            for r in affected.get("ranges", []):
                for event in r.get("events", []):
                    if "fixed" in event:
                        fixed = event["fixed"]

        severity_score = None
        for s in vuln.get("severity", []):
            if s.get("type") == "CVSS_V3":
                severity_score = s.get("score", "")

        severity = parse_cvss_severity(severity_score)
        url = get_advisory_url(vuln_id)
        command = get_fix_command(package_name, fixed, ecosystem)

        results.append({
            "id": vuln_id,
            "description": description,
            "fixed": fixed,
            "severity": severity,
            "command": command,
            "url": url,
        })

    return results
