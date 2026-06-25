import json
from pathlib import Path

_LOOKUP_PATH = Path(__file__).parent / "data" / "cpe_lookup.json"

try:
    with open(_LOOKUP_PATH) as _f:
        LOOKUP_TABLE: dict = json.load(_f)
except (OSError, json.JSONDecodeError):
    LOOKUP_TABLE = {}


def enrich_packages(packages: list) -> list:
    """
    Adds a 'cpe' key to each package dict.

    Lookup order:
    1. cpe_lookup.json keyed by "ecosystem.lower():name"
    2. Heuristic: vendor = name, product = name
    3. cpe = None when version or name is missing
    """
    result = []
    for pkg in packages:
        name = pkg.get("name", "")
        version = pkg.get("version")
        ecosystem = pkg.get("ecosystem", "")

        if not version or not name:
            cpe = None
        else:
            base_ecosystem = ecosystem.split(":", 1)[0].lower()
            key = f"{base_ecosystem}:{name}"
            entry = LOOKUP_TABLE.get(key)
            if entry:
                vendor = entry.get("vendor", name)
                product = entry.get("product", name)
            else:
                vendor, product = name, name
            cpe = f"cpe:2.3:a:{vendor}:{product}:{version}:*:*:*:*:*:*:*"

        result.append({**pkg, "cpe": cpe})

    return result
