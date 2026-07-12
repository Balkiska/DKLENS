import docker
from docker.errors import DockerException, ImageNotFound, APIError


def get_docker_client():
    """Connect to Docker daemon."""
    try:
        client = docker.from_env()
        client.ping()
        return client
    except DockerException:
        
# Docker daemon unreachable (not running, not installed, or no permissions)
        print("[ERROR] Docker is not running or not installed.")
        raise RuntimeError("Docker is not running or not installed.")


def validate_and_pull_image(image_name: str):
    """Check if image exists locally, pull it if not."""
    client = get_docker_client()

    try:
        # Fast path: image is already present locally
        image = client.images.get(image_name)
        print(f"[OK] Image found locally: {image_name}")
        return image
    except ImageNotFound:

        # Not local: try pulling it from the registry (e.g. Docker Hub)
        print(f"[INFO] Image not found locally, pulling: {image_name}")
        try:
            image = client.images.pull(image_name)
            print(f"[OK] Image pulled successfully: {image_name}")
            return image
        except APIError as e:

             # Pull failed (bad tag, network issue, auth required, etc.)
            print(f"[ERROR] Failed to pull image: {e}")
            raise RuntimeError(f"Failed to pull image: {e}")
