"""Set the native model's local data parameter after cloning; no simulation needed."""

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data-folder", type=Path, default=ROOT / "powerbi/data")
    a = p.parse_args()
    folder = a.data_folder.resolve()
    if not (folder / "export_manifest.json").exists():
        p.error("Folder must contain the Power BI CSV export and manifest")
    file = ROOT / "powerbi/StockSense.SemanticModel/model.bim"
    model = json.loads(file.read_text())
    # Power Query text literals escape quotes by doubling; backslash is literal in M.
    path = str(folder).replace('"', '""')
    next(x for x in model["model"]["expressions"] if x["name"] == "DataFolder")[
        "expression"
    ] = (
        '"'
        + path
        + '" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]'
    )
    file.write_text(json.dumps(model, indent=2, ensure_ascii=False) + "\n")
    print(
        "DataFolder configured. Open powerbi/StockSense.pbip in Windows Power BI Desktop and select Refresh."
    )
