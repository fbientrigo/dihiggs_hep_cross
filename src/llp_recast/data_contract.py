"""Machine-readable and enforceable canonical model-point handoff contract.

This is the sole active model-point interface entering the LLP recast layer.
The old single-mass/lifetime contract is retained only as an archived
historical artifact; no runtime importer or alias is provided.

## Why this contract exists

``docs/DOWNSTREAM_INTERFACE_GAP_REPORT.md`` (produced against the
``dihiggs`` high-mass H2 2HDM point factory, see that repo's
``docs/HIGH_MASS_H2_CONTRACT.md`` and
``docs/contracts/high_mass_point_schema.yaml``) found that v1 cannot
represent a high-mass point without lossy translation: v1 has a single
``m_scalar_GeV`` (no ``m_A``/``m_Hp``/heavy-state hierarchy at all), a single
``ctau_mm`` (conflating physical and detector-response lifetime), a
five-channel BR list (missing ``BR_cc``, ``BR_tt``, ``BR_gammagamma``,
``BR_Zgamma``, ``BR_hh``), no ``model_variant``, no cascade-state flags, and
no structural distinction between a canonical MadGraph cross section and a
non-canonical scaling estimate. This contract carries all of those semantics
in one named-field interface.

## Design decisions (see docs/contracts/model_point_to_llp_recast_contract.md for
## the full write-up; summarized here so the code and its rationale travel
## together)

1. **``sigma_production_fb`` is never self-certifying.** A ``sigma_source``
   enum column is required; only ``sigma_source == "DIRECT_MADGRAPH_POINT"``
   may be treated as the canonical, physically-trustworthy production value.
   Other values (currently ``G_SQUARED_SCALING_ESTIMATE``,
   ``OTHER_ESTIMATE``) are accepted rows (carrying a non-canonical estimate
   is legitimate), but the validator tracks them separately
   (``ValidationReport.non_canonical_sigma_rows``) and ``describe()`` prints
   an explicit non-canonical note so a caller cannot accidentally treat one
   as canonical just because the column is populated. ``sigma_provenance``
   (free text/dict) carries human context but is never consulted for the
   canonical/non-canonical decision -- only ``sigma_source`` is.

2. **Physical vs. response lifetime are separate columns, never aliased.**
   ``ctau_physical_mm`` must equal ``hbar_c / total_width_GeV`` for every
   row (this is the width-derived, physically meaningful quantity).
   ``ctau_response_mm`` is a distinct column. For
   ``model_variant == PHYSICAL_DECAYS_NO_HEAVY_CASCADES`` (Variant B, which
   never independently tunes a response lifetime) the validator requires
   ``ctau_response_mm == ctau_physical_mm`` exactly (rel_tol 1e-9). For
   ``model_variant == FACTORIZED_G_ONLY`` (Variant A) no equality is
   required in either direction -- the two are legitimately allowed to
   differ (a response study may fix ``ctau_response_mm`` independently) and
   are also *not forbidden* from coincidentally matching, per the mission
   spec's instruction to "not require equality for Variant A rows" (this is
   a deliberate relaxation versus the upstream
   ``high_mass_point_schema.yaml``, which additionally rejects a bit-for-bit
   coincidental match for Variant A; see the "open questions" note in
   ``docs/contracts/model_point_to_llp_recast_contract.md``).

3. **``model_variant`` is a checked enum**: ``FACTORIZED_G_ONLY`` or
   ``PHYSICAL_DECAYS_NO_HEAVY_CASCADES``. Anything else is rejected.

4. **Cascade-open flags are conditionally enforced.** All four
   (``H2_to_AZ_open``, ``H2_to_HpW_open``, ``H2_to_AA_open``,
   ``H2_to_HpHm_open``) are required columns for every row (computed as a
   diagnostic regardless of variant, per ``cascade_contract.yaml``), but are
   only required to be false for ``PHYSICAL_DECAYS_NO_HEAVY_CASCADES`` rows.
   ``FACTORIZED_G_ONLY`` rows may have any value in these columns.

5. **BR invariants cover the full 10-channel list** (``BR_bb, BR_cc, BR_tt,
   BR_tautau, BR_WW, BR_ZZ, BR_gg, BR_gammagamma, BR_Zgamma, BR_hh``), fixing
   v1's 5-channel subset which silently dropped ``BR_cc``, ``BR_tt``,
   ``BR_gammagamma``, ``BR_Zgamma`` and ``BR_hh`` from both the required
   column list and the sum invariant.

6. **Mass hierarchy invariant**: ``m_h_GeV < m_H2_GeV < m_A_GeV`` (strict,
   no tolerance -- these are meant to be well-separated scan coordinates,
   not near-degenerate), ``m_A_GeV == m_Hp_GeV`` (abs_tol 1e-6 GeV) and
   ``Delta_heavy_GeV == m_A_GeV - m_H2_GeV`` (abs_tol 1e-6 GeV).

7. **``production_process`` is a checked value**, currently only
   ``"pp -> H2 H2"``. A future contract revision (v3+) would extend this
   enum for cascade/heavy-state production; this version deliberately does
   not.

8. **Decay/production ownership provenance** (``production_owner``,
   ``decay_owner``, ``response_decay_channel``) records which pipeline stage
   is responsible for the numbers in a row, closing the gap report's
   "Decay ownership" finding (v1 had no way to say "this BR_bb is the
   physical BR" vs. "this sample was forced to decay 100% to bb for a
   response study"). ``decay_owner == "PYTHIA_FORCED_RESPONSE_STUDY"`` is
   only valid on ``FACTORIZED_G_ONLY`` rows (Variant B never forces a decay)
   and requires a non-empty, non-``"NONE"`` ``response_decay_channel``.

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

# --- required columns (mission field list, cross-checked against
# DOWNSTREAM_INTERFACE_GAP_REPORT.md) ---------------------------------------
REQUIRED_COLUMNS = [
    "schema_version",
    "point_id",
    "model_variant",
    "m_h_GeV",
    "m_H2_GeV",
    "m_A_GeV",
    "m_Hp_GeV",
    "Delta_heavy_GeV",
    "g_hH2H2_GeV",
    "total_width_GeV",
    "ctau_physical_mm",
    "ctau_response_mm",
    "lifetime_mode",
    "BR_bb",
    "BR_cc",
    "BR_tt",
    "BR_tautau",
    "BR_WW",
    "BR_ZZ",
    "BR_gg",
    "BR_gammagamma",
    "BR_Zgamma",
    "BR_hh",
    "production_process",
    "production_owner",
    "decay_owner",
    "response_decay_channel",
    "H2_to_AZ_open",
    "H2_to_HpW_open",
    "H2_to_AA_open",
    "H2_to_HpHm_open",
    "theory_status",
    "experimental_status",
    "sigma_production_fb",
    "sigma_source",
    "sigma_provenance",
    "producer_commit",
    "config_hash",
    "input_hash",
]

BR_COLUMNS = [
    "BR_bb",
    "BR_cc",
    "BR_tt",
    "BR_tautau",
    "BR_WW",
    "BR_ZZ",
    "BR_gg",
    "BR_gammagamma",
    "BR_Zgamma",
    "BR_hh",
]

CASCADE_FLAG_COLUMNS = [
    "H2_to_AZ_open",
    "H2_to_HpW_open",
    "H2_to_AA_open",
    "H2_to_HpHm_open",
]

# The canonical contract intentionally has no aliases. Ambiguous historical
# names such as `ctau_mm` are not accepted as runtime substitutes.
ALIASES: dict = {}

SCHEMA_VERSION = "model_point_to_llp_recast.canonical.v1"
VARIANT_A = "FACTORIZED_G_ONLY"
VARIANT_B = "PHYSICAL_DECAYS_NO_HEAVY_CASCADES"
ALLOWED_MODEL_VARIANT = {VARIANT_A, VARIANT_B}

PHYSICAL_LIFETIME_MODE = "PHYSICAL_PREDICTION"
RESPONSE_LIFETIME_MODE = "DETECTOR_RESPONSE_EXPERIMENT"
ALLOWED_LIFETIME_MODE = {PHYSICAL_LIFETIME_MODE, RESPONSE_LIFETIME_MODE}

CANONICAL_SIGMA_SOURCE = "DIRECT_MADGRAPH_POINT"
ALLOWED_SIGMA_SOURCE = {
    CANONICAL_SIGMA_SOURCE,
    "G_SQUARED_SCALING_ESTIMATE",
    "OTHER_ESTIMATE",
}

ALLOWED_PRODUCTION_PROCESS = {"pp -> H2 H2"}

ALLOWED_PRODUCTION_OWNER = {"CANONICAL_EVALUATOR", "DOWNSTREAM_MADGRAPH"}

DECAY_OWNER_RESPONSE_FORCED = "PYTHIA_FORCED_RESPONSE_STUDY"
ALLOWED_DECAY_OWNER = {"CANONICAL_EVALUATOR", DECAY_OWNER_RESPONSE_FORCED}

ALLOWED_THEORY_STATUS = {"PASS", "FAIL", "UNCHECKED"}
ALLOWED_EXPERIMENTAL_STATUS = {"PASS", "FAIL", "UNCHECKED", "NOT_APPLICABLE"}

FALSY_STRINGS = {"false", "0", "no", "off"}
TRUTHY_STRINGS = {"true", "1", "yes", "on"}
REQUIRED_NONEMPTY_COLUMNS = [
    "schema_version",
    "point_id",
    "model_variant",
    "lifetime_mode",
    "production_process",
    "production_owner",
    "decay_owner",
    "response_decay_channel",
    "theory_status",
    "experimental_status",
    "sigma_source",
    "sigma_provenance",
    "producer_commit",
    "config_hash",
    "input_hash",
]
POSITIVE_NUMERIC_COLUMNS = [
    "m_h_GeV",
    "m_H2_GeV",
    "m_A_GeV",
    "m_Hp_GeV",
    "Delta_heavy_GeV",
    "total_width_GeV",
    "ctau_physical_mm",
    "ctau_response_mm",
]
FINITE_NUMERIC_COLUMNS = ["g_hH2H2_GeV"]
NONNEGATIVE_NUMERIC_COLUMNS = ["sigma_production_fb"]

MODEL_POINT_CONTRACT = {
    "name": "model_point_to_llp_recast",
    "produced_by": (
        "the dihiggs high-mass H2 2HDM point factory "
        "(DihiggsPointV2Evaluator, schema dihiggs.high_mass_point.v1) "
        "plus downstream MadGraph/Pythia enrichment"
    ),
    "consumed_by": "src/llp_recast and canonical MadGraph/recast handoff paths",
    "required_columns": REQUIRED_COLUMNS,
    "aliases": ALIASES,
    "invariants": [
        {
            "name": "required semantic fields are populated",
            "kind": "nonempty",
            "columns": list(REQUIRED_NONEMPTY_COLUMNS),
        },
        {
            "name": "schema_version is canonical",
            "kind": "enum",
            "column": "schema_version",
            "allowed": [SCHEMA_VERSION],
            "columns": ["schema_version"],
        },
        {
            "name": "positive masses, width, and lifetimes",
            "kind": "positive_numbers",
            "columns": list(POSITIVE_NUMERIC_COLUMNS),
        },
        {
            "name": "g_hH2H2_GeV is finite",
            "kind": "finite_numbers",
            "columns": list(FINITE_NUMERIC_COLUMNS),
        },
        {
            "name": "sigma_production_fb is finite and non-negative",
            "kind": "nonnegative_numbers",
            "columns": list(NONNEGATIVE_NUMERIC_COLUMNS),
        },
        {
            "name": "branching fractions are in [0, 1]",
            "kind": "fraction_range",
            "columns": list(BR_COLUMNS),
        },
        {
            "name": "cascade-state flags are explicit booleans",
            "kind": "boolean_flags",
            "columns": list(CASCADE_FLAG_COLUMNS),
        },
        # ctau_physical_mm is the width-derived, physically meaningful
        # lifetime; must equal hbar_c / total_width_GeV for every row,
        # regardless of variant. ctau_response_mm is NOT covered by this
        # invariant (see the response_ctau_equals_physical_for_variant_b
        # invariant below for the narrower, variant-B-only check).
        {
            "name": "ctau_physical_mm == hbar_c / total_width_GeV",
            "kind": "ctau_ratio",
            "output": "ctau_physical_mm",
            "numerator": HBAR_C_GEV_MM,
            "denominator": "total_width_GeV",
            "columns": ["ctau_physical_mm", "total_width_GeV"],
            "rel_tol": 1e-6,
        },
        # Full 10-channel BR list.
        {
            "name": "sum(10-channel BR) <= 1",
            "kind": "sum_le_one",
            "columns": list(BR_COLUMNS),
            "abs_tol": 1e-6,
        },
        {
            "name": "model_variant in {FACTORIZED_G_ONLY, PHYSICAL_DECAYS_NO_HEAVY_CASCADES}",
            "kind": "enum",
            "column": "model_variant",
            "allowed": sorted(ALLOWED_MODEL_VARIANT),
            "columns": ["model_variant"],
        },
        {
            "name": "lifetime_mode in {PHYSICAL_PREDICTION, DETECTOR_RESPONSE_EXPERIMENT}",
            "kind": "enum",
            "column": "lifetime_mode",
            "allowed": sorted(ALLOWED_LIFETIME_MODE),
            "columns": ["lifetime_mode"],
        },
        {
            "name": "sigma_source in allowed enum",
            "kind": "enum",
            "column": "sigma_source",
            "allowed": sorted(ALLOWED_SIGMA_SOURCE),
            "columns": ["sigma_source"],
        },
        {
            "name": "production_process == 'pp -> H2 H2' (only value this contract version accepts)",
            "kind": "enum",
            "column": "production_process",
            "allowed": sorted(ALLOWED_PRODUCTION_PROCESS),
            "columns": ["production_process"],
        },
        {
            "name": "production_owner in allowed enum",
            "kind": "enum",
            "column": "production_owner",
            "allowed": sorted(ALLOWED_PRODUCTION_OWNER),
            "columns": ["production_owner"],
        },
        {
            "name": "decay_owner in allowed enum",
            "kind": "enum",
            "column": "decay_owner",
            "allowed": sorted(ALLOWED_DECAY_OWNER),
            "columns": ["decay_owner"],
        },
        {
            "name": "theory_status in allowed enum",
            "kind": "enum",
            "column": "theory_status",
            "allowed": sorted(ALLOWED_THEORY_STATUS),
            "columns": ["theory_status"],
        },
        {
            "name": "experimental_status in allowed enum",
            "kind": "enum",
            "column": "experimental_status",
            "allowed": sorted(ALLOWED_EXPERIMENTAL_STATUS),
            "columns": ["experimental_status"],
        },
        # mA = mHp, mh < mH2 < mA, Delta_heavy = mA - mH2.
        {
            "name": "hierarchy: m_h_GeV < m_H2_GeV < m_A_GeV == m_Hp_GeV; Delta_heavy_GeV == m_A_GeV - m_H2_GeV",
            "kind": "hierarchy",
            "columns": ["m_h_GeV", "m_H2_GeV", "m_A_GeV", "m_Hp_GeV", "Delta_heavy_GeV"],
            "mass_equal_abs_tol": 1e-6,
            "delta_abs_tol": 1e-6,
        },
        # Cascade-open flags must be false for PHYSICAL_DECAYS_NO_HEAVY_CASCADES;
        # unrestricted (diagnostic only) for FACTORIZED_G_ONLY.
        {
            "name": "cascade-open flags false for PHYSICAL_DECAYS_NO_HEAVY_CASCADES",
            "kind": "cascade_forbidden_for_variant_b",
            "columns": ["model_variant"] + CASCADE_FLAG_COLUMNS,
        },
        # ctau_response_mm must exactly equal ctau_physical_mm for Variant B;
        # no constraint either way for Variant A.
        {
            "name": "lifetime mode and response lifetime are semantically consistent",
            "kind": "lifetime_mode_consistency",
            "columns": ["model_variant", "lifetime_mode", "ctau_physical_mm", "ctau_response_mm"],
            "rel_tol": 1e-9,
        },
        # decay_owner=PYTHIA_FORCED_RESPONSE_STUDY only valid for Variant A,
        # and only with a real forced channel recorded.
        {
            "name": "decay_owner=PYTHIA_FORCED_RESPONSE_STUDY only valid for FACTORIZED_G_ONLY with a named response_decay_channel",
            "kind": "decay_owner_consistency",
            "columns": ["decay_owner", "model_variant", "response_decay_channel"],
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


def _is_falsy(raw):
    return (raw or "").strip().lower() in FALSY_STRINGS


def is_canonical_sigma_source(value):
    """True iff `value` is the one sigma_source value this contract treats
    as a trustworthy, physically canonical production cross section."""
    return (value or "").strip() == CANONICAL_SIGMA_SOURCE


class ValidationReport:
    def __init__(self, path):
        self.path = path
        self.contract_name = MODEL_POINT_CONTRACT["name"]
        self.missing_columns = []
        self.invariant_violations = []  # (name, count, first_example)
        self.non_canonical_sigma_rows = []  # row indices with sigma_source != canonical
        self.n_rows = 0
        self.error = ""

    @property
    def ok(self):
        return not (self.error or self.missing_columns or self.invariant_violations)

    def describe(self):
        if self.ok:
            lines = [
                "[recast][OK] %s satisfies %s (%d rows)"
                % (self.path, self.contract_name, self.n_rows)
            ]
        else:
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
        if self.non_canonical_sigma_rows:
            lines.append(
                "  - [info] %d row(s) carry sigma_source != %r (non-canonical "
                "production estimate); sigma_production_fb in these rows must "
                "NOT be treated as the canonical physical cross section "
                "(first row: %d)"
                % (
                    len(self.non_canonical_sigma_rows),
                    CANONICAL_SIGMA_SOURCE,
                    self.non_canonical_sigma_rows[0],
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


def _nonempty_problem(row, inv):
    missing = [col for col in inv["columns"] if not (row.get(col) or "").strip()]
    return "missing value(s): " + ", ".join(missing) if missing else ""


def _number_range_problem(row, inv, *, minimum, maximum=None):
    for col in inv["columns"]:
        value = _to_float(row.get(col))
        if not _finite(value) or value < minimum or (maximum is not None and value > maximum):
            bound = f"[{minimum}, {maximum}]" if maximum is not None else f"> {minimum}"
            return f"{col}={row.get(col)!r} is not a finite value in {bound}"
    return ""


def _positive_numbers_problem(row, inv):
    for col in inv["columns"]:
        value = _to_float(row.get(col))
        if not _finite(value) or value <= 0.0:
            return f"{col}={row.get(col)!r} is not a finite positive value"
    return ""


def _finite_numbers_problem(row, inv):
    return _number_range_problem(row, inv, minimum=float("-inf"))


def _nonnegative_numbers_problem(row, inv):
    return _number_range_problem(row, inv, minimum=0.0)


def _fraction_range_problem(row, inv):
    return _number_range_problem(row, inv, minimum=0.0, maximum=1.0)


def _boolean_flags_problem(row, inv):
    for col in inv["columns"]:
        value = (row.get(col) or "").strip().lower()
        if value not in FALSY_STRINGS | TRUTHY_STRINGS:
            return f"{col}={row.get(col)!r} is not an explicit boolean"
    return ""


def _enum_problem(row, inv):
    value = (row.get(inv["column"]) or "").strip()
    if not value:
        return ""
    if value not in inv["allowed"]:
        return "%s=%r not in allowed %s" % (
            inv["column"],
            value,
            ", ".join(inv["allowed"]),
        )
    return ""


def _hierarchy_problem(row, inv):
    m_h = _to_float(row.get("m_h_GeV"))
    m_H2 = _to_float(row.get("m_H2_GeV"))
    m_A = _to_float(row.get("m_A_GeV"))
    m_Hp = _to_float(row.get("m_Hp_GeV"))
    delta = _to_float(row.get("Delta_heavy_GeV"))
    if not all(_finite(x) for x in (m_h, m_H2, m_A, m_Hp, delta)):
        return ""
    if not (m_h < m_H2 < m_A):
        return "hierarchy violated: m_h_GeV=%r, m_H2_GeV=%r, m_A_GeV=%r (require m_h < m_H2 < m_A)" % (
            m_h,
            m_H2,
            m_A,
        )
    if abs(m_A - m_Hp) > inv.get("mass_equal_abs_tol", 1e-6):
        return "m_A_GeV=%r != m_Hp_GeV=%r" % (m_A, m_Hp)
    expected_delta = m_A - m_H2
    if abs(delta - expected_delta) > inv.get("delta_abs_tol", 1e-6):
        return "Delta_heavy_GeV=%r but m_A_GeV - m_H2_GeV=%r" % (delta, expected_delta)
    return ""


def _cascade_problem(row, inv):
    variant = (row.get("model_variant") or "").strip()
    if variant != VARIANT_B:
        return ""
    for col in CASCADE_FLAG_COLUMNS:
        raw = row.get(col)
        if not _is_falsy(raw):
            return "%s=%r must be false/False/0 for %s" % (col, raw, VARIANT_B)
    return ""


def _lifetime_mode_problem(row, inv):
    variant = (row.get("model_variant") or "").strip()
    mode = (row.get("lifetime_mode") or "").strip()
    phys = _to_float(row.get("ctau_physical_mm"))
    resp = _to_float(row.get("ctau_response_mm"))
    if not _finite(phys) or not _finite(resp):
        return ""
    if variant == VARIANT_B and mode != PHYSICAL_LIFETIME_MODE:
        return f"{VARIANT_B} requires lifetime_mode={PHYSICAL_LIFETIME_MODE!r}"
    if mode == RESPONSE_LIFETIME_MODE and variant != VARIANT_A:
        return f"{RESPONSE_LIFETIME_MODE} is only valid for {VARIANT_A}"
    if mode != PHYSICAL_LIFETIME_MODE:
        return ""
    scale = max(abs(phys), abs(resp), 1e-300)
    if abs(phys - resp) / scale > inv.get("rel_tol", 1e-9):
        return "ctau_response_mm=%r != ctau_physical_mm=%r for explicit physical lifetime mode" % (
            resp,
            phys,
        )
    return ""


def _decay_owner_problem(row, inv):
    decay_owner = (row.get("decay_owner") or "").strip()
    if decay_owner != DECAY_OWNER_RESPONSE_FORCED:
        return ""
    variant = (row.get("model_variant") or "").strip()
    channel = (row.get("response_decay_channel") or "").strip()
    if variant != VARIANT_A:
        return "decay_owner=%s only valid for %s rows (got model_variant=%r)" % (
            DECAY_OWNER_RESPONSE_FORCED,
            VARIANT_A,
            variant,
        )
    if not channel or channel.upper() == "NONE":
        return "decay_owner=%s requires a non-empty response_decay_channel" % (
            DECAY_OWNER_RESPONSE_FORCED
        )
    return ""


_KIND_HANDLERS = {
    "nonempty": _nonempty_problem,
    "positive_numbers": _positive_numbers_problem,
    "finite_numbers": _finite_numbers_problem,
    "nonnegative_numbers": _nonnegative_numbers_problem,
    "fraction_range": _fraction_range_problem,
    "boolean_flags": _boolean_flags_problem,
    "ctau_ratio": _ctau_problem,
    "sum_le_one": _sum_problem,
    "enum": _enum_problem,
    "hierarchy": _hierarchy_problem,
    "cascade_forbidden_for_variant_b": _cascade_problem,
    "lifetime_mode_consistency": _lifetime_mode_problem,
    "decay_owner_consistency": _decay_owner_problem,
}


def validate_csv(path, check_invariants=True):
    """Validate a model-point CSV against MODEL_POINT_CONTRACT. Returns
    a ValidationReport; never raises on validation failure."""
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
        report.missing_columns = [c for c in REQUIRED_COLUMNS if c not in present]
        invariants = MODEL_POINT_CONTRACT["invariants"] if check_invariants else []
        counts = {}
        for inv in invariants:
            cols = inv.get("columns", [])
            if all(c in present for c in cols if c):
                counts[inv["name"]] = [0, "", inv]
        check_sigma_source = "sigma_source" in present
        for row in reader:
            report.n_rows += 1
            for name, entry in counts.items():
                inv = entry[2]
                handler = _KIND_HANDLERS.get(inv.get("kind"))
                problem = handler(row, inv) if handler else ""
                if problem:
                    entry[0] += 1
                    if not entry[1]:
                        entry[1] = "row %d: %s" % (report.n_rows, problem)
            if check_sigma_source:
                source = (row.get("sigma_source") or "").strip()
                if source and source in ALLOWED_SIGMA_SOURCE and not is_canonical_sigma_source(source):
                    report.non_canonical_sigma_rows.append(report.n_rows)
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
        description="Validate a model-point CSV against the canonical LLP recast input contract."
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
        help="check only column presence, skip semantic invariants",
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
