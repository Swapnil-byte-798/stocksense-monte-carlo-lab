-- Run: sqlite3 -header -column output/experiments.db < sql/analysis.sql
-- Repeated identical configurations are legitimate replicates, not duplicate mistakes.
WITH ranked AS (
  SELECT *, ROW_NUMBER() OVER (PARTITION BY config_id ORDER BY id DESC) AS version_rank
  FROM runs
)
SELECT id, config_id, method, selected_order,
       COALESCE(json_extract(result_json, '$.config.data_context.currency'), 'INR') AS currency,
       json_extract(result_json, '$.config.data_context.stock_code') AS stock_code,
       ROUND(mean_profit, 2) AS mean_profit,
       ROUND(tail_profit, 2) AS tail_profit
FROM ranked WHERE version_rank = 1 ORDER BY id DESC LIMIT 20;

-- Compare the selected policy with its paired baseline, preserving complete provenance.
SELECT id, config_id,
       ROUND(json_extract(result_json, '$.paired_delta_ci95.estimate'), 2) AS paired_mean_delta,
       ROUND(json_extract(result_json, '$.paired_delta_ci95.low'), 2) AS delta_ci_low,
       ROUND(json_extract(result_json, '$.paired_delta_ci95.high'), 2) AS delta_ci_high,
       json_extract(result_json, '$.config.seed') AS seed,
       json_extract(result_json, '$.provenance.version') AS engine_version
FROM runs ORDER BY id DESC LIMIT 20;
