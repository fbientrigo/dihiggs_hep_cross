"""Machine-readable + enforceable version of the model-point -> LLP recast
input contract (docs/contracts/model_point_to_llp_recast_contract.md).

The prose contract describes how a 2HDM (or other BSM scalar-pair) scan point
must be packaged before it enters the recast layer. This module turns the
"Required columns" table and the ctau consistency rule into something a script
can check, so a hand-built or drifted model-point CSV fails loudly instead of
silently laundering a wrong lifetime into the recast.

CLI:

    python -m llp_recast.data_contract --input model_points.csv

Programmatic:

    from llp_recast.data_contract import validate_csv, MODEL_POINT_CONTRACT
    report = validate_csv("model_points.csv")
    if not report.ok:
        raise SystemExit(report.describe())
"""
from __future__ import annotations

import argparse
import csv
import math
import os
import sys

from .constants import HBAR_C_GEV_MM

# Columns every model point must carry (contract "Required columns per model
# point"). Kept in one place so the recast entry points and this validator
# agree on the schema.
REQUIRED_COLUMNS = [
    "model",
    "point_id",
    "m_scalar_GeV",
    "total_width_GeV",
    "ctau_mm",
    "sigma_production_fb",
    "BR_bb",
    "BR_WW",
    "BR_ZZ",
    "BR_gg",
    "BR_tautau",
    "BR_hadronic_proxy",
    "beta_gamma_source",
    "recast_channel_hint",
]

ALLOWED_BETA_GAMMA_SOURCE = {
    "assumed_flat",
    "mg5_pythia_truth",
    "analytic_kinematics",
}

# The same physical quantity is named ctau_mm_H2 in dihiggs_boundary's CSVs.
ALIASES = {
    "ctau_mm": ["ctau_mm_H2"],
    "total_width_GeV": ["total_width_H2"],
    "m_scalar_GeV": ["mS_GeV"],
}

MODEL_POINT_CONTRACT = {
    "name": "model_point_to_llp_recast_v1",
    "produced_by": "a BSM scalar-pair scan (e.g. dihiggs / dihiggs_boundary)",
    "consumed_by": "src/llp_recast, scripts/03_paper_s_benchmark_proxy.py",
    "required_columns": REQUIRED_COLUMNS,
    "aliases": ALIASES,
    "invariants": [
        # ctau_mm must equal hbar_c / total_width_GeV (contract: "must equal
        # HBAR_C_GEV_MM / total_width_GeV; do not supply an independently-
        # guessed value").
        {
            "name": "ctau_mm == hbar_c / total_width_GeV",
            "output": "ctau_mm",
            "numerator": HBAR_C_GEV_MM,
            "denominator": "total_width_GeV",
            "rel_tol": 1e-4,
        },
        # Exclusive BRs must not sum above 1 (contract: "must sum to <= 1").
        {
            "name": "sum(BR_bb..BR_tautau) <= 1",
            "kind": "sum_le_one",
            "columns": ["BR_bb", "BR_WW", "BR_ZZ", "BR_gg", "BR_tautau"],
            "abs_tol": 1e-6,
        },
    ],
}


def _to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return float("nan")


def _finite(x):
    return isinstance(x, float) and math.isfinite(x)


class ValidationReport:
    def __init__(self, path):
        self.path = path
        self.contract_name = MODEL_POINT_CONTRACT["name"]
        self.missing_columns = []
        self.invariant_violations = []  # (name, count, first_example)
        self.bad_enum_rows = []  # (row_index, value) for beta_gamma_source
        self.n_rows = 0
        self.error = ""

    @property
    def ok(self):
        return not (
            self.error
            or self.missing_columns
            or self.invariant_violations
            or self.bad_enum_rows
        )

    def describe(self):
        if self.ok:
            return "[recast][OK] %s satisfies %s (%d rows)" % (
                self.path,
                self.contract_name,
                self.n_rows,
            )
        lines = ["[recast][FAIL] %s violates %s:" % (self.path, self.contract_name)]
        if self.error:
            lines.append("  - %s" % self.error)
        if self.missing_columns:
            lines.append(
                "  - missing required columns: %s" % ", ".join(self.missing_columns)
            )
        for name, count, example in self.invariant_violations:
            lines.append(
                "  - invariant %r violated in %d row(s); first: %s"
                % (name, count, example)
            )
        if self.bad_enum_rows:
            idx, val = self.bad_enum_rows[0]
            lines.append(
                "  - beta_gamma_source has %d illegal value(s); first: row %d = %r "
                "(allowed: %s)"
                % (
                    len(self.bad_enum_rows),
                    idx,
                    val,
                    ", ".join(sorted(ALLOWED_BETA_GAMMA_SOURCE)),
                )
            )
        return "\n".join(lines)


def _ctau_problem(row, inv):
    denom = _to_float(row.get(inv["denominator"]))
    actual = _to_float(row.get(inv["output"]))
    if not _finite(denom) or denom <= 0 or not _finite(actual):
        return ""
    expected = inv["numerator"] / denom
    scale = max(abs(expected), abs(actual), 1e-300)
    if abs(actual - expected) / scale > inv.get("rel_tol", 1e-4):
        return "%s=%r but hbar_c/%s=%r" % (
            inv["output"],
            actual,
            inv["denominator"],
            expected,
        )
    return ""


def _sum_problem(row, inv):
    total = 0.0
    seen_any = False
    for col in inv["columns"]:
        v = _to_float(row.get(col))
        if _finite(v):
            total += v
            seen_any = True
    if seen_any and total > 1.0 + inv.get("abs_tol", 1e-6):
        return "sum=%r > 1" % total
    return ""


def validate_csv(path, check_invariants=True):
    """Validate a model-point CSV against MODEL_POINT_CONTRACT. Returns a
    ValidationReport; never raises on validation failure."""
    report = ValidationReport(path)
    try:
        fh = open(path, newline="")
    except OSError as exc:
        report.error = "cannot open input: %s" % exc
        return report
    with fh:
        reader = csv.DictReader(fh)
        if reader.fieldnames is None:
            report.error = "empty CSV (no header)"
            return report
        present = set(reader.fieldnames)
        report.missing_columns = [
            c for c in REQUIRED_COLUMNS if c not in present
        ]
        invariants = MODEL_POINT_CONTRACT["invariants"] if check_invariants else []
        counts = {}
        for inv in invariants:
            cols = inv.get("columns", [inv.get("output"), inv.get("denominator")])
            if all(c in present for c in cols if c):
                counts[inv["name"]] = [0, "", inv]
        check_enum = "beta_gamma_source" in present
        for row in reader:
            report.n_rows += 1
            for name, entry in counts.items():
                inv = entry[2]
                problem = (
                    _sum_problem(row, inv)
                    if inv.get("kind") == "sum_le_one"
                    else _ctau_problem(row, inv)
                )
                if problem:
                    entry[0] += 1
                    if not entry[1]:
                        entry[1] = "row %d: %s" % (report.n_rows, problem)
            if check_enum:
                val = (row.get("beta_gamma_source") or "").strip()
                if val and val not in ALLOWED_BETA_GAMMA_SOURCE:
                    report.bad_enum_rows.append((report.n_rows, val))
        report.invariant_violations = [
            (name, e[0], e[1]) for name, e in counts.items() if e[0] > 0
        ]
    return report


def _repo_root():
    # src/llp_recast/data_contract.py -> repo root is three levels up.
    return os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )


def contract_yaml_path():
    return os.path.join(
        _repo_root(), "contracts", MODEL_POINT_CONTRACT["name"] + ".yaml"
    )


def emit(path=None):
    """Write MODEL_POINT_CONTRACT to contracts/<name>.yaml. Returns the path."""
    import yaml

    path = path or contract_yaml_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w") as fh:
        yaml.safe_dump(
            MODEL_POINT_CONTRACT, fh, sort_keys=False, default_flow_style=False
        )
    os.replace(tmp, path)
    return path


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Validate a model-point CSV against the LLP recast input contract."
    )
    parser.add_argument(
        "--emit",
        action="store_true",
        help="write the machine-readable contract to contracts/ and exit",
    )
    parser.add_argument("--input", help="model-point CSV to validate")
    parser.add_argument(
        "--no-invariants",
        action="store_true",
        help="check only column presence + enums, skip numeric invariants",
    )
    args = parser.parse_args(argv)
    if args.emit:
        print("[recast] wrote %s" % emit())
        return 0
    if not args.input:
        parser.error("--input is required unless --emit is given")
    report = validate_csv(args.input, check_invariants=not args.no_invariants)
    print(report.describe(), file=sys.stderr if not report.ok else sys.stdout)
    return 0 if report.ok else 2


if __name__ == "__main__":
    sys.exit(main())
