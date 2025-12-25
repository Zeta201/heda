# heda/utils/httputils.py

import os
import requests
from typing import Any, Dict, Optional

from dotenv import load_dotenv
load_dotenv()

BACKEND_URL = os.environ.get("HEDA_BACKEND_URL")
BACKEND_AUTH_TOKEN = os.environ.get("BACKEND_AUTH_TOKEN")

class RequestError(Exception):
    """Custom exception for request failures."""
    pass


def post_json(
    endpoint: str,
    payload: Dict[str, Any],
    timeout: int = 10
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
    headers = {"x-auth-token": BACKEND_AUTH_TOKEN}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=timeout)
    except requests.RequestException as e:
        raise RequestError(f"Request to {url} failed: {e}") from e

    if response.status_code != 200:
        raise RequestError(f"Request failed [{response.status_code}]: {response.text}")

    try:
        return response.json()
    except ValueError as e:
        raise RequestError(f"Invalid JSON response from {url}: {e}") from e
