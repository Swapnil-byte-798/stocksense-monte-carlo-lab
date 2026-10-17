"""Offline schema, model-reference, mart-grain and accounting checks. Not a Desktop renderer."""

import csv
import hashlib
import json
from pathlib import Path
import re
import sys
import warnings

warnings.filterwarnings("ignore", category=DeprecationWarning)
from jsonschema import Draft7Validator, RefResolver

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "powerbi"


def validate():
    store = {}
    for p in (P / "schemas").rglob("*.json"):
        s = json.loads(p.read_text())
        u = "https://developer.microsoft.com/" + str(p.relative_to(P / "schemas"))
        store[u] = s
        if "$id" in s:
            store[s["$id"]] = s
    checked = 0
    for p in list((P / "StockSense.Report").rglob("*.json")) + [
        P / "StockSense.Report/definition.pbir",
        P / "StockSense.SemanticModel/definition.pbism",
        P / "StockSense.pbip",
    ]:
        obj = json.loads(p.read_text())
        url = obj["$schema"]
        schema = store[url]
        errors = list(
            Draft7Validator(
                schema, resolver=RefResolver(url, schema, store=store)
            ).iter_errors(obj)
        )
        if errors:
            raise ValueError(
                f"{p.relative_to(ROOT)}: " + "; ".join(e.message for e in errors[:5])
            )
        checked += 1
    manifest = json.loads((P / "data/export_manifest.json").read_text())
    tables = {}
    for name, types in manifest["schema"].items():
        file = P / "data" / f"{name}.csv"
        assert (
            hashlib.sha256(file.read_bytes()).hexdigest()
            == manifest["files"][file.name]["sha256"]
        ), f"{name} hash"
        with file.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            assert reader.fieldnames == list(types), name
            tables[name] = list(reader)
        assert len(tables[name]) == manifest["table_rows"][name], name
    model = json.loads((P / "StockSense.SemanticModel/model.bim").read_text())["model"]
    columns = {t["name"]: {c["name"] for c in t["columns"]} for t in model["tables"]}
    measures = {
        t["name"]: {m["name"] for m in t.get("measures", [])} for t in model["tables"]
    }
    for table in model["tables"]:
        assert columns[table["name"]] == set(manifest["schema"][table["name"]])
        for c in table["columns"]:
            assert c["dataType"] == manifest["schema"][table["name"]][c["name"]]
    for rel in model["relationships"]:
        for side in ("from", "to"):
            assert rel[side + "Column"] in columns[rel[side + "Table"]]
        pk = [r[rel["toColumn"]] for r in tables[rel["toTable"]]]
        assert len(pk) == len(set(pk)), f"Duplicate dimension key: {rel}"
        assert {r[rel["fromColumn"]] for r in tables[rel["fromTable"]]}.issubset(
            set(pk)
        ), f"Orphan relationship: {rel}"

    def expressions(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if (
                    k in ("Column", "Measure")
                    and isinstance(v, dict)
                    and "Expression" in v
                ):
                    table = v["Expression"]["SourceRef"]["Entity"]
                    prop = v["Property"]
                    assert prop in (measures if k == "Measure" else columns)[table], (
                        table,
                        prop,
                    )
                expressions(v)
        elif isinstance(o, list):
            for v in o:
                expressions(v)

    for file in (P / "StockSense.Report").rglob("visual.json"):
        expressions(json.loads(file.read_text()))
    assert len(tables["Products"]) == 5 and len(tables["WeeklySales"]) == 520
    assert (
        len({(r["stock_code"], r["week_start"]) for r in tables["WeeklySales"]}) == 520
    )
    assert len(tables["Scenarios"]) == 27 and len(tables["SimulationSummary"]) == 135
    assert (
        len({(r["stock_code"], r["scenario_key"]) for r in tables["SimulationSummary"]})
        == 135
    )
    assert len(tables["ReplayWeekly"]) == 780
    for row in tables["ReplayWeekly"]:
        assert row["training_last_week"] < row["week_start"]
        assert (
            abs(
                float(row["fulfilled_units"])
                + float(row["unmet_proxy_units"])
                - float(row["observed_sales"])
            )
            < 1e-8
        )
    for row in tables["SimulationSummary"]:
        assert (
            float(row["paired_ci_low_gbp"])
            <= float(row["paired_delta_gbp"])
            <= float(row["paired_ci_high_gbp"])
        )
        assert 0 <= float(row["fill_rate_proxy"]) <= 1
    for key in {
        (r["stock_code"], r["scenario_key"]) for r in tables["SimulationSummary"]
    }:
        counts = [
            int(r["worlds"])
            for r in tables["ProfitHistogram"]
            if (r["stock_code"], r["scenario_key"]) == key
        ]
        assert sum(counts) == manifest["evaluation_worlds"]
    print(
        f"Validated {checked} native report/project files against Microsoft schemas; 12 model tables, relationships, visual field references, CSV hashes/grains, replay accounting and histogram totals."
    )
    return checked


if __name__ == "__main__":
    validate()
