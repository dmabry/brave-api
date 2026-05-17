import sys
import zipfile

from email.parser import Parser
from pathlib import Path

from packaging.requirements import InvalidRequirement
from packaging.requirements import Requirement


BLOCKED_RUNTIME_REQUIREMENTS = {
    "coverage",
    "moto",
    "numpy",
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
}


def main() -> int:
    """Validate that a built wheel has installable runtime metadata."""
    if len(sys.argv) != 2:
        sys.stderr.write("Usage: validate-wheel-metadata.py dist/brave_search-*.whl\n")
        return 2

    wheel = Path(sys.argv[1])
    if not wheel.is_file() or wheel.suffix != ".whl":
        sys.stderr.write(f"Expected a wheel file, got {wheel}\n")
        return 2

    with zipfile.ZipFile(wheel) as archive:
        metadata_paths = [name for name in archive.namelist() if name.endswith(".dist-info/METADATA")]
        if len(metadata_paths) != 1:
            sys.stderr.write(f"Expected one METADATA file in {wheel}, found {len(metadata_paths)}\n")
            return 1

        metadata = Parser().parsestr(archive.read(metadata_paths[0]).decode("utf-8"))

    requirements = metadata.get_all("Requires-Dist") or []
    parsed_requirements = []
    invalid_requirements = []

    for requirement in requirements:
        try:
            parsed_requirements.append(Requirement(requirement))
        except InvalidRequirement as exc:
            invalid_requirements.append(f"{requirement!r}: {exc}")

    if invalid_requirements:
        sys.stderr.write("Invalid Requires-Dist entries:\n")
        for requirement in invalid_requirements:
            sys.stderr.write(f"  - {requirement}\n")
        return 1

    blocked = [
        requirement for requirement in parsed_requirements if requirement.name.lower() in BLOCKED_RUNTIME_REQUIREMENTS
    ]
    if blocked:
        sys.stderr.write("Runtime metadata includes development-only or heavy dependencies:\n")
        for requirement in blocked:
            sys.stderr.write(f"  - {requirement}\n")
        return 1

    sys.stdout.write(f"Validated {wheel.name} metadata with {len(parsed_requirements)} runtime dependencies.\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
