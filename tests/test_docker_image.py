# tests/test_docker_image.py
# Tests image validation with a real local image.
# Requires Docker to be running.

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scanner.docker_image import validate_and_pull_image

if __name__ == "__main__":
    # Test 1: image that exists locally
    print("=== TEST 1: existing image ===")
    img = validate_and_pull_image("alpine:3.18")
    print(f"Image id: {img.id[:12]}")

    # Test 2: image that does not exist
    print("\n=== TEST 2: non-existing image ===")
    img = validate_and_pull_image("image-qui-nexiste-pas:latest")
