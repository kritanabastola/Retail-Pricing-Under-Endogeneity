"""Download or checksum the Kilts files used by the cereals panel.

Python's SSL store on this machine rejected the Booth certificate, so the
download uses ``curl``. If that fails, the printed URLs are the manual step.
Raw files stay in ``data/raw`` and are gitignored.
"""

from __future__ import annotations

import argparse
import hashlib
import logging
import shutil
import subprocess
from pathlib import Path

from pricing_research.data.sources import CATEGORIES, CategoryFiles

LOGGER = logging.getLogger(__name__)


def sha256_file(path: Path) -> str:
    """Return the hex SHA-256 of a file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _download(url: str, destination: Path) -> None:
    curl = shutil.which("curl")
    if curl is None:
        raise RuntimeError(
            "curl is not available. Download this file manually and place it at "
            f"{destination}:\n{url}"
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".partial")
    command = [curl, "-fL", "--retry", "3", "--retry-delay", "2", "-o", str(temporary), url]
    LOGGER.info("Downloading %s", url)
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        temporary.unlink(missing_ok=True)
        raise RuntimeError(
            "Automatic download failed. Save the file manually as "
            f"{destination}.\nURL: {url}\ncurl said: {completed.stderr.strip()}"
        )
    temporary.replace(destination)


def ensure_category_files(raw_dir: Path, spec: CategoryFiles, force: bool = False) -> list[Path]:
    """Download any missing category file and return the local paths."""
    targets = (
        (spec.movement_url, raw_dir / spec.movement_zip),
        (spec.upc_url, raw_dir / spec.upc_csv),
    )
    saved: list[Path] = []
    for url, path in targets:
        if path.exists() and path.stat().st_size > 0 and not force:
            LOGGER.info("Using existing %s", path)
        else:
            _download(url, path)
        saved.append(path)
    return saved


def main() -> None:
    """Fetch cereals and oatmeal files when they are not already local."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Fetch selected Kilts category files")
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--category", choices=sorted(CATEGORIES), action="append")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    names = args.category or ["cereals", "oatmeal"]
    for name in names:
        spec = CATEGORIES[name]
        paths = ensure_category_files(args.raw_dir, spec, force=args.force)
        for path in paths:
            print(f"{name}\t{path}\t{path.stat().st_size}\t{sha256_file(path)}")


if __name__ == "__main__":
    main()
