import importlib.util
import json
import zipfile
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "13_h2_benchmark_handoff.py"
spec = importlib.util.spec_from_file_location("h2_benchmark_handoff", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


def _candidate(path, status=mod.REQUIRED_SOFT_SCALE_STATUS):
    selected = {
        "point_id": "H2scan_mH150_tb300000",
        "m_H2_GeV": 150.0,
        "mA_GeV": 450.0,
        "mHp_GeV": 450.0,
        "tan_beta": 300000.0,
        "sin_beta_minus_alpha": 1.0,
        "lambda1_target": 1.0,
        "lambda6_input": 1e-10,
        "lambda7_input": 0.0,
        "yukawa_type": "Type I",
        "m12_sq_construction_GeV2": 0.075,
        "M2_construction_GeV2": 22499.9999995,
        "m12_sq_roundtrip_reconstructed_GeV2": 0.0749997525,
        "soft_scale_export_status": status,
        "total_width_GeV": 4.56118529862185e-14,
        "ctau_mm": 4.326221529733112,
        "br_bb": 0.7567374858085787,
    }
    path.write_text(
        json.dumps({"scan_producer_commit": mod.REQUIRED_PRODUCER_COMMIT, "selected_candidate": selected}),
        encoding="utf-8",
    )
    return selected


def _ufo(path):
    root = "frozen/"
    schema = {"properties": {"coupling_mode": {"enum": ["PI_FIXED"]}}}
    members = {
        "MODEL_CARD.md": "bb decay declared. Runtime support is pending.",
        "KNOWN_LIMITATIONS.md": "Not a complete 2HDM UFO",
        "schemas/point.schema.json": json.dumps(schema),
        "README_PACK_A.md": "h2 is generated stable in the LHE",
        "model/LLscalar_v3_UFO_runtime/parameters.py": (
            "Mh2 = Parameter(name = 'Mh2', nature = 'external', type = 'real')\n"
            "ctauh2 = Parameter(name = 'ctauh2', nature = 'external', type = 'real')\n"
        ),
        "model/LLscalar_v3_UFO_runtime/particles.py": (
            "h2 = Particle(pdg_code = 9000006,\n              name = 'h2')\n"
            "H = Particle(pdg_code = 25,\n             name = 'H')\n"
        ),
        "model/LLscalar_v3_UFO_runtime/vertices.py": "particles = [ P.H, P.h2, P.h2 ]\ncouplings = {(0,0):C.GC_90}\n",
    }
    with zipfile.ZipFile(path, "w") as archive:
        for name, contents in members.items():
            archive.writestr(root + name, contents)


def test_emits_exact_blocker_and_preserves_construction_values(tmp_path):
    candidate_path = tmp_path / "candidate.json"
    ufo_path = tmp_path / "ufo.zip"
    selected = _candidate(candidate_path)
    _ufo(ufo_path)

    handoff = mod.build_handoff(candidate_path, ufo_path)

    assert handoff["status"] == "BLOCKED_BY_UFO"
    assert handoff["candidate"]["construction"]["m12_sq_GeV2"] == selected["m12_sq_construction_GeV2"]
    assert handoff["candidate"]["construction"]["M2_GeV2"] == selected["M2_construction_GeV2"]
    assert handoff["candidate"]["roundtrip_diagnostic"] == {
        "m12_sq_GeV2": selected["m12_sq_roundtrip_reconstructed_GeV2"],
        "accepted_as_construction": False,
    }
    assert [item["id"] for item in handoff["mismatches"]] == [
        "FULL_2HDM_CONSTRUCTION_UNAVAILABLE",
        "PRODUCTION_COUPLING_NOT_REPLAYABLE",
        "BB_DECAY_RUNTIME_UNVALIDATED",
        "MASS_AND_WIDTH_DEFAULT_MISMATCH",
    ]
    assert handoff["cross_section"] == {"value": None, "created": False}
    assert handoff["ufo"]["external_parameters"] == ["Mh2", "ctauh2"]


def test_rejects_unvalidated_soft_scale_status(tmp_path):
    candidate_path = tmp_path / "candidate.json"
    ufo_path = tmp_path / "ufo.zip"
    _candidate(candidate_path, status="UNVALIDATED")

    with pytest.raises(ValueError, match="soft_scale_export_status must be"):
        mod.build_handoff(candidate_path, ufo_path)


def test_roundtrip_value_cannot_replace_missing_construction_value(tmp_path):
    candidate_path = tmp_path / "candidate.json"
    ufo_path = tmp_path / "ufo.zip"
    selected = _candidate(candidate_path)
    del selected["m12_sq_construction_GeV2"]
    candidate_path.write_text(
        json.dumps({"scan_producer_commit": mod.REQUIRED_PRODUCER_COMMIT, "selected_candidate": selected}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="m12_sq_construction_GeV2"):
        mod.build_handoff(candidate_path, ufo_path)


def test_roundtrip_value_is_rejected_as_construction_input(tmp_path):
    candidate_path = tmp_path / "candidate.json"
    ufo_path = tmp_path / "ufo.zip"
    selected = _candidate(candidate_path)
    selected["m12_sq_construction_GeV2"] = selected["m12_sq_roundtrip_reconstructed_GeV2"]
    candidate_path.write_text(
        json.dumps({"scan_producer_commit": mod.REQUIRED_PRODUCER_COMMIT, "selected_candidate": selected}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="diagnostic round-trip"):
        mod.build_handoff(candidate_path, ufo_path)
