import logging
import os

import pandas as pd

logger = logging.getLogger(__name__)


def _detect_format(file_path: str) -> str:
    """Detect file format from extension and magic bytes. Returns 'excel', 'csv', or 'unknown'."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext in (".xlsx", ".xls"):
        return "excel"
    if ext in (".csv", ".tsv", ".txt"):
        return "csv"

    # Check magic bytes for Excel (ZIP-based .xlsx or OLE2 .xls)
    try:
        with open(file_path, "rb") as f:
            header = f.read(8)
        if header[:4] == b"PK\x03\x04":  # ZIP (xlsx)
            return "excel"
        if header[:8] == b"\xd0\xcf\x11\xe0\xa1\xb1\x1a\xe1":  # OLE2 (xls)
            return "excel"
    except OSError:
        pass

    return "csv"  # default to CSV for plain text files


def list_sheets(file_path: str) -> list[str]:
    """Return sheet names for an Excel file. Returns [] for CSV/TSV."""
    fmt = _detect_format(file_path)
    if fmt != "excel":
        return []
    try:
        xls = pd.ExcelFile(file_path)
        return xls.sheet_names
    except Exception:
        return []


def _read_file(file_path: str, fmt: str, ext: str, sheet_name: str | None) -> pd.DataFrame:
    """Try to read a tabular file, falling back across formats if parsing fails.

    Always tries all plausible formats. Order depends on detected format/extension.
    """
    excel_reader = ("excel", lambda: pd.read_excel(file_path, sheet_name=sheet_name or 0, header=None))
    # Try multiple Excel engines for edge cases (xlrd for .xls, openpyxl for .xlsx)
    excel_xlrd = ("excel-xlrd", lambda: pd.read_excel(file_path, sheet_name=sheet_name or 0, header=None, engine="xlrd"))
    csv_reader = ("csv", lambda: pd.read_csv(file_path, header=None))
    tsv_reader = ("tsv", lambda: pd.read_csv(file_path, header=None, sep="\t"))

    if fmt == "excel":
        readers = [excel_reader, excel_xlrd, csv_reader]
    elif ext == ".tsv":
        readers = [tsv_reader, csv_reader]
    elif ext in (".csv", ".txt"):
        readers = [csv_reader, excel_reader]
    else:
        # Unknown extension — try everything, Excel first (publisher downloads often lack extensions)
        readers = [excel_reader, excel_xlrd, csv_reader, tsv_reader]

    last_err = None
    for name, reader in readers:
        try:
            df = reader()
            if len(df) > 0:
                logger.info("Successfully read %s as %s", file_path, name)
                return df
        except Exception as e:
            logger.debug("Failed to read %s as %s: %s", file_path, name, e)
            last_err = e

    raise ValueError(f"Could not read {file_path} in any format: {last_err}")


def read_and_clean(file_path: str, sheet_name: str | None = None) -> tuple[pd.DataFrame, dict]:
    """Read a tabular file and apply cleaning heuristics.

    Returns (cleaned_df, metadata_dict).
    """
    fmt = _detect_format(file_path)
    ext = os.path.splitext(file_path)[1].lower()

    # Read raw — try detected format first, fall back to alternatives
    df = _read_file(file_path, fmt, ext, sheet_name)

    original_shape = df.shape

    # Detect header row: first row where >50% of cells are non-empty strings
    header_row = _detect_header_row(df)
    if header_row is not None:
        df.columns = df.iloc[header_row].astype(str)
        df = df.iloc[header_row + 1 :].reset_index(drop=True)

    # Drop columns that are 100% NaN
    df = df.dropna(axis=1, how="all")

    # Drop rows that are 100% NaN
    df = df.dropna(axis=0, how="all")

    # Strip whitespace from string columns
    for col in df.select_dtypes(include=["object"]).columns:
        df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)

    # Attempt numeric coercion on object columns
    for col in df.select_dtypes(include=["object"]).columns:
        converted = pd.to_numeric(df[col], errors="coerce")
        if converted.notna().sum() > df[col].notna().sum() * 0.5:
            df[col] = converted

    df = df.reset_index(drop=True)

    metadata = {
        "row_count": len(df),
        "col_count": len(df.columns),
        "original_rows": original_shape[0],
        "original_cols": original_shape[1],
        "header_row_detected": header_row,
    }

    logger.info(
        "Cleaned %s: %dx%d -> %dx%d",
        file_path,
        original_shape[0],
        original_shape[1],
        metadata["row_count"],
        metadata["col_count"],
    )
    return df, metadata


def _detect_header_row(df: pd.DataFrame, max_scan: int = 20) -> int | None:
    """Find the first row where >50% of cells are non-empty strings."""
    for i in range(min(len(df), max_scan)):
        row = df.iloc[i]
        non_empty_strings = sum(
            1 for v in row if isinstance(v, str) and v.strip()
        )
        if non_empty_strings > len(row) * 0.5:
            return i
    return None


def generate_preview(df: pd.DataFrame, max_rows: int = 10) -> str:
    """Generate a plain-text preview table for Slack."""
    preview_df = df.head(max_rows)
    return preview_df.to_string(index=False, max_colwidth=20)


def save_clean(df: pd.DataFrame, output_path: str, fmt: str = "csv") -> str:
    """Save cleaned DataFrame. Returns the output path."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if fmt == "csv":
        df.to_csv(output_path, index=False)
    elif fmt == "excel":
        df.to_excel(output_path, index=False)
    else:
        raise ValueError(f"Unsupported format: {fmt}")
    logger.info("Saved cleaned data to %s", output_path)
    return output_path
