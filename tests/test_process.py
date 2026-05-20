import os

import pandas as pd

from panda.processing.archive import extract_file, list_zip_contents
from panda.processing.tabular import (
    generate_preview,
    list_sheets,
    read_and_clean,
    save_clean,
)


def test_read_csv(sample_csv):
    df, meta = read_and_clean(sample_csv)
    assert meta["row_count"] == 4
    assert meta["col_count"] == 3
    assert "Gene_ID" in df.columns


def test_read_excel_multi_sheet(sample_excel_multi_sheet):
    sheets = list_sheets(sample_excel_multi_sheet)
    assert sheets == ["RNA-Seq", "Proteomics"]

    # Clean sheet
    df, meta = read_and_clean(sample_excel_multi_sheet, sheet_name="RNA-Seq")
    assert meta["row_count"] == 2
    assert "Gene" in df.columns

    # Messy sheet with empty header rows
    df, meta = read_and_clean(sample_excel_multi_sheet, sheet_name="Proteomics")
    assert meta["row_count"] == 2
    assert "Protein" in df.columns


def test_generate_preview(sample_csv):
    df, _ = read_and_clean(sample_csv)
    preview = generate_preview(df, max_rows=2)
    assert "BRCA1" in preview
    assert "TP53" in preview


def test_save_clean(sample_csv, tmp_dir):
    df, _ = read_and_clean(sample_csv)
    out = os.path.join(tmp_dir, "output", "cleaned.csv")
    save_clean(df, out)
    assert os.path.exists(out)
    reloaded = pd.read_csv(out)
    assert len(reloaded) == 4


def test_list_zip_contents(sample_zip):
    contents = list_zip_contents(sample_zip)
    assert len(contents) == 2
    names = [c["name"] for c in contents]
    assert "data/counts.csv" in names
    assert "data/metadata.csv" in names


def test_extract_from_zip(sample_zip, tmp_dir):
    dest = os.path.join(tmp_dir, "extracted")
    os.makedirs(dest)
    path = extract_file(sample_zip, "data/counts.csv", dest)
    assert os.path.exists(path)
    df = pd.read_csv(path)
    assert len(df) == 4
