from __future__ import annotations

import os
import pkgutil
import re

from dataclasses import dataclass
from pathlib import Path
from typing import Dict
from typing import Mapping
from typing import Optional
from typing import Protocol
from typing import Tuple
from typing import Union
from typing import runtime_checkable
from urllib.parse import urlparse


GOGGLE_PARAMETER = "goggles"
LEGACY_GOGGLE_PARAMETER = "goggles_id"
GOGGLE_SUFFIX = ".goggle"
MAX_GOGGLE_BYTES = 2 * 1024 * 1024

_PACKAGE_NAME = "brave.goggles"
_METADATA_RE = re.compile(r"^!\s*([A-Za-z_][\w-]*)\s*:\s*(.*)$")
_PACKAGE_RESOURCE_RE = re.compile(r"^[A-Za-z0-9_-]+(?:\.goggle)?$")
_SUPPORTED_PARAMETER_NAMES = {GOGGLE_PARAMETER, LEGACY_GOGGLE_PARAMETER}


@dataclass(frozen=True)
class ParsedGoggle:
    """A lightweight parse of Goggle source text."""

    text: str
    metadata: Mapping[str, str]
    instructions: Tuple[str, ...]


@runtime_checkable
class GoggleSource(Protocol):
    """Interface implemented by concrete Goggle adapters."""

    def request_value(self) -> str:
        """Return the value to send as the Brave goggles parameter."""


@dataclass(frozen=True)
class UrlGoggle:
    """A hosted Goggle referenced by URL."""

    url: str

    def request_value(self) -> str:
        """Return the hosted Goggle URL to send to Brave."""
        if not _is_goggle_url(self.url):
            raise ValueError("Goggle URL must be an absolute http or https URL")
        return self.url


@dataclass(frozen=True)
class InlineGoggle:
    """A Goggle definition passed inline."""

    definition: str

    def request_value(self) -> str:
        """Return a validated inline Goggle definition."""
        parse_goggle(self.definition)
        return self.definition


@dataclass(frozen=True)
class LocalGoggle:
    """A local .goggle file read from an explicit filesystem path."""

    path: Union[str, os.PathLike]
    encoding: str = "utf-8"

    def request_value(self) -> str:
        """Read and return a validated local Goggle definition."""
        path = Path(self.path).expanduser()
        if path.suffix != GOGGLE_SUFFIX:
            raise ValueError("Local Goggle files must use the .goggle extension")
        if not path.is_file():
            raise FileNotFoundError(f"Local Goggle file does not exist: {path}")
        if path.stat().st_size > MAX_GOGGLE_BYTES:
            raise ValueError("Local Goggle file exceeds the 2MB Brave API limit")

        definition = path.read_text(encoding=self.encoding)
        parse_goggle(definition)
        return definition


@dataclass(frozen=True)
class PackageGoggle:
    """A .goggle file bundled with the brave.goggles package."""

    name: str

    def request_value(self) -> str:
        """Read and return a validated package-bundled Goggle definition."""
        resource_name = _package_resource_name(self.name)
        data = pkgutil.get_data(_PACKAGE_NAME, resource_name)
        if data is None:
            raise FileNotFoundError(f"Package Goggle does not exist: {self.name}")
        if len(data) > MAX_GOGGLE_BYTES:
            raise ValueError("Package Goggle file exceeds the 2MB Brave API limit")

        definition = data.decode("utf-8")
        parse_goggle(definition)
        return definition


GoggleInput = Union[str, os.PathLike, GoggleSource]


def from_url(url: str) -> UrlGoggle:
    """Create a hosted URL Goggle adapter."""

    return UrlGoggle(url)


def from_text(definition: str) -> InlineGoggle:
    """Create an inline Goggle adapter."""

    return InlineGoggle(definition)


def from_file(path: Union[str, os.PathLike]) -> LocalGoggle:
    """Create a local file Goggle adapter."""

    return LocalGoggle(path)


def from_package(name: str) -> PackageGoggle:
    """Create a package-bundled Goggle adapter."""

    return PackageGoggle(name)


def parse_goggle(definition: str) -> ParsedGoggle:
    """Parse Goggle text enough to validate local and inline sources safely."""

    if not isinstance(definition, str):
        raise TypeError("Goggle definition must be a string")
    if not definition.strip():
        raise ValueError("Goggle definition cannot be empty")
    if len(definition.encode("utf-8")) > MAX_GOGGLE_BYTES:
        raise ValueError("Goggle definition exceeds the 2MB Brave API limit")

    metadata = {}
    instructions = []

    for raw_line in definition.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("!"):
            metadata_match = _METADATA_RE.match(line)
            if metadata_match:
                key, value = metadata_match.groups()
                metadata[key] = value
            continue

        instructions.append(line)

    if not instructions:
        raise ValueError("Goggle definition must contain at least one instruction")

    return ParsedGoggle(text=definition, metadata=metadata, instructions=tuple(instructions))


def resolve_goggle(source: GoggleInput) -> str:
    """Return the Brave API value for any supported Goggle source."""

    return _adapter_for(source).request_value()


def to_request_params(
    source: Optional[GoggleInput],
    *,
    parameter_name: str = GOGGLE_PARAMETER,
) -> Dict[str, str]:
    """Return Brave request params for a Goggle source.

    The default parameter follows current Brave API docs. Pass
    parameter_name="goggles_id" only when integrating with legacy caller code.
    """

    if parameter_name not in _SUPPORTED_PARAMETER_NAMES:
        raise ValueError("parameter_name must be 'goggles' or 'goggles_id'")
    if source is None:
        return {}
    return {parameter_name: resolve_goggle(source)}


def _adapter_for(source: GoggleInput) -> GoggleSource:
    if isinstance(source, GoggleSource):
        return source
    if isinstance(source, os.PathLike):
        return LocalGoggle(source)
    if isinstance(source, str):
        if _is_goggle_url(source):
            return UrlGoggle(source)
        if _looks_like_goggle_path(source):
            return LocalGoggle(source)
        return InlineGoggle(source)

    raise TypeError("Goggle source must be a URL, definition, path, or GoggleSource")


def _is_goggle_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _looks_like_goggle_path(value: str) -> bool:
    return Path(value).suffix == GOGGLE_SUFFIX


def _package_resource_name(name: str) -> str:
    if not _PACKAGE_RESOURCE_RE.fullmatch(name):
        raise ValueError("Package Goggle names may only contain letters, numbers, '_' and '-'")
    if name.endswith(GOGGLE_SUFFIX):
        return name
    return f"{name}{GOGGLE_SUFFIX}"
