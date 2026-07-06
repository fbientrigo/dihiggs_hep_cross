#!/usr/bin/env bash
set -euo pipefail

# Run from ~/code/dihiggs_jets
if [[ ! -d "data/hepdata/atlas_dvjets_139fb/yaml_raw" ]]; then
  echo "[ERROR] Expected data/hepdata/atlas_dvjets_139fb/yaml_raw" >&2
  echo "Run from ~/code/dihiggs_jets after extracting the HEPData YAML bundle." >&2
  exit 2
fi

mkdir -p src/llp_recast scripts tests docs/sdd docs/contracts docs/recast outputs agents

touch src/llp_recast/__init__.py

cat > requirements.txt <<'EOF'
PyYAML>=6.0
pandas>=2.0
pytest>=8.0
EOF

cat > pytest.ini <<'EOF'
[pytest]
pythonpath = src
testpaths = tests
addopts = -q
EOF

cat > pyproject.toml <<'EOF'
[project]
name = "dihiggs-jets-llp-recast"
version = "0.1.0"
description = "Minimal ATLAS DV+jets HEPData recast scaffold for LLP scalar studies"
requires-python = ">=3.10"
dependencies = ["PyYAML>=6.0", "pandas>=2.0"]

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
addopts = "-q"
EOF

cat > src/llp_recast/constants.py <<'EOF'
"""Physics and analysis constants for the minimal LLP recast scaffold."""

HBAR_C_GEV_MM = 1.973269804e-13  # c*tau[mm] = hbar*c / Gamma[GeV]
ATLAS_DVJETS_LUMI_FB = 139.0
ATLAS_DVJETS_SQRTS_TEV = 13.0
ID_R_MIN_MM = 4.0
ID_R_MAX_MM = 300.0
ID_Z_MAX_MM = 300.0
EOF

cat > src/llp_recast/recast_math.py <<'EOF'
from __future__ import annotations

import math
from dataclasses import dataclass

from .constants import HBAR_C_GEV_MM


def ctau_mm_from_width_gev(total_width_gev: float) -> float:
    """Convert total width in GeV to c*tau in mm."""
    if total_width_gev <= 0 or not math.isfinite(total_width_gev):
        return math.inf
    return HBAR_C_GEV_MM / total_width_gev


def width_gev_from_ctau_mm(ctau_mm: float) -> float:
    """Convert c*tau in mm to total width in GeV."""
    if ctau_mm <= 0 or not math.isfinite(ctau_mm):
        return math.inf
    return HBAR_C_GEV_MM / ctau_mm


def decay_probability_between_radii(lab_decay_length_mm: float, r_min_mm: float, r_max_mm: float) -> float:
    """Probability for an LLP with exponential lab decay length to decay between two radii.

    This is a geometric proxy. It ignores eta/z acceptance and detector/reconstruction effects.
    """
    if lab_decay_length_mm <= 0 or not math.isfinite(lab_decay_length_mm):
        return 0.0
    if r_max_mm <= r_min_mm:
        return 0.0
    p = math.exp(-r_min_mm / lab_decay_length_mm) - math.exp(-r_max_mm / lab_decay_length_mm)
    return max(0.0, min(1.0, p))


def event_probability_at_least_one(single_llp_probability: float, n_llp: int = 2) -> float:
    """Event probability that at least one of n LLPs satisfies a condition."""
    p = max(0.0, min(1.0, single_llp_probability))
    if n_llp <= 0:
        return 0.0
    return 1.0 - (1.0 - p) ** n_llp


def expected_yield(lumi_fb: float, xsec_fb: float, br_factor: float, acceptance_efficiency: float) -> float:
    """Expected event yield for cross section in fb and luminosity in fb^-1."""
    vals = [lumi_fb, xsec_fb, br_factor, acceptance_efficiency]
    if any((v < 0 or not math.isfinite(v)) for v in vals):
        return math.nan
    return lumi_fb * xsec_fb * br_factor * acceptance_efficiency


@dataclass(frozen=True)
class ToyScalarPoint:
    mass_gev: float
    ctau_mm: float
    beta_gamma: float
    xsec_fb: float
    br_had: float
    eps_reco_proxy: float

    @property
    def total_width_gev(self) -> float:
        return width_gev_from_ctau_mm(self.ctau_mm)

    @property
    def lab_decay_length_mm(self) -> float:
        return self.beta_gamma * self.ctau_mm
EOF

cat > src/llp_recast/hepdata_yaml.py <<'EOF'
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class TableSummary:
    path: str
    filename: str
    group: str
    dependent_headers: str
    independent_headers: str
    qualifiers: str
    n_dependent: int
    n_independent: int
    n_values_first_dep: int


def classify_table_name(name: str) -> str:
    low = name.lower()
    if "yield" in low:
        return "yields"
    if "excl_xsec" in low or "xsec" in low:
        return "cross_section_limits"
    if "excl" in low:
        return "exclusion_limits"
    if "acceptance" in low:
        return "acceptance"
    if "event_efficiency" in low:
        return "event_efficiency"
    if "vertex_efficiency" in low:
        return "vertex_efficiency"
    if "cutflow" in low:
        return "cutflow"
    return "other"


def load_yaml(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data if isinstance(data, dict) else {}


def _header_name(obj: Any) -> str:
    if isinstance(obj, dict):
        header = obj.get("header", {})
        if isinstance(header, dict):
            name = header.get("name", "")
            units = header.get("units")
            if units:
                return f"{name} [{units}]"
            return str(name)
    return ""


def _qualifiers(dep: Any) -> str:
    if not isinstance(dep, dict):
        return ""
    quals = dep.get("qualifiers", [])
    parts: list[str] = []
    if isinstance(quals, list):
        for q in quals:
            if isinstance(q, dict):
                name = q.get("name", "")
                value = q.get("value", "")
                units = q.get("units")
                if units:
                    parts.append(f"{name}={value} {units}")
                else:
                    parts.append(f"{name}={value}")
    return "; ".join(parts)


def summarize_table(path: str | Path, root: str | Path | None = None) -> TableSummary:
    p = Path(path)
    data = load_yaml(p)
    deps = data.get("dependent_variables", [])
    indeps = data.get("independent_variables", [])
    if not isinstance(deps, list):
        deps = []
    if not isinstance(indeps, list):
        indeps = []

    dep_headers = [_header_name(d) for d in deps]
    indep_headers = [_header_name(d) for d in indeps]
    qualifiers = [_qualifiers(d) for d in deps[:3]]
    n_values_first = 0
    if deps and isinstance(deps[0], dict) and isinstance(deps[0].get("values"), list):
        n_values_first = len(deps[0]["values"])

    rel = str(p.relative_to(root)) if root is not None else str(p)
    return TableSummary(
        path=rel,
        filename=p.name,
        group=classify_table_name(p.name),
        dependent_headers=" | ".join(h for h in dep_headers if h),
        independent_headers=" | ".join(h for h in indep_headers if h),
        qualifiers=" || ".join(q for q in qualifiers if q),
        n_dependent=len(deps),
        n_independent=len(indeps),
        n_values_first_dep=n_values_first,
    )


def find_yaml_tables(root: str | Path) -> list[Path]:
    r = Path(root)
    return sorted(list(r.rglob("*.yaml")) + list(r.rglob("*.yml")))


def safe_slug(text: str) -> str:
    text = re.sub(r"[^A-Za-z0-9_.=-]+", "_", text.strip())
    return re.sub(r"_+", "_", text).strip("_") or "table"
EOF

cat > scripts/01_hepdata_inventory.py <<'EOF'
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from collections import Counter
from dataclasses import asdict
from pathlib import Path

from llp_recast.hepdata_yaml import find_yaml_tables, summarize_table


def main() -> int:
    ap = argparse.ArgumentParser(description="Inventory local ATLAS DV+jets HEPData YAML tables")
    ap.add_argument("--yaml-root", default="data/hepdata/atlas_dvjets_139fb/yaml_raw")
    ap.add_argument("--outdir", default="outputs/hepdata_inventory")
    args = ap.parse_args()

    root = Path(args.yaml_root)
    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    tables = find_yaml_tables(root)
    summaries = [summarize_table(p, root=root) for p in tables]
    counts = Counter(s.group for s in summaries)

    csv_path = outdir / "atlas_dvjets_table_inventory.csv"
    with csv_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(asdict(summaries[0]).keys()) if summaries else ["path"])
        writer.writeheader()
        for s in summaries:
            writer.writerow(asdict(s))

    md_path = outdir / "atlas_dvjets_table_inventory.md"
    lines = []
    lines.append("# ATLAS DV+jets HEPData inventory\n")
    lines.append(f"YAML root: `{root}`\n")
    lines.append(f"Total YAML files: **{len(tables)}**\n")
    lines.append("## Counts by group\n")
    for group, n in sorted(counts.items()):
        lines.append(f"- `{group}`: {n}")
    lines.append("\n## Candidate tables for first recast\n")
    for s in summaries:
        if s.group in {"yields", "cross_section_limits", "acceptance", "event_efficiency", "vertex_efficiency", "cutflow"}:
            lines.append(f"- `{s.path}` — {s.group}")
            if s.dependent_headers:
                lines.append(f"  - dependent: {s.dependent_headers[:220]}")
            if s.independent_headers:
                lines.append(f"  - independent: {s.independent_headers[:220]}")
    md_path.write_text("\n".join(lines), encoding="utf-8")

    print(f"[OK] wrote {csv_path}")
    print(f"[OK] wrote {md_path}")
    print("[COUNTS]")
    for group, n in sorted(counts.items()):
        print(f"  {group:24s} {n}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
EOF
chmod +x scripts/01_hepdata_inventory.py

cat > scripts/02_toy_s_recast.py <<'EOF'
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from llp_recast.constants import ATLAS_DVJETS_LUMI_FB, ID_R_MIN_MM, ID_R_MAX_MM
from llp_recast.recast_math import (
    ToyScalarPoint,
    ctau_mm_from_width_gev,
    decay_probability_between_radii,
    event_probability_at_least_one,
    expected_yield,
)


def parse_csv_floats(text: str) -> list[float]:
    return [float(x.strip()) for x in text.split(",") if x.strip()]


def main() -> int:
    ap = argparse.ArgumentParser(description="Toy S->hadronic LLP recast proxy for ATLAS DV+jets")
    ap.add_argument("--masses", default="100,170,250", help="Comma-separated scalar masses in GeV")
    ap.add_argument("--ctau-mm", default="10,30,100,300,1000", help="Comma-separated proper c*tau values in mm")
    ap.add_argument("--beta-gamma", type=float, default=1.0)
    ap.add_argument("--xsec-fb", type=float, default=1.0, help="Toy production cross section in fb")
    ap.add_argument("--br-had", type=float, default=0.8, help="Toy hadronic BR per LLP")
    ap.add_argument("--eps-reco-proxy", type=float, default=0.10, help="Explicit placeholder for DV/event reconstruction efficiency")
    ap.add_argument("--out", default="outputs/toy_s_recast/toy_s_recast_summary.csv")
    args = ap.parse_args()

    masses = parse_csv_floats(args.masses)
    ctaus = parse_csv_floats(args.ctau_mm)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for m in masses:
        for ctau in ctaus:
            p = ToyScalarPoint(
                mass_gev=m,
                ctau_mm=ctau,
                beta_gamma=args.beta_gamma,
                xsec_fb=args.xsec_fb,
                br_had=args.br_had,
                eps_reco_proxy=args.eps_reco_proxy,
            )
            p_single_id = decay_probability_between_radii(p.lab_decay_length_mm, ID_R_MIN_MM, ID_R_MAX_MM)
            p_event_id = event_probability_at_least_one(p_single_id, n_llp=2)
            br_factor = p.br_had ** 2
            aeff_proxy = p_event_id * p.eps_reco_proxy
            nsig = expected_yield(ATLAS_DVJETS_LUMI_FB, p.xsec_fb, br_factor, aeff_proxy)
            rows.append({
                "mass_gev": m,
                "ctau_mm": ctau,
                "total_width_gev_from_ctau": p.total_width_gev,
                "beta_gamma": p.beta_gamma,
                "lab_decay_length_mm": p.lab_decay_length_mm,
                "xsec_fb_toy": p.xsec_fb,
                "br_had_per_llp": p.br_had,
                "br_factor_pair_had": br_factor,
                "p_single_decay_ID_4_300mm": p_single_id,
                "p_event_at_least_one_ID": p_event_id,
                "eps_reco_proxy_explicit_placeholder": p.eps_reco_proxy,
                "aeff_proxy": aeff_proxy,
                "nsig_139fb_proxy": nsig,
                "quality_flag": "GEOMETRY_PLUS_PLACEHOLDER_EFF_NOT_EXCLUSION",
            })

    with out.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] wrote {out}")
    print("[NOTE] This is a proxy only. It is not an ATLAS exclusion.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
EOF
chmod +x scripts/02_toy_s_recast.py

cat > tests/test_recast_math.py <<'EOF'
import math

from llp_recast.constants import HBAR_C_GEV_MM
from llp_recast.recast_math import (
    ctau_mm_from_width_gev,
    decay_probability_between_radii,
    event_probability_at_least_one,
    expected_yield,
)


def test_ctau_width_roundtrip_for_one_mm():
    width = HBAR_C_GEV_MM / 1.0
    assert math.isclose(ctau_mm_from_width_gev(width), 1.0, rel_tol=1e-12)


def test_decay_probability_between_radii_is_bounded():
    p = decay_probability_between_radii(100.0, 4.0, 300.0)
    assert 0.0 <= p <= 1.0
    assert p > 0.0


def test_event_probability_at_least_one_two_llps():
    assert math.isclose(event_probability_at_least_one(0.5, 2), 0.75)


def test_expected_yield_units_fb():
    assert math.isclose(expected_yield(139.0, 1.0, 1.0, 0.1), 13.9)
EOF

cat > tests/test_hepdata_yaml.py <<'EOF'
from llp_recast.hepdata_yaml import classify_table_name


def test_classify_core_tables():
    assert classify_table_name("yields_trackless_sr_observed.yaml") == "yields"
    assert classify_table_name("excl_xsec_ewk.yaml") == "cross_section_limits"
    assert classify_table_name("event_efficiency_trackless_r_1150_mm.yaml") == "event_efficiency"
    assert classify_table_name("vertex_efficiency_r_180_300_mm.yaml") == "vertex_efficiency"
    assert classify_table_name("cutflow_trackless_ewk.yaml") == "cutflow"
EOF

cat > docs/sdd/llp_s_recast_sdd.md <<'EOF'
# SDD — Minimal LLP scalar recast against ATLAS DV+jets HEPData

## Goal

Build a small, auditable analysis layer that connects a scalar-like LLP signal to public ATLAS DV+jets HEPData products.

This is not a full ATLAS reproduction. It is a staged phenomenological recast scaffold.

## Context

The working physics case is a neutral scalar-like LLP `S`, motivated by the paper workflow `pp -> h* -> S S`, but intended to be reusable for our own BSM scalar-pair topology generated through FeynRules/UFO/MadGraph/Pythia.

## Inputs

1. Local HEPData YAML bundle:

```text
data/hepdata/atlas_dvjets_139fb/yaml_raw/HEPData-ins2628398-v2-yaml/
```

2. Future signal MC:

```text
FeynRules -> UFO -> MadGraph5_aMC@NLO -> Pythia -> truth-level recast
```

3. Current or future 2HDM scan outputs with at least:

```text
mass, total_width, partial_widths, branching ratios, production cross section or proxy
```

## Non-goals

- Do not claim an official ATLAS exclusion.
- Do not emulate LRT or material maps beyond public efficiency proxies.
- Do not treat prompt Delphes output as a valid displaced-object reconstruction.
- Do not identify the paper's effective `lambda` with `lambda6` or `lambda7` without a model matching.

## Requirements

### R1 — HEPData inventory

The analysis must discover and classify local YAML tables into:

- yields;
- exclusion limits;
- cross-section limits;
- acceptance;
- event efficiency;
- vertex efficiency;
- cutflow.

### R2 — Toy scalar proxy

The analysis must support a toy scalar `S` benchmark grid:

```text
mS = 100, 170, 250 GeV
ctau = configurable
sigma = configurable
BR_had = configurable
```

### R3 — Geometry proxy

For each benchmark, compute:

```text
P(4 mm < R < 300 mm)
P(at least one of two LLPs decays in ID)
```

### R4 — Yield proxy

For each benchmark, compute:

```text
Nsig = L * sigma * BR_factor * Aepsilon_proxy
```

with explicit quality flags.

### R5 — Future MC interface

A future MadGraph/Pythia stage must provide:

```text
mS, beta_gamma distribution, LLP decay position, truth jets, charged multiplicity proxy, DV mass proxy
```

## Acceptance criteria

- `pytest` passes.
- `scripts/01_hepdata_inventory.py` writes CSV and Markdown inventory.
- `scripts/02_toy_s_recast.py` writes a toy benchmark summary CSV.
- Outputs explicitly state they are proxies, not exclusions.
EOF

cat > docs/contracts/recast_output_schema.md <<'EOF'
# Contract — minimal recast output schema

Required columns for a first scalar LLP recast table:

| Column | Meaning | Status |
|---|---|---|
| `mass_gev` | LLP scalar mass | required |
| `total_width_gev` | total decay width | required or derived |
| `ctau_mm` | proper decay length | required or derived |
| `beta_gamma` | boost proxy or event-level value | proxy until MC |
| `lab_decay_length_mm` | beta_gamma * ctau | derived |
| `br_bb` | BR to bb | optional |
| `br_gg` | BR to gg | optional |
| `br_WW` | BR to WW | optional |
| `br_ZZ` | BR to ZZ | optional |
| `br_hadronic_proxy` | hadronic decay proxy | required |
| `p_single_decay_ID_4_300mm` | one-LLP ID decay probability | derived |
| `p_event_at_least_one_ID` | event-level ID probability | derived |
| `eps_vertex_proxy` | public/table efficiency or placeholder | required with quality flag |
| `eps_event_proxy` | public/table efficiency or placeholder | required with quality flag |
| `aeff_proxy` | acceptance times efficiency proxy | derived |
| `xsec_fb` | signal production cross section | required for yield |
| `nsig_139fb_proxy` | expected signal yield | derived |
| `quality_flag` | e.g. `TRUTH_PROXY`, `TABLE_INTERPOLATED`, `FULL_MC_REQUIRED` | required |
EOF

cat > docs/recast/presentation_minimum_points.md <<'EOF'
# Minimum points for the meeting

## 1. Dataset status

The ATLAS DV+jets HEPData YAML bundle is now local. It contains yields, cross-section limits, acceptance, event efficiencies, vertex efficiencies and cutflows.

## 2. Scientific interpretation

This enables a phenomenological recast path, not a full ATLAS analysis reproduction. Signal generation remains our responsibility through FeynRules/UFO/MadGraph/Pythia.

## 3. Immediate next analysis

Build two notebooks/scripts:

1. HEPData inventory and table extraction.
2. Toy `S` scalar truth-level proxy with ID decay probability and expected yield.

Decision requested: use Trackless SR / ATLAS DV+jets as the first validation channel.
EOF

cat > agents/antigravity_or_codex_prompt.md <<'EOF'
You are a senior HEP phenomenology + research software engineer working inside a local folder, not necessarily a git repo.

Goal:
Build a minimal but useful SDD/TDD analysis scaffold for a scalar-like LLP recast using local ATLAS DV+jets HEPData YAML files.

Context:
- The local folder is `~/code/dihiggs_jets`.
- The official HEPData YAML bundle is already extracted under:
  `data/hepdata/atlas_dvjets_139fb/yaml_raw/HEPData-ins2628398-v2-yaml/`
- Automated download was blocked by Cloudflare, so do not download from HEPData.
- Use only the local YAML files.
- This is not a full ATLAS reproduction and must not claim official exclusions.
- The physics target is inspired by `pp -> h* -> S S`, where S is a long-lived neutral scalar, but the scaffold must be reusable for our own UFO/MadGraph/Pythia signal.

Engineering requirements:
- Follow SDD/TDD.
- Keep modules small.
- Keep outputs explicit about proxy quality.
- Use Python, PyYAML, pandas, pytest.
- Do not add heavy frameworks.

Immediate tasks:
1. Run `pytest` and fix failures.
2. Run `scripts/01_hepdata_inventory.py` and inspect outputs.
3. Run `scripts/02_toy_s_recast.py` and inspect outputs.
4. Improve the HEPData parser enough to extract selected tables into tidy CSV:
   - `yields_trackless_sr_observed.yaml`
   - `yields_trackless_sr_expected_ewk.yaml`
   - `excl_xsec_ewk.yaml`
   - `cutflow_trackless_ewk.yaml`
   - `acceptance_trackless_ewk.yaml`
   - `event_efficiency_trackless_r_1150_mm.yaml`
   - `vertex_efficiency_r_180_300_mm.yaml`
5. Add tests for the tidy-table extractor.
6. Create a short `outputs/recast_readiness_report.md` summarizing what can be used now and what still requires MadGraph/Pythia.

Scientific constraints:
- Separate BR, geometric acceptance, reconstruction efficiency and event efficiency.
- Do not confuse the paper's effective hSS coupling lambda with 2HDM lambda6/lambda7.
- Use `ctau_mm = 1.973269804e-13 / Gamma_GeV`.
- For the first proxy, use `P(4 mm < R < 300 mm) = exp(-4/L) - exp(-300/L)`, where `L = beta_gamma * ctau_mm`.
- Use `Nsig = L_fb * sigma_fb * BR_factor * Aepsilon`.

Definition of done:
- Tests pass.
- Inventory output exists.
- Toy S recast CSV exists.
- Report states that this is a proxy, not an official exclusion.
- The next step toward accuracy is clearly listed as UFO/MadGraph/Pythia signal generation and validation against paper benchmarks.
EOF

cat > Makefile <<'EOF'
.PHONY: test inventory toy all

test:
	pytest

inventory:
	python3 scripts/01_hepdata_inventory.py

toy:
	python3 scripts/02_toy_s_recast.py

all: test inventory toy
EOF

echo "[OK] LLP recast scaffold created."
echo "Next:"
echo "  python3 -m venv .venv"
echo "  source .venv/bin/activate"
echo "  pip install -r requirements.txt"
echo "  make all"
