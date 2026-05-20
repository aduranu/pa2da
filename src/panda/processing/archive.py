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


def _detect_extension(file_path: str) -> str:
    """Detect file extension from magic bytes when the filename lacks one."""
    try:
        with open(file_path, "rb") as f:
            header = f.read(8)
        if header[:4] == b"PK\x03\x04":
            return ".xlsx"
        if header[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":
            return ".xls"
    except OSError:
        pass
    return ""


def extract_file(zip_path: str, member_name: str, dest_dir: str) -> str:
    """Extract a single file from a ZIP archive. Returns the extracted file path.

    If the extracted file has no extension, attempts to detect the format
    from magic bytes and renames accordingly.
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extract(member_name, dest_dir)
    extracted = os.path.join(dest_dir, member_name)

    # If no extension, detect and rename
    _, ext = os.path.splitext(extracted)
    if not ext:
        detected = _detect_extension(extracted)
        if detected:
            renamed = extracted + detected
            os.rename(extracted, renamed)
            logger.info("Renamed %s -> %s (detected format)", extracted, renamed)
            return renamed

    return extracted
