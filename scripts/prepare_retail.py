"""Rebuild attributed aggregates: python scripts/prepare_retail.py [--workbook PATH]."""

import argparse
import hashlib
from pathlib import Path
import sys
import urllib.request
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from stocklab.preparation import SOURCE, ZIP_SHA, prepare

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workbook", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    workbook = args.workbook
    if workbook is None:
        raw = root / "data/raw"
        raw.mkdir(parents=True, exist_ok=True)
        archive = raw / "online-retail-ii.zip"
        if not archive.exists():
            urllib.request.urlretrieve(SOURCE, archive)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != ZIP_SHA:
            raise ValueError("Official ZIP checksum mismatch")
        with zipfile.ZipFile(archive) as zipped:
            # Exact known member, never arbitrary paths from an archive.
            workbook = raw / "online_retail_II.xlsx"
            workbook.write_bytes(zipped.read("online_retail_II.xlsx"))
    result = prepare(workbook, root / "stocklab/data")
    print(
        f"{result['raw_rows']:,} original rows -> {result['cleaned_rows']:,} cleaned rows -> 520 SKU-weeks"
    )
