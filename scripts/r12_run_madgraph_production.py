#!/usr/bin/env python3
"""R12 Mission: Complete Six-g MadGraph Production Campaign Driver."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "src"))

from llp_recast.r11_madgraph_pilot import (
    G0_GEV,
    SIGMA0_PB,
    calculate_g2_prediction,
    calculate_relative_residual,
    extract_madgraph_xsec,
    extract_run_card_applied_from_banner,
    parse_lhe_events,
)
from llp_recast.r12_madgraph_production import (
    R12_G_TARGETS,
    R12_SEEDS,
    combine_inverse_variance,
    fmt_g_dir,
    sha256_file,
    validate_banner_file,
    validate_lhe_file,
)

DEFAULT_OUT_DIR = REPO_ROOT / "results" / "r12_madgraph_per_g_production"
CONFIG_PATH = REPO_ROOT / "configs" / "r10_effective_scan.json"


def discover_mg5_exec(cli_arg: Path | None) -> Path | None:
    if cli_arg and cli_arg.exists():
        return cli_arg
    env_path = os.environ.get("MG5_EXEC")
    if env_path and Path(env_path).exists():
        return Path(env_path)

    which_mg5 = shutil.which("mg5_aMC") or shutil.which("mg5")
    if which_mg5:
        return Path(which_mg5)

    home_local = Path.home() / ".local" / "mg5amcnlo" / "3.5.3" / "bin" / "mg5_aMC"
    if home_local.exists():
        return home_local

    return None


def discover_ufo_zip(cli_arg: Path | None) -> Path | None:
    if cli_arg and cli_arg.exists():
        return cli_arg
    env_path = os.environ.get("DIHIGGS_UFO_ZIP")
    if env_path and Path(env_path).exists():
        return Path(env_path)

    candidates = [
        REPO_ROOT.parent / "_worktrees" / "h2-model-derived-pack-b" / "releases"
        / "pack_b" / "candidates" / "H2scan_mH150_tb300000_MODEL_DERIVED" / "h2_model_derived_ufo.zip",
        REPO_ROOT.parent / "h2-model-derived-pack-b" / "releases"
        / "pack_b" / "candidates" / "H2scan_mH150_tb300000_MODEL_DERIVED" / "h2_model_derived_ufo.zip",
        REPO_ROOT.parent / "ufos" / "releases" / "pack_b" / "candidates" / "H2scan_mH150_tb300000_MODEL_DERIVED" / "h2_model_derived_ufo.zip",
    ]
    for cand in candidates:
        if cand.exists():
            return cand

    return None


def load_g_values_from_config(config_path: Path) -> list[float]:
    if not config_path.exists():
        return R12_G_TARGETS
    data = json.loads(config_path.read_text(encoding="utf-8"))
    return data.get("grid", {}).get("g_hH2H2_GeV", R12_G_TARGETS)


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run R12 Six-g MadGraph Production Campaign Driver.")
    parser.add_argument("--mg5-exec", type=Path, default=None, help="Path to mg5_aMC executable.")
    parser.add_argument("--ufo-zip", type=Path, default=None, help="Path to canonical UFO model zip archive.")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT_DIR, help="Output directory for production campaign.")
    parser.add_argument("--g-values", type=float, nargs="+", default=None, help="Coupling values to execute.")
    parser.add_argument("--seeds", type=int, nargs="+", default=None, help="Production seeds (expects 2 seeds).")

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument("--execute", action="store_true", help="Physically execute MadGraph runs (fail if MG5 unavailable).")
    mode_group.add_argument("--reuse-existing", action="store_true", help="Recompute summaries from existing evidence without running MG5.")
    mode_group.add_argument("--verify-only", action="store_true", help="Verify existing evidence without performing writes except reports.")
    mode_group.add_argument("--resume", action="store_true", help="Skip runs that pass verification; rerun incomplete/corrupt runs.")

    return parser.parse_args(args)


def check_run_artifacts_valid(run_dir: Path, g: float, seed: int) -> tuple[bool, str]:
    expected_files = [
        "param_card.dat",
        "run_card_overrides.dat",
        "run_card_applied.dat",
        "proc_card.dat",
        "banner.txt",
        "madgraph_run.txt",
        "unweighted_events.lhe.gz",
        "run_manifest.json",
    ]
    for fname in expected_files:
        p = run_dir / fname
        if not p.exists():
            return False, f"Missing expected artifact {fname}"

    lhe_val = validate_lhe_file(run_dir / "unweighted_events.lhe.gz")
    if not lhe_val["valid"]:
        return False, f"LHE validation failed: {lhe_val['error']}"

    banner_val = validate_banner_file(run_dir / "banner.txt", expected_g=g, expected_seed=seed)
    if not banner_val["valid"]:
        return False, f"Banner validation failed: {banner_val['error']}"

    return True, "Valid"


def execute_single_run(
    mg5_exec: Path,
    proc_dir: Path,
    param_default: Path,
    run_dir: Path,
    g_target: float,
    seed: int,
    run_name: str,
) -> tuple[float, float]:
    ghphiphi_target = -abs(g_target)
    run_dir.mkdir(parents=True, exist_ok=True)

    proc_card_path = run_dir / "proc_card.dat"
    proc_card_path.write_text(
        "import model ./ufo/pi_ufo_baseline_v1_release_candidate_hotfix1/model/LLscalar_v3_UFO_runtime\n"
        "generate g g > H > h2 h2\n"
        "output proc_output -f\n",
        encoding="utf-8",
    )

    param_card_path = run_dir / "param_card.dat"
    run_overrides_path = run_dir / "run_card_overrides.dat"
    run_applied_path = run_dir / "run_card_applied.dat"
    banner_path = run_dir / "banner.txt"
    log_path = run_dir / "madgraph_run.txt"
    lhe_path = run_dir / "unweighted_events.lhe.gz"

    run_override_text = (
        "1000 = nevents ! Number of unweighted events requested\n"
        f"{seed} = iseed ! rnd seed\n"
        "1 = lpp1 ! beam 1 type\n"
        "1 = lpp2 ! beam 2 type\n"
        "6500.0 = ebeam1 ! beam 1 total energy in GeV\n"
        "6500.0 = ebeam2 ! beam 2 total energy in GeV\n"
        "nn23lo1 = pdlabel ! PDF set\n"
        "230000 = lhaid ! LHAPDF ID\n"
        "False = fixed_ren_scale\n"
        "False = fixed_fac_scale\n"
        "-1 = dynamical_scale_choice\n"
        "1.0 = scalefact\n"
        "0 = nhel\n"
        "4 = maxjetflavor\n"
        "True = use_syst\n"
    )
    run_overrides_path.write_text(run_override_text, encoding="utf-8")

    # Generate custom param_card
    param_text = param_default.read_text(encoding="utf-8")
    lines = param_text.splitlines()
    new_lines = []
    in_frblock = False
    ghphiphi_found = False
    for line in lines:
        if line.strip().lower().startswith("block frblock"):
            in_frblock = True
            new_lines.append(line)
            continue
        if in_frblock:
            if line.strip().lower().startswith("block ") or line.strip().lower().startswith("decay "):
                in_frblock = False
            elif line.strip().startswith("3 "):
                line = f"    3 {ghphiphi_target:.17e} # GHphiphi [GeV] = -g_target"
                ghphiphi_found = True
        new_lines.append(line)

    if not ghphiphi_found:
        raise ValueError(f"Could not find Block FRBlock 3 in {param_default}")

    param_card_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")

    # Copy cards into proc_dir/Cards
    shutil.copy(param_card_path, proc_dir / "Cards" / "param_card.dat")
    shutil.copy(run_overrides_path, proc_dir / "Cards" / "run_card.dat")

    # Execute event generation in MadGraph
    mg_run_tag = f"{fmt_g_dir(g_target)}_{run_name}"
    with open(log_path, "w", encoding="utf-8") as log_fh:
        run_cmd = subprocess.run(
            ["./bin/generate_events", "-f", mg_run_tag],
            cwd=proc_dir,
            stdout=log_fh,
            stderr=subprocess.STDOUT,
            text=True,
        )

    if run_cmd.returncode != 0:
        raise RuntimeError(f"MadGraph run failed for {mg_run_tag}. See {log_path}")

    run_output_dir = proc_dir / "Events" / mg_run_tag
    raw_lhe = run_output_dir / "unweighted_events.lhe.gz"
    banner_file = run_output_dir / f"{mg_run_tag}_tag_1_banner.txt"

    shutil.copy(raw_lhe, lhe_path)
    shutil.copy(banner_file, banner_path)

    applied_run_card = extract_run_card_applied_from_banner(banner_path)
    run_applied_path.write_text(applied_run_card, encoding="utf-8")

    xsec, xsec_err = extract_madgraph_xsec(banner_path)

    # Write run_manifest.json
    run_manifest = {
        "g_hH2H2_GeV": g_target,
        "GHphiphi_GeV": ghphiphi_target,
        "run_name": run_name,
        "seed": seed,
        "sigma_pb": xsec,
        "sigma_error_pb": xsec_err,
        "banner_sha256": sha256_file(banner_path),
        "lhe_sha256": sha256_file(lhe_path),
        "event_count": 1000,
    }
    (run_dir / "run_manifest.json").write_text(json.dumps(run_manifest, indent=2) + "\n", encoding="utf-8")

    return xsec, xsec_err


def main(args: list[str] | None = None) -> int:
    parsed = parse_args(args)
    out_dir = parsed.out_dir
    g_targets = parsed.g_values if parsed.g_values else load_g_values_from_config(CONFIG_PATH)
    seeds = parsed.seeds if parsed.seeds else R12_SEEDS

    if len(seeds) != 2:
        raise ValueError(f"Expected exactly 2 seeds, got {len(seeds)}")

    mode = "execute"
    if parsed.reuse_existing:
        mode = "reuse-existing"
    elif parsed.verify_only:
        mode = "verify-only"
    elif parsed.resume:
        mode = "resume"
    elif parsed.execute:
        mode = "execute"

    print(f"=== R12 Mission: Six-g MadGraph Production Campaign Driver ===")
    print(f"Mode: {mode}")
    print(f"Output directory: {out_dir}")
    print(f"Couplings ({len(g_targets)}): {g_targets}")
    print(f"Seeds ({len(seeds)}): {seeds}")

    mg5_exec = discover_mg5_exec(parsed.mg5_exec)
    ufo_zip = discover_ufo_zip(parsed.ufo_zip)

    if mode == "execute":
        if not mg5_exec:
            raise FileNotFoundError("MadGraph executable (mg5_aMC) not found. Cannot run in --execute mode.")
        if not ufo_zip or not ufo_zip.exists():
            raise FileNotFoundError("Canonical UFO zip archive not found. Cannot run in --execute mode.")

    ufo_sha256 = sha256_file(ufo_zip) if (ufo_zip and ufo_zip.exists()) else ""

    proc_dir = out_dir / "proc_output"
    param_default = proc_dir / "Cards" / "param_card_default.dat"

    if mode in ("execute", "resume"):
        out_dir.mkdir(parents=True, exist_ok=True)
        if ufo_zip and ufo_zip.exists():
            ufo_work_dir = out_dir / "ufo"
            if not ufo_work_dir.exists():
                print(f"Unpacking UFO model from {ufo_zip} -> {ufo_work_dir}...")
                ufo_work_dir.mkdir(parents=True, exist_ok=True)
                subprocess.run(["unzip", "-q", str(ufo_zip), "-d", str(ufo_work_dir)], check=True)

            ufo_model_path = ufo_work_dir / "pi_ufo_baseline_v1_release_candidate_hotfix1" / "model" / "LLscalar_v3_UFO_runtime"

            if not proc_dir.exists() and mg5_exec:
                print("Generating MadGraph process directory 'proc_output'...")
                master_proc_card = out_dir / "proc_card_master.dat"
                master_proc_card.write_text(
                    f"import model {ufo_model_path.resolve()}\n"
                    "generate g g > H > h2 h2\n"
                    f"output {proc_dir.resolve()} -f\n",
                    encoding="utf-8",
                )
                res = subprocess.run([str(mg5_exec), str(master_proc_card)], capture_output=True, text=True)
                if res.returncode != 0 or not proc_dir.exists():
                    raise RuntimeError(f"Failed to generate MadGraph process directory:\n{res.stderr}\n{res.stdout}")

    run_records: list[dict[str, Any]] = []
    verification_results: list[dict[str, Any]] = []

    # Map of (g, run_name) -> (sigma, sigma_err)
    sigma_results: dict[tuple[float, str], tuple[float, float]] = {}

    for g in g_targets:
        g_dir_name = fmt_g_dir(g)
        g_dir = out_dir / g_dir_name

        for idx, seed in enumerate(seeds, start=1):
            run_name = f"run_{idx:02d}"
            run_dir = g_dir / run_name
            point_id = f"mg_r12_{g_dir_name}_{run_name}"
            ghphiphi = -abs(g)

            print(f"\n--- Point {point_id} (g = {g} GeV, seed = {seed}) ---")

            valid, reason = check_run_artifacts_valid(run_dir, g=g, seed=seed)

            should_run = False
            if mode == "execute":
                should_run = True
            elif mode == "resume":
                should_run = not valid
            elif mode in ("reuse-existing", "verify-only"):
                if not valid:
                    raise FileNotFoundError(f"Run {point_id} artifacts invalid/missing in {mode} mode: {reason}")

            if should_run:
                if not mg5_exec:
                    raise RuntimeError(f"Cannot execute {point_id}: MadGraph executable not available.")
                print(f"Executing physical MadGraph run for {point_id}...")
                xsec, xsec_err = execute_single_run(
                    mg5_exec=mg5_exec,
                    proc_dir=proc_dir,
                    param_default=param_default,
                    run_dir=run_dir,
                    g_target=g,
                    seed=seed,
                    run_name=run_name,
                )
            else:
                print(f"Reusing existing evidence for {point_id}...")
                banner_path = run_dir / "banner.txt"
                xsec, xsec_err = extract_madgraph_xsec(banner_path)

            banner_sha = sha256_file(run_dir / "banner.txt") if (run_dir / "banner.txt").exists() else ""
            lhe_sha = sha256_file(run_dir / "unweighted_events.lhe.gz") if (run_dir / "unweighted_events.lhe.gz").exists() else ""

            # Update run_manifest.json if needed
            manifest_path = run_dir / "run_manifest.json"
            manifest_data = {
                "point_id": point_id,
                "g_hH2H2_GeV": g,
                "GHphiphi_GeV": ghphiphi,
                "run_name": run_name,
                "seed": seed,
                "sigma_pb": xsec,
                "sigma_error_pb": xsec_err,
                "banner_sha256": banner_sha,
                "lhe_sha256": lhe_sha,
                "event_count": 1000,
            }
            if mode != "verify-only":
                manifest_path.write_text(json.dumps(manifest_data, indent=2) + "\n", encoding="utf-8")

            run_records.append({
                "point_id": point_id,
                "g_hH2H2_GeV": g,
                "GHphiphi_GeV": ghphiphi,
                "run_name": run_name,
                "seed": seed,
                "sigma_pb": xsec,
                "sigma_error_pb": xsec_err,
                "banner_sha256": banner_sha,
                "lhe_sha256": lhe_sha,
                "status": "VALID",
            })

            verification_results.append({
                "point_id": point_id,
                "valid": valid if not should_run else True,
                "reason": reason if not should_run else "Executed",
            })

            sigma_results[(g, run_name)] = (xsec, xsec_err)

    # First locate baseline g = 63.59142520075966 combined cross section
    g0_val = 63.59142520075966
    s0_r1, e0_r1 = sigma_results.get((g0_val, "run_01"), (0.0, 0.0))
    s0_r2, e0_r2 = sigma_results.get((g0_val, "run_02"), (0.0, 0.0))
    g0_combined, g0_combined_err = combine_inverse_variance(s0_r1, e0_r1, s0_r2, e0_r2)

    combined_rows: list[dict[str, Any]] = []

    for g in g_targets:
        s_r1, e_r1 = sigma_results[(g, "run_01")]
        s_r2, e_r2 = sigma_results[(g, "run_02")]
        s_comb, e_comb = combine_inverse_variance(s_r1, e_r1, s_r2, e_r2)

        s_struct = calculate_g2_prediction(g, g0=G0_GEV, sigma0=SIGMA0_PB)
        rel_res = calculate_relative_residual(s_comb, s_struct)

        scale_sq = (g / G0_GEV) ** 2
        if g0_combined > 0 and scale_sq > 0:
            ratio_g0 = (s_comb / g0_combined) / scale_sq
            rel_err_comb = (e_comb / s_comb) if s_comb > 0 else 0.0
            rel_err_g0 = (g0_combined_err / g0_combined) if g0_combined > 0 else 0.0
            ratio_err = ratio_g0 * math.sqrt(rel_err_comb**2 + rel_err_g0**2)
            pull = (ratio_g0 - 1.0) / ratio_err if ratio_err > 0 else 0.0
        else:
            ratio_g0 = 1.0
            ratio_err = 0.0
            pull = 0.0

        combined_rows.append({
            "g_hH2H2_GeV": g,
            "GHphiphi_GeV": -abs(g),
            "sigma_run_01": s_r1,
            "sigma_run_02": s_r2,
            "sigma_combined": s_comb,
            "combined_error": e_comb,
            "sigma_structural": s_struct,
            "relative_residual": rel_res,
            "ratio_to_direct_g0": ratio_g0,
            "ratio_error": ratio_err,
            "pull": pull,
        })

    if mode != "verify-only":
        # Write production_runs.csv
        runs_csv_path = out_dir / "production_runs.csv"
        with open(runs_csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(run_records[0].keys()))
            writer.writeheader()
            writer.writerows(run_records)

        # Write production_combined_vs_g.csv
        comb_csv_path = out_dir / "production_combined_vs_g.csv"
        with open(comb_csv_path, "w", newline="", encoding="utf-8") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(combined_rows[0].keys()))
            writer.writeheader()
            writer.writerows(combined_rows)

        # Write production_summary.json
        summary_data = {
            "campaign": "r12_madgraph_per_g_production",
            "g_targets": g_targets,
            "seeds": seeds,
            "total_runs": len(run_records),
            "combined_g_points": len(combined_rows),
            "ufo_sha256": ufo_sha256,
            "runs": run_records,
            "combined": combined_rows,
        }
        (out_dir / "production_summary.json").write_text(json.dumps(summary_data, indent=2) + "\n", encoding="utf-8")

        # Write artifact_manifest.json
        manifest_files = [
            "production_runs.csv",
            "production_combined_vs_g.csv",
            "production_summary.json",
            "verification_report.json",
        ]
        for g in g_targets:
            g_dir_name = fmt_g_dir(g)
            for run_name in ("run_01", "run_02"):
                for fname in ("param_card.dat", "run_card_overrides.dat", "run_card_applied.dat", "proc_card.dat", "banner.txt", "madgraph_run.txt", "unweighted_events.lhe.gz", "run_manifest.json"):
                    manifest_files.append(f"{g_dir_name}/{run_name}/{fname}")

        art_manifest: dict[str, str] = {}
        for rel_p in manifest_files:
            full_p = out_dir / rel_p
            if full_p.exists():
                art_manifest[rel_p] = sha256_file(full_p)

        (out_dir / "artifact_manifest.json").write_text(json.dumps(art_manifest, indent=2) + "\n", encoding="utf-8")

    # Write verification_report.json
    ver_report = {
        "status": "PASSED" if all(v["valid"] for v in verification_results) else "FAILED",
        "total_runs_checked": len(verification_results),
        "passed_runs": sum(1 for v in verification_results if v["valid"]),
        "results": verification_results,
    }
    if mode != "verify-only":
        (out_dir / "verification_report.json").write_text(json.dumps(ver_report, indent=2) + "\n", encoding="utf-8")

    print("\nProduction campaign complete.")
    print(f"Total runs: {len(run_records)}")
    print(f"Combined points: {len(combined_rows)}")
    print(f"Verification status: {ver_report['status']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
