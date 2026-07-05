# scanner/packages.py
# Reads installed packages from an extracted Docker filesystem.
# Supports Alpine, Wolfi, Debian, Ubuntu, and RPM-based distros.

import os
import sqlite3
import re


def detect_distro(fs_path: str) -> str:
    if os.path.exists(os.path.join(fs_path, "lib", "apk", "db", "installed")):
        if os.path.exists(os.path.join(fs_path, "etc", "alpine-release")):
            return "alpine"
        return "wolfi"
    if os.path.exists(os.path.join(fs_path, "var", "lib", "rpm", "rpmdb.sqlite")) or os.path.exists(os.path.join(fs_path, "var", "lib", "rpm", "Packages.db")):
        return "rpm"
    if os.path.exists(os.path.join(fs_path, "var", "lib", "dpkg", "status")):
        os_release = os.path.join(fs_path, "etc", "os-release")
        try:
            with open(os_release, "r", errors="replace") as f:
                for line in f:
                    if line.startswith("ID=") and "ubuntu" in line.lower():
                        return "ubuntu"
        except Exception:
            pass
        return "debian"
    return "unknown"


def get_alpine_version(fs_path: str) -> str:
    release_path = os.path.join(fs_path, "etc", "alpine-release")
    with open(release_path, "r", errors="replace") as f:
        version = f.read().strip()
    parts = version.split(".")
    return f"Alpine:v{parts[0]}.{parts[1]}"


def get_rpm_ecosystem(fs_path: str) -> str:
    """
    Return the OSV ecosystem identifier for RPM-based distros.
    OSV indexes all Red Hat family distros under "Red Hat".
    """
    return "Red Hat"


def parse_apk_packages(fs_path: str, ecosystem: str = None) -> list:
    db_path = os.path.join(fs_path, "lib", "apk", "db", "installed")
    if ecosystem is None:
        ecosystem = get_alpine_version(fs_path)
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
                current["ecosystem"] = ecosystem
                packages.append(current)
                current = {}
    return packages


def parse_dpkg_packages(fs_path: str, ecosystem: str = "Debian") -> list:
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
                current["ecosystem"] = ecosystem
                packages.append(current)
                current = {}
    return packages


def parse_rpm_packages(fs_path: str) -> list:
    """
    Parse RPM packages from /var/lib/rpm/rpmdb.sqlite.
    The database has two tables we use:
    - Name: maps package name -> hnum (package ID)
    - Packages: stores binary blob per package containing name + version
    We join them to get name + version for each package.
    """
    rpm_dir = os.path.join(fs_path, "var", "lib", "rpm")
    db_path = os.path.join(rpm_dir, "rpmdb.sqlite")
    if not os.path.exists(db_path):
        db_path = os.path.join(rpm_dir, "Packages.db")
    ecosystem = get_rpm_ecosystem(fs_path)
    packages = []

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()

        # get all package names with their ID
        cursor.execute("SELECT key, hnum FROM Name")
        name_rows = cursor.fetchall()

        for pkg_name, hnum in name_rows:
            try:
                # get the binary blob for this package
                cursor.execute("SELECT blob FROM Packages WHERE hnum=?", (hnum,))
                row = cursor.fetchone()
                if not row:
                    continue

                blob = row[0]
                # extract readable strings from the binary blob
                strings = re.findall(b'[a-zA-Z0-9._+-]{2,50}', blob)
                strings = [s.decode("latin-1") for s in strings]

                # version comes right after the package name in the blob
                version = None
                for i, s in enumerate(strings):
                    if s == pkg_name and i + 1 < len(strings):
                        candidate = strings[i + 1]
                        if re.match(r'^\d+[\d._-]*$', candidate):
                            version = candidate
                            break

                if version:
                    packages.append({
                        "name": pkg_name,
                        "version": version,
                        "ecosystem": ecosystem,
                    })

            except Exception:
                continue

        conn.close()

    except Exception as e:
        print(f"[WARN] Could not read RPM database: {e}")

    return packages


def extract_packages(fs_path: str) -> list:
    distro = detect_distro(fs_path)
    print(f"Detected distro: {distro}")

    if distro == "alpine":
        return parse_apk_packages(fs_path)
    elif distro == "wolfi":
        return parse_apk_packages(fs_path, ecosystem="Wolfi")
    elif distro == "ubuntu":
        return parse_dpkg_packages(fs_path, ecosystem="Ubuntu")
    elif distro == "debian":
        return parse_dpkg_packages(fs_path)
    elif distro == "rpm":
        return parse_rpm_packages(fs_path)
    else:
        print("Unknown distro, cannot extract packages.")
        return []
