Here is a ready-to-import Grafana dashboard JSON. It includes:

* κ (overall) stat + time series
* FP rate (range & rolling)
* Cost (total) + cost by method
* p95 latency per method
* Evaluations count by method
* Downgrades (budget/timeout) total + by reason

How to use:

1. In Grafana → Dashboards → Import → paste the JSON from the canvas.
2. Pick your Prometheus datasource (or set the `DS_PROMETHEUS` variable to your UID).
3. Optional: filter by `env`, `artifact_type`, and `method` using the dashboard variables.

If your metric names differ, tweak the queries in-place. The panels expect:

* `phase2:kappa_overall` (or `phase2_kappa_overall`)
* `resolutions_false_positive_total`, `resolutions_applied_total`
* `judge_cost_usd_sum`
* `judge_latency_ms_bucket` (Prometheus histogram)
* `judge_evaluations_total`
* `judge_budget_downgrade_total`

```
{
  "annotations": {
    "list": []
  },
  "editable": true,
  "fiscalYearStartMonth": 1,
  "graphTooltip": 0,
  "id": null,
  "links": [],
  "liveNow": false,
  "panels": [
    {
      "type": "stat",
      "title": "Fleiss' κ (overall)",
      "gridPos": {"h": 6, "w": 6, "x": 0, "y": 0},
      "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
      "targets": [
        {"expr": "phase2:kappa_overall or phase2_kappa_overall", "legendFormat": "κ"}
      ],
      "options": {
        "reduceOptions": {"calcs": ["lastNotNull"], "fields": ""},
        "orientation": "auto",
        "textMode": "auto",
        "colorMode": "value",
        "graphMode": "area",
        "justifyMode": "auto"
      },
      "fieldConfig": {"defaults": {"unit": "none", "thresholds": {"mode": "absolute", "steps": [{"color": "red", "value": null}, {"color": "green", "value": 0.8}]}}}
    },

    {
      "type": "timeseries",
      "title": "κ over time",
      "gridPos": {"h": 6, "w": 12, "x": 6, "y": 0},
      "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
      "targets": [
        {"expr": "phase2:kappa_overall", "legendFormat": "κ overall"}
      ],
      "fieldConfig": {"defaults": {"unit": "none"}},
      "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    },

    {
      "type": "table",
      "title": "Per-method evaluations (count)",
      "gridPos": {"h": 7, "w": 6, "x": 0, "y": 6},
      "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
      "targets": [
        {"expr": "sum by (method) (increase(judge_evaluations_total{env=~\"$env\", artifact_type=~\"$artifact_type\"}[$__range]))", "legendFormat": "{{method}}"}
      ],
      "options": {"showHeader": true}
    },

    {
      "type": "stat",
      "title": "False positive rate (range)",
      "gridPos": {"h": 6, "w": 6, "x": 6, "y": 6},
      "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
      "targets": [
        {"expr": "(increase(resolutions_false_positive_total{env=~\"$env\"}[$__range]) / clamp_min(increase(resolutions_applied_total{env=~\"$env\"}[$__range]), 1))", "legendFormat": "FP rate"}
      ],
      "fieldConfig": {"defaults": {"unit": "percentunit", "thresholds": {"mode": "absolute", "steps": [{"color": "green", "value": null}, {"color": "red", "value": 0.02}]}}},
      "options": {"reduceOptions": {"calcs": ["lastNotNull"], "fields": ""}}
    },

    {
      "type": "timeseries",
      "title": "FP rate (rolling)",
      "gridPos": {"h": 6, "w": 6, "x": 12, "y": 6},
      "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
      "targets": [
        {"expr": "(rate(resolutions_false_positive_total{env=~\"$env\"}[5m]) / clamp_min(rate(resolutions_applied_total{env=~\"$env\"}[5m]), 1))", "legendFormat": "FP rate"}
      ],
      "fieldConfig": {"defaults": {"unit": "percentunit"}},
      "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    },

    {
      "type": "stat",
      "title": "Cost (USD, range)",
      "gridPos": {"h": 6, "w": 6, "x": 0, "y": 13},
      "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
      "targets": [
        {"expr": "sum(increase(judge_cost_usd_sum{env=~\"$env\"}[$__range]))", "legendFormat": "cost"}
      ],
      "fieldConfig": {"defaults": {"unit": "currencyUSD"}},
      "options": {"reduceOptions": {"calcs": ["lastNotNull"], "fields": ""}}
    },

    {
      "type": "bargauge",
      "title": "Cost by method (range)",
      "gridPos": {"h": 6, "w": 12, "x": 6, "y": 13},
      "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
      "targets": [
        {"expr": "sum by (method) (increase(judge_cost_usd_sum{env=~\"$env\", artifact_type=~\"$artifact_type\"}[$__range]))", "legendFormat": "{{method}}"}
      ],
      "fieldConfig": {"defaults": {"unit": "currencyUSD"}},
      "options": {"displayMode": "basic", "min": 0}
    },

    {
      "type": "timeseries",
      "title": "p95 latency by method (ms)",
      "gridPos": {"h": 7, "w": 12, "x": 0, "y": 19},
      "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
      "targets": [
        {"expr": "histogram_quantile(0.95, sum by (le, method) (rate(judge_latency_ms_bucket{env=~\"$env\", method=~\"$method\", artifact_type=~\"$artifact_type\"}[5m])))", "legendFormat": "p95 {{method}}"}
      ],
      "fieldConfig": {"defaults": {"unit": "ms"}},
      "options": {"legend": {"displayMode": "list", "placement": "bottom"}}
    },

    {
      "type": "stat",
      "title": "Downgrades (budget/timeout) — range",
      "gridPos": {"h": 7, "w": 6, "x": 12, "y": 19},
      "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
      "targets": [
        {"expr": "sum(increase(judge_budget_downgrade_total{env=~\"$env\"}[$__range]))", "legendFormat": "downgrades"}
      ],
      "options": {"reduceOptions": {"calcs": ["lastNotNull"], "fields": ""}}
    },

    {
      "type": "table",
      "title": "Downgrades by reason (range)",
      "gridPos": {"h": 7, "w": 12, "x": 0, "y": 26},
      "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
      "targets": [
        {"expr": "sum by (reason) (increase(judge_budget_downgrade_total{env=~\"$env\"}[$__range]))", "legendFormat": "{{reason}}"}
      ],
      "options": {"showHeader": true}
    }
  ],
  "refresh": "30s",
  "schemaVersion": 39,
  "style": "dark",
  "tags": ["phase2", "judge", "ai"],
  "templating": {
    "list": [
      {
        "name": "DS_PROMETHEUS",
        "type": "datasource",
        "query": "prometheus",
        "label": "Prometheus",
        "current": {"selected": true},
        "hide": 0
      },
      {
        "name": "env",
        "type": "query",
        "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
        "query": "label_values(judge_evaluations_total, env)",
        "refresh": 2,
        "includeAll": true,
        "multi": true,
        "label": "Environment",
        "current": {"text": "All", "value": [".*"]}
      },
      {
        "name": "artifact_type",
        "type": "query",
        "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
        "query": "label_values(judge_evaluations_total, artifact_type)",
        "refresh": 2,
        "includeAll": true,
        "multi": true,
        "label": "Artifact type",
        "current": {"text": "All", "value": [".*"]}
      },
      {
        "name": "method",
        "type": "query",
        "datasource": {"type": "prometheus", "uid": "${DS_PROMETHEUS}"},
        "query": "label_values(judge_evaluations_total, method)",
        "refresh": 2,
        "includeAll": true,
        "multi": true,
        "label": "Method",
        "current": {"text": "All", "value": [".*"]}
      }
    ]
  },
  "time": {"from": "now-7d", "to": "now"},
  "timepicker": {"refresh_intervals": ["5s","10s","30s","1m","5m","15m","1h","6h"]},
  "timezone": "utc",
  "title": "Phase 2 — Judge Quality & Cost",
  "uid": "phase2-judge-dashboard",
  "version": 1
}
```
