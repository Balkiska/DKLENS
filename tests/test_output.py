# Test file for display only.
# Uses fake data to validate Rich output without requiring Docker.
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from cli.output import show_table, show_json

FAKE_FINDINGS = [
    {
        "package": "openssl",
        "version": "1.1.1u",
        "severity": "HIGH",
        "fix": "Upgrade to 1.1.1w",
    },
    {
        "package": "musl",
        "version": "1.2.3",
        "severity": "MEDIUM",
        "fix": None,
    },
]

if __name__ == "__main__":
    print("=== TEST TABLE ===")
    show_table("test-image:fake", FAKE_FINDINGS)
    print("\n=== TEST JSON ===")
    show_json("test-image:fake", FAKE_FINDINGS)
