#!/usr/bin/env python3
"""Emit the H2 benchmark handoff without executing the frozen UFO."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path


REQUIRED_SOFT_SCALE_STATUS = "VALIDATED_BY_SET_PARAM_PHYS_REPLAY"
CONSTRUCTION_FIELDS = (
    "m12_sq_construction_GeV2",
    "M2_construction_GeV2",
)
UFO_MEMBERS = {
    "model_card": "MODEL_CARD.md",
    "limitations": "KNOWN_LIMITATIONS.md",
    "schema": "schemas/point.schema.json",
    "readme": "README_PACK_A.md",
    "parameters": "model/LLscalar_v3_UFO_runtime/parameters.py",
    "particles": "model/LLscalar_v3_UFO_runtime/particles.py",
    "vertices": "model/LLscalar_v3_UFO_runtime/vertices.py",
}
UFO_GIT_COMMIT = "a6065bfc6359c2b74d40e17972a1c697a4d9a843"
REQUIRED_PRODUCER_COMMIT = "31adde89d831195adde927b364046723ba29e3fe"
UPSTREAM_BENCHMARK_COMMIT = "92ad4d80f537bffd8663e42f1c6881e82849feab"


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_member(archive: zipfile.ZipFile, suffix: str) -> str:
    matches = [name for name in archive.namelist() if name.endswith("/" + suffix)]
    if len(matches) != 1:
        raise ValueError(f"UFO archive must contain exactly one {suffix}; found {len(matches)}")
    return archive.read(matches[0]).decode("utf-8")


def inspect_ufo(path: Path) -> dict:
    with zipfile.ZipFile(path) as archive:
        text = {name: _read_member(archive, suffix) for name, suffix in UFO_MEMBERS.items()}

    schema = json.loads(text["schema"])
    modes = schema["properties"]["coupling_mode"]["enum"]
    external_parameters = sorted(
        set(re.findall(r"Parameter\(name\s*=\s*'([^']+)',\s*nature\s*=\s*'external'", text["parameters"]))
    )
    blocks = re.findall(r"Parameter\((.*?)(?=\n\n[A-Za-z_]\w*\s*=\s*Parameter|\Z)", text["parameters"], re.S)
    defaults = {}
    for block in blocks:
        name = re.search(r"name\s*=\s*'([^']+)'", block)
        value = re.search(r"nature\s*=\s*'external'[\s\S]*?value\s*=\s*([0-9.eE+-]+)", block)
        if name and value:
            defaults[name.group(1)] = float(value.group(1))
    particles = {
        name: int(pdg)
        for pdg, name in re.findall(
            r"pdg_code\s*=\s*(-?\d+),\s*\n\s*name\s*=\s*'([^']+)'", text["particles"]
        )
        if name in {"H", "h2"}
    }
    width_formula = re.search(
        r"Wh2\s*=\s*Parameter\([\s\S]*?value\s*=\s*'([^']+)'", text["parameters"]
    )
    readme = " ".join(text["readme"].split())
    signatures = {
        "pack_is_not_full_2hdm": "Not a complete 2HDM UFO" in text["limitations"],
        "h2_is_stable_in_lhe": "h2 is generated stable in the LHE" in readme,
        "bb_runtime_is_pending": "bb" in text["model_card"] and "Runtime support is pending" in text["model_card"],
        "production_is_pi_fixed": modes == ["PI_FIXED"],
    }
    failed = [name for name, present in signatures.items() if not present]
    if failed:
        raise ValueError(f"frozen UFO no longer matches expected static contract: {failed}")

    return {
        "archive": path.name,
        "path": str(path),
        "pack_name": "pi_ufo_baseline_v1",
        "pack_version": "frozen_hotfix1",
        "git_commit": UFO_GIT_COMMIT,
        "sha256": _sha256(path),
        "inspection_mode": "STATIC_ZIP_CONTENT_ONLY",
        "accepted_coupling_modes": modes,
        "external_parameters": external_parameters,
        "external_defaults": defaults,
        "particles": particles,
        "production_vertex": "[ P.H, P.h2, P.h2 ]" in text["vertices"],
        "production_coupling": "GC_90" if "GC_90" in text["vertices"] else None,
        "h2_width_internal_formula": width_formula.group(1) if width_formula else None,
        "parameter_map": {
            "mH2": "Mh2",
            "mA": None,
            "mHp": None,
            "tan_beta": None,
            "sin_beta_minus_alpha": None,
            "m12_sq": None,
            "M2": None,
            "lambda6": None,
            "lambda7": None,
            "yukawa_type": None,
            "total_width": "Wh2",
        },
        "signatures": signatures,
    }


def build_handoff(candidate_path: Path, ufo_path: Path) -> dict:
    candidate_document = json.loads(candidate_path.read_text(encoding="utf-8"))
    candidate = candidate_document["selected_candidate"]
    producer_commit = candidate_document.get("scan_producer_commit")
    if producer_commit != REQUIRED_PRODUCER_COMMIT:
        raise ValueError(f"scan_producer_commit must be {REQUIRED_PRODUCER_COMMIT}, got {producer_commit!r}")
    status = candidate.get("soft_scale_export_status")
    if status != REQUIRED_SOFT_SCALE_STATUS:
        raise ValueError(
            f"soft_scale_export_status must be {REQUIRED_SOFT_SCALE_STATUS}, got {status!r}"
        )
    missing = [field for field in CONSTRUCTION_FIELDS if field not in candidate]
    if missing:
        raise ValueError(f"missing construction soft-scale fields: {missing}")
    diagnostic = candidate.get("m12_sq_roundtrip_reconstructed_GeV2")
    if diagnostic is not None and candidate["m12_sq_construction_GeV2"] == diagnostic:
        raise ValueError("diagnostic round-trip m12_sq cannot be used as construction input")

    ufo = inspect_ufo(ufo_path)
    schema_inputs = {
        "mphi_GeV",
        "mh_GeV",
        "Mbar2_GeV2",
        "coupling_mode",
        "ctau_mm",
        "branching_ratios",
    }
    required_2hdm_inputs = [
        "mA_GeV",
        "mHp_GeV",
        "tan_beta",
        "sin_beta_minus_alpha",
        "lambda1_target",
        "lambda6_input",
        "lambda7_input",
        "yukawa_type",
        *CONSTRUCTION_FIELDS,
    ]

    return {
        "schema_version": "hep_cross.h2_benchmark_handoff.v1",
        "status": "BLOCKED_BY_UFO",
        "candidate_source": {
            "repository": "https://github.com/fbientrigo/dihiggs",
            "benchmark_commit": UPSTREAM_BENCHMARK_COMMIT,
            "producer_commit": producer_commit,
            "path": "benchmarks/FIRST_H2_RECAST_CANDIDATE.json",
            "file": candidate_path.name,
            "sha256": _sha256(candidate_path),
        },
        "candidate": {
            "point_id": candidate["point_id"],
            "construction": {
                "m12_sq_GeV2": candidate["m12_sq_construction_GeV2"],
                "M2_GeV2": candidate["M2_construction_GeV2"],
                "soft_scale_export_status": status,
            },
            "roundtrip_diagnostic": {
                "m12_sq_GeV2": diagnostic,
                "accepted_as_construction": False,
            },
            "physics": {
                key: candidate[key]
                for key in (
                    "m_H2_GeV",
                    "mA_GeV",
                    "mHp_GeV",
                    "tan_beta",
                    "sin_beta_minus_alpha",
                    "lambda1_target",
                    "lambda6_input",
                    "lambda7_input",
                    "yukawa_type",
                    "total_width_GeV",
                    "ctau_mm",
                    "br_bb",
                )
            },
        },
        "ufo": ufo,
        "mismatches": [
            {
                "id": "FULL_2HDM_CONSTRUCTION_UNAVAILABLE",
                "candidate_fields": required_2hdm_inputs,
                "ufo_unrepresentable_fields": [field for field in required_2hdm_inputs if field not in schema_inputs],
                "ufo_observation": "Frozen point schema has no full 2HDM construction contract.",
            },
            {
                "id": "PRODUCTION_COUPLING_NOT_REPLAYABLE",
                "candidate_requirement": {
                    "M2_construction_GeV2": candidate["M2_construction_GeV2"],
                    "m12_sq_construction_GeV2": candidate["m12_sq_construction_GeV2"],
                },
                "ufo_observation": {
                    "accepted_coupling_modes": ufo["accepted_coupling_modes"],
                    "coupling": ufo["production_coupling"],
                },
            },
            {
                "id": "BB_DECAY_RUNTIME_UNVALIDATED",
                "candidate_requirement": {"br_bb": candidate["br_bb"], "ctau_mm": candidate["ctau_mm"]},
                "ufo_observation": "h2 is stable in LHE; declared bb decay runtime is pending.",
            },
            {
                "id": "MASS_AND_WIDTH_DEFAULT_MISMATCH",
                "expected": {"mH2_GeV": candidate["m_H2_GeV"], "total_width_GeV": candidate["total_width_GeV"]},
                "ufo_actual_default": {
                    "mass_parameter": "Mh2",
                    "mH2_GeV": ufo["external_defaults"].get("Mh2"),
                    "width_parameter": "Wh2",
                    "width_formula": ufo["h2_width_internal_formula"],
                    "ctauh2_default": ufo["external_defaults"].get("ctauh2"),
                },
            },
        ],
        "cross_section": {"value": None, "created": False},
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--ufo", required=True, type=Path)
    parser.add_argument("--output", required=True, help="JSON path, or - for stdout")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = json.dumps(build_handoff(args.candidate, args.ufo), indent=2, sort_keys=True) + "\n"
    if args.output == "-":
        sys.stdout.write(payload)
    else:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
