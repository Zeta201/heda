import json
from pathlib import Path
from tabulate import tabulate

from heda.validate import (
    load_experiment_yaml,
    validate_experiment,
    ExperimentValidationError,
)

class ClaimCheckError(Exception):
    pass

OPERATORS = {
    ">=": lambda actual, expected: actual >= expected,
    "<=": lambda actual, expected: actual <= expected,
    "==": lambda actual, expected: actual == expected,
}

def load_metrics() -> dict:
    metrics_path = Path("outputs/metrics.json")
    if not metrics_path.exists():
        raise ClaimCheckError("outputs/metrics.json not found")

    try:
        with open(metrics_path, "r") as f:
            metrics = json.load(f)
    except json.JSONDecodeError as e:
        raise ClaimCheckError(f"Invalid metrics.json: {e}")

    if not isinstance(metrics, dict):
        raise ClaimCheckError("metrics.json must be a JSON object")

    return metrics

def check_claims() -> None:
    # 1. Load + validate experiment.yaml
    try:
        experiment = load_experiment_yaml(Path("experiment.yaml"))
        validate_experiment(experiment)
    except ExperimentValidationError as e:
        raise ClaimCheckError(f"Experiment validation failed: {e}")

    # 2. Load metrics
    metrics = load_metrics()

    table = []
    any_fail = False

    # 3. Evaluate each claim
    for claim in experiment["claims"]:
        metric = claim["metric"]
        operator = claim["operator"]
        expected = claim["value"]

        actual = metrics.get(metric, None)
        if actual is None:
            status = "MISSING"
            any_fail = True
            actual_display = "N/A"
        else:
            if OPERATORS[operator](actual, expected):
                status = "PASS"
            else:
                status = "FAIL"
                any_fail = True
            actual_display = actual

        table.append([metric, expected, actual_display, status])

    # 4. Format table
    table_str = tabulate(table, headers=["Metric", "Expected", "Actual", "Status"], tablefmt="github")

    # 5. Print table to console
    print("\nClaim Evaluation Results:\n")
    print(table_str)

    # 6. Save table to outputs/claim_report.txt
    report_dir = Path(".heda/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / "claim_report.txt"

    with open(report_path, "w") as f:
        f.write("Claim Evaluation Results:\n\n")
        f.write(table_str + "\n")

    print(f"\n✔ Claim report saved to {report_path.resolve()}")

    # 7. Fail if any claim failed
    if any_fail:
        raise ClaimCheckError("Some claims failed. See table above or outputs/claim_report.txt")
