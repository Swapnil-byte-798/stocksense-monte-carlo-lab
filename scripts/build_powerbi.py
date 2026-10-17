"""Build the native PBIP/PBIR report and TMSL semantic model from export schema."""

import json
from pathlib import Path
import uuid

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "powerbi"
REPORT = P / "StockSense.Report"
MODEL = P / "StockSense.SemanticModel"
BASE = "https://developer.microsoft.com/json-schemas/fabric/"


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n")


def measure(name, expression, fmt=None):
    result = {
        "name": name,
        "expression": expression,
        "displayFolder": "StockSense measures",
    }
    if fmt:
        result["formatString"] = fmt
    return result


def build():
    export = json.loads((P / "data/export_manifest.json").read_text())
    write(
        P / "StockSense.pbip",
        {
            "$schema": BASE + "pbip/pbipProperties/1.0.0/schema.json",
            "version": "1.0",
            "artifacts": [{"report": {"path": "StockSense.Report"}}],
            "settings": {"enableAutoRecovery": True},
        },
    )
    write(
        REPORT / "definition.pbir",
        {
            "$schema": BASE + "item/report/definitionProperties/2.0.0/schema.json",
            "version": "4.0",
            "datasetReference": {"byPath": {"path": "../StockSense.SemanticModel"}},
        },
    )
    write(
        MODEL / "definition.pbism",
        {
            "$schema": BASE
            + "item/semanticModel/definitionProperties/1.0.0/schema.json",
            "version": "4.0",
            "settings": {},
        },
    )
    tables = []
    mtypes = {
        "string": "type text",
        "int64": "Int64.Type",
        "double": "type number",
        "dateTime": "type date",
    }
    for name, cols in export["schema"].items():
        columns = []
        for col, kind in cols.items():
            c = {
                "name": col,
                "dataType": kind,
                "sourceColumn": col,
                "summarizeBy": (
                    "none"
                    if kind in ("string", "dateTime")
                    or col.endswith(("_key", "_index", "_order"))
                    else "sum"
                ),
            }
            if kind == "dateTime":
                c["formatString"] = "yyyy-mm-dd"
            elif (
                "rate" in col
                or "probability" in col
                or "fraction" in col
                or col == "wape"
            ):
                c["formatString"] = "0.0%"
            elif "gbp" in col:
                c["formatString"] = "£#,0.00;(£#,0.00);£0.00"
            columns.append(c)
        transforms = ", ".join(
            '{"' + col + '", ' + mtypes[kind] + "}" for col, kind in cols.items()
        )
        expression = [
            "let",
            f'    Source = Csv.Document(File.Contents(DataFolder & "\\{name}.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]),',
            "    Headers = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),",
            f'    Typed = Table.TransformColumnTypes(Headers, {{{transforms}}}, "en-GB")',
            "in",
            "    Typed",
        ]
        tables.append(
            {
                "name": name,
                "columns": columns,
                "partitions": [
                    {
                        "name": name,
                        "mode": "import",
                        "source": {"type": "m", "expression": expression},
                    }
                ],
            }
        )
    money = "£#,0.00;(£#,0.00);£0.00"
    # Default to a named archival product/scenario only when that dimension is unfiltered.
    context = 'VAR p = IF(NOT ISCROSSFILTERED(Products), "85123A", SELECTEDVALUE(Products[stock_code]))\nVAR s = IF(NOT ISCROSSFILTERED(Scenarios), "R20-C55-S0", SELECTEDVALUE(Scenarios[scenario_key]))\n'
    metrics = {
        "Selected order": "selected_order",
        "Baseline order": "baseline_order",
        "Modeled weekly profit GBP": "mean_profit_proxy_gbp",
        "Baseline modeled profit GBP": "baseline_profit_proxy_gbp",
        "Worst 5% profit GBP": "tail_profit_proxy_gbp",
        "Paired modeled difference GBP": "paired_delta_gbp",
        "Numerical CI low GBP": "paired_ci_low_gbp",
        "Numerical CI high GBP": "paired_ci_high_gbp",
        "Simulated fill proxy": "fill_rate_proxy",
        "Baseline fill proxy": "baseline_fill_rate_proxy",
        "Loss probability": "loss_probability",
        "Evaluation worlds": "evaluation_worlds",
    }
    measures = []
    for title, col in metrics.items():
        dax = (
            context
            + f"RETURN IF(NOT ISBLANK(p) && NOT ISBLANK(s), CALCULATE(MAX(SimulationSummary[{col}]), KEEPFILTERS(Products[stock_code]=p), KEEPFILTERS(Scenarios[scenario_key]=s)))"
        )
        fmt = (
            "0.0%"
            if "rate" in col or "probability" in col
            else money if "gbp" in col else "#,0"
        )
        measures.append(measure(title, dax, fmt))
    measures.append(
        measure(
            "Scenario selection",
            context
            + 'RETURN IF(ISBLANK(p) || ISBLANK(s), "Choose one product and one complete scenario", p & " | " & s & " | modeled outcomes; not actual savings")',
        )
    )
    measures.extend(
        [
            measure("Observed weekly units", "SUM(WeeklySales[units])", "#,0"),
            measure(
                "Replay weekly profit GBP",
                "AVERAGE(ReplayWeekly[profit_proxy_gbp])",
                money,
            ),
            measure(
                "Replay fill proxy",
                "DIVIDE(SUM(ReplayWeekly[fulfilled_units]), SUM(ReplayWeekly[observed_sales]))",
                "0.0%",
            ),
            measure(
                "Replay unmet proxy", "SUM(ReplayWeekly[unmet_proxy_units])", "#,0"
            ),
            measure(
                "Replay tail GBP",
                "AVERAGE(ReplaySummary[worst_5pct_profit_proxy_gbp])",
                money,
            ),
            measure("Replay average order", "AVERAGE(ReplayWeekly[order])", "#,0"),
            measure("Raw source rows", "MAX(CleaningAudit[rows])", "#,0"),
            measure("Removed sale lines", "SUM(CleaningAudit[removed])", "#,0"),
            measure(
                "Curve mean GBP",
                context
                + "RETURN IF(NOT ISBLANK(p) && NOT ISBLANK(s), CALCULATE(MAX(PolicyCurve[mean_profit_proxy_gbp]), KEEPFILTERS(Products[stock_code]=p), KEEPFILTERS(Scenarios[scenario_key]=s)))",
                money,
            ),
            measure(
                "Curve tail GBP",
                context
                + "RETURN IF(NOT ISBLANK(p) && NOT ISBLANK(s), CALCULATE(MAX(PolicyCurve[tail_profit_proxy_gbp]), KEEPFILTERS(Products[stock_code]=p), KEEPFILTERS(Scenarios[scenario_key]=s)))",
                money,
            ),
            measure(
                "Curve score GBP",
                context
                + "RETURN IF(NOT ISBLANK(p) && NOT ISBLANK(s), CALCULATE(MAX(PolicyCurve[score_gbp]), KEEPFILTERS(Products[stock_code]=p), KEEPFILTERS(Scenarios[scenario_key]=s)))",
                money,
            ),
            measure(
                "Histogram worlds",
                context
                + "RETURN IF(NOT ISBLANK(p) && NOT ISBLANK(s), CALCULATE(SUM(ProfitHistogram[worlds]), KEEPFILTERS(Products[stock_code]=p), KEEPFILTERS(Scenarios[scenario_key]=s)))",
                "#,0",
            ),
        ]
    )
    next(t for t in tables if t["name"] == "SimulationSummary")["measures"] = measures
    relationships = []
    for table in (
        "WeeklySales",
        "SimulationSummary",
        "PolicyCurve",
        "ProfitHistogram",
        "ReplaySummary",
        "ReplayWeekly",
        "ForecastDiagnostics",
    ):
        relationships.append(
            {
                "name": str(uuid.uuid5(uuid.NAMESPACE_URL, table + "-Product")),
                "fromTable": table,
                "fromColumn": "stock_code",
                "toTable": "Products",
                "toColumn": "stock_code",
                "crossFilteringBehavior": "oneDirection",
            }
        )
    for table in ("SimulationSummary", "PolicyCurve", "ProfitHistogram"):
        relationships.append(
            {
                "name": str(uuid.uuid5(uuid.NAMESPACE_URL, table + "-Scenario")),
                "fromTable": table,
                "fromColumn": "scenario_key",
                "toTable": "Scenarios",
                "toColumn": "scenario_key",
                "crossFilteringBehavior": "oneDirection",
            }
        )
    for table in ("WeeklySales", "ReplayWeekly"):
        relationships.append(
            {
                "name": str(uuid.uuid5(uuid.NAMESPACE_URL, table + "-Week")),
                "fromTable": table,
                "fromColumn": "week_start",
                "toTable": "Weeks",
                "toColumn": "week_start",
                "crossFilteringBehavior": "oneDirection",
            }
        )
    model = {
        "name": "StockSense",
        "compatibilityLevel": 1567,
        "model": {
            "culture": "en-GB",
            "defaultPowerBIDataSourceVersion": "powerBI_V3",
            "dataAccessOptions": {
                "legacyRedirects": True,
                "returnErrorValuesAsNull": True,
            },
            "tables": tables,
            "relationships": relationships,
            "expressions": [
                {
                    "name": "DataFolder",
                    "kind": "m",
                    "expression": '"C:\\StockSense\\powerbi\\data" meta [IsParameterQuery=true, Type="Text", IsParameterQueryRequired=true]',
                }
            ],
            "annotations": [
                {
                    "name": "PBI_QueryOrder",
                    "value": json.dumps(["DataFolder"] + list(export["schema"])),
                }
            ],
        },
    }
    write(MODEL / "model.bim", model)
    (P / "measures.dax").write_text(
        "\n\n".join("// " + m["name"] + "\n" + m["expression"] for m in measures) + "\n"
    )

    def schema(kind, version):
        return BASE + f"item/report/definition/{kind}/{version}/schema.json"

    write(
        REPORT / "definition/version.json",
        {"$schema": schema("versionMetadata", "1.0.0"), "version": "2.0.0"},
    )
    write(
        REPORT / "definition/report.json",
        {
            "$schema": schema("report", "3.0.0"),
            "themeCollection": {
                "baseTheme": {
                    "name": "CY24SU06",
                    "reportVersionAtImport": {
                        "visual": "1.8.50",
                        "report": "2.0.50",
                        "page": "1.3.50",
                    },
                    "type": "SharedResources",
                }
            },
            "settings": {"useStylableVisualContainerHeader": True},
        },
    )
    ids = []

    def literal(v):
        return {
            "expr": {
                "Literal": {
                    "Value": (
                        "'" + v.replace("'", "''") + "'"
                        if isinstance(v, str)
                        else "true" if v is True else "false" if v is False else str(v)
                    )
                }
            }
        }

    def field(table, col, ms=False):
        return {
            ("Measure" if ms else "Column"): {
                "Expression": {"SourceRef": {"Entity": table}},
                "Property": col,
            }
        }

    def projection(table, col, ms=False):
        return {
            "field": field(table, col, ms),
            "queryRef": table + "." + col,
            "nativeQueryRef": col,
        }

    def page(name, label, title, subtitle):
        ids.append(name)
        path = REPORT / "definition/pages" / name
        write(
            path / "page.json",
            {
                "$schema": schema("page", "2.0.0"),
                "name": name,
                "displayName": label,
                "displayOption": "FitToPage",
                "height": 900,
                "width": 1440,
                "objects": {
                    "background": [
                        {
                            "properties": {
                                "color": {"solid": {"color": literal("#F3F6F2")}},
                                "transparency": literal(0),
                            }
                        }
                    ]
                },
            },
        )
        visual(
            path,
            "header",
            "textbox",
            24,
            12,
            1392,
            85,
            {},
            None,
            {
                "general": [
                    {
                        "properties": {
                            "paragraphs": [
                                {
                                    "textRuns": [
                                        {
                                            "value": "STOCKSENSE  /  " + title,
                                            "textStyle": {
                                                "fontFamily": "Segoe UI",
                                                "fontSize": "25pt",
                                                "fontWeight": "bold",
                                                "color": "#173E39",
                                            },
                                        }
                                    ]
                                },
                                {
                                    "textRuns": [
                                        {
                                            "value": subtitle,
                                            "textStyle": {
                                                "fontSize": "11pt",
                                                "color": "#526C64",
                                            },
                                        }
                                    ]
                                },
                            ]
                        }
                    }
                ]
            },
        )
        return path

    def visual(path, name, kind, x, y, w, h, roles, title=None, objects=None):
        v = {"visualType": kind, "drillFilterOtherVisuals": True}
        if roles:
            v["query"] = {
                "queryState": {
                    role: {"projections": [projection(*f) for f in fields]}
                    for role, fields in roles.items()
                }
            }
        if (
            roles
            and kind in ("lineChart", "clusteredColumnChart")
            and "Category" in roles
        ):
            v["query"]["sortDefinition"] = {
                "sort": [
                    {"field": field(*roles["Category"][0]), "direction": "Ascending"}
                ],
                "isDefaultSort": False,
            }
        if objects:
            v["objects"] = objects
        v["visualContainerObjects"] = {
            "background": [
                {
                    "properties": {
                        "show": literal(True),
                        "color": {"solid": {"color": literal("#FFFFFF")}},
                        "transparency": literal(0),
                    }
                }
            ],
            "border": [
                {
                    "properties": {
                        "show": literal(True),
                        "color": {"solid": {"color": literal("#DCE6DE")}},
                        "radius": literal(10),
                    }
                }
            ],
        }
        if title:
            v["visualContainerObjects"]["title"] = [
                {
                    "properties": {
                        "show": literal(True),
                        "text": literal(title),
                        "fontSize": literal(12),
                        "fontColor": {"solid": {"color": literal("#173E39")}},
                    }
                }
            ]
        write(
            path / "visuals" / name / "visual.json",
            {
                "$schema": schema("visualContainer", "2.3.0"),
                "name": name,
                "position": {
                    "x": x,
                    "y": y,
                    "z": len(list(path.glob("visuals/*"))),
                    "height": h,
                    "width": w,
                    "tabOrder": len(list(path.glob("visuals/*"))),
                },
                "visual": v,
            },
        )

    def slicers(p, scenario=True):
        visual(
            p,
            "product",
            "slicer",
            24,
            108,
            820 if scenario else 1392,
            74,
            {"Values": [("Products", "product_label")]},
            "Product · clear selection for default 85123A",
        )
        if scenario:
            visual(
                p,
                "scenario",
                "slicer",
                860,
                108,
                556,
                74,
                {"Values": [("Scenarios", "scenario_label")]},
                "Scenario · default risk 20%, cost 55%, no stress",
            )

    def card(p, name, metric, x, y, w=268):
        visual(
            p,
            name,
            "card",
            x,
            y,
            w,
            105,
            {"Values": [("SimulationSummary", metric, True)]},
            metric,
        )

    def table(p, name, cols, x, y, w, h, title):
        visual(p, name, "tableEx", x, y, w, h, {"Values": cols}, title)

    p = page(
        "DecisionSummary",
        "01 · Decision summary",
        "DECISIONS UNDER UNCERTAINTY",
        "Real UCI sales • GBP modeled economics • archival planning week 2011-12-05 • not actual business savings",
    )
    slicers(p)
    for i, m in enumerate(
        [
            "Selected order",
            "Modeled weekly profit GBP",
            "Worst 5% profit GBP",
            "Simulated fill proxy",
            "Loss probability",
        ]
    ):
        card(p, "kpi" + str(i), m, 24 + i * 281, 202)
    table(
        p,
        "selection",
        [("SimulationSummary", "Scenario selection", True)],
        24,
        326,
        1392,
        75,
        "Selection status",
    )
    visual(
        p,
        "profit",
        "clusteredBarChart",
        24,
        420,
        820,
        330,
        {
            "Category": [("ReplayWeekly", "policy")],
            "Y": [("SimulationSummary", "Replay weekly profit GBP", True)],
        },
        "39-week historical replay · average profit proxy per product-week",
    )
    table(
        p,
        "uncertainty",
        [
            ("SimulationSummary", m, True)
            for m in [
                "Baseline order",
                "Baseline modeled profit GBP",
                "Baseline fill proxy",
                "Paired modeled difference GBP",
                "Numerical CI low GBP",
                "Numerical CI high GBP",
            ]
        ],
        860,
        420,
        556,
        330,
        "Final-refit simulation · paired numerical interval only",
    )
    table(
        p,
        "caution",
        [("ModelNotes", "topic"), ("ModelNotes", "explanation")],
        24,
        768,
        1392,
        110,
        "Interpret before acting · no inventory availability or measured purchase costs",
    )
    p = page(
        "ObservedSales",
        "02 · Observed sales",
        "OBSERVED SALES",
        "104 complete Monday–Sunday weeks • missing sale weeks zero-filled • sales are a demand proxy",
    )
    slicers(p, False)
    visual(
        p,
        "history",
        "lineChart",
        24,
        204,
        1392,
        380,
        {
            "Category": [("Weeks", "week_start")],
            "Y": [("SimulationSummary", "Observed weekly units", True)],
            "Series": [("Weeks", "split")],
        },
        "Weekly sales · training 52 / validation 13 / test 39",
    )
    table(
        p,
        "weekly",
        [
            ("Products", "stock_code"),
            ("Weeks", "week_start"),
            ("Weeks", "split"),
            ("SimulationSummary", "Observed weekly units", True),
        ],
        24,
        604,
        850,
        270,
        "Observed weekly panel · export this visual as CSV",
    )
    table(
        p,
        "products",
        [
            ("Products", "stock_code"),
            ("Products", "description"),
            ("Products", "training_units"),
            ("Products", "reference_price_gbp"),
        ],
        892,
        604,
        524,
        270,
        "Products chosen from initial training only",
    )
    p = page(
        "PolicyReplay",
        "03 · Historical policy test",
        "TEST POLICIES CHRONOLOGICALLY",
        "39 held-out weeks per product • prior 52 weeks only • fixed assumed costs • full delivery • weekly reset",
    )
    slicers(p, False)
    visual(
        p,
        "profits",
        "clusteredBarChart",
        24,
        202,
        686,
        300,
        {
            "Category": [("ReplayWeekly", "policy")],
            "Y": [("SimulationSummary", "Replay weekly profit GBP", True)],
        },
        "Profit proxy · all four policies, including unfavorable results",
    )
    visual(
        p,
        "fill",
        "clusteredBarChart",
        730,
        202,
        686,
        300,
        {
            "Category": [("ReplayWeekly", "policy")],
            "Y": [("SimulationSummary", "Replay fill proxy", True)],
        },
        "Fulfilled observed units · lower orders can reduce service",
    )
    visual(
        p,
        "weeklyprofit",
        "lineChart",
        24,
        522,
        1392,
        220,
        {
            "Category": [("Weeks", "week_start")],
            "Y": [("SimulationSummary", "Replay weekly profit GBP", True)],
            "Series": [("ReplayWeekly", "policy")],
        },
        "Out-of-time weekly profit proxy · no Monte Carlo selection noise",
    )
    table(
        p,
        "diagnostics",
        [
            ("Products", "stock_code"),
            ("ForecastDiagnostics", "split"),
            ("ForecastDiagnostics", "policy"),
            ("ForecastDiagnostics", "mae_units"),
            ("ForecastDiagnostics", "wape"),
        ],
        24,
        762,
        1392,
        112,
        "Forecast diagnostics · reorder policies are not forecasts",
    )
    p = page(
        "ScenarioLab",
        "04 · Scenario explorer",
        "EXPLORE DECLARED ASSUMPTIONS",
        "27 scenarios × 5 products • cost 45/55/65% • risk 0/20/50% • hypothetical supplier failure 0/10/25%",
    )
    slicers(p)
    for i, m in enumerate(
        [
            "Selected order",
            "Modeled weekly profit GBP",
            "Worst 5% profit GBP",
            "Simulated fill proxy",
            "Evaluation worlds",
        ]
    ):
        card(p, "kpi" + str(i), m, 24 + i * 281, 202)
    table(
        p,
        "selection",
        [("SimulationSummary", "Scenario selection", True)],
        24,
        326,
        1392,
        74,
        "One product and one scenario · slicers select precomputed seeded simulations",
    )
    visual(
        p,
        "distribution",
        "clusteredColumnChart",
        24,
        420,
        1392,
        300,
        {
            "Category": [("ProfitHistogram", "bin_index")],
            "Y": [("SimulationSummary", "Histogram worlds", True)],
        },
        "Selected-policy profit distribution · bin index, see bounds below",
    )
    table(
        p,
        "bins",
        [
            ("Products", "stock_code"),
            ("Scenarios", "scenario_key"),
            ("ProfitHistogram", "bin_index"),
            ("ProfitHistogram", "bin_low_gbp"),
            ("ProfitHistogram", "bin_high_gbp"),
            ("ProfitHistogram", "worlds"),
        ],
        24,
        740,
        1392,
        135,
        "Bin bounds and underlying counts · filter product/scenario before export",
    )
    p = page(
        "DecisionCurve",
        "05 · Decision curve",
        "SEE WHY THE ORDER CHANGES",
        "106 candidate quantities per product/scenario • score combines mean profit and worst-tail profit • curves use selection worlds",
    )
    slicers(p)
    visual(
        p,
        "curve",
        "lineChart",
        24,
        204,
        1392,
        400,
        {
            "Category": [("PolicyCurve", "order")],
            "Y": [
                ("SimulationSummary", m, True)
                for m in ["Curve mean GBP", "Curve tail GBP", "Curve score GBP"]
            ],
        },
        "Expected return, downside, and blended objective versus quantity",
    )
    table(
        p,
        "curvevalues",
        [
            ("Products", "stock_code"),
            ("Scenarios", "scenario_key"),
            ("PolicyCurve", "order"),
            ("PolicyCurve", "mean_profit_proxy_gbp"),
            ("PolicyCurve", "tail_profit_proxy_gbp"),
            ("PolicyCurve", "score_gbp"),
            ("PolicyCurve", "fill_rate_proxy"),
        ],
        24,
        624,
        1392,
        250,
        "Inspect/export candidate scores · selected quantity is independently evaluated",
    )
    p = page(
        "DataQuality",
        "06 · Data quality & learning",
        "TRUST THE DATA, QUESTION THE MODEL",
        "Chen, D. (2012), UCI Online Retail II • DOI 10.24432/C5CG6D • CC BY 4.0 • filtered/aggregated derivative",
    )
    table(
        p,
        "audit",
        [
            ("CleaningAudit", "stage"),
            ("CleaningAudit", "removed"),
            ("CleaningAudit", "rows"),
        ],
        24,
        110,
        580,
        400,
        "Sequential audit · each excluded row counted once",
    )
    table(
        p,
        "notes",
        [("ModelNotes", "topic"), ("ModelNotes", "explanation")],
        624,
        110,
        792,
        400,
        "Data and modeling boundaries",
    )
    table(
        p,
        "provenance",
        [
            ("Products", "stock_code"),
            ("Scenarios", "scenario_key"),
            ("SimulationSummary", "config_id"),
            ("SimulationSummary", "method"),
            ("SimulationSummary", "seed"),
            ("SimulationSummary", "replicates"),
            ("SimulationSummary", "history_sha256"),
        ],
        24,
        530,
        1392,
        344,
        "Run provenance · Python export manifest carries hashes and schema",
    )
    write(
        REPORT / "definition/pages/pages.json",
        {
            "$schema": schema("pagesMetadata", "1.0.0"),
            "pageOrder": ids,
            "activePageName": ids[0],
        },
    )
    write(
        P / "StockSense-theme.json",
        {
            "name": "StockSense · Evergreen",
            "dataColors": [
                "#087F73",
                "#E4A648",
                "#577DA3",
                "#A8798C",
                "#789565",
                "#C36C52",
            ],
            "background": "#F3F6F2",
            "foreground": "#173E39",
            "tableAccent": "#087F73",
            "textClasses": {
                "title": {"fontFace": "Segoe UI", "fontSize": 14, "color": "#173E39"},
                "label": {"fontFace": "Segoe UI", "fontSize": 11, "color": "#526C64"},
                "callout": {
                    "fontFace": "Segoe UI Semibold",
                    "fontSize": 30,
                    "color": "#087F73",
                },
            },
        },
    )
    print(
        f"Built native Power BI project: {len(ids)} pages, {len(tables)} tables, {len(measures)} DAX measures"
    )


if __name__ == "__main__":
    build()
