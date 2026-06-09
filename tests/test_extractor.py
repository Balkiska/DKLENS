import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner.extractor import extract_filesystem

if __name__ == "__main__":
    print("=== TEST: extract alpine:3.18 filesystem ===")
    fs_path = extract_filesystem("alpine:3.18")

    print("\nTop-level directories in extracted filesystem:")
    for entry in sorted(os.listdir(fs_path)):
        print(f"  {entry}")

    apk_db = os.path.join(fs_path, "lib", "apk", "db", "installed")
    if os.path.exists(apk_db):
        print("\napk database found.")
    else:
        print("\napk database NOT found.")
