# vulns/euvd_client.py
# Integration with the European Vulnerability Database (EUVD).
# API: https://euvdservices.enisa.europa.eu

import httpx

EUVD_API_URL = "https://euvdservices.enisa.europa.eu/api/search"


def query_euvd(cve_id: str) -> dict:
    """
    Query the EUVD API for a given CVE identifier.
    Returns a dict with id, description, score, url if found.
    """
    try:
        response = httpx.get(
            EUVD_API_URL,
            params={"text": cve_id, "page": 0, "size": 5},
            headers={"accept": "application/json"},
            timeout=10,
        )
        if response.status_code != 200:
            return {}

        data = response.json()
        items = data.get("items", [])

        # find the item that matches our CVE
        for item in items:
            aliases = item.get("aliases", "")
            if cve_id in aliases:
                return {
                    "euvd_id": item.get("id"),
                    "description": item.get("description", ""),
                    "base_score": item.get("baseScore"),
                    "score_version": item.get("baseScoreVersion"),
                    "url": f"https://euvd.enisa.europa.eu/ENISA/{item.get('id')}",
                }
        return {}

    except Exception:
        return {}
