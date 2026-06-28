# api/main.py
# Optional FastAPI REST API for DockLens.
# Allows external tools to scan Docker images via HTTP requests.

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from scanner.docker_image import validate_and_pull_image
from scanner.extractor import extract_filesystem
from scanner.packages import extract_packages
from vulns.scanner import scan_packages
from cve.cpe import enrich_packages

app = FastAPI(
    title="DockLens API",
    description="Docker Image Security Scanner REST API",
    version="1.0.0"
)


class ScanRequest(BaseModel):
    image: str
    no_cache: bool = False


class ScanResponse(BaseModel):
    image: str
    total_packages: int
    vulnerabilities_found: int
    findings: list


@app.get("/")
def root():
    return {"message": "DockLens API is running. Use POST /scan to scan an image."}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/scan", response_model=ScanResponse)
def scan(request: ScanRequest):
    """
    Scan a Docker image for known vulnerabilities.
    The image must be available locally or on Docker Hub.
    """
    try:
        validate_and_pull_image(request.image)
        fs_path = extract_filesystem(request.image)
        packages = extract_packages(str(fs_path))
        packages = enrich_packages(packages)
        findings = scan_packages(packages, no_cache=request.no_cache)

        vulns_found = len([f for f in findings if f["severity"] != "NONE"])

        return ScanResponse(
            image=request.image,
            total_packages=len(packages),
            vulnerabilities_found=vulns_found,
            findings=findings
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
