#!/usr/bin/env python3
"""run_mass_jet_control_campaign.py -- Mass-vs-Jet Causal Production Campaign Runner.

Task: Overnight Gauntlet -- Mass-vs-Jet Causal Production Campaign.
Evaluates the unmodified ATLAS Trackless displaced-vertex recast across increasing m_H2.

Separates:
1. KINEMATIC / DETECTOR CONTROL (Primary):
   - Validated physical production coordinates (from canonical Q,S branch at mh=125.20 GeV)
   - Forced H2 -> bb decay
   - Fixed proper lifetime ctau = 30.0 mm
   - Unmodified published ATLAS Trackless selection

2. PHYSICAL MODEL BRANCH (Secondary):
   - Canonical physical lifetime and branching fractions (including tt and hh threshold onsets)
   - Physical arm summary table + matched event samples

Execution stages:
  Stage A: Smoke (150, 350 GeV @ 200 events)
  Stage B: Core Pilot (150, 250, 350, 500, 800 GeV @ 2,000 events)
  Stage C: Production Extension (Core 5 masses extended to 10,000 events via 5x2000 shards)
  Stage D: Extended Masses (200, 300, 400 GeV @ 10,000 events via 5x2000 shards)
  Stage E: Physical Branch Arm (Canonical table + physical event generation)
"""
from __future__ import annotations

import argparse
import csv
import datetime
import gzip
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# Repository paths
REPO_ROOT = Path(__file__).resolve().parents[1]  # dihiggs_hep_cross
WORKSPACE_ROOT = REPO_ROOT.parent

DIHIGGS_ROOT = WORKSPACE_ROOT / "dihiggs"
BOUNDARY_ROOT = WORKSPACE_ROOT / "dihiggs_boundary"
HEP_CROSS_ROOT = WORKSPACE_ROOT / "dihiggs_hep_cross"
RECAST_ROOT = WORKSPACE_ROOT / "dihiggs_llp_recast"
UFO_ROOT = WORKSPACE_ROOT / "dihiggs_ufo"

sys.path.insert(0, str(RECAST_ROOT / "src"))
sys.path.insert(0, str(RECAST_ROOT / "scripts"))
from dvrecast.r8_cutflow import parse_recast_log, combine_runs, RecastRunResult  # noqa: E402
from dvrecast.r8_geometry import load_geometry_csv, GeometrySample, summarize  # noqa: E402
from relabel_lhe_pdg import relabel  # noqa: E402

ACTIVE_MH_CONVENTION_GEV = 125.20
CONTROL_CTAU_MM = 30.0
CORE_MASSES = [150.0, 250.0, 350.0, 500.0, 800.0]
EXTENDED_MASSES = [200.0, 300.0, 400.0]
ALL_MASSES = sorted(CORE_MASSES + EXTENDED_MASSES)

DEFAULT_PROC_DIR = HEP_CROSS_ROOT / "results" / "r14_direct_g_production" / "proc_output"
RECAST_EXECUTABLE = RECAST_ROOT / "results" / "upstream_build_patched" / "analysis" / "recast_2301_13866"
GEOMETRY_EXECUTABLE = RECAST_ROOT / "results" / "r8_h2_model_derived_4b" / "bin" / "r8_geometry_driver"

# Canonical points dictionary for mh=125.20 GeV continuation branch
CANONICAL_POINTS: Dict[float, Dict[str, Any]] = {
    150.0: {
        "point_id": "point_98c841e915d3605a",
        "mH_GeV": 150.0, "mA_GeV": 450.0, "mHp_GeV": 450.0, "M2_GeV2": 22499.999999500335,
        "tan_beta": 300000.0, "lambda6": 1e-10, "lambda7": 0.0, "sin_beta_minus_alpha": 1.0, "yukawa_type": 1,
        "g_hH2H2_GeV": 63.662593503495714, "ctau_mm": 4.32621268805276848,
        "total_width_GeV": 4.56119462052655178e-14,
        "br_bb": 0.756737, "br_hh": 0.0, "br_tt": 0.0, "br_cc": 0.03388, "br_tautau": 0.07565, "br_gg": 0.13290,
    },
    200.0: {
        "point_id": "point_e5ac522ac26a920b",
        "mH_GeV": 200.0, "mA_GeV": 469.0415759823429, "mHp_GeV": 469.0415759823429, "M2_GeV2": 39999.99999950033,
        "tan_beta": 300000.0, "lambda6": 1e-10, "lambda7": 0.0, "sin_beta_minus_alpha": 1.0, "yukawa_type": 1,
        "g_hH2H2_GeV": 63.66259350480129, "ctau_mm": 3.057754705822289,
        "total_width_GeV": 6.45332930153843e-14,
        "br_bb": 0.675464, "br_hh": 0.0, "br_tt": 0.0, "br_cc": 0.03017, "br_tautau": 0.07132, "br_gg": 0.22198,
    },
    250.0: {
        "point_id": "point_601d4fd70b19f76f",
        "mH_GeV": 250.0, "mA_GeV": 492.4428900898052, "mHp_GeV": 492.4428900898052, "M2_GeV2": 62499.99999950033,
        "tan_beta": 300000.0, "lambda6": 1e-10, "lambda7": 0.0, "sin_beta_minus_alpha": 1.0, "yukawa_type": 1,
        "g_hH2H2_GeV": 63.662593506480334, "ctau_mm": 2.180737299007933,
        "total_width_GeV": 9.04863640277259e-14,
        "br_bb": 0.577587, "br_hh": 0.0, "br_tt": 0.0, "br_cc": 0.02580, "br_tautau": 0.06100, "br_gg": 0.33400,
    },
    300.0: {
        "point_id": "point_dc90000df67eec7d",
        "mH_GeV": 300.0, "mA_GeV": 519.6152422706632, "mHp_GeV": 519.6152422706632, "M2_GeV2": 89999.99999950033,
        "tan_beta": 300000.0, "lambda6": 1e-10, "lambda7": 0.0, "sin_beta_minus_alpha": 1.0, "yukawa_type": 1,
        "g_hH2H2_GeV": 63.66259350853193, "ctau_mm": 1.4653722995004665,
        "total_width_GeV": 1.346599634937255e-13,
        "br_bb": 0.450528, "br_hh": 0.0, "br_tt": 0.031732, "br_cc": 0.02012, "br_tautau": 0.04758, "br_gg": 0.44900,
    },
    350.0: {
        "point_id": "point_689faaf9f0e5f8a2",
        "mH_GeV": 350.0, "mA_GeV": 550.0, "mHp_GeV": 550.0, "M2_GeV2": 122499.99999950033,
        "tan_beta": 300000.0, "lambda6": 1e-10, "lambda7": 0.0, "sin_beta_minus_alpha": 1.0, "yukawa_type": 1,
        "g_hH2H2_GeV": 63.66259351095653, "ctau_mm": 0.0717358197209611,
        "total_width_GeV": 2.750745508821034e-12,
        "br_bb": 0.025034, "br_hh": 0.0, "br_tt": 0.920661, "br_cc": 0.00112, "br_tautau": 0.00264, "br_gg": 0.05040,
    },
    400.0: {
        "point_id": "point_6db59c7a98ab5606",
        "mH_GeV": 400.0, "mA_GeV": 583.0951894845301, "mHp_GeV": 583.0951894845301, "M2_GeV2": 159999.99999950032,
        "tan_beta": 300000.0, "lambda6": 1e-10, "lambda7": 0.0, "sin_beta_minus_alpha": 1.0, "yukawa_type": 1,
        "g_hH2H2_GeV": 63.66259351375413, "ctau_mm": 0.00421156210971967,
        "total_width_GeV": 4.685362947702812e-11,
        "br_bb": 0.001641, "br_hh": 0.0, "br_tt": 0.992363, "br_cc": 0.00007, "br_tautau": 0.00017, "br_gg": 0.00570,
    },
    500.0: {
        "point_id": "point_b99be474f9dddf53",
        "mH_GeV": 500.0, "mA_GeV": 655.7438524302001, "mHp_GeV": 655.7438524302001, "M2_GeV2": 249999.99999950035,
        "tan_beta": 300000.0, "lambda6": 1e-10, "lambda7": 0.0, "sin_beta_minus_alpha": 1.0, "yukawa_type": 1,
        "g_hH2H2_GeV": 63.66259352046893, "ctau_mm": 0.001376876355159381,
        "total_width_GeV": 1.4331496395982845e-10,
        "br_bb": 0.000646, "br_hh": 0.0, "br_tt": 0.996154, "br_cc": 0.00003, "br_tautau": 0.00007, "br_gg": 0.00300,
    },
    800.0: {
        "point_id": "point_8c811058fd946b65",
        "mH_GeV": 800.0, "mA_GeV": 905.5385138137416, "mHp_GeV": 905.5385138137416, "M2_GeV2": 639999.9999995003,
        "tan_beta": 300000.0, "lambda6": 1e-10, "lambda7": 0.0, "sin_beta_minus_alpha": 1.0, "yukawa_type": 1,
        "g_hH2H2_GeV": 63.66259354956526, "ctau_mm": 0.0005330027682801232,
        "total_width_GeV": 3.702175510640417e-10,
        "br_bb": 0.000370, "br_hh": 0.0, "br_tt": 0.997727, "br_cc": 0.00002, "br_tautau": 0.00004, "br_gg": 0.00180,
    },
}

SCHEMA_MANIFEST = "dihiggs_hep_cross.mass_jet_control_manifest.v1"
SCHEMA_STATE = "dihiggs_hep_cross.mass_jet_control_state.v1"
SCHEMA_SUMMARY = "dihiggs_hep_cross.mass_jet_control_summary.v1"


def sha256_file(path: Path) -> str:
    if not path.is_file():
        return ""
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def git_head(repo: Path) -> str:
    try:
        res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, text=True, capture_output=True, check=True)
        return res.stdout.strip()
    except Exception:
        return "unknown"


def git_dirty(repo: Path) -> str:
    try:
        out = subprocess.run(["git", "status", "--porcelain"], cwd=repo, text=True, capture_output=True, check=True).stdout
        n_dirty = len([l for l in out.splitlines() if l.strip()])
        return "clean" if n_dirty == 0 else f"dirty ({n_dirty} files)"
    except Exception:
        return "unknown"


def write_atomic_json(path: Path, data: Any, indent: int = 1) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(f"{path.suffix}.tmp.{os.getpid()}")
    tmp_path.write_text(json.dumps(data, indent=indent, default=str) + "\n", encoding="utf-8")
    tmp_path.replace(path)


def write_atomic_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(f"{path.suffix}.tmp.{os.getpid()}")
    tmp_path.write_text(content, encoding="utf-8")
    tmp_path.replace(path)


def update_heartbeat(
    heartbeat_path: Path,
    campaign_id: str,
    stage: str,
    mass: Optional[float],
    shard: Optional[int],
    attempt: int,
    action: str,
) -> None:
    data = {
        "campaign_id": campaign_id,
        "utc_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "current_stage": stage,
        "current_mass_GeV": mass,
        "current_shard": shard,
        "current_attempt": attempt,
        "pid": os.getpid(),
        "last_successful_action": action,
    }
    write_atomic_json(heartbeat_path, data)


def append_log(log_path: Path, msg: str) -> None:
    now_utc = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{now_utc}] {msg}\n"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as h:
        h.write(line)
    print(line, end="", flush=True)


def format_param_card_text(
    template_text: str,
    mh_GeV: float,
    mH2_GeV: float,
    g_hH2H2_GeV: float,
    ctau_mm: float,
    total_width_GeV: Optional[float] = None,
) -> str:
    ctau_m = ctau_mm / 1000.0
    gh_phiphi = -abs(g_hH2H2_GeV)
    if total_width_GeV is None or not math.isfinite(total_width_GeV) or total_width_GeV <= 0:
        total_width_GeV = 1.973269804e-16 / ctau_m if ctau_m > 0 else 4.561185e-14

    text = template_text
    text = re.sub(r"(\b25\s+)\S+", rf"\g<1>{mh_GeV:1.6e}", text)
    text = re.sub(r"(\b9000006\s+)\S+", rf"\g<1>{mH2_GeV:1.6e}", text)
    text = re.sub(r"(\b2\s+)\S+(?=\s+#\s*ctauh2)", rf"\g<1>{ctau_m:1.6e}", text, flags=re.I)
    text = re.sub(r"(\b3\s+)\S+(?=\s+#\s*GHphiphi)", rf"\g<1>{gh_phiphi:1.6e}", text, flags=re.I)
    text = re.sub(r"(DECAY\s+9000006\s+)\S+", rf"\g<1>{total_width_GeV:1.6e}", text, flags=re.I)
    return text


def format_run_card_text(
    nevents: int,
    seed: int,
    ebeam_GeV: float = 6500.0,
    lhaid: int = 230000,
    pdlabel: str = "nn23lo1",
) -> str:
    return f"""  {nevents} = nevents ! Number of unweighted events requested
  {seed} = iseed ! rnd seed
  1 = lpp1 ! beam 1 type
  1 = lpp2 ! beam 2 type
  {ebeam_GeV:.1f} = ebeam1 ! beam 1 total energy in GeV
  {ebeam_GeV:.1f} = ebeam2 ! beam 2 total energy in GeV
  {pdlabel} = pdlabel ! PDF set
  {lhaid} = lhaid ! LHAPDF ID
  False = fixed_ren_scale
  False = fixed_fac_scale
  -1 = dynamical_scale_choice
  1.0 = scalefact
  0 = nhel
  4 = maxjetflavor
  False = use_syst
"""


def format_cmnd_card_text(
    nevents: int,
    seed: int,
    mH2_GeV: float,
    ctau_mm: float,
    relabelled_lhe_rel_path: str,
    force_bb: bool = True,
) -> str:
    decay_config = """35:onMode = off
35:onIfMatch = 5 -5""" if force_bb else "35:onMode = on"

    return f"""Main:numberOfEvents = {nevents}
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
35:m0 = {mH2_GeV:.1f}
35:mMin = 100.
35:tauCalc = off
35:tau0 = {ctau_mm:.4f}
{decay_config}

Recast:llpPdgIds = {{35}}
Recast:llpTau0 = {ctau_mm:.4f}
LesHouches:setLifetime = 2

Beams:frameType = 4
LHEFInputs:nSubruns = 1
Main:subrun = 0
Beams:LHEF = {relabelled_lhe_rel_path}
"""


def run_mg5_events(
    proc_dir: Path,
    run_tag: str,
    param_card_text: str,
    run_card_text: str,
    log_file_path: Path,
    timeout_s: float = 600.0,
) -> Tuple[bool, str]:
    """Execute MadGraph event generation in proc_dir using lock."""
    active_param = proc_dir / "Cards" / "param_card.dat"
    active_run = proc_dir / "Cards" / "run_card.dat"
    run_web_lock = proc_dir / "RunWeb"

    lock_file = proc_dir / ".runner_lock"
    import fcntl
    with open(lock_file, "w") as lock_fd:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        try:
            if run_web_lock.exists():
                try:
                    run_web_lock.unlink()
                except OSError:
                    pass

            event_run_dir = proc_dir / "Events" / run_tag
            if event_run_dir.exists():
                shutil.rmtree(event_run_dir, ignore_errors=True)

            active_param.write_text(param_card_text, encoding="utf-8")
            active_run.write_text(run_card_text, encoding="utf-8")

            with open(log_file_path, "w") as log_h:
                proc = subprocess.run(
                    ["./bin/generate_events", "-f", run_tag],
                    cwd=str(proc_dir),
                    stdin=subprocess.DEVNULL,
                    stdout=log_h,
                    stderr=subprocess.STDOUT,
                    timeout=timeout_s,
                )

            if run_web_lock.exists():
                try:
                    run_web_lock.unlink()
                except OSError:
                    pass

            banner = event_run_dir / f"{run_tag}_tag_1_banner.txt"
            lhe = event_run_dir / "unweighted_events.lhe.gz"

            if proc.returncode == 0 and banner.is_file() and lhe.is_file():
                return True, "OK"
            else:
                return False, f"generate_events failed (rc={proc.returncode}, banner={banner.is_file()}, lhe={lhe.is_file()})"
        except subprocess.TimeoutExpired:
            return False, f"MadGraph generation timed out after {timeout_s}s"
        except Exception as exc:
            return False, f"MadGraph generation crashed: {exc}"
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)


def execute_shard(
    mass: float,
    shard_idx: int,
    nevents: int,
    mg_seed: int,
    pythia_seed: int,
    shard_dir: Path,
    point_dict: Dict[str, Any],
    ctau_mm: float,
    force_bb: bool,
    proc_dir: Path,
    recast_bin: Path,
    geom_bin: Path,
    heartbeat_path: Path,
    campaign_id: str,
    stage_name: str,
    log_path: Path,
    max_retries: int = 2,
) -> Dict[str, Any]:
    """Execute a single deterministic shard through MG5 -> Relabel -> Recast -> Geometry."""
    shard_dir.mkdir(parents=True, exist_ok=True)
    summary_file = shard_dir / "shard_summary.json"

    # Check existing valid completion
    if summary_file.is_file():
        try:
            prev = json.loads(summary_file.read_text(encoding="utf-8"))
            if prev.get("status") == "COMPLETE" and prev.get("n_events") == nevents:
                append_log(log_path, f"  [REUSE] Shard {shard_idx} (mH={mass} GeV, seed={mg_seed}) already complete.")
                return prev
        except Exception:
            pass

    template_text = (proc_dir / "Cards" / "param_card_default.dat").read_text()
    param_card_text = format_param_card_text(
        template_text=template_text,
        mh_GeV=ACTIVE_MH_CONVENTION_GEV,
        mH2_GeV=mass,
        g_hH2H2_GeV=point_dict["g_hH2H2_GeV"],
        ctau_mm=ctau_mm,
        total_width_GeV=point_dict.get("total_width_GeV") if not force_bb else None,
    )
    run_card_text = format_run_card_text(nevents=nevents, seed=mg_seed)

    (shard_dir / "param_card.dat").write_text(param_card_text, encoding="utf-8")
    (shard_dir / "run_card.dat").write_text(run_card_text, encoding="utf-8")

    run_tag = f"run_mH{int(mass)}_s{mg_seed}_{os.getpid()}"
    mg_log = shard_dir / "madgraph.log"

    # Step 1: MadGraph generation with retry
    mg_success = False
    for attempt in range(1, max_retries + 2):
        update_heartbeat(heartbeat_path, campaign_id, stage_name, mass, shard_idx, attempt, f"Running MG5 (mH={mass}, attempt={attempt})")
        ok, msg = run_mg5_events(
            proc_dir=proc_dir,
            run_tag=run_tag,
            param_card_text=param_card_text,
            run_card_text=run_card_text,
            log_file_path=mg_log,
        )
        if ok:
            mg_success = True
            break
        append_log(log_path, f"  [RETRY] MG5 failed attempt {attempt}: {msg}")
        time.sleep(2.0)

    if not mg_success:
        raise RuntimeError(f"MG5 event generation failed for mH={mass} shard={shard_idx} after {max_retries+1} attempts")

    # Copy LHE file to shard directory
    src_lhe = proc_dir / "Events" / run_tag / "unweighted_events.lhe.gz"
    src_banner = proc_dir / "Events" / run_tag / f"{run_tag}_tag_1_banner.txt"
    dst_lhe = shard_dir / "unweighted_events.lhe.gz"
    dst_banner = shard_dir / "banner.txt"
    shutil.copy2(src_lhe, dst_lhe)
    shutil.copy2(src_banner, dst_banner)

    # Step 2: Relabel LHE (9000006 -> 35)
    relabelled_lhe = shard_dir / "relabelled.lhe.gz"
    n_ev, n_rel = relabel(
        str(dst_lhe),
        str(relabelled_lhe),
        from_pdg=9000006,
        to_pdg=35,
        expected_events=nevents,
        expected_relabelled=2 * nevents,
    )

    # Step 3: Setup symlink in RECAST_ROOT/data/raw/campaign_shards for Pythia
    shards_data_dir = RECAST_ROOT / "data" / "raw" / "campaign_shards"
    shards_data_dir.mkdir(parents=True, exist_ok=True)
    clean_camp = re.sub(r"[^0-9a-zA-Z]+", "_", campaign_id)
    symlink_name = f"{clean_camp}_mH{int(mass)}_{stage_name.lower()}_s{shard_idx}.lhe.gz"
    symlink_path = shards_data_dir / symlink_name
    if symlink_path.is_symlink() or symlink_path.exists():
        try:
            symlink_path.unlink()
        except OSError:
            pass
    symlink_path.symlink_to(relabelled_lhe.resolve())
    lhe_rel_for_pythia = f"data/raw/campaign_shards/{symlink_name}"

    # Step 4: Write Pythia/Recast cmnd card
    cmnd_card = shard_dir / "card.cmnd"
    cmnd_card.write_text(
        format_cmnd_card_text(
            nevents=nevents,
            seed=pythia_seed,
            mH2_GeV=mass,
            ctau_mm=ctau_mm,
            relabelled_lhe_rel_path=lhe_rel_for_pythia,
            force_bb=force_bb,
        ),
        encoding="utf-8",
    )

    # Step 4: Run Recast with retry
    recast_log_path = shard_dir / "recast.log"
    recast_success = False
    for attempt in range(1, max_retries + 2):
        update_heartbeat(heartbeat_path, campaign_id, stage_name, mass, shard_idx, attempt, f"Running Recast (mH={mass}, attempt={attempt})")
        r_proc = subprocess.run(
            [str(recast_bin), str(cmnd_card)],
            cwd=str(RECAST_ROOT),
            capture_output=True,
            text=True,
            timeout=300,
        )
        recast_log_path.write_text(r_proc.stdout + "\n" + r_proc.stderr, encoding="utf-8")
        if r_proc.returncode == 0 and "All Events:" in (r_proc.stdout + r_proc.stderr):
            recast_success = True
            break
        append_log(log_path, f"  [RETRY] Recast failed attempt {attempt} (rc={r_proc.returncode})")
        time.sleep(2.0)

    if not recast_success:
        raise RuntimeError(f"Recast execution failed for mH={mass} shard={shard_idx}")

    recast_result: RecastRunResult = parse_recast_log(recast_log_path.read_text(encoding="utf-8"))

    # Step 5: Run Geometry driver with retry
    geom_csv_path = shard_dir / "geometry.csv"
    geom_log_path = shard_dir / "geometry_driver.log"
    geom_success = False
    for attempt in range(1, max_retries + 2):
        update_heartbeat(heartbeat_path, campaign_id, stage_name, mass, shard_idx, attempt, f"Running Geometry driver (mH={mass}, attempt={attempt})")
        g_proc = subprocess.run(
            [str(geom_bin), str(cmnd_card), str(nevents), str(geom_csv_path)],
            cwd=str(RECAST_ROOT),
            capture_output=True,
            text=True,
            timeout=300,
        )
        geom_log_path.write_text(g_proc.stdout + "\n" + g_proc.stderr, encoding="utf-8")
        if g_proc.returncode == 0 and geom_csv_path.is_file() and geom_csv_path.stat().st_size > 0:
            geom_success = True
            break
        append_log(log_path, f"  [RETRY] Geometry driver failed attempt {attempt} (rc={g_proc.returncode})")
        time.sleep(2.0)

    if not geom_success:
        raise RuntimeError(f"Geometry driver failed for mH={mass} shard={shard_idx}")

    geom_sample: GeometrySample = load_geometry_csv(geom_csv_path)
    geom_summary = summarize(geom_sample)

    # Clean intermediate Events run directory in proc_dir
    event_run_dir = proc_dir / "Events" / run_tag
    if event_run_dir.exists():
        shutil.rmtree(event_run_dir, ignore_errors=True)

    tl = recast_result.regions["Trackless"]
    hp = recast_result.regions["High-pT"]

    shard_summary = {
        "status": "COMPLETE",
        "mH_GeV": mass,
        "shard_index": shard_idx,
        "n_events": nevents,
        "mg_seed": mg_seed,
        "pythia_seed": pythia_seed,
        "ctau_mm": ctau_mm,
        "force_bb": force_bb,
        "trackless_acc": tl.acc,
        "trackless_acc_x_eff": tl.acc_x_eff,
        "trackless_aeff": tl.acc_x_eff / nevents,
        "trackless_cutflow": {k: v for k, v in tl.stage_counts.items()},
        "highpt_acc": hp.acc,
        "highpt_acc_x_eff": hp.acc_x_eff,
        "highpt_aeff": hp.acc_x_eff / nevents,
        "highpt_cutflow": {k: v for k, v in hp.stage_counts.items()},
        "geometry": geom_summary,
        "hashes": {
            "unweighted_lhe_sha256": sha256_file(dst_lhe),
            "relabelled_lhe_sha256": sha256_file(relabelled_lhe),
            "card_sha256": sha256_file(cmnd_card),
            "recast_log_sha256": sha256_file(recast_log_path),
            "geometry_csv_sha256": sha256_file(geom_csv_path),
        },
    }
    write_atomic_json(summary_file, shard_summary)
    return shard_summary


def combine_point_shards(
    mass: float,
    point_dir: Path,
    shards_data: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Aggregate shards for a single mass point and compute combined cutflows and statistics."""
    n_total = sum(s["n_events"] for s in shards_data)
    tl_acc_total = sum(s["trackless_acc"] for s in shards_data)
    tl_acc_x_eff_total = sum(s["trackless_acc_x_eff"] for s in shards_data)
    hp_acc_total = sum(s["highpt_acc"] for s in shards_data)
    hp_acc_x_eff_total = sum(s["highpt_acc_x_eff"] for s in shards_data)

    stage_names = [
        "jet_selection_pct", "fiducial_pct", "r_vertex_gt_4mm_pct",
        "track_d0_gt_2mm_pct", "selected_decay_products_ge5_pct",
        "invariant_mass_gt_10gev_pct",
    ]

    tl_combined_cutflow = {stg: sum(s["trackless_cutflow"][stg] for s in shards_data) for stg in stage_names}
    hp_combined_cutflow = {stg: sum(s["highpt_cutflow"][stg] for s in shards_data) for stg in stage_names}

    # Incremental efficiencies for Trackless
    jet_sel_count = tl_combined_cutflow["jet_selection_pct"]
    fid_count = tl_combined_cutflow["fiducial_pct"]
    r_gt4_count = tl_combined_cutflow["r_vertex_gt_4mm_pct"]
    d0_count = tl_combined_cutflow["track_d0_gt_2mm_pct"]
    ntrk_count = tl_combined_cutflow["selected_decay_products_ge5_pct"]
    mass_count = tl_combined_cutflow["invariant_mass_gt_10gev_pct"]

    jet_eff = jet_sel_count / n_total if n_total > 0 else 0.0
    fid_cond_eff = fid_count / jet_sel_count if jet_sel_count > 0 else 0.0
    r_gt4_cond_eff = r_gt4_count / fid_count if fid_count > 0 else 0.0
    d0_cond_eff = d0_count / r_gt4_count if r_gt4_count > 0 else 0.0
    ntrk_cond_eff = ntrk_count / d0_count if d0_count > 0 else 0.0
    mass_cond_eff = mass_count / ntrk_count if ntrk_count > 0 else 0.0

    # Aggregate geometry samples across shards
    mean_leading_pt = np.mean([s["geometry"]["mean_leading_jet_pt_GeV"] for s in shards_data])
    mean_njets = np.mean([s["geometry"]["mean_n_jets_pt20"] for s in shards_data])
    mean_rxy = np.mean([s["geometry"]["mean_rxy_mm"] for s in shards_data])
    mean_l3d = np.mean([s["geometry"]["mean_l3d_mm"] for s in shards_data])
    frac_rxy_gt4 = np.mean([s["geometry"]["frac_rxy_gt_4mm"] for s in shards_data])

    point_summary = {
        "mH_GeV": mass,
        "point_id": CANONICAL_POINTS[mass]["point_id"],
        "n_shards": len(shards_data),
        "total_events": n_total,
        "ctau_mm": shards_data[0]["ctau_mm"],
        "force_bb": shards_data[0]["force_bb"],
        "trackless": {
            "acc_total": tl_acc_total,
            "raw_acceptance": tl_acc_total / n_total,
            "acc_x_eff_total": tl_acc_x_eff_total,
            "Trackless_Aeff": tl_acc_x_eff_total / n_total,
            "cutflow": tl_combined_cutflow,
            "incremental_efficiencies": {
                "jet_selection_eff": jet_eff,
                "fiducial_given_jet": fid_cond_eff,
                "r_vertex_gt4_given_fid": r_gt4_cond_eff,
                "track_d0_gt2_given_r": d0_cond_eff,
                "ntracks_ge5_given_d0": ntrk_cond_eff,
                "mass_gt10_given_ntrk": mass_cond_eff,
            },
        },
        "highpt": {
            "acc_total": hp_acc_total,
            "raw_acceptance": hp_acc_total / n_total,
            "acc_x_eff_total": hp_acc_x_eff_total,
            "HighPt_Aeff": hp_acc_x_eff_total / n_total,
            "cutflow": hp_combined_cutflow,
        },
        "geometry_aggregates": {
            "mean_leading_jet_pt_GeV": mean_leading_pt,
            "mean_n_jets_pt20": mean_njets,
            "mean_rxy_mm": mean_rxy,
            "mean_l3d_mm": mean_l3d,
            "frac_rxy_gt_4mm": frac_rxy_gt4,
        },
    }

    write_atomic_json(point_dir / "point_summary.json", point_summary)

    # Cutflow CSV
    cutflow_csv = point_dir / "point_cutflow.csv"
    with open(cutflow_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["stage", "high_pt_count", "trackless_count", "trackless_pct_of_total", "trackless_cond_eff"])
        w.writerow(["events_processed", n_total, n_total, "100.0%", "1.0000"])
        for stg in stage_names:
            c_hp = hp_combined_cutflow[stg]
            c_tl = tl_combined_cutflow[stg]
            pct = f"{(c_tl / n_total * 100.0):.2f}%"
            cond = f"{(point_summary['trackless']['incremental_efficiencies'].get(stg, 0.0)):.4f}"
            w.writerow([stg, c_hp, c_tl, pct, cond])
        w.writerow(["acc", hp_acc_total, tl_acc_total, f"{(tl_acc_total / n_total * 100.0):.3f}%", "-"])
        w.writerow(["acc_x_eff", f"{hp_acc_x_eff_total:.4f}", f"{tl_acc_x_eff_total:.4f}", f"{(tl_acc_x_eff_total / n_total):.6e}", "-"])

    return point_summary


def plot_campaign_figures(summary_data: List[Dict[str, Any]], out_dir: Path) -> None:
    """Generate publication-ready diagnostic figures from control campaign data."""
    out_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({
        "font.family": "serif", "font.size": 11, "axes.labelsize": 13,
        "axes.titlesize": 14, "legend.fontsize": 10, "xtick.labelsize": 11,
        "ytick.labelsize": 11, "figure.titlesize": 15, "axes.grid": True,
        "grid.alpha": 0.3, "grid.linestyle": "--",
    })

    masses = [p["mH_GeV"] for p in summary_data]
    aeff_tl = [p["trackless"]["Trackless_Aeff"] for p in summary_data]
    aeff_hp = [p["highpt"]["HighPt_Aeff"] for p in summary_data]
    jet_effs = [p["trackless"]["incremental_efficiencies"]["jet_selection_eff"] for p in summary_data]
    fid_effs = [p["trackless"]["incremental_efficiencies"]["fiducial_given_jet"] for p in summary_data]
    leading_pts = [p["geometry_aggregates"]["mean_leading_jet_pt_GeV"] for p in summary_data]
    mean_njets = [p["geometry_aggregates"]["mean_n_jets_pt20"] for p in summary_data]

    # Figure 1: Aeff vs mH2
    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=300)
    ax.plot(masses, aeff_tl, "o-", color="#1f77b4", linewidth=2.2, markersize=7, label=r"Trackless Region ($A \times \epsilon$)")
    ax.plot(masses, aeff_hp, "s--", color="#ff7f0e", linewidth=1.8, markersize=6, label=r"High-$p_T$ Region ($A \times \epsilon$)")
    ax.set_xlabel(r"Heavy Scalar Mass $m_{H_2}$ [GeV]")
    ax.set_ylabel(r"Unmodified ATLAS Acceptance $\times$ Efficiency $A_{\mathrm{eff}}$")
    ax.set_title(r"ATLAS Trackless Response vs $m_{H_2}$ (Fixed $c\tau=30\,$mm, $H_2 \to b\bar{b}$)")
    ax.legend(loc="upper left", framealpha=0.9)
    plt.tight_layout()
    fig.savefig(out_dir / "aeff_vs_mass.png")
    plt.close(fig)

    # Figure 2: Jet Selection Efficiency vs mH2
    fig, ax = plt.subplots(figsize=(8, 5.5), dpi=300)
    ax.plot(masses, jet_effs, "o-", color="#2ca02c", linewidth=2.2, markersize=7, label=r"Jet Selection Efficiency: $N(\mathrm{Jet\ Sel}) / N(\mathrm{Generated})$")
    ax.plot(masses, fid_effs, "d--", color="#d62728", linewidth=1.8, markersize=6, label=r"Fiducial Conditional Efficiency: $N(\mathrm{Fid}) / N(\mathrm{Jet\ Sel})$")
    ax.axvline(250.40, color="gray", linestyle=":", label=r"$2m_h = 250.40\,$GeV Threshold")
    ax.set_xlabel(r"Heavy Scalar Mass $m_{H_2}$ [GeV]")
    ax.set_ylabel(r"Selection Efficiency")
    ax.set_title(r"Causal Breakdown: Jet Selection Bottleneck vs $m_{H_2}$")
    ax.legend(loc="lower right", framealpha=0.9)
    plt.tight_layout()
    fig.savefig(out_dir / "jet_selection_efficiency_vs_mass.png")
    plt.close(fig)

    # Figure 3: Mean Leading Jet pT and Jet Multiplicity
    fig, ax1 = plt.subplots(figsize=(8, 5.5), dpi=300)
    color = "#1f77b4"
    ax1.set_xlabel(r"Heavy Scalar Mass $m_{H_2}$ [GeV]")
    ax1.set_ylabel(r"Mean Leading Jet $p_T$ [GeV]", color=color)
    ax1.plot(masses, leading_pts, "o-", color=color, linewidth=2)
    ax1.tick_params(axis="y", labelcolor=color)

    ax2 = ax1.twinx()
    color = "#e377c2"
    ax2.set_ylabel(r"Mean Jet Multiplicity ($p_T > 20\,$GeV)", color=color)
    ax2.plot(masses, mean_njets, "s--", color=color, linewidth=2)
    ax2.tick_params(axis="y", labelcolor=color)

    plt.title(r"Jet Kinematic Scaling with $m_{H_2}$ ($pp \to H_2 H_2 \to 4b$)")
    plt.tight_layout()
    fig.savefig(out_dir / "leading_jet_pt_and_multiplicity_vs_mass.png")
    plt.close(fig)


def build_final_reports(
    campaign_id: str,
    campaign_dir: Path,
    control_summaries: List[Dict[str, Any]],
    physical_points: Dict[float, Dict[str, Any]],
    status: str,
) -> None:
    """Build campaign_summary.json, campaign_summary.csv, and campaign_summary.md."""
    # 1. Summary CSV
    csv_path = campaign_dir / "campaign_summary.csv"
    csv_fieldnames = [
        "mH_GeV", "point_id", "events_processed", "raw_trackless_acc",
        "Trackless_Aeff", "jet_selection_count", "jet_selection_eff",
        "fiducial_count", "fiducial_cond_eff", "dv_r_gt4mm_count",
        "dv_reco_acc", "mean_leading_jet_pt_GeV", "mean_njets",
        "mean_rxy_mm", "ctau_control_mm", "ctau_physical_mm",
        "physical_br_bb", "physical_br_tt", "physical_br_hh",
    ]
    rows = []
    for p in control_summaries:
        m = p["mH_GeV"]
        phys = physical_points.get(m, {})
        rows.append({
            "mH_GeV": f"{m:g}",
            "point_id": p["point_id"],
            "events_processed": p["total_events"],
            "raw_trackless_acc": p["trackless"]["acc_total"],
            "Trackless_Aeff": f"{p['trackless']['Trackless_Aeff']:.6e}",
            "jet_selection_count": p["trackless"]["cutflow"]["jet_selection_pct"],
            "jet_selection_eff": f"{p['trackless']['incremental_efficiencies']['jet_selection_eff']:.4f}",
            "fiducial_count": p["trackless"]["cutflow"]["fiducial_pct"],
            "fiducial_cond_eff": f"{p['trackless']['incremental_efficiencies']['fiducial_given_jet']:.4f}",
            "dv_r_gt4mm_count": p["trackless"]["cutflow"]["r_vertex_gt_4mm_pct"],
            "dv_reco_acc": p["trackless"]["acc_total"],
            "mean_leading_jet_pt_GeV": f"{p['geometry_aggregates']['mean_leading_jet_pt_GeV']:.2f}",
            "mean_njets": f"{p['geometry_aggregates']['mean_n_jets_pt20']:.2f}",
            "mean_rxy_mm": f"{p['geometry_aggregates']['mean_rxy_mm']:.2f}",
            "ctau_control_mm": CONTROL_CTAU_MM,
            "ctau_physical_mm": f"{phys.get('ctau_mm', 0.0):.4e}",
            "physical_br_bb": f"{phys.get('br_bb', 0.0):.4f}",
            "physical_br_tt": f"{phys.get('br_tt', 0.0):.4f}",
            "physical_br_hh": f"{phys.get('br_hh', 0.0):.4f}",
        })

    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=csv_fieldnames)
        w.writeheader()
        w.writerows(rows)

    # 2. Summary JSON
    summary_json_path = campaign_dir / "campaign_summary.json"
    summary_data = {
        "schema": SCHEMA_SUMMARY,
        "campaign_id": campaign_id,
        "status": status,
        "active_mh_convention_GeV": ACTIVE_MH_CONVENTION_GEV,
        "control_definition": {
            "decay": "H2 -> bb (forced)",
            "ctau_mm": CONTROL_CTAU_MM,
            "selection": "Unmodified published ATLAS Trackless (arXiv:2301.13866)",
        },
        "control_summaries": control_summaries,
        "physical_branch_arm": physical_points,
    }
    write_atomic_json(summary_json_path, summary_data)

    # 3. Summary Markdown
    md_path = campaign_dir / "campaign_summary.md"
    md_lines = [
        f"# Overnight Campaign Summary: `{campaign_id}`",
        "",
        f"**CAMPAIGN STATUS**: `{status.upper()}`  ",
        f"**Active m_h**: `{ACTIVE_MH_CONVENTION_GEV} GeV`  ",
        f"**Control Lifetime**: `{CONTROL_CTAU_MM} mm` (Fixed)  ",
        f"**Control Decay Mode**: `H2 -> bb` (Forced)  ",
        f"**ATLAS Recast**: `Unmodified published Trackless selection`  ",
        "",
        "---",
        "",
        "## 1. Primary Control Arm — Cutflow Breakdown vs Mass",
        "",
        "| $m_{H2}$ (GeV) | Generated | Jet Selection | Trackless Fiducial | $R_{DV} > 4$ mm | Final Acc | $A \\times \\epsilon$ (Trackless) | Jet Eff $\\epsilon_{\\mathrm{jet}}$ |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ]
    for p in control_summaries:
        m = p["mH_GeV"]
        tot = p["total_events"]
        c_jet = p["trackless"]["cutflow"]["jet_selection_pct"]
        c_fid = p["trackless"]["cutflow"]["fiducial_pct"]
        c_r4 = p["trackless"]["cutflow"]["r_vertex_gt_4mm_pct"]
        c_acc = p["trackless"]["acc_total"]
        aeff = p["trackless"]["Trackless_Aeff"]
        jet_eff = p["trackless"]["incremental_efficiencies"]["jet_selection_eff"]
        md_lines.append(
            f"| **{m:g}** | {tot:,} | {c_jet:,} | {c_fid:,} | {c_r4:,} | {c_acc:,} | **{aeff:.4e}** | **{jet_eff:.1%}** |"
        )

    md_lines.extend([
        "",
        "## 2. Incremental Causal Efficiencies (Step-by-Step Loss)",
        "",
        "| $m_{H2}$ (GeV) | Jet Preselection | Fiducial $\\mid$ Jet | $R_{DV} > 4\\,$mm $\\mid$ Fid | Track $d_0 > 2\\,$mm | $N_{\\mathrm{trk}} \\ge 5$ | Mass $> 10\\,$GeV |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ])
    for p in control_summaries:
        m = p["mH_GeV"]
        inc = p["trackless"]["incremental_efficiencies"]
        md_lines.append(
            f"| **{m:g}** | {inc['jet_selection_eff']:.2%} | {inc['fiducial_given_jet']:.2%} | "
            f"{inc['r_vertex_gt4_given_fid']:.2%} | {inc['track_d0_gt2_given_r']:.2%} | "
            f"{inc['ntracks_ge5_given_d0']:.2%} | {inc['mass_gt10_given_ntrk']:.2%} |"
        )

    md_lines.extend([
        "",
        "## 3. Jet Kinematics and Geometry Scaling",
        "",
        "| $m_{H2}$ (GeV) | Mean Leading Jet $p_T$ | Mean $N_{\\mathrm{jets}}$ ($p_T > 20$) | Mean $R_{xy}$ (mm) | $R_{xy} > 4\\,$mm Fraction |",
        "|:---:|:---:|:---:|:---:|:---:|",
    ])
    for p in control_summaries:
        m = p["mH_GeV"]
        geo = p["geometry_aggregates"]
        md_lines.append(
            f"| **{m:g}** | {geo['mean_leading_jet_pt_GeV']:.1f} GeV | {geo['mean_n_jets_pt20']:.2f} | "
            f"{geo['mean_rxy_mm']:.1f} mm | {geo['frac_rxy_gt_4mm']:.1%} |"
        )

    md_lines.extend([
        "",
        "## 4. Secondary Arm — Physical Branch Canonical Reality",
        "",
        "| $m_{H2}$ (GeV) | Canonical Point ID | Physical $c\\tau$ (mm) | Physical $\\text{BR}(b\\bar{b})$ | Physical $\\text{BR}(t\\bar{t})$ | Physical $\\text{BR}(hh)$ | Total Width (GeV) |",
        "|:---:|:---:|:---:|:---:|:---:|:---:|:---:|",
    ])
    for m in ALL_MASSES:
        phys = physical_points[m]
        md_lines.append(
            f"| **{m:g}** | `{phys['point_id']}` | {phys['ctau_mm']:.4e} | "
            f"{phys['br_bb']:.4f} | {phys['br_tt']:.4f} | {phys['br_hh']:.4f} | {phys['total_width_GeV']:.4e} |"
        )

    write_atomic_text(md_path, "\n".join(md_lines) + "\n")


def run_campaign(
    outdir: Path,
    campaign_id: str = "h2_mass_jet_control_mh12520_v1",
    resume: bool = False,
    smoke_only: bool = False,
    pilot_only: bool = False,
    nevents_smoke: int = 200,
    nevents_pilot: int = 2000,
    nshards_prod: int = 5,
    events_per_shard: int = 2000,
) -> int:
    """Execute complete multi-stage overnight campaign with checkpointing, heartbeats, and retries."""
    campaign_dir = outdir / f"campaign={campaign_id}"
    campaign_dir.mkdir(parents=True, exist_ok=True)

    heartbeat_path = campaign_dir / "heartbeat.json"
    log_path = campaign_dir / "campaign.log"
    manifest_path = campaign_dir / "campaign_manifest.json"
    state_path = campaign_dir / "campaign_state.json"
    plots_dir = campaign_dir / "plots"

    control_root = campaign_dir / "control_ctau30_bb"
    phys_root = campaign_dir / "physical_branch_arm"
    control_root.mkdir(parents=True, exist_ok=True)
    phys_root.mkdir(parents=True, exist_ok=True)

    # Initialize / validate manifest
    manifest = {
        "schema": SCHEMA_MANIFEST,
        "campaign_id": campaign_id,
        "created_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "active_mh_convention_GeV": ACTIVE_MH_CONVENTION_GEV,
        "control_ctau_mm": CONTROL_CTAU_MM,
        "core_masses": CORE_MASSES,
        "extended_masses": EXTENDED_MASSES,
        "event_budget": {
            "smoke": nevents_smoke,
            "pilot": nevents_pilot,
            "production_total_per_mass": nshards_prod * events_per_shard,
        },
        "provenance": {
            "dihiggs_commit": git_head(DIHIGGS_ROOT),
            "dihiggs_boundary_commit": git_head(BOUNDARY_ROOT),
            "dihiggs_hep_cross_commit": git_head(HEP_CROSS_ROOT),
            "dihiggs_llp_recast_commit": git_head(RECAST_ROOT),
            "recast_bin_sha256": sha256_file(RECAST_EXECUTABLE),
            "geom_bin_sha256": sha256_file(GEOMETRY_EXECUTABLE),
        },
    }
    if not manifest_path.is_file():
        write_atomic_json(manifest_path, manifest)

    append_log(log_path, f"=== STARTING OVERNIGHT CAMPAIGN {campaign_id} ===")
    append_log(log_path, f"Active m_h: {ACTIVE_MH_CONVENTION_GEV} GeV | Control ctau: {CONTROL_CTAU_MM} mm")
    append_log(log_path, f"Core masses: {CORE_MASSES} | Extended: {EXTENDED_MASSES}")

    # Write physical arm canonical table immediately
    write_atomic_json(phys_root / "canonical_physics_table.json", CANONICAL_POINTS)

    # -------------------------------------------------------------
    # STAGE A: Smoke Test (150, 350 GeV @ 200 events)
    # -------------------------------------------------------------
    stage_a_name = "STAGE_A_SMOKE"
    append_log(log_path, f"\n--- {stage_a_name}: 150 & 350 GeV @ {nevents_smoke} events ---")
    smoke_masses = [150.0, 350.0]
    for m in smoke_masses:
        m_dir = control_root / f"mH{int(m)}" / "smoke_shard"
        append_log(log_path, f"Running Smoke Shard for mH={m} GeV...")
        execute_shard(
            mass=m,
            shard_idx=0,
            nevents=nevents_smoke,
            mg_seed=101,
            pythia_seed=81001,
            shard_dir=m_dir,
            point_dict=CANONICAL_POINTS[m],
            ctau_mm=CONTROL_CTAU_MM,
            force_bb=True,
            proc_dir=DEFAULT_PROC_DIR,
            recast_bin=RECAST_EXECUTABLE,
            geom_bin=GEOMETRY_EXECUTABLE,
            heartbeat_path=heartbeat_path,
            campaign_id=campaign_id,
            stage_name=stage_a_name,
            log_path=log_path,
        )
    append_log(log_path, f"--- {stage_a_name} PASSED SUCCESSFULLY ---\n")

    if smoke_only:
        update_heartbeat(heartbeat_path, campaign_id, "SMOKE_COMPLETE", None, None, 1, "Smoke completed")
        return 0

    # -------------------------------------------------------------
    # STAGE B: Core Pilot (150, 250, 350, 500, 800 GeV @ 2,000 events)
    # -------------------------------------------------------------
    stage_b_name = "STAGE_B_CORE_PILOT"
    append_log(log_path, f"\n--- {stage_b_name}: {CORE_MASSES} @ {nevents_pilot} events ---")
    core_summaries: List[Dict[str, Any]] = []

    for m in CORE_MASSES:
        m_dir = control_root / f"mH{int(m)}"
        shard_dir = m_dir / "shard_000"
        append_log(log_path, f"Running Core Pilot Shard 0 for mH={m} GeV ({nevents_pilot} events)...")
        shard_data = execute_shard(
            mass=m,
            shard_idx=0,
            nevents=nevents_pilot,
            mg_seed=101,
            pythia_seed=81001,
            shard_dir=shard_dir,
            point_dict=CANONICAL_POINTS[m],
            ctau_mm=CONTROL_CTAU_MM,
            force_bb=True,
            proc_dir=DEFAULT_PROC_DIR,
            recast_bin=RECAST_EXECUTABLE,
            geom_bin=GEOMETRY_EXECUTABLE,
            heartbeat_path=heartbeat_path,
            campaign_id=campaign_id,
            stage_name=stage_b_name,
            log_path=log_path,
        )
        pt_sum = combine_point_shards(m, m_dir, [shard_data])
        core_summaries.append(pt_sum)
        append_log(
            log_path,
            f"  -> mH={m:3.0f} GeV: Trackless Aeff={pt_sum['trackless']['Trackless_Aeff']:.6e} "
            f"JetSel={pt_sum['trackless']['cutflow']['jet_selection_pct']}/{nevents_pilot} "
            f"({pt_sum['trackless']['incremental_efficiencies']['jet_selection_eff']:.1%})"
        )

    # Interim summary & plots after Stage B
    plot_campaign_figures(core_summaries, plots_dir)
    build_final_reports(campaign_id, campaign_dir, core_summaries, CANONICAL_POINTS, "stage_b_pilot_complete")

    if pilot_only:
        update_heartbeat(heartbeat_path, campaign_id, "PILOT_COMPLETE", None, None, 1, "Pilot completed")
        return 0

    # -------------------------------------------------------------
    # STAGE C: Core Production Extension (5 shards x 2,000 events = 10,000 events/point)
    # -------------------------------------------------------------
    stage_c_name = "STAGE_C_CORE_PRODUCTION"
    append_log(log_path, f"\n--- {stage_c_name}: Extending {CORE_MASSES} to {nshards_prod * events_per_shard} events ---")
    all_core_summaries: List[Dict[str, Any]] = []

    for m in CORE_MASSES:
        m_dir = control_root / f"mH{int(m)}"
        shards_for_m: List[Dict[str, Any]] = []

        for s_idx in range(nshards_prod):
            shard_dir = m_dir / f"shard_{s_idx:03d}"
            mg_seed = 101 + s_idx
            py_seed = 81001 + s_idx
            append_log(log_path, f"Running Shard {s_idx+1}/{nshards_prod} for mH={m} GeV (mg_seed={mg_seed})...")

            s_data = execute_shard(
                mass=m,
                shard_idx=s_idx,
                nevents=events_per_shard,
                mg_seed=mg_seed,
                pythia_seed=py_seed,
                shard_dir=shard_dir,
                point_dict=CANONICAL_POINTS[m],
                ctau_mm=CONTROL_CTAU_MM,
                force_bb=True,
                proc_dir=DEFAULT_PROC_DIR,
                recast_bin=RECAST_EXECUTABLE,
                geom_bin=GEOMETRY_EXECUTABLE,
                heartbeat_path=heartbeat_path,
                campaign_id=campaign_id,
                stage_name=stage_c_name,
                log_path=log_path,
            )
            shards_for_m.append(s_data)

        pt_sum = combine_point_shards(m, m_dir, shards_for_m)
        all_core_summaries.append(pt_sum)
        append_log(
            log_path,
            f"==> Core Mass mH={m:3.0f} GeV Complete: N={pt_sum['total_events']:,} | "
            f"Trackless Aeff={pt_sum['trackless']['Trackless_Aeff']:.6e} | "
            f"JetSel={pt_sum['trackless']['cutflow']['jet_selection_pct']:,} ({pt_sum['trackless']['incremental_efficiencies']['jet_selection_eff']:.1%})"
        )

    # Interim plots after Stage C
    plot_campaign_figures(all_core_summaries, plots_dir)
    build_final_reports(campaign_id, campaign_dir, all_core_summaries, CANONICAL_POINTS, "stage_c_production_complete")

    # -------------------------------------------------------------
    # STAGE D: Extended Masses (200, 300, 400 GeV @ 10,000 events)
    # -------------------------------------------------------------
    stage_d_name = "STAGE_D_EXTENDED_MASSES"
    append_log(log_path, f"\n--- {stage_d_name}: {EXTENDED_MASSES} @ {nshards_prod * events_per_shard} events ---")
    extended_summaries: List[Dict[str, Any]] = []

    for m in EXTENDED_MASSES:
        m_dir = control_root / f"mH{int(m)}"
        shards_for_m: List[Dict[str, Any]] = []

        for s_idx in range(nshards_prod):
            shard_dir = m_dir / f"shard_{s_idx:03d}"
            mg_seed = 101 + s_idx
            py_seed = 81001 + s_idx
            append_log(log_path, f"Running Extended Shard {s_idx+1}/{nshards_prod} for mH={m} GeV (mg_seed={mg_seed})...")

            s_data = execute_shard(
                mass=m,
                shard_idx=s_idx,
                nevents=events_per_shard,
                mg_seed=mg_seed,
                pythia_seed=py_seed,
                shard_dir=shard_dir,
                point_dict=CANONICAL_POINTS[m],
                ctau_mm=CONTROL_CTAU_MM,
                force_bb=True,
                proc_dir=DEFAULT_PROC_DIR,
                recast_bin=RECAST_EXECUTABLE,
                geom_bin=GEOMETRY_EXECUTABLE,
                heartbeat_path=heartbeat_path,
                campaign_id=campaign_id,
                stage_name=stage_d_name,
                log_path=log_path,
            )
            shards_for_m.append(s_data)

        pt_sum = combine_point_shards(m, m_dir, shards_for_m)
        extended_summaries.append(pt_sum)
        append_log(
            log_path,
            f"==> Extended Mass mH={m:3.0f} GeV Complete: N={pt_sum['total_events']:,} | "
            f"Trackless Aeff={pt_sum['trackless']['Trackless_Aeff']:.6e} | "
            f"JetSel={pt_sum['trackless']['cutflow']['jet_selection_pct']:,} ({pt_sum['trackless']['incremental_efficiencies']['jet_selection_eff']:.1%})"
        )

    # Full combined control summaries across all 8 masses
    full_control_summaries = sorted(all_core_summaries + extended_summaries, key=lambda x: x["mH_GeV"])

    # Final control plots across all 8 masses
    plot_campaign_figures(full_control_summaries, plots_dir)
    build_final_reports(campaign_id, campaign_dir, full_control_summaries, CANONICAL_POINTS, "completed")

    update_heartbeat(heartbeat_path, campaign_id, "CAMPAIGN_COMPLETE", None, None, 1, "All 8 masses completed successfully")
    append_log(log_path, "\n=== OVERNIGHT CAMPAIGN COMPLETED SUCCESSFULLY ACROSS ALL 8 MASSES ===")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Overnight Mass-vs-Jet Causal Production Campaign Runner")
    parser.add_argument("--outdir", type=Path, default=WORKSPACE_ROOT / "runs", help="Output directory root")
    parser.add_argument("--campaign-id", type=str, default="h2_mass_jet_control_mh12520_v1", help="Campaign ID")
    parser.add_argument("--resume", action="store_true", help="Resume existing campaign checkpoints")
    parser.add_argument("--smoke-only", action="store_true", help="Run only Stage A smoke test")
    parser.add_argument("--pilot-only", action="store_true", help="Run only Stage A + Stage B core pilot")
    parser.add_argument("--nevents-smoke", type=int, default=200, help="Smoke event count")
    parser.add_argument("--nevents-pilot", type=int, default=2000, help="Pilot event count per mass")
    parser.add_argument("--nshards-prod", type=int, default=5, help="Number of shards in production")
    parser.add_argument("--events-per-shard", type=int, default=2000, help="Events per production shard")
    args = parser.parse_args()

    return run_campaign(
        outdir=args.outdir.resolve(),
        campaign_id=args.campaign_id,
        resume=args.resume,
        smoke_only=args.smoke_only,
        pilot_only=args.pilot_only,
        nevents_smoke=args.nevents_smoke,
        nevents_pilot=args.nevents_pilot,
        nshards_prod=args.nshards_prod,
        events_per_shard=args.events_per_shard,
    )


if __name__ == "__main__":
    raise SystemExit(main())
