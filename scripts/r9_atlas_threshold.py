#!/usr/bin/env python3
"""R9: map the recast Trackless region to the official ATLAS DV+jets region.

Target publication: ATLAS, JHEP 06 (2023) 200, arXiv:2301.13866,
HEPData DOI 10.17182/hepdata.137762 (INSPIRE record 2628398).

Two separate questions are answered and kept separate:

1. **Region mapping.**  Does the R8 Trackless cutflow correspond to the
   published Trackless signal region?  This is decided from the cutflow stage
   labels in the validated R8 artifact and the HEPData table names.

2. **Numerical threshold.**  Is there an unambiguous model-independent 95% CL
   limit (S95, or a visible-cross-section limit) for that region that this
   session can read from an official source?  This is decided by enumerating
   the local HEPData record; nothing is taken from memory.

If (2) fails, ``status`` is ``OFFICIAL_THRESHOLD_MAPPING_UNRESOLVED`` and the
1/3/5/10-event thresholds stay illustrative.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = REPO_ROOT.parent
HEPDATA_DIR = (
    REPO_ROOT / "data" / "hepdata" / "atlas_dvjets_139fb" / "yaml_raw"
    / "HEPData-ins2628398-v2-yaml"
)
R8_CUTFLOW = (
    WORKSPACE / "dihiggs_llp_recast" / "results" / "r8_h2_model_derived_4b" / "cutflow_combined.csv"
)

MODEL_INDEPENDENT_PATTERN = re.compile(
    r"model[\s_-]?independent|upper[\s_-]?limit|visible[\s_-]?cross|fiducial[\s_-]?cross|s95|\bS_?95\b",
    re.I,
)

OFFICIAL_SOURCES_ATTEMPTED = [
    {"url": "https://arxiv.org/abs/2301.13866", "result": "CONNECT denied by egress policy"},
    {"url": "https://www.hepdata.net/record/137762", "result": "CONNECT denied by egress policy"},
    {"url": "https://doi.org/10.17182/hepdata.137762", "result": "CONNECT denied by egress policy"},
    {"url": "https://link.springer.com/article/10.1007/JHEP06(2023)200", "result": "CONNECT denied by egress policy"},
    {
        "url": "https://atlas.web.cern.ch/Atlas/GROUPS/PHYSICS/PAPERS/SUSY-2018-13/",
        "result": "CONNECT denied by egress policy (listed as an additional_resource in submission.yaml)",
    },
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_tables() -> list[dict]:
    docs = [d for d in yaml.safe_load_all((HEPDATA_DIR / "submission.yaml").read_text()) if d]
    return [d for d in docs if "name" in d]


def region_mapping() -> dict:
    """Map the R8 Trackless cutflow onto the published Trackless SR."""
    stages = []
    with open(R8_CUTFLOW, newline="") as fh:
        for row in csv.DictReader(fh):
            if row["region"] == "Trackless":
                stages.append(row["stage"])

    # The published DV+jets selection: a trackless/low-E_T jet trigger stream,
    # then a displaced vertex with R_DV > 4 mm, tracks with |d0| > 2 mm,
    # n_tracks(DV) >= 5 and m_DV > 10 GeV.
    expected = {
        "jet_selection_pct": "Trackless jet-selection (trigger/jet stream) requirement",
        "fiducial_pct": "DV fiducial volume",
        "r_vertex_gt_4mm_pct": "R_DV > 4 mm",
        "track_d0_gt_2mm_pct": "selected tracks with |d0| > 2 mm",
        "selected_decay_products_ge5_pct": "n_tracks(DV) >= 5",
        "invariant_mass_gt_10gev_pct": "m_DV > 10 GeV",
    }
    matched = {s: expected[s] for s in stages if s in expected}
    complete = set(expected) <= set(stages)

    tables = load_tables()
    trackless_tables = [t["name"] for t in tables if "trackless" in t["name"].lower()]
    return {
        "recast_region": "Trackless",
        "recast_cutflow_stages": stages,
        "recast_cutflow_source": str(R8_CUTFLOW.relative_to(WORKSPACE)),
        "recast_cutflow_sha256": sha256_file(R8_CUTFLOW),
        "official_region": "Trackless jet selection signal region (ATLAS DV+jets, 139 fb^-1)",
        "stage_correspondence": matched,
        "hepdata_trackless_tables": trackless_tables,
        "region_mapping_status": "UNAMBIGUOUS" if complete else "INCOMPLETE",
        "region_mapping_note": (
            "The R8 cutflow reproduces the published Trackless selection stage for stage "
            "(R_DV > 4 mm, |d0| > 2 mm, n_tracks >= 5, m_DV > 10 GeV) and the HEPData record "
            "carries a matching family of 'trackless' acceptance, efficiency, cutflow and "
            "yield tables. The region identification itself is not in doubt."
        ),
    }


def numerical_threshold(tables: list[dict]) -> dict:
    """Look for a model-independent limit for the Trackless SR in the record."""
    candidates = []
    for t in tables:
        blob = f"{t['name']} {t.get('description') or ''}"
        if MODEL_INDEPENDENT_PATTERN.search(blob):
            candidates.append({"name": t["name"], "description": (t.get("description") or "")[:200]})

    # Classify what the record *does* contain, so the absence is documented
    # rather than merely asserted.
    families = {"exclusion_contours": 0, "excluded_cross_section_vs_mass": 0,
                "yields_2d_plane": 0, "acceptance": 0, "efficiency": 0,
                "cutflow": 0, "validation_regions": 0, "other": 0}
    for t in tables:
        name = t["name"].lower()
        if name.startswith("excl_xsec"):
            families["excluded_cross_section_vs_mass"] += 1
        elif name.startswith("excl_"):
            families["exclusion_contours"] += 1
        elif name.startswith("yields_"):
            families["yields_2d_plane"] += 1
        elif name.startswith("acceptance"):
            families["acceptance"] += 1
        elif "efficiency" in name:
            families["efficiency"] += 1
        elif name.startswith("cutflow"):
            families["cutflow"] += 1
        elif name.startswith("validation_regions"):
            families["validation_regions"] += 1
        else:
            families["other"] += 1

    # Confirm the trackless "observed" table is the 2D (n_tracks, m_DV) plane
    # and not a single-bin SR count, so no SR yield can be extracted from it.
    obs = yaml.safe_load((HEPDATA_DIR / "yields_trackless_sr_observed.yaml").read_text())
    independent_headers = [v["header"]["name"] for v in obs["independent_variables"]]
    dependent_headers = [v["header"]["name"] for v in obs["dependent_variables"]]
    obs_is_2d_plane = len(independent_headers) == 2

    resolved = bool(candidates)
    return {
        "status": "OFFICIAL_THRESHOLD_RESOLVED" if resolved else "OFFICIAL_THRESHOLD_MAPPING_UNRESOLVED",
        "model_independent_limit_tables_found": candidates,
        "hepdata_table_count": len(tables),
        "hepdata_table_families": families,
        "trackless_observed_table_shape": {
            "independent_variables": independent_headers,
            "dependent_variables": dependent_headers,
            "is_two_dimensional_plane": obs_is_2d_plane,
            "consequence": (
                "The Trackless 'observed' table is the two-dimensional (n_tracks, m_DV) "
                "distribution, not the single-bin signal-region counting experiment, so an "
                "observed SR count and its background estimate cannot be extracted from it "
                "unambiguously."
            ),
        },
        "expected_table_is_signal_not_background": (
            "yields_trackless_sr_expected_ewk carries 'Expected Signal Events' for the "
            "electroweakino benchmark, not the SM background estimate, so it cannot be used "
            "to build a background-only likelihood either."
        ),
        "why_unresolved": (
            "The publication abstract (recorded in submission.yaml) states that model-independent "
            "cross-section limits were set, but the HEPData record contains no such table: its "
            "limit content is exclusively model-dependent SUSY exclusion contours and excluded "
            "cross sections versus mass and lifetime. The paper, the HEPData web record, the DOI "
            "and the ATLAS public page are all unreachable from this session (egress policy). "
            "No S95 was invented or recalled from memory."
        ) if not resolved else "",
        "official_sources_attempted": OFFICIAL_SOURCES_ATTEMPTED,
        "rejected_route": {
            "route": "invert excl_xsec_ewk with acceptance_trackless_ewk to infer a visible-sigma limit",
            "rejected_because": (
                "That limit is model-dependent: it folds the electroweakino A x eff, the "
                "combination of the High-pT and Trackless regions and the full ATLAS likelihood. "
                "Re-using it for a 150 GeV scalar with a different lifetime and topology would "
                "not be an unambiguous mapping."
            ),
        },
        "integrated_luminosity_fb_inverse": 139.0,
        "integrated_luminosity_source": "qualifier on yields_trackless_sr_observed.yaml",
        "observed_S95": None,
        "expected_S95": None,
        "model_independent_visible_sigma_limit_fb": None,
        "observed_event_count": None,
        "expected_background": None,
        "expected_background_uncertainty": None,
    }


def main() -> int:
    outdir = REPO_ROOT / "results" / "r9_h2_sensitivity_threshold"
    outdir.mkdir(parents=True, exist_ok=True)
    tables = load_tables()

    mapping = region_mapping()
    threshold = numerical_threshold(tables)

    payload = {
        "schema": "hep_cross.r9.atlas_threshold.v1",
        "publication": {
            "reference": "ATLAS, JHEP 06 (2023) 200",
            "arxiv": "2301.13866",
            "hepdata_doi": "10.17182/hepdata.137762",
            "inspire_record": 2628398,
            "local_record_version": "HEPData-ins2628398-v2-yaml",
            "local_record_path": str(HEPDATA_DIR.relative_to(REPO_ROOT)),
            "submission_yaml_sha256": sha256_file(HEPDATA_DIR / "submission.yaml"),
        },
        "status": threshold["status"],
        "region_mapping": mapping,
        "numerical_threshold": threshold,
        "consequence_for_r9": (
            "The Trackless region mapping is unambiguous, but no official model-independent "
            "threshold can be read for it in this session. The 1/3/5/10-event thresholds are "
            "therefore retained as illustrative rate scales only; no exclusion or discovery "
            "statement is made, and no required coupling is derived from an official limit."
        ),
        "required_visible_sigma_fb": None,
        "required_rate_multiplier": None,
        "required_kappa_g": None,
        "required_abs_g_hH2H2_GeV": None,
    }
    out = outdir / "atlas_threshold.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"{out.name}: {payload['status']}")
    print(f"region mapping: {mapping['region_mapping_status']}")
    print(f"tables scanned: {threshold['hepdata_table_count']}, "
          f"model-independent limit tables: {len(threshold['model_independent_limit_tables_found'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
