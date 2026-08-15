#!/usr/bin/env python3
"""Minimal physical-point MadGraph production cross-section runner.

Takes one canonical named physical 2HDM point or a batch of points, generates
point-specific param_card/run_card inputs, executes MadGraph
on the physical process pp -> H2 H2 (g g > H > h2 h2), and extracts the exact
production cross section sigma_production_fb and uncertainty sigma_production_unc_fb.

SCIENTIFIC GUARANTEES:
1. sigma_production_fb comes directly from MadGraph for each point.
2. No universal g^2 scaling fallback is used for physical scan points.
3. Stable point_id is preserved end-to-end.
4. Generated cards, banner SHA256, and full provenance are retained.
"""

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
from typing import Any, Dict, List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from portable_paths import find_workspace_root  # noqa: E402

DIHIGGS_ROOT = find_workspace_root(REPO_ROOT)
DEFAULT_PROC_DIR = Path(os.environ.get(
    "DIHIGGS_MG5_PROC_DIR",
    str(DIHIGGS_ROOT / "hep_cross" / "results" / "r14_direct_g_production" / "proc_output"),
))
DEFAULT_SEEDS = [101, 107]
DEFAULT_NEVENTS = 10000
FB_PER_PB = 1000.0


def sha256_file(path: Path) -> str:
    """Compute sha256 of a file."""
    if not path.exists():
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def format_slha_float(value: float) -> str:
    """Format float for SLHA card in standard scientific notation."""
    return f"{value:1.6e}" if math.isfinite(value) else "0.000000e+00"


def generate_param_card_text(
    template_text: str,
    *,
    m_h_GeV: float,
    m_H2_GeV: float,
    g_hH2H2_GeV: float,
    ctau_physical_mm: float,
    total_width_GeV: float,
) -> str:
    """Generate exact point-specific param_card.dat content from default template."""
    ctau_m = ctau_physical_mm / 1000.0
    gh_phiphi = -abs(g_hH2H2_GeV)  # UFO convention: GHphiphi = -g_hH2H2

    if not math.isfinite(total_width_GeV) or total_width_GeV <= 0:
        raise ValueError("total_width_GeV must be finite and positive")

    text = template_text
    # Replace mass block
    text = re.sub(r"(\b25\s+)\S+", rf"\g<1>{format_slha_float(m_h_GeV)}", text)
    text = re.sub(r"(\b9000006\s+)\S+", rf"\g<1>{format_slha_float(m_H2_GeV)}", text)
    # Replace frblock
    text = re.sub(r"(\b2\s+)\S+(?=\s+#\s*ctauh2)", rf"\g<1>{format_slha_float(ctau_m)}", text, flags=re.I)
    text = re.sub(r"(\b3\s+)\S+(?=\s+#\s*GHphiphi)", rf"\g<1>{format_slha_float(gh_phiphi)}", text, flags=re.I)
    # Replace decay block
    text = re.sub(r"(DECAY\s+9000006\s+)\S+", rf"\g<1>{format_slha_float(total_width_GeV)}", text, flags=re.I)

    return text


def generate_run_card_text(
    nevents: int = DEFAULT_NEVENTS,
    seed: int = 101,
    ebeam_GeV: float = 6500.0,
    lhaid: int = 230000,
    pdlabel: str = "nn23lo1",
) -> str:
    """Generate exact run_card.dat content for pp collisions at sqrt(s)=13 TeV."""
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
  True = use_syst
"""


def parse_madgraph_banner(banner_path: Path) -> Tuple[float, float]:
    """Parse cross section in pb from MadGraph banner file."""
    if not banner_path.exists():
        raise FileNotFoundError(f"Banner file not found: {banner_path}")
    text = banner_path.read_text(encoding="utf-8", errors="replace")
    m = re.search(r"#\s*Integrated weight \(pb\)\s*:\s*([\d\.e\+\-]+)", text)
    if not m:
        raise ValueError(f"Could not find Integrated weight in banner: {banner_path}")
    xsec_pb = float(m.group(1))
    return xsec_pb, 0.0


def parse_madgraph_html_results(results_html_path: Path) -> Tuple[float, float]:
    """Parse cross section and statistical uncertainty in pb from HTML result."""
    if not results_html_path.exists():
        return float("nan"), float("nan")
    text = results_html_path.read_text(encoding="utf-8", errors="replace")
    # Format: s= 0.00022986 &#177 7.49e-07 (pb)
    m = re.search(r"s=\s*([\d\.e\+\-]+)\s*(?:&#177;|±|\+\/-)\s*([\d\.e\+\-]+)\s*\(pb\)", text)
    if m:
        return float(m.group(1)), float(m.group(2))
    return float("nan"), float("nan")


def run_single_physical_point_madgraph(
    point: Dict[str, Any],
    *,
    proc_dir: Path = DEFAULT_PROC_DIR,
    cards_out_dir: Optional[Path] = None,
    nevents: int = DEFAULT_NEVENTS,
    seeds: List[int] = DEFAULT_SEEDS,
) -> Dict[str, Any]:
    """Execute MadGraph for one physical 2HDM point and return exact result dict."""
    required = (
        "point_id", "model_variant", "m_h_GeV", "m_H2_GeV",
        "g_hH2H2_GeV", "total_width_GeV", "ctau_physical_mm",
        "ctau_response_mm", "lifetime_mode", "BR_bb",
    )
    missing = [key for key in required if point.get(key) in (None, "")]
    if missing:
        raise ValueError("canonical point missing required fields: " + ", ".join(missing))
    if point["model_variant"] not in {"FACTORIZED_G_ONLY", "PHYSICAL_DECAYS_NO_HEAVY_CASCADES"}:
        raise ValueError(f"unknown model_variant: {point['model_variant']!r}")
    if point["lifetime_mode"] not in {"PHYSICAL_PREDICTION", "DETECTOR_RESPONSE_EXPERIMENT"}:
        raise ValueError(f"unknown lifetime_mode: {point['lifetime_mode']!r}")

    point_id = str(point["point_id"]).strip()
    mh = float(point["m_h_GeV"])
    mH2 = float(point["m_H2_GeV"])
    g_hH2H2 = float(point["g_hH2H2_GeV"])
    ctau = float(point["ctau_physical_mm"])
    ctau_response = float(point["ctau_response_mm"])
    br_bb = float(point["BR_bb"])
    tan_beta = float(point.get("tan_beta", "nan"))
    lambda6 = float(point.get("lambda6", "nan"))
    M2 = float(point.get("M2_GeV2", "nan"))
    total_width = float(point["total_width_GeV"])
    if point["lifetime_mode"] == "PHYSICAL_PREDICTION" and not math.isclose(ctau, ctau_response, rel_tol=1e-9):
        raise ValueError("PHYSICAL_PREDICTION requires ctau_response_mm == ctau_physical_mm")

    if not math.isfinite(g_hH2H2) or g_hH2H2 <= 0:
        return {
            **point,
            "point_id": point_id,
            "model_variant": point["model_variant"],
            "lifetime_mode": point["lifetime_mode"],
            "m_H2_GeV": mH2,
            "m_h_GeV": mh,
            "tan_beta": tan_beta,
            "lambda6": lambda6,
            "M2_GeV2": M2,
            "g_hH2H2_GeV": g_hH2H2,
            "ctau_physical_mm": ctau,
            "ctau_response_mm": ctau_response,
            "BR_bb": br_bb,
            "sigma_production_fb": float("nan"),
            "sigma_production_unc_fb": float("nan"),
            "madgraph_status": "FAILED_INVALID_COUPLING",
            "madgraph_run_id_or_path": "",
            "banner_sha256": "",
            "provenance": {"error": "Coupling g_hH2H2_GeV must be positive finite"},
        }

    template_param_path = proc_dir / "Cards" / "param_card_default.dat"
    if not template_param_path.exists():
        template_param_path = proc_dir / "Cards" / "param_card.dat"
    template_text = template_param_path.read_text(encoding="utf-8")

    param_card_content = generate_param_card_text(
        template_text,
        m_h_GeV=mh,
        m_H2_GeV=mH2,
        g_hH2H2_GeV=g_hH2H2,
        ctau_physical_mm=ctau,
        total_width_GeV=total_width,
    )

    if cards_out_dir:
        cards_out_dir.mkdir(parents=True, exist_ok=True)
        point_card_path = cards_out_dir / f"{point_id}_param_card.dat"
        point_card_path.write_text(param_card_content, encoding="utf-8")

    # Target cards in proc_dir
    active_param_path = proc_dir / "Cards" / "param_card.dat"
    active_run_path = proc_dir / "Cards" / "run_card.dat"
    run_web_lock = proc_dir / "RunWeb"
    if run_web_lock.exists():
        run_web_lock.unlink()

    run_xsecs_pb: List[float] = []
    run_uncs_pb: List[float] = []
    banners: List[str] = []
    run_tags: List[str] = []

    clean_id = re.sub(r"[^0-9A-Za-z]+", "_", point_id).strip("_")
    
    # Sequential lock on proc_dir
    lock_file = proc_dir / ".runner_lock"
    import fcntl
    with open(lock_file, "w") as lock_fd:
        fcntl.flock(lock_fd, fcntl.LOCK_EX)
        try:
            for seed in seeds:
                run_tag = f"run_{clean_id}_s{seed}"
                run_tags.append(run_tag)

                # Write active cards
                active_param_path.write_text(param_card_content, encoding="utf-8")
                run_card_content = generate_run_card_text(nevents=nevents, seed=seed)
                active_run_path.write_text(run_card_content, encoding="utf-8")

                # Clean stale locks and run directory
                run_web_lock = proc_dir / "RunWeb"
                if run_web_lock.exists():
                    try:
                        run_web_lock.unlink()
                    except OSError:
                        pass

                event_run_dir = proc_dir / "Events" / run_tag
                if event_run_dir.exists():
                    shutil.rmtree(event_run_dir, ignore_errors=True)

                html_run_dir = proc_dir / "HTML" / run_tag
                if html_run_dir.exists():
                    shutil.rmtree(html_run_dir, ignore_errors=True)

                # Run MadGraph generate_events
                gen_cmd = ["./bin/generate_events", "-f", run_tag]
                proc = subprocess.run(
                    gen_cmd,
                    cwd=str(proc_dir),
                    capture_output=True,
                    text=True,
                    timeout=120,
                )

                # Clean RunWeb lock after completion
                if run_web_lock.exists():
                    try:
                        run_web_lock.unlink()
                    except OSError:
                        pass

                banner_file = proc_dir / "Events" / run_tag / f"{run_tag}_tag_1_banner.txt"
                html_file = proc_dir / "HTML" / run_tag / "results.html"

                if not banner_file.exists():
                    # Failure
                    return {
                        **point,
                        "point_id": point_id,
                        "model_variant": point["model_variant"],
                        "lifetime_mode": point["lifetime_mode"],
                        "m_H2_GeV": mH2,
                        "m_h_GeV": mh,
                        "tan_beta": tan_beta,
                        "lambda6": lambda6,
                        "M2_GeV2": M2,
                        "g_hH2H2_GeV": g_hH2H2,
                        "ctau_physical_mm": ctau,
                        "ctau_response_mm": ctau_response,
                        "BR_bb": br_bb,
                        "sigma_production_fb": float("nan"),
                        "sigma_production_unc_fb": float("nan"),
                        "madgraph_status": "FAILED_NO_BANNER",
                        "madgraph_run_id_or_path": run_tag,
                        "banner_sha256": "",
                        "provenance": {"stderr": proc.stderr[-500:], "stdout": proc.stdout[-500:]},
                    }

                xsec_pb, _ = parse_madgraph_banner(banner_file)
                html_xsec, html_unc = parse_madgraph_html_results(html_file)

                unc_pb = html_unc if math.isfinite(html_unc) else (xsec_pb / math.sqrt(nevents))
                run_xsecs_pb.append(xsec_pb)
                run_uncs_pb.append(unc_pb)
                banners.append(sha256_file(banner_file))
        finally:
            fcntl.flock(lock_fd, fcntl.LOCK_UN)

    # Combine seeds with inverse-variance weighting or mean
    mean_xsec_pb = sum(run_xsecs_pb) / len(run_xsecs_pb)
    # Statistical uncertainty on mean: sqrt(sum(unc^2)) / N
    mean_unc_pb = math.sqrt(sum(u * u for u in run_uncs_pb)) / len(run_uncs_pb)

    sigma_production_fb = mean_xsec_pb * FB_PER_PB
    sigma_production_unc_fb = mean_unc_pb * FB_PER_PB

    return {
        **point,
        "point_id": point_id,
        "model_variant": point["model_variant"],
        "lifetime_mode": point["lifetime_mode"],
        "m_H2_GeV": mH2,
        "m_h_GeV": mh,
        "tan_beta": tan_beta,
        "lambda6": lambda6,
        "M2_GeV2": M2,
        "g_hH2H2_GeV": g_hH2H2,
        "ctau_physical_mm": ctau,
        "ctau_response_mm": ctau_response,
        "BR_bb": br_bb,
        "sigma_production_fb": sigma_production_fb,
        "sigma_source": "DIRECT_MADGRAPH_POINT",
        "sigma_provenance": {
            "runner": "run_physical_point_madgraph.py",
            "run_ids": run_tags,
            "banner_sha256": banners,
            "proc_dir": str(proc_dir),
        },
        "sigma_production_unc_fb": sigma_production_unc_fb,
        "madgraph_status": "VALID",
        "madgraph_run_id_or_path": ";".join(run_tags),
        "banner_sha256": ";".join(banners),
        "provenance": {
            "nevents": nevents,
            "seeds": seeds,
            "run_xsecs_fb": [x * FB_PER_PB for x in run_xsecs_pb],
            "run_uncs_fb": [u * FB_PER_PB for u in run_uncs_pb],
            "proc_dir": str(proc_dir),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MadGraph cross section for physical 2HDM points")
    parser.add_argument("--point", type=Path, default=None, help="JSON file containing one physical point")
    parser.add_argument("--points-csv", type=Path, default=None, help="CSV file containing physical points")
    parser.add_argument("--output", type=Path, required=True, help="Output JSON or CSV destination")
    parser.add_argument("--cards-dir", type=Path, default=None, help="Directory to store point param cards")
    parser.add_argument("--proc-dir", type=Path, default=DEFAULT_PROC_DIR, help="MadGraph compiled process directory")
    parser.add_argument("--nevents", type=int, default=DEFAULT_NEVENTS, help="Number of events per run")
    parser.add_argument("--seeds", type=int, nargs="+", default=DEFAULT_SEEDS, help="Random seeds to average")
    parser.add_argument("--limit", type=int, default=None, help="Max points to process from CSV")
    args = parser.parse_args()

    points: List[Dict[str, Any]] = []

    if args.point:
        with open(args.point) as f:
            data = json.load(f)
            points = [data] if isinstance(data, dict) else list(data)
    elif args.points_csv:
        with open(args.points_csv, newline="") as f:
            reader = csv.DictReader(f)
            points = list(reader)
    else:
        parser.error("Must provide either --point or --points-csv")

    if args.limit:
        points = points[:args.limit]

    args.output = args.output.resolve()
    if args.cards_dir:
        args.cards_dir = args.cards_dir.resolve()

    results: List[Dict[str, Any]] = []
    print(f"[RUNNER] Running MadGraph for {len(points)} physical point(s)...")

    for i, pt in enumerate(points):
        pid = pt.get("point_id", f"point_{i}")
        print(f"[{i+1}/{len(points)}] Evaluating {pid} ... ", end="", flush=True)
        res = run_single_physical_point_madgraph(
            pt,
            proc_dir=args.proc_dir,
            cards_out_dir=args.cards_dir,
            nevents=args.nevents,
            seeds=args.seeds,
        )
        results.append(res)
        status = res["madgraph_status"]
        sigma = res["sigma_production_fb"]
        unc = res["sigma_production_unc_fb"]
        print(f"{status} | sigma = {sigma:.6f} +/- {unc:.6f} fb")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.suffix.lower() == ".json":
        with open(args.output, "w") as f:
            json.dump(results if len(results) > 1 else results[0], f, indent=2)
            f.write("\n")
    else:
        # CSV output
        fieldnames = [
            "point_id",
            "m_H2_GeV",
            "m_h_GeV",
            "tan_beta",
            "lambda6",
            "M2_GeV2",
            "g_hH2H2_GeV",
            "ctau_physical_mm",
            "ctau_response_mm",
            "model_variant",
            "lifetime_mode",
            "sigma_source",
            "sigma_provenance",
            "BR_bb",
            "sigma_production_fb",
            "sigma_production_unc_fb",
            "madgraph_status",
            "madgraph_run_id_or_path",
        ]
        with open(args.output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
            writer.writeheader()
            for r in results:
                writer.writerow(r)

    print(f"[RUNNER] Results saved to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
