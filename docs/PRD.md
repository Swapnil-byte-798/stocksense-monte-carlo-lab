# Product requirements · StockSense 2.0

The product helps a retail analyst explain weekly inventory decisions using real observations and declared assumptions. It also gives a hiring reviewer inspectable evidence of data engineering, statistics, optimization, SQL and Power BI skills. Recruitment and actual profit uplift are not promised outcomes.

Power BI is the primary interface, with no web-development knowledge required. Python prepares data, selects policies, evaluates uncertainty and exports import-mode tables. Six pages cover summary, sales, historical policies, scenarios, decision curve and data quality. Slicers select precomputed runs; new simulation assumptions require Python export then Refresh.

Acceptance requires reproducible source lineage, a temporal evaluation without future leakage, complete baseline comparisons, clear service trade-offs, schema-checked native report definitions, and a documented Windows Desktop refresh/visual acceptance check. Data and schema checks do not substitute for Desktop rendering evidence.

Out of scope: live procurement, causal savings, true lost-demand recovery, service constraints, multi-period stock flows, supplier calibration, real-time Python execution from slicers and Power BI Service deployment. The lognormal scenario is a separate teaching/analytic reference.
