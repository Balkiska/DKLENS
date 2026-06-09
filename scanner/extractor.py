# scanner/extractor.py
# Extracts the filesystem from a Docker image by unpacking its layers.

import docker
import tarfile
import tempfile
import os
import json
from pathlib import Path


def extract_filesystem(image_name: str) -> Path:
    """Export image filesystem using docker save and extract all layers."""
    client = docker.from_env()

    tmpdir = tempfile.mkdtemp(prefix="docklens_")
    image_tar = os.path.join(tmpdir, "image.tar")
    filesystem_dir = os.path.join(tmpdir, "filesystem")
    os.makedirs(filesystem_dir)

    print(f"[INFO] Exporting image: {image_name}")

    # Save image to tar
    image = client.images.get(image_name)
    with open(image_tar, "wb") as f:
        for chunk in image.save(named=True):
            f.write(chunk)

    print("[INFO] Extracting layers...")

    # Open the image tar
    with tarfile.open(image_tar, "r") as tar:
        # Read manifest to get layer order
        manifest_file = tar.extractfile("manifest.json")
        manifest = json.load(manifest_file)
        layers = manifest[0]["Layers"]

        # Extract each layer in order
        for layer_path in layers:
            layer_file = tar.extractfile(layer_path)
            with tarfile.open(fileobj=layer_file, mode="r") as layer_tar:
                for member in layer_tar.getmembers():
                    # Skip whiteout files (deleted files marker)
                    if ".wh." in member.name:
                        continue
                    try:
                        layer_tar.extract(member, path=filesystem_dir, filter="data")
                    except Exception:
                        pass

    print(f"[OK] Filesystem extracted to: {filesystem_dir}")
    return Path(filesystem_dir)
