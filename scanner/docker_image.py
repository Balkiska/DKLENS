import docker
import sys
from docker.errors import DockerException, ImageNotFound, APIError


def get_docker_client():
    """Connect to Docker daemon."""
    try:
        client = docker.from_env()
        client.ping()
        return client
    except DockerException:
        print("[ERROR] Docker is not running or not installed.")
        sys.exit(1)


def validate_and_pull_image(image_name: str):
    """Check if image exists locally, pull it if not."""
    client = get_docker_client()

    try:
        image = client.images.get(image_name)
        print(f"[OK] Image found locally: {image_name}")
        return image
    except ImageNotFound:
        print(f"[INFO] Image not found locally, pulling: {image_name}")
        try:
            image = client.images.pull(image_name)
            print(f"[OK] Image pulled successfully: {image_name}")
            return image
        except APIError as e:
            print(f"[ERROR] Failed to pull image: {e}")
            sys.exit(1)
