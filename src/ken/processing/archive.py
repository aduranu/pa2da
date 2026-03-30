import os
import zipfile
import logging

logger = logging.getLogger(__name__)

TABULAR_EXTENSIONS = {".xlsx", ".xls", ".csv", ".tsv"}


def list_zip_contents(zip_path: str) -> list[dict]:
    """List tabular files inside a ZIP archive.

    Returns list of {name, size_bytes, is_tabular}.
    """
    entries = []
    with zipfile.ZipFile(zip_path, "r") as zf:
        for info in zf.infolist():
            if info.is_dir():
                continue
            ext = os.path.splitext(info.filename)[1].lower()
            entries.append({
                "name": info.filename,
                "size_bytes": info.file_size,
                "is_tabular": ext in TABULAR_EXTENSIONS,
            })
    tabular = [e for e in entries if e["is_tabular"]]
    logger.info("ZIP %s: %d total files, %d tabular", zip_path, len(entries), len(tabular))
    return tabular if tabular else entries  # fall back to all files if no tabular detected


def extract_file(zip_path: str, member_name: str, dest_dir: str) -> str:
    """Extract a single file from a ZIP archive. Returns the extracted file path."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extract(member_name, dest_dir)
    return os.path.join(dest_dir, member_name)
