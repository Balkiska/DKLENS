# scanner/packages.py
# Reads installed packages from an extracted Docker filesystem.

import os


def detect_distro(fs_path: str) -> str:
    """
    Detect the Linux distribution from the extracted filesystem.
    Returns 'alpine', 'debian' or 'unknown'.
    """
    if os.path.exists(os.path.join(fs_path, "lib", "apk", "db", "installed")):
        return "alpine"
    if os.path.exists(os.path.join(fs_path, "var", "lib", "dpkg", "status")):
        return "debian"
    return "unknown"


def parse_apk_packages(fs_path: str) -> list:
    """
    Parse Alpine packages from /lib/apk/db/installed.
    Returns a list of dicts with name, version, ecosystem.
    """
    db_path = os.path.join(fs_path, "lib", "apk", "db", "installed")
    packages = []
    current = {}

    with open(db_path, "r", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line.startswith("P:"):
                current["name"] = line[2:]
            elif line.startswith("V:"):
                current["version"] = line[2:]
            elif line == "" and "name" in current and "version" in current:
                current["ecosystem"] = "Alpine"
                packages.append(current)
                current = {}

    return packages


def parse_dpkg_packages(fs_path: str) -> list:
    """
    Parse Debian/Ubuntu packages from /var/lib/dpkg/status.
    Returns a list of dicts with name, version, ecosystem.
    """
    db_path = os.path.join(fs_path, "var", "lib", "dpkg", "status")
    packages = []
    current = {}

    with open(db_path, "r", errors="replace") as f:
        for line in f:
            line = line.strip()
            if line.startswith("Package:"):
                current["name"] = line.split(":", 1)[1].strip()
            elif line.startswith("Version:"):
                current["version"] = line.split(":", 1)[1].strip()
            elif line == "" and "name" in current and "version" in current:
                current["ecosystem"] = "Debian"
                packages.append(current)
                current = {}

    return packages


def extract_packages(fs_path: str) -> list:
    """
    Auto-detect distro and extract installed packages.
    Returns a list of dicts with name, version, ecosystem.
    """
    distro = detect_distro(fs_path)
    print(f"Detected distro: {distro}")

    if distro == "alpine":
        return parse_apk_packages(fs_path)
    elif distro == "debian":
        return parse_dpkg_packages(fs_path)
    else:
        print("Unknown distro, cannot extract packages.")
        return []
