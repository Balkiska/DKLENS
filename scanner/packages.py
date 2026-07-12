# scanner/packages.py
# Reads installed packages from an extracted Docker filesystem.
# Supports Alpine, Wolfi, Debian, Ubuntu, and RPM-based distros.

import os
import re
import sqlite3
import subprocess


def detect_distro(fs_path: str) -> str:
    """
    Detect the Linux distribution from the extracted filesystem.
    Returns 'alpine', 'wolfi', 'ubuntu', 'debian', 'rpm_sqlite', 'rpm_bdb', 'rpm_ndb' or 'unknown'.
    """
    if os.path.exists(os.path.join(fs_path, "lib", "apk", "db", "installed")):
        if os.path.exists(os.path.join(fs_path, "etc", "alpine-release")):
            return "alpine"
        return "wolfi"

    rpm_dir = os.path.join(fs_path, "var", "lib", "rpm")
    if os.path.exists(os.path.join(rpm_dir, "rpmdb.sqlite")):
        return "rpm_sqlite"
    if os.path.exists(os.path.join(rpm_dir, "Packages.db")):
        return "rpm_ndb"
    if os.path.exists(os.path.join(rpm_dir, "Packages")):
        return "rpm_bdb"

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
    """
    Read /etc/alpine-release and build the OSV ecosystem identifier.
    "3.18.12" -> "Alpine:v3.18"
    """
    release_path = os.path.join(fs_path, "etc", "alpine-release")
    with open(release_path, "r", errors="replace") as f:
        version = f.read().strip()
    parts = version.split(".")
    return f"Alpine:v{parts[0]}.{parts[1]}"


def parse_apk_packages(fs_path: str, ecosystem: str = None) -> list:
    """
    Parse Alpine/Wolfi packages from /lib/apk/db/installed.
    """
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
    """
    Parse Debian/Ubuntu packages from /var/lib/dpkg/status.
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
                current["ecosystem"] = ecosystem
                packages.append(current)
                current = {}

    return packages


def parse_rpm_packages(fs_path: str) -> list:
    """
    Parse RPM packages from /var/lib/rpm/rpmdb.sqlite.
    Supports Fedora, Rocky Linux 9, AlmaLinux 9, Red Hat UBI9.
    """
    rpm_dir = os.path.join(fs_path, "var", "lib", "rpm")
    db_path = os.path.join(rpm_dir, "rpmdb.sqlite")
    if not os.path.exists(db_path):
        db_path = os.path.join(rpm_dir, "Packages.db")
    packages = []

    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        cursor = conn.cursor()

        cursor.execute("SELECT key, hnum FROM Name")
        name_rows = cursor.fetchall()

        for pkg_name, hnum in name_rows:
            try:
                cursor.execute("SELECT blob FROM Packages WHERE hnum=?", (hnum,))
                row = cursor.fetchone()
                if not row:
                    continue

                blob = row[0]
                strings = re.findall(b"[a-zA-Z0-9._+-]{2,50}", blob)
                strings = [s.decode("latin-1") for s in strings]

                version = None
                for i, s in enumerate(strings):
                    if s == pkg_name and i + 1 < len(strings):
                        candidate = strings[i + 1]
                        if re.match(r"^\d+[\d._-]*$", candidate):
                            version = candidate
                            break

                if version:
                    packages.append(
                        {
                            "name": pkg_name,
                            "version": version,
                            "ecosystem": "Red Hat",
                        }
                    )

            except Exception:
                continue

        conn.close()

    except Exception as e:
        print(f"[WARN] Could not read RPM SQLite database: {e}")

    return packages


def parse_rpm_bdb_packages(fs_path: str) -> list:
    """
    Parse RPM packages from BerkeleyDB format.
    Method 1: native rpm command (works on Kali/systems with BDB support).
    Method 2: db_dump fallback (works on modern Debian/Ubuntu/Nix).
    """
    packages = []
    rpm_dir = os.path.join(fs_path, "var", "lib", "rpm")

    # Method 1: try native rpm command first
    try:
        result = subprocess.run(
            ["rpm", "--dbpath", rpm_dir, "-qa", "--qf", "%{NAME} %{VERSION}\n"],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.stdout.strip():
            for line in result.stdout.strip().split("\n"):
                parts = line.strip().split(" ", 1)
                if len(parts) == 2:
                    name, version = parts
                    if name and version:
                        packages.append(
                            {
                                "name": name,
                                "version": version,
                                "ecosystem": "Red Hat",
                            }
                        )
            if packages:
                print(f"[INFO] RPM BDB read via rpm command: {len(packages)} packages")
                return packages
    except Exception:
        pass

    # Method 2: fallback to db_dump
    print("[INFO] rpm command returned 0 packages, trying db_dump fallback...")
    try:
        # db_dump -p prints each record as two lines: " <key>" then " <value>".
        # Non-printable bytes are escaped as \xx (hex), so we decode them back
        # to real bytes before using them.
        def decode_escaped_bytes(text):
            raw = bytearray()
            i = 0
            while i < len(text):
                if text[i] == "\\":
                    if text[i + 1] == "\\":
                        raw.append(0x5C)  # literal backslash byte
                        i += 2
                    else:
                        raw.append(int(text[i + 1 : i + 3], 16))
                        i += 3
                else:
                    raw.append(ord(text[i]))
                    i += 1
            return bytes(raw)

        def dump_db_pairs(path):
            result = subprocess.run(
                ["db_dump", "-p", path], capture_output=True, text=True, timeout=60
            )
            lines = result.stdout.split("\n")
            pairs = []
            i = 0
            while i < len(lines):
                raw_line = lines[i]
                if raw_line.startswith(" ") and len(raw_line.strip()) > 1:
                    key = decode_escaped_bytes(raw_line.strip())
                    value = decode_escaped_bytes(lines[i + 1].strip())
                    pairs.append((key, value))
                    i += 2
                else:
                    i += 1
            return pairs

        # The Name db maps package name -> header number (hnum).
        # The Packages db maps header number (hnum) -> full RPM header (binary blob).
        # We join them on hnum, same as parse_rpm_packages() does with sqlite above.
        name_entries = dump_db_pairs(os.path.join(rpm_dir, "Name"))
        blob_by_hnum = dict(dump_db_pairs(os.path.join(rpm_dir, "Packages")))

        for name_bytes, hnum_value in name_entries:
            pkg_name = name_bytes.decode("latin-1")
            blob = blob_by_hnum.get(hnum_value[:4])
            if blob is None:
                continue

            strings = re.findall(b"[a-zA-Z0-9._+-]{2,50}", blob)
            strings = [s.decode("latin-1") for s in strings]

            for i, s in enumerate(strings):
                if s == pkg_name and i + 1 < len(strings):
                    candidate = strings[i + 1]
                    if re.match(r"^\d+[\d._-]*$", candidate):
                        packages.append(
                            {
                                "name": pkg_name,
                                "version": candidate,
                                "ecosystem": "Red Hat",
                            }
                        )
                        break

        if packages:
            print(f"[INFO] RPM BDB read via db_dump: {len(packages)} packages")

    except Exception as e:
        print(f"[WARN] Could not read BerkeleyDB RPM database: {e}")

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
    elif distro == "wolfi":
        return parse_apk_packages(fs_path, ecosystem="Wolfi")
    elif distro == "ubuntu":
        return parse_dpkg_packages(fs_path, ecosystem="Ubuntu")
    elif distro == "debian":
        return parse_dpkg_packages(fs_path)
    elif distro == "rpm_sqlite":
        return parse_rpm_packages(fs_path)
    elif distro == "rpm_bdb":
        return parse_rpm_bdb_packages(fs_path)
    elif distro == "rpm_ndb":
        return parse_rpm_bdb_packages(fs_path)
    else:
        print("Unknown distro, cannot extract packages.")
        return []
