import json
import os
from pathlib import Path
import requests
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.environ.get("HEDA_BACKEND_URL")

class RequestError(Exception):
    """Custom exception for request failures."""
    pass

CONFIG_DIR = Path.home() / ".config" / "heda"
CONFIG_FILE = CONFIG_DIR / "config.json"

def load_config() -> dict:
    if CONFIG_FILE.exists():
        return json.loads(CONFIG_FILE.read_text())
    return {}

def save_config(config: dict):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(json.dumps(config, indent=2))
    
def post_json(
    endpoint: str,
    payload: Dict[str, Any],
    timeout: int = 50
) -> Dict[str, Any]:
    """
    Send a POST request with JSON payload to the backend and return JSON response.

    Args:
        endpoint: Backend endpoint, e.g., "/init"
        payload: Dictionary to send as JSON
        timeout: Request timeout in seconds

    Returns:
        Parsed JSON response

    Raises:
        RequestError: if the request fails or response is not 200
    """
    url = f"{BACKEND_URL.rstrip('/')}{endpoint}"
    config = load_config()
    token = config.get("access_token")

    if not token:
        raise RequestError(
            "Not logged in. Run `heda login` first."
        )
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    try:
        response = requests.post(url,
            headers=headers,
            json=payload,
            timeout=timeout)
    except requests.RequestException as e:
        raise RequestError(f"Request to {url} failed: {e}") from e

    if response.status_code == 401:
        raise RequestError(
            "Authentication failed. Please run `heda login` again."
        )

    if response.status_code != 200:
        raise RequestError(
            f"Request failed [{response.status_code}]: {response.text}"
        )

    try:
        return response.json()
    except ValueError as e:
        raise RequestError(f"Invalid JSON response from {url}: {e}") from e

def post_multipart(
    endpoint: str,
    files: List[Path],
    form_data: Optional[Dict[str, Any]] = None,
    timeout: int = 120
) -> Dict[str, Any]:
    """POST multipart/form-data with files and optional form fields."""
    url = f"{BACKEND_URL.rstrip('/')}{endpoint}"
    
    config = load_config()
    token = config.get("access_token")

    if not token:
        raise RequestError(
            "Not logged in. Run `heda login` first."
        )
        
    headers = {
        "Authorization": f"Bearer {token}",
    }

    root = Path(".").resolve()

    multipart_files: List[Tuple[str, Tuple[str, bytes, str]]] = [
        (
            "files",
            (
                str(f.resolve().relative_to(root)),
                f.read_bytes(),
                "application/octet-stream",
            ),
        )
        for f in files
    ]

    try:
        response = requests.post(
            url,
            headers=headers,
            files=multipart_files,
            data=form_data,
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise RequestError(f"Multipart request to {url} failed: {e}") from e
    except ValueError as e:
        raise RequestError(f"Invalid JSON response from {url}: {e}") from e

def get_json(
    endpoint: str,
    params: Optional[Dict[str, Any]] = None,
    timeout: int = 50
) -> Dict[str, Any]:
    """
    Send a GET request with query parameters to the backend and return JSON response.

    Args:
        endpoint: Backend endpoint, e.g., "/onboard/status"
        params: Dictionary of query parameters
        timeout: Request timeout in seconds

    Returns:
        Parsed JSON response

    Raises:
        RequestError: if the request fails or response is not 200
    """
    url = f"{BACKEND_URL.rstrip('/')}{endpoint}"
    config = load_config()
    token = config.get("access_token")

    if not token:
        raise RequestError(
            "Not logged in. Run `heda login` first."
        )
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            params=params,
            timeout=timeout,
        )
    except requests.RequestException as e:
        raise RequestError(f"Request to {url} failed: {e}") from e

    if response.status_code != 200:
        raise RequestError(f"Request failed [{response.status_code}]: {response.text}")

    try:
        return response.json()
    except ValueError as e:
        raise RequestError(f"Invalid JSON response from {url}: {e}") from e
