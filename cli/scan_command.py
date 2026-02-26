import re
import subprocess

IMAGE_REF_REGEX = r"^[a-z0-9]+([._/-][a-z0-9]+)*(:[a-zA-Z0-9._-]+)?$"


def validate_image_ref(image: str) -> None:
    if not re.match(IMAGE_REF_REGEX, image):
        raise ValueError(f"Référence d'image invalide: '{image}' (ex: nginx:alpine)")


def run_cmd(cmd):
    return subprocess.run(cmd, capture_output=True, text=True)


def check_docker_installed() -> None:
    try:
        result = run_cmd(["docker", "--version"])
        if result.returncode != 0:
            raise RuntimeError("Docker installé mais non fonctionnel.")
    except FileNotFoundError:
        raise RuntimeError("Docker non installé.")


def check_docker_running() -> None:
    result = run_cmd(["docker", "info"])
    if result.returncode != 0:
        raise RuntimeError("Docker daemon non accessible.")


def image_exists_locally(image: str) -> bool:
    result = run_cmd(["docker", "image", "inspect", image])
    return result.returncode == 0


def pull_image(image: str) -> None:
    result = subprocess.run(["docker", "pull", image])
    if result.returncode != 0:
        raise RuntimeError(f"Impossible de pull {image}")


def scan_entry(image: str, auto_pull=True) -> None:
    validate_image_ref(image)
    check_docker_installed()
    check_docker_running()

    if image_exists_locally(image):
        print(f" Image trouvée: {image}")
        return

    print(f"Image absente: {image}")

    if auto_pull:
        print(f" docker pull {image}")
        pull_image(image)
        print("Image téléchargée")
    else:
        raise RuntimeError("Image absente et pull désactivé.")
