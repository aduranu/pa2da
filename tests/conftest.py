import os
import tempfile
import zipfile

import pandas as pd
import pytest


@pytest.fixture
def tmp_dir():
    with tempfile.TemporaryDirectory(prefix="panda_test_") as d:
        yield d


@pytest.fixture
def sample_csv(tmp_dir):
    """Create a simple CSV with a header."""
    path = os.path.join(tmp_dir, "sample.csv")
    df = pd.DataFrame({
        "Gene_ID": ["BRCA1", "TP53", "EGFR", "MYC"],
        "Sample_1": [12.45, 45.67, 8.91, 33.21],
        "Sample_2": [11.23, 44.12, 9.05, 31.87],
    })
    df.to_csv(path, index=False)
    return path


@pytest.fixture
def sample_excel_multi_sheet(tmp_dir):
    """Create an Excel file with multiple sheets and messy headers."""
    path = os.path.join(tmp_dir, "multi_sheet.xlsx")
    with pd.ExcelWriter(path) as writer:
        df1 = pd.DataFrame({
            "Gene": ["BRCA1", "TP53"],
            "Expression": [12.5, 45.6],
        })
        df1.to_excel(writer, sheet_name="RNA-Seq", index=False)

        # Sheet with empty header rows (common in supplements)
        df2 = pd.DataFrame([
            [None, None, None],
            [None, None, None],
            ["Protein", "Abundance", "P-value"],
            ["TP53", "1234.5", "0.001"],
            ["EGFR", "5678.9", "0.05"],
        ])
        df2.to_excel(writer, sheet_name="Proteomics", index=False, header=False)
    return path


@pytest.fixture
def sample_zip(tmp_dir, sample_csv):
    """Create a ZIP with multiple tabular files."""
    zip_path = os.path.join(tmp_dir, "supplement.zip")
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(sample_csv, "data/counts.csv")
        path2 = os.path.join(tmp_dir, "metadata.csv")
        pd.DataFrame({"Sample": ["S1", "S2"], "Group": ["Control", "Treatment"]}).to_csv(
            path2, index=False
        )
        zf.write(path2, "data/metadata.csv")
    return zip_path
