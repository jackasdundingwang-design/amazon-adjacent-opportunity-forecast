"""Monthly proxy forecasts; not a new-product success or population estimator."""
import argparse
import datetime as dt
import json
import math
import re
import shutil
from pathlib import Path

HORIZON = 18
MODEL = "google/timesfm-2.5-200m-pytorch"


def month_index(value):
    if not re.fullmatch(r"\d{4}-\d{2}", value):
        raise ValueError("month must be YYYY-MM")
    date = dt.date.fromisoformat(value + "-01")
    return date.year * 12 + date.month - 1


def month_label(index):
    return f"{index // 12:04d}-{index % 12 + 1:02d}"


def validate(data):
    for key in ("series_id", "source", "scope", "unit"):
        if not isinstance(data.get(key), str) or not data[key].strip():
            raise ValueError(f"missing {key}")
    if data["scope"] not in ("sample", "category_proxy", "market"):
        raise ValueError("invalid scope")
    if data["scope"] == "market" and not data.get("coverage_evidence"):
        raise ValueError("market requires coverage_evidence")
    if data["unit"] not in ("units", "searches"):
        raise ValueError("unsupported unit")
    cutoff = dt.date.fromisoformat(data["as_of"])
    rows = data["observations"]
    if not 12 <= len(rows) <= 512:
        raise ValueError("need 12..512 complete monthly observations")
    indices = [month_index(row["month"]) for row in rows]
    if any(b != a + 1 for a, b in zip(indices, indices[1:])):
        raise ValueError("duplicate, missing or unordered months")
    if indices[-1] >= cutoff.year * 12 + cutoff.month - 1:
        raise ValueError("partial or future month is forbidden")
    values = [row["value"] for row in rows]
    if any(isinstance(v, bool) or not isinstance(v, (int, float))
           or not math.isfinite(v) or v < 0 for v in values):
        raise ValueError("values must be finite nonnegative numbers; missing is not zero")
    return indices[-1], values


def seasonal(values):
    return [float(values[-12 + i % 12]) for i in range(HORIZON)], None


def metrics(actual, predicted):
    errors = [p - a for p, a in zip(predicted, actual)]
    total = sum(actual)
    return {"mae": sum(map(abs, errors)) / len(errors),
            "wape": sum(map(abs, errors)) / total if total else None,
            "mean_bias": sum(errors) / len(errors)}


def preflight():
    import psutil
    free_ram = psutil.virtual_memory().available / 2**30
    free_disk = shutil.disk_usage(Path.home()).free / 2**30
    result = {"available_ram_gib": free_ram, "free_disk_gib": free_disk,
              "ready": free_ram >= 4 and free_disk >= 2}
    return result


def load_model(revision):
    if not revision or not re.fullmatch(r"[a-f0-9]{40}", revision):
        raise ValueError("provide official 40-character model revision")
    if not preflight()["ready"]:
        raise RuntimeError("insufficient available RAM/disk; use seasonal backend")
    import numpy as np
    import torch
    import timesfm
    torch.set_num_threads(4)
    model = timesfm.TimesFM_2p5_200M_torch.from_pretrained(
        MODEL, revision=revision, torch_compile=False)
    model.compile(timesfm.ForecastConfig(
        max_context=512, max_horizon=32, per_core_batch_size=1,
        normalize_inputs=True, use_continuous_quantile_head=True,
        infer_is_positive=True, fix_quantile_crossing=True))

    def predict(values):
        point, q = model.forecast(horizon=HORIZON,
                                  inputs=[np.asarray(values, dtype=np.float32)])
        if point.shape != (1, HORIZON) or q.shape != (1, HORIZON, 10):
            raise RuntimeError("unexpected model output shape")
        if not np.isfinite(point).all() or not np.isfinite(q).all():
            raise RuntimeError("nonfinite model output")
        return np.maximum(point[0], 0).tolist(), np.maximum(q[0, :, 1:10], 0).tolist()
    return predict


def run(data, predict, backend, revision=None):
    last, values = validate(data)
    point, quantiles = predict(values)
    baseline, _ = seasonal(values)
    result = {"series_id": data["series_id"], "as_of": data["as_of"],
              "source": data["source"], "scope": data["scope"], "unit": data["unit"],
              "last_observed_month": month_label(last),
              "forecast_origin": "last_observed_month_not_as_of",
              "stale_months": month_index(data["as_of"][:7]) - last - 1,
              "backend": backend, "model_revision": revision,
              "production_approved": False,
              "months": [month_label(last + i + 1) for i in range(HORIZON)],
              "point": point, "seasonal_baseline": baseline,
              "sum_months_7_18_point": sum(point[6:18]),
              "sum_months_1_18_point": sum(point),
              "q10_to_q90_uncalibrated": quantiles,
              "population": None, "backtest": None,
              "warning": "Proxy trend only; no calibrated success probability or population estimate. Single holdout cannot establish 18-month accuracy."}
    if len(values) >= 42:
        actual = values[-HORIZON:]
        test_point, test_q = predict(values[:-HORIZON])
        naive, _ = seasonal(values[:-HORIZON])
        result["backtest"] = {"type": "single_retrospective_18_month_holdout",
                              "model": metrics(actual, test_point),
                              "seasonal": metrics(actual, naive)}
        if test_q is not None:
            result["backtest"]["nominal_80_empirical_coverage"] = sum(
                row[0] <= a <= row[8] for row, a in zip(test_q, actual)) / HORIZON
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path)
    parser.add_argument("--backend", choices=("seasonal", "timesfm"), default="seasonal")
    parser.add_argument("--revision")
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        print(json.dumps(preflight()))
        return
    if args.input is None:
        parser.error("--input is required")
    data = json.loads(args.input.read_text())
    validate(data)  # Reject unsuitable data before downloading any model.
    predict = load_model(args.revision) if args.backend == "timesfm" else seasonal
    print(json.dumps(run(data, predict, args.backend, args.revision), allow_nan=False))


if __name__ == "__main__":
    main()
