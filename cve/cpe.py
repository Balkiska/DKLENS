import json
from pathlib import Path

# Local JSON table mapping known packages to their proper CPE vendor/product names
_LOOKUP_PATH = Path(__file__).parent / "data" / "cpe_lookup.json"

try:
    with open(_LOOKUP_PATH) as _f:
        LOOKUP_TABLE: dict = json.load(_f)
except (OSError, json.JSONDecodeError):

# Missing or invalid file: fall back to the heuristic-only path
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
             # Can't build a meaningful CPE without name + version
            cpe = None
        else:
             # Ecosystem may include a version suffix (e.g. "Alpine:v3.18"), keep only the distro part
            base_ecosystem = ecosystem.split(":", 1)[0].lower()
            key = f"{base_ecosystem}:{name}"
            entry = LOOKUP_TABLE.get(key)
            if entry:
            # Known package: use the correct vendor/product from the lookup table
                vendor = entry.get("vendor", name)
                product = entry.get("product", name)
            else:
            # Unknown package: fall back to using the package name for both
                vendor, product = name, name
            cpe = f"cpe:2.3:a:{vendor}:{product}:{version}:*:*:*:*:*:*:*"

        result.append({**pkg, "cpe": cpe})

    return result
