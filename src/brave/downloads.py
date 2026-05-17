import re

from pathlib import Path
from typing import Optional
from typing import Union

import requests

from .exceptions import BraveError


DEFAULT_DOWNLOAD_TIMEOUT = 10.0
_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9._ -]+")
_REPEATED_WHITESPACE = re.compile(r"\s+")


def safe_pdf_filename(title: Optional[str], age: Optional[str] = None) -> str:
    """Return a filesystem-safe PDF filename derived from result metadata."""
    stem = "-".join(part for part in (title, age) if part)
    stem = _UNSAFE_FILENAME_CHARS.sub("_", stem)
    stem = _REPEATED_WHITESPACE.sub(" ", stem).strip(" ._-")

    if not stem:
        stem = "download"

    return f"{stem[:150]}.pdf"


def download_pdf_file(
    url: str,
    path: Union[str, Path] = "downloads",
    title: Optional[str] = None,
    age: Optional[str] = None,
    timeout: float = DEFAULT_DOWNLOAD_TIMEOUT,
) -> str:
    """Download a PDF and return the path to the written file."""
    target_directory = Path(path)
    try:
        target_directory.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise BraveError(f"Error preparing PDF download directory {target_directory}: {exc}") from exc

    target_path = target_directory / safe_pdf_filename(title=title, age=age)

    try:
        response = requests.get(url, timeout=timeout)
    except requests.RequestException as exc:
        raise BraveError(f"Error downloading PDF: {exc}") from exc

    if response.status_code != 200:
        raise BraveError(f"Error downloading PDF: status code {response.status_code}")

    try:
        target_path.write_bytes(response.content)
    except OSError as exc:
        raise BraveError(f"Error writing PDF to {target_path}: {exc}") from exc

    return str(target_path)
