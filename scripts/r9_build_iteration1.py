#!/usr/bin/env python3
"""R9 Iteration 1: frozen baseline, coupling-scaling law and yield thresholds.

Produces, under ``results/r9_h2_sensitivity_threshold``:

``baseline.json``
    Every frozen R8 quantity, each carried with the file it was read from and
    that file's SHA-256, plus an independent recomputation of the yield chain.

``madgraph_scaling_fit.json``
    The exponent ``p`` in ``sigma/sigma0 = kappa_g**p``.  MadGraph cannot be
    re-executed in this environment (see the recorded egress denials), so ``p``
    is established *structurally* by tracing ``GHphiphi`` through the shipped
    UFO: it enters exactly one coupling, which enters exactly one vertex, which
    is used once in the single diagram of ``g g > H > h2 h2``, while the
    mediator width is an external constant.  The amplitude is therefore
    strictly linear in the coupling and ``p = 2`` exactly.  Every link of that
    chain is verified here against the shipped files and recorded with hashes.

``madgraph_coupling_scaling.csv``
    The four requested kappa points with the analytic sigma and *empty*
    measured columns, flagged ``NOT_EXECUTED_MADGRAPH_UNAVAILABLE_EGRESS_BLOCKED``.

``yield_thresholds.csv``
    Recomputed 1/3/5/10-event illustrative thresholds.

``madgraph_deck/``
    Cards reproducing the canonical run settings exactly, for an operator with
    MadGraph access.
"""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from llp_recast.r9_threshold import (  # noqa: E402
    ILLUSTRATIVE_EVENT_TARGETS,
    SIGMA_COUPLING_EXPONENT,
    expected_events,
    scaled_sigma_pb,
    sigma_4b_fb,
    visible_sigma_fb,
    yield_thresholds,
)

WORKSPACE = REPO_ROOT.parent
UFO_ZIP = (
    WORKSPACE / "dihiggs_ufo" / "releases" / "pack_b" / "candidates"
    / "H2scan_mH150_tb300000_MODEL_DERIVED" / "h2_model_derived_ufo.zip"
)
UFO_PARAM_CARD = UFO_ZIP.parent / "param_card.dat"
PRODUCTION_MANIFEST = REPO_ROOT / "artifacts" / "h2_first_physical" / "production_manifest.json"
BANNER = (
    REPO_ROOT / "artifacts" / "h2_first_physical" / "madgraph" / "run_01" / "run_01_tag_1_banner.txt"
)
R8_NORMALIZATION = (
    WORKSPACE / "dihiggs_llp_recast" / "results" / "r8_h2_model_derived_4b" / "normalization.json"
)
COUPLING_ARTIFACT = (
    WORKSPACE / "dihiggs" / "benchmarks" / "H2scan_mH150_tb300000_production_coupling.json"
)

BENCHMARK_ID = "H2scan_mH150_tb300000"
LUMINOSITY_FB_INVERSE = 139.0
KAPPA_SCAN = (0.5, 1.0, 2.0, 4.0)

BLOCKED_SOURCES = [
    {"host": "launchpadlibrarian.net", "purpose": "MG5_aMC tarball download", "result": "403 to CONNECT (egress policy denial)"},
    {"host": "cp3.irmp.ucl.ac.be", "purpose": "MadGraph upstream mirror", "result": "CONNECT refused"},
    {"host": "feynrules.irmp.ucl.ac.be", "purpose": "MadGraph/FeynRules mirror", "result": "CONNECT refused"},
    {"host": "madgraph.phys.ucl.ac.be", "purpose": "MadGraph upstream mirror", "result": "CONNECT refused"},
    {"host": "zenodo.org", "purpose": "MadGraph archival copy", "result": "CONNECT refused"},
    {"host": "github.com release assets (mg5amcnlo)", "purpose": "MG5_aMC source", "result": "403, repository outside session scope"},
]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sourced(value, path: Path, note: str = ""):
    entry = {
        "value": value,
        "source_path": str(path.relative_to(WORKSPACE)),
        "source_sha256": sha256_file(path),
    }
    if note:
        entry["note"] = note
    return entry


# ---------------------------------------------------------------------------
# Structural verification of the coupling-scaling law
# ---------------------------------------------------------------------------

def verify_ufo_scaling_chain() -> dict:
    """Trace GHphiphi through the shipped UFO and assert the linearity chain."""
    checks: list[dict] = []
    with zipfile.ZipFile(UFO_ZIP) as zf:
        names = zf.namelist()
        model_files = {}
        for member in names:
            base = Path(member).name
            if base in ("parameters.py", "couplings.py", "vertices.py", "decays.py", "particles.py"):
                data = zf.read(member)
                model_files[base] = {
                    "member": member,
                    "text": data.decode("utf-8", errors="replace"),
                    "sha256": hashlib.sha256(data).hexdigest(),
                }

    missing = {"parameters.py", "couplings.py", "vertices.py", "decays.py"} - set(model_files)
    if missing:
        raise SystemExit(f"UFO archive is missing expected model files: {sorted(missing)}")

    # 1. GHphiphi is a single external real parameter.
    params = model_files["parameters.py"]["text"]
    decls = re.findall(r"^GHphiphi = Parameter\(", params, re.M)
    nature = re.search(r"GHphiphi = Parameter\((?:.|\n)*?nature = '(\w+)'", params)
    checks.append({
        "step": "GHphiphi is declared exactly once as an external parameter",
        "declarations": len(decls),
        "nature": nature.group(1) if nature else None,
        "passed": len(decls) == 1 and bool(nature) and nature.group(1) == "external",
        "file": model_files["parameters.py"]["member"],
        "sha256": model_files["parameters.py"]["sha256"],
    })

    # 2. GHphiphi appears in exactly one coupling definition.
    couplings = model_files["couplings.py"]["text"]
    active_coupling_lines = [
        line for line in couplings.splitlines()
        if "GHphiphi" in line and not line.lstrip().startswith("#")
    ]
    owning = re.findall(
        r"^(GC_\d+) = Coupling\(name = '\1',\s*\n\s*value = '([^']*GHphiphi[^']*)'", couplings, re.M
    )
    checks.append({
        "step": "GHphiphi appears in exactly one active coupling",
        "active_lines_mentioning_GHphiphi": len(active_coupling_lines),
        "couplings": [{"name": n, "value": v} for n, v in owning],
        "passed": len(owning) == 1 and len(active_coupling_lines) == 1,
        "file": model_files["couplings.py"]["member"],
        "sha256": model_files["couplings.py"]["sha256"],
    })
    coupling_name = owning[0][0] if owning else None

    # 3. That coupling appears in exactly one vertex, and that vertex is H h2 h2.
    vertices = model_files["vertices.py"]["text"]
    uses = re.findall(rf"C\.{coupling_name}\b", vertices) if coupling_name else []
    vertex_blocks = re.findall(
        r"^(V_\d+) = Vertex\(name = '\1',\s*\n\s*particles = \[([^\]]*)\](?:.|\n)*?couplings = \{[^}]*C\.(GC_\d+)[^}]*\}",
        vertices, re.M,
    )
    owning_vertices = [
        {"vertex": v, "particles": [p.strip() for p in parts.split(",")]}
        for v, parts, c in vertex_blocks if c == coupling_name
    ]
    expected_particles = ["P.H", "P.h2", "P.h2"]
    checks.append({
        "step": f"{coupling_name} is used by exactly one vertex, and it is (H, h2, h2)",
        "uses": len(uses),
        "vertices": owning_vertices,
        "passed": (
            len(uses) == 1 and len(owning_vertices) == 1
            and owning_vertices[0]["particles"] == expected_particles
        ),
        "file": model_files["vertices.py"]["member"],
        "sha256": model_files["vertices.py"]["sha256"],
    })

    # 4. No decay width in the model depends on GHphiphi.
    decays = model_files["decays.py"]["text"]
    checks.append({
        "step": "no partial width in decays.py depends on GHphiphi",
        "occurrences": decays.count("GHphiphi"),
        "passed": "GHphiphi" not in decays,
        "file": model_files["decays.py"]["member"],
        "sha256": model_files["decays.py"]["sha256"],
    })

    # 5. The mediator width used at run time is an external constant, not Auto.
    banner_text = BANNER.read_text(errors="replace")
    wh = re.search(r"^DECAY\s+25\s+(\S+)\s*#\s*WH", banner_text, re.M)
    checks.append({
        "step": "mediator (PDG 25) width is a fixed external number in the run param card, not 'Auto'",
        "DECAY_25_value_GeV": wh.group(1) if wh else None,
        "passed": bool(wh) and wh.group(1).lower() != "auto",
        "file": str(BANNER.relative_to(WORKSPACE)),
        "sha256": sha256_file(BANNER),
    })

    # 6. The generated process is the single-diagram s-channel one.
    proc = re.search(r"^generate (g g > H > h2 h2)\s*$", banner_text, re.M)
    checks.append({
        "step": "generated process is 'g g > H > h2 h2'",
        "process": proc.group(1) if proc else None,
        "passed": bool(proc),
        "file": str(BANNER.relative_to(WORKSPACE)),
        "sha256": sha256_file(BANNER),
    })

    # 7. H -> h2 h2 is kinematically closed, so the mediator cannot acquire a
    #    GHphiphi-dependent width even if the width were computed.
    param_card = UFO_PARAM_CARD.read_text()
    mh = float(re.search(r"^\s*25\s+(\S+)", param_card, re.M).group(1))
    mh2 = float(re.search(r"^\s*9000006\s+(\S+)", param_card, re.M).group(1))
    checks.append({
        "step": "H -> h2 h2 is kinematically closed (m_H < 2 m_h2)",
        "m_H_GeV": mh,
        "m_h2_GeV": mh2,
        "passed": mh < 2.0 * mh2,
        "file": str(UFO_PARAM_CARD.relative_to(WORKSPACE)),
        "sha256": sha256_file(UFO_PARAM_CARD),
    })

    all_passed = all(c["passed"] for c in checks)
    return {"all_passed": all_passed, "checks": checks, "ufo_zip_sha256": sha256_file(UFO_ZIP)}


def build_madgraph_deck(outdir: Path, baseline_ghphiphi: float, baseline_ctau_m: float) -> list[str]:
    """Write cards an operator can run in a MadGraph-capable environment."""
    deck = outdir / "madgraph_deck"
    deck.mkdir(parents=True, exist_ok=True)
    written: list[str] = []

    proc_card = deck / "proc_card.dat"
    proc_card.write_text(
        "# R9 coupling-scaling deck -- identical topology to the canonical R8 production.\n"
        "# Reproduces the MG5ProcCard recorded in\n"
        "# artifacts/h2_first_physical/madgraph/run_01/run_01_tag_1_banner.txt\n"
        "import model ./pi_ufo_baseline_v1_release_candidate_hotfix1/model/LLscalar_v3_UFO_runtime\n"
        "generate g g > H > h2 h2\n"
        "output r9_h2_scaling -f\n",
        encoding="utf-8",
    )
    written.append(str(proc_card.relative_to(REPO_ROOT)))

    run_card = deck / "run_card_fragment.dat"
    run_card.write_text(
        "# Integration-only settings, byte-compatible with the canonical run_card.\n"
        "# Cross sections only: no unweighted events are needed for the scaling fit.\n"
        "  1000   = nevents\n"
        "  1      = lpp1\n"
        "  1      = lpp2\n"
        "  6500.0 = ebeam1\n"
        "  6500.0 = ebeam2\n"
        "  nn23lo1 = pdlabel\n"
        "  230000 = lhaid\n"
        "  False  = fixed_ren_scale\n"
        "  False  = fixed_fac_scale\n"
        "  -1     = dynamical_scale_choice\n"
        "  1.0    = scalefact\n"
        "  0      = nhel\n"
        "  4      = maxjetflavor\n"
        "  True   = use_syst\n",
        encoding="utf-8",
    )
    written.append(str(run_card.relative_to(REPO_ROOT)))

    for kappa in KAPPA_SCAN:
        card = deck / f"param_card_kappa_{str(kappa).replace('.', 'p')}.dat"
        card.write_text(
            "Block MASS\n"
            "  25 1.25130000000000000e+02 # SM-like scalar\n"
            "  9000006 1.50000000000000000e+02 # H2\n"
            "Block FRBlock\n"
            f"  2 {baseline_ctau_m:.17e} # ctauh2 [m] (unchanged)\n"
            f"  3 {kappa * baseline_ghphiphi:.17e} # GHphiphi [GeV] = {kappa} x baseline\n",
            encoding="utf-8",
        )
        written.append(str(card.relative_to(REPO_ROOT)))

    runner = deck / "run_commands.sh"
    runner.write_text(
        "#!/usr/bin/env bash\n"
        "# R9 coupling-scaling runs. Requires MG5_aMC (canonical production used 3.5.3)\n"
        "# and the Pack B UFO unpacked next to this script.\n"
        "#\n"
        "# These runs could NOT be executed in the session that produced this deck:\n"
        "# every MadGraph distribution host is denied by the environment's egress\n"
        "# policy. See madgraph_scaling_fit.json -> blocked_sources.\n"
        "set -euo pipefail\n"
        "MG5=${MG5:-mg5_aMC}\n"
        '"$MG5" proc_card.dat\n'
        "for k in " + " ".join(str(k).replace(".", "p") for k in KAPPA_SCAN) + "; do\n"
        "  cp \"param_card_kappa_${k}.dat\" r9_h2_scaling/Cards/param_card.dat\n"
        "  cat run_card_fragment.dat >> r9_h2_scaling/Cards/run_card.dat\n"
        "  (cd r9_h2_scaling && ./bin/generate_events -f \"kappa_${k}\")\n"
        "done\n"
        "# Then: python3 ../../../scripts/r9_ingest_madgraph_scaling.py --help\n",
        encoding="utf-8",
    )
    runner.chmod(0o755)
    written.append(str(runner.relative_to(REPO_ROOT)))
    return written


def main() -> int:
    outdir = REPO_ROOT / "results" / "r9_h2_sensitivity_threshold"
    outdir.mkdir(parents=True, exist_ok=True)

    production = json.loads(PRODUCTION_MANIFEST.read_text())
    normalization = json.loads(R8_NORMALIZATION.read_text())
    coupling = json.loads(COUPLING_ARTIFACT.read_text())

    sigma_pb = production["madgraph"]["combined_sigma_pb"]
    br_bb = production["normalization"]["BR_bb"]
    br_bb_sq = production["normalization"]["BR_bb_squared"]
    a_eff = normalization["regions"]["Trackless"]["a_eff_acc_x_eff"]
    ghphiphi = production["ufo"]["GHphiphi_GeV"]
    g_abs = coupling["coupling"]["g_hH2H2_GeV"]
    ctau_mm = coupling["replay"]["ctau_mm"]
    ctau_m = production["ufo"]["lifetime_mm"] / 1000.0

    # Independent recomputation of the whole yield chain.
    sigma4b = sigma_4b_fb(sigma_pb, br_bb_sq)
    vis_fb = visible_sigma_fb(sigma_pb, br_bb_sq, a_eff)
    n_expected = expected_events(vis_fb, LUMINOSITY_FB_INVERSE)

    baseline = {
        "schema": "hep_cross.r9.baseline.v1",
        "benchmark_id": BENCHMARK_ID,
        "luminosity_fb_inverse": LUMINOSITY_FB_INVERSE,
        "luminosity_source": (
            "R9 task specification; the R8 normalization artifact deliberately leaves "
            "luminosity_fb_inv null because it was not present in the recast repository"
        ),
        "frozen_inputs": {
            "m_H2_GeV": sourced(production["ufo"]["mass_GeV"], PRODUCTION_MANIFEST),
            "ctau_mm": sourced(ctau_mm, COUPLING_ARTIFACT),
            "total_width_GeV": sourced(coupling["replay"]["total_width_GeV"], COUPLING_ARTIFACT),
            "g_hH2H2_GeV": sourced(g_abs, COUPLING_ARTIFACT),
            "GHphiphi_GeV": sourced(ghphiphi, PRODUCTION_MANIFEST,
                                    "GHphiphi = -g_hH2H2 (2HDMC c = -i g; UFO vertex +i GHphiphi)"),
            "sigma_H2H2_pb": sourced(sigma_pb, PRODUCTION_MANIFEST,
                                     "inverse-variance combination of run_01 and run_02"),
            "BR_bb": sourced(br_bb, PRODUCTION_MANIFEST),
            "BR_bb_squared": sourced(br_bb_sq, PRODUCTION_MANIFEST),
            "Trackless_Aeff": sourced(a_eff, R8_NORMALIZATION, "a_eff_acc_x_eff"),
            "Trackless_visible_sigma_fb": sourced(
                normalization["regions"]["Trackless"]["visible_sigma_fb_acc_x_eff"], R8_NORMALIZATION
            ),
        },
        "recomputed": {
            "sigma_4b_fb": sigma4b,
            "Trackless_visible_sigma_fb": vis_fb,
            "Trackless_expected_events": n_expected,
            "formula": "sigma[pb] * 1000 * BR_bb^2 * (A x eff) * L[fb^-1]",
        },
        "r8_status": {
            "recast_validation_status": normalization["recast_validation_status"],
            "acceptance_status": normalization["acceptance_status"],
            "exclusion_status": normalization["exclusion_status"],
            "highpt_statistics_status": normalization["highpt_statistics_status"],
        },
        "provenance": {
            "dihiggs_merge_commit": coupling.get("benchmark_commit"),
            "ufo_merge_commit": production["ufo"]["merge_commit"],
            "coupling_artifact_merge_commit": production["coupling_artifact"]["merge_commit"],
        },
    }
    (outdir / "baseline.json").write_text(json.dumps(baseline, indent=2) + "\n", encoding="utf-8")

    # ---- scaling law --------------------------------------------------------
    chain = verify_ufo_scaling_chain()
    if not chain["all_passed"]:
        failed = [c["step"] for c in chain["checks"] if not c["passed"]]
        raise SystemExit(f"UFO scaling chain verification FAILED: {failed}")

    mg = production["madgraph"]
    fit = {
        "schema": "hep_cross.r9.madgraph_scaling_fit.v1",
        "question": "Does sigma(pp -> H2H2) scale quadratically with |g_hH2H2|?",
        "fitted_exponent_p": SIGMA_COUPLING_EXPONENT,
        "exponent_uncertainty": 0.0,
        "method": "STRUCTURAL_EXACT",
        "quadratic_scaling": "PASS",
        "argument": (
            "GHphiphi enters exactly one UFO coupling (GC_90 = i*GHphiphi), that coupling "
            "enters exactly one vertex (V_7 = H h2 h2), and that vertex is used once in the "
            "single diagram of 'g g > H > h2 h2'. No decay width in the model depends on "
            "GHphiphi, the mediator width is a fixed external number in the run param card "
            "(not 'Auto'), and H -> h2 h2 is kinematically closed. The amplitude is therefore "
            "strictly linear in GHphiphi with no interference, no competing diagram and no "
            "width or propagator feedback, so |M|^2 and hence sigma scale as GHphiphi^2 with "
            "phase space unchanged. p = 2 exactly, not approximately."
        ),
        "changing_GHphiphi_affects": {
            "overall_matrix_element_normalization": True,
            "mediator_width": False,
            "interference": False,
            "additional_diagrams": False,
            "phase_space_distributions": False,
        },
        "structural_verification": chain,
        "empirical_fit": None,
        "empirical_fit_status": "NOT_EXECUTED_MADGRAPH_UNAVAILABLE_EGRESS_BLOCKED",
        "empirical_fit_blocker": (
            "MG5_aMC is not installed in this environment and cannot be obtained: every "
            "MadGraph distribution host is denied by the session's egress policy. "
            "Separately, the canonical version 3.5.3 is no longer published upstream "
            "(launchpad's 3.5.x series now offers 3.5.6/3.5.8/3.5.9/3.5.10/3.5.12 only). "
            "No cross section was invented or recalled to fill the gap."
        ),
        "blocked_sources": BLOCKED_SOURCES,
        "available_empirical_evidence_at_kappa_1": {
            "note": (
                "The only measured cross sections that exist for this model point are the two "
                "independent canonical runs at kappa_g = 1. They are statistically compatible, "
                "which validates the integration but does not by itself test the scaling law."
            ),
            "sigma_run_01_pb": mg["sigma_run_1_pb"],
            "sigma_run_01_error_pb": mg["sigma_run_1_error_pb"],
            "sigma_run_02_pb": mg["sigma_run_2_pb"],
            "sigma_run_02_error_pb": mg["sigma_run_2_error_pb"],
            "compatibility": mg["compatibility"],
        },
        "canonical_run_configuration": {
            "madgraph_version": mg["version"],
            "process": mg["process"],
            "sqrt_s_TeV": mg["sqrt_s_TeV"],
            "pdf": mg["pdf"],
            "scales": mg["scales"],
            "diagram_interpretation": mg["diagram_interpretation"],
        },
    }
    (outdir / "madgraph_scaling_fit.json").write_text(json.dumps(fit, indent=2) + "\n", encoding="utf-8")

    # ---- the four requested kappa points -----------------------------------
    scaling_rows = []
    for kappa in KAPPA_SCAN:
        analytic = scaled_sigma_pb(sigma_pb, kappa)
        scaling_rows.append({
            "kappa_g": f"{kappa:.6f}",
            "GHphiphi_GeV": f"{kappa * ghphiphi:.17e}",
            "abs_g_hH2H2_GeV": f"{kappa * g_abs:.17e}",
            "sigma_pb": "",
            "integration_error_pb": "",
            "sigma_over_sigma_baseline": "",
            "expected_kappa_g_squared": f"{kappa ** 2:.17e}",
            "relative_residual": "",
            "analytic_sigma_pb": f"{analytic:.17e}",
            "param_card": f"madgraph_deck/param_card_kappa_{str(kappa).replace('.', 'p')}.dat",
            "log": "",
            "sha256": "",
            "status": "NOT_EXECUTED_MADGRAPH_UNAVAILABLE_EGRESS_BLOCKED",
        })
    scaling_csv = outdir / "madgraph_coupling_scaling.csv"
    with open(scaling_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, lineterminator="\n", fieldnames=list(scaling_rows[0].keys()))
        writer.writeheader()
        writer.writerows(scaling_rows)

    # ---- illustrative yield thresholds -------------------------------------
    thresholds = yield_thresholds(
        ILLUSTRATIVE_EVENT_TARGETS,
        baseline_events=n_expected,
        baseline_sigma_pb=sigma_pb,
        baseline_visible_sigma_fb=vis_fb,
        baseline_abs_coupling_gev=g_abs,
    )
    thresholds_csv = outdir / "yield_thresholds.csv"
    with open(thresholds_csv, "w", newline="", encoding="utf-8") as fh:
        fieldnames = [
            "target_events", "rate_multiplier", "kappa_g", "required_abs_g_hH2H2_GeV",
            "required_GHphiphi_GeV", "required_sigma_H2H2_pb", "required_visible_sigma_fb",
            "interpretation",
        ]
        writer = csv.DictWriter(fh, lineterminator="\n", fieldnames=fieldnames)
        writer.writeheader()
        for t in thresholds:
            row = t.as_row()
            row["required_GHphiphi_GeV"] = -row["required_abs_g_hH2H2_GeV"]
            row["interpretation"] = "ILLUSTRATIVE_RATE_SCALE_NOT_DISCOVERY_OR_EXCLUSION"
            writer.writerow({k: row[k] for k in fieldnames})

    deck_files = build_madgraph_deck(outdir, ghphiphi, ctau_m)

    print(f"baseline expected Trackless events = {n_expected!r}")
    print(f"structural scaling chain: {len(chain['checks'])} checks, all passed")
    print(f"wrote {scaling_csv.name}, {thresholds_csv.name}, deck ({len(deck_files)} files)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
