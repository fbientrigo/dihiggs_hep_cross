#!/usr/bin/env python3
"""R10 Phase 3: ctau efficiency scan using Pythia + ATLAS DV+jets recast.

Runs the validated ATLAS DV+jets recast binary against relabelled H2H2 production
samples for all 8 ctau points (2 seeds x 1000 events = 2000 events per ctau).
Computes Trackless_Aeff and HighPt_Aeff with statistical uncertainties.
"""

from __future__ import annotations

import csv
import hashlib
import json
import math
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = REPO_ROOT / "configs" / "r10_effective_scan.json"
OUT_DIR = REPO_ROOT / "results" / "r10_effective_ctau_g_br_scan"
CARDS_DIR = OUT_DIR / "cards"
LOGS_DIR = OUT_DIR / "logs"

# Paths to the validated recast binary and relabelled LHE files
RECAST_EXE = Path(
    "/home/fabi/atlas_dihiggs/_worktrees/r8-h2-model-derived-recast/results/upstream_build_patched/analysis/recast_2301_13866"
)
LHE_RUN01 = Path(
    "/home/fabi/atlas_dihiggs/_worktrees/r8-h2-model-derived-recast/data/raw/r8_h2_model_derived_4b/relabelled_run_01.lhe.gz"
)
LHE_RUN02 = Path(
    "/home/fabi/atlas_dihiggs/_worktrees/r8-h2-model-derived-recast/data/raw/r8_h2_model_derived_4b/relabelled_run_02.lhe.gz"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def ctau_tag(ctau_mm: float) -> str:
    s = f"{ctau_mm:.16g}".replace(".", "p")
    return f"ctau_{s}"


def parse_recast_output(log_text: str) -> dict[str, float]:
    """Parse stdout of recast_2301_13866 for cutflow metrics."""
    res = {}
    for line in log_text.splitlines():
        line = line.strip()
        if ":" in line:
            parts = line.split(":", 1)
            key = parts[0].strip()
            val_str = parts[1].strip()
            try:
                val = float(val_str.split()[0])
                res[key] = val
            except (ValueError, IndexError):
                pass
    return res


def write_cmnd_card(path: Path, ctau_mm: float, seed: int, lhe_path: Path) -> None:
    content = f"""! R10 Effective scan card: H2 H2 -> b b~ b b~, ctau = {ctau_mm:.16g} mm
Main:numberOfEvents = 1000
Main:timesAllowErrors = 3
Init:showChangedSettings = on
Init:showChangedParticleData = off
Next:numberCount = 5000
Next:numberShowInfo = 0
Next:numberShowProcess = 0
Next:numberShowEvent = 0

Random:setSeed = on
Random:seed = {seed}

PartonLevel:MPI = off
PartonLevel:ISR = on
PartonLevel:FSR = on
HadronLevel:Hadronize = on
Tune:pp = 21

Higgs:useBSM = on
35:m0 = 150.
35:mMin = 100.
35:tauCalc = off
35:tau0 = {ctau_mm:.16g}
35:onMode = off
35:onIfMatch = 5 -5

Recast:llpPdgIds = {{35}}
Recast:llpTau0 = {ctau_mm:.16g}
LesHouches:setLifetime = 2

Beams:frameType = 4
LHEFInputs:nSubruns = 1
Main:subrun = 0
Beams:LHEF = {lhe_path.resolve()}
"""
    path.write_text(content, encoding="utf-8")


def run_recast_single(card_path: Path, log_path: Path) -> dict[str, float]:
    if log_path.exists() and log_path.stat().st_size > 0:
        return parse_recast_output(log_path.read_text(encoding="utf-8"))
    proc = subprocess.run(
        [str(RECAST_EXE), str(card_path)],
        cwd=RECAST_EXE.parent,
        capture_output=True,
        text=True,
    )
    log_path.write_text(proc.stdout + "\n" + proc.stderr, encoding="utf-8")
    if proc.returncode != 0:
        raise RuntimeError(f"recast_2301_13866 failed on {card_path} with exit code {proc.returncode}")
    return parse_recast_output(proc.stdout)


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    ctau_values = config["grid"]["ctau_mm"]
    hbar_c = config["hbar_c_GeV_mm"]

    CARDS_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "ctau_mm",
        "total_width_GeV",
        "generated_events",
        "selected_trackless_events",
        "Trackless_Aeff",
        "Trackless_Aeff_stat_uncertainty",
        "selected_highpt_events",
        "HighPt_Aeff",
        "Trackless_status",
        "HighPt_status",
        "provenance_path",
    ]

    rows = []
    print(f"Running ctau efficiency scan for {len(ctau_values)} ctau values...")

    for ctau in ctau_values:
        tag = ctau_tag(ctau)
        width_gev = hbar_c / ctau

        card1 = CARDS_DIR / f"{tag}_run01.cmnd"
        card2 = CARDS_DIR / f"{tag}_run02.cmnd"
        log1 = LOGS_DIR / f"{tag}_run01.log"
        log2 = LOGS_DIR / f"{tag}_run02.log"

        write_cmnd_card(card1, ctau, seed=81001, lhe_path=LHE_RUN01)
        write_cmnd_card(card2, ctau, seed=81002, lhe_path=LHE_RUN02)

        out1 = run_recast_single(card1, log1)
        out2 = run_recast_single(card2, log2)

        # Parse Acc and Acc x Eff
        acc_tl1 = out1.get("Trackless Acc", 0.0)
        acc_tl2 = out2.get("Trackless Acc", 0.0)
        aeff_tl1 = out1.get("Trackless Acc x Eff", 0.0)
        aeff_tl2 = out2.get("Trackless Acc x Eff", 0.0)

        acc_hp1 = out1.get("High-pT Acc", 0.0)
        acc_hp2 = out2.get("High-pT Acc", 0.0)
        aeff_hp1 = out1.get("High-pT Acc x Eff", 0.0)
        aeff_hp2 = out2.get("High-pT Acc x Eff", 0.0)

        n_gen = 2000
        n_tl_sel = int(round(acc_tl1 + acc_tl2))
        n_hp_sel = int(round(acc_hp1 + acc_hp2))

        trackless_aeff = (aeff_tl1 + aeff_tl2) / n_gen
        highpt_aeff = (aeff_hp1 + aeff_hp2) / n_gen

        # Statistical uncertainty: binomial / Poisson on selected events
        if trackless_aeff > 0:
            trackless_aeff_unc = trackless_aeff * math.sqrt(max(1, n_tl_sel)) / max(1, n_tl_sel)
        else:
            trackless_aeff_unc = 1.0 / n_gen

        tl_status = "VALIDATED" if n_tl_sel >= 10 else "LOW_MC_STATISTICS"
        hp_status = "VALIDATED" if n_hp_sel >= 10 else "INSUFFICIENT_MC_STATISTICS"

        provenance = LOGS_DIR / f"{tag}_summary.json"
        summary_data = {
            "ctau_mm": ctau,
            "total_width_GeV": width_gev,
            "generated_events": n_gen,
            "run01": {
                "card": str(card1.relative_to(REPO_ROOT)),
                "card_sha256": sha256_file(card1),
                "log": str(log1.relative_to(REPO_ROOT)),
                "log_sha256": sha256_file(log1),
                "trackless_acc": acc_tl1,
                "trackless_acc_x_eff": aeff_tl1,
            },
            "run02": {
                "card": str(card2.relative_to(REPO_ROOT)),
                "card_sha256": sha256_file(card2),
                "log": str(log2.relative_to(REPO_ROOT)),
                "log_sha256": sha256_file(log2),
                "trackless_acc": acc_tl2,
                "trackless_acc_x_eff": aeff_tl2,
            },
            "combined": {
                "selected_trackless_events": n_tl_sel,
                "Trackless_Aeff": trackless_aeff,
                "Trackless_Aeff_stat_uncertainty": trackless_aeff_unc,
                "selected_highpt_events": n_hp_sel,
                "HighPt_Aeff": highpt_aeff,
                "Trackless_status": tl_status,
                "HighPt_status": hp_status,
            },
        }
        provenance.write_text(json.dumps(summary_data, indent=2) + "\n", encoding="utf-8")

        rows.append(
            {
                "ctau_mm": f"{ctau:.16g}",
                "total_width_GeV": f"{width_gev:.16e}",
                "generated_events": n_gen,
                "selected_trackless_events": n_tl_sel,
                "Trackless_Aeff": f"{trackless_aeff:.16g}",
                "Trackless_Aeff_stat_uncertainty": f"{trackless_aeff_unc:.16g}",
                "selected_highpt_events": n_hp_sel,
                "HighPt_Aeff": f"{highpt_aeff:.16g}",
                "Trackless_status": tl_status,
                "HighPt_status": hp_status,
                "provenance_path": str(provenance.relative_to(REPO_ROOT)),
            }
        )

        print(
            f"  ctau = {ctau:8.3f} mm -> Trackless_Aeff = {trackless_aeff:.6f} "
            f"+/- {trackless_aeff_unc:.6f} (sel={n_tl_sel}, status={tl_status})"
        )

    out_csv = OUT_DIR / "efficiency_vs_ctau.csv"
    with open(out_csv, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"[OK] Wrote {out_csv} ({len(rows)} ctau points)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
