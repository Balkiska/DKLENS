import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner.extractor import extract_filesystem
from scanner.packages import extract_packages

if __name__ == "__main__":
    print("=== TEST: extract packages from alpine:3.18 ===")
    fs_path = extract_filesystem("alpine:3.18")
    packages = extract_packages(fs_path)

    print(f"\nFound {len(packages)} packages:")
    for pkg in packages[:10]:
        print(f"  {pkg['name']} {pkg['version']} ({pkg['ecosystem']})")
    print("  ...")
