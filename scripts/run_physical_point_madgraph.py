#!/usr/bin/env python3
"""Minimal physical-point MadGraph production cross-section runner.

Takes one canonical physical 2HDM point (dihiggs.point.v2 schema) or a batch of
points, generates point-specific param_card/run_card inputs, executes MadGraph
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

PHYSICS_CONVENTIONS_SCHEMA = "physics_conventions_v3"
PHYSICS_CONVENTIONS_COMMIT = "087ba246e9a9fa34b16249b52629a62703893b5c"
PHYSICS_CONVENTIONS_SHA256 = "4f3a938ed54dbc779d25f691ce1dd06fe17af69751105dc3b69ccb6b7d92fff6"
_HISTORICAL_MASS_CONVENTIONS = {
    "mh_125p13_pdg_2026_historical_replay",
    "mh_125p13_high_mass_v1",
    "mh_125p09_lambda1_boundary_legacy",
    "mh_125p0_ufo_autoresearch_legacy",
}

def _mass_convention(point: Dict[str, Any]) -> Dict[str, Any]:
    nested = point.get("mass_convention")
    return nested if isinstance(nested, dict) else point


def _v3_provenance_state(point: Dict[str, Any]) -> tuple[bool, bool]:
    nested = _mass_convention(point)
    values = (
        point.get("physics_conventions_schema", nested.get("schema_version")),
        point.get("physics_conventions_commit", nested.get("source_commit")),
        point.get("physics_conventions_sha256", nested.get("source_sha256")),
    )
    present = any(value is not None for value in values)
    valid = values == (
        PHYSICS_CONVENTIONS_SCHEMA,
        PHYSICS_CONVENTIONS_COMMIT,
        PHYSICS_CONVENTIONS_SHA256,
    )
    return present, valid


def resolve_ghphiphi_GeV(point: Dict[str, Any]) -> float:
    """Resolve the UFO parameter using v3's signed physical mapping.

    Magnitude-only input is accepted only for explicitly identified historical
    replay points; it cannot silently enter the new-production path.
    """
    has_provenance, valid_provenance = _v3_provenance_state(point)
    nested = _mass_convention(point)
    if has_provenance:
        if not valid_provenance:
            raise ValueError("v3 physics convention provenance is incomplete or mismatched")
        if point.get("coupling_prescription") != "physical_2HDM":
            raise ValueError("v3 production currently supports only physical_2HDM coupling")
        mass_id = point.get("mass_convention_id", nested.get("convention_id"))
        mass_text = point.get("m_h_GeV_text", nested.get("m_h_GeV_text"))
        if mass_id != "mh_125p20_active_2026" or str(mass_text) != "125.20":
            raise ValueError("v3 new production requires active convention id and decimal m_h text 125.20")
        try:
            signed = float(point["g_physical_hphiphi_GeV"])
            magnitude = float(point["g_physical_hphiphi_abs_GeV"])
            compatibility_magnitude = float(point["g_hH2H2_GeV"])
            raw_real = float(point["two_hdmc_hphiphi_real_GeV"])
            raw_imag = float(point["two_hdmc_hphiphi_imag_GeV"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError("v3 physical coupling fields are incomplete") from exc
        scale = max(1.0, abs(signed), abs(magnitude), abs(raw_imag))
        if (
            not all(math.isfinite(value) for value in (signed, magnitude, compatibility_magnitude, raw_real, raw_imag))
            or magnitude <= 0
            or not math.isclose(magnitude, abs(signed), rel_tol=1e-9, abs_tol=1e-12)
            or not math.isclose(compatibility_magnitude, magnitude, rel_tol=1e-9, abs_tol=1e-12)
            or not math.isclose(raw_imag, -signed, rel_tol=1e-9, abs_tol=1e-12)
            or abs(raw_real) > 1e-12 * scale
        ):
            raise ValueError("v3 physical coupling fields are inconsistent with the declared convention")
        return -signed

    convention_id = point.get("mass_convention_id") or point.get("convention_id")
    if point.get("historical_replay") is True and convention_id in _HISTORICAL_MASS_CONVENTIONS:
        value = point.get("g_hH2H2_GeV", point.get("g"))
        if value is None or not math.isfinite(float(value)) or float(value) <= 0:
            raise ValueError("historical replay requires a positive finite magnitude coupling")
        return -abs(float(value))
    raise ValueError(
        "new production requires complete physics_conventions_v3 provenance and signed coupling fields; "
        "magnitude-only input requires an explicit historical convention and historical_replay=true"
    )

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


# Field names the SM-like Higgs mass travels under, newest first:
# dihiggs.high_mass_point.v1 -> m_h_GeV, dihiggs.point.v2 -> mh_input_GeV,
# dihiggs_boundary evaluate_point CSV -> mh.
M_H_FIELD_ALIASES = ("m_h_GeV", "mh_input_GeV", "mh")


def _resolve_numeric_aliases(
    point: Dict[str, Any], canonical: str, aliases: Tuple[str, ...], *, require_canonical: bool = False
) -> float:
    present: List[Tuple[str, float]] = []
    for key in (canonical, *aliases):
        raw = point.get(key)
        if raw is None or (isinstance(raw, str) and not raw.strip()):
            continue
        if isinstance(raw, bool):
            raise ValueError(f"point field {key} must be a finite number")
        try:
            value = float(raw)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"point field {key} must be a finite number") from exc
        if not math.isfinite(value):
            raise ValueError(f"point field {key} must be a finite number")
        present.append((key, value))
    if not present:
        raise KeyError(
            f"point {point.get('point_id', '<unknown>')!r} carries no {canonical}; "
            f"expected {', '.join((canonical, *aliases))}"
        )
    if require_canonical and present[0][0] != canonical:
        raise KeyError(f"new v3 production requires canonical point field {canonical}")
    selected = present[0][1]
    for key, value in present[1:]:
        if not math.isclose(value, selected, rel_tol=1e-12, abs_tol=1e-15):
            raise ValueError(f"point aliases for {canonical} disagree ({present[0][0]} vs {key})")
    return selected


def resolve_m_h_GeV(point: Dict[str, Any]) -> float:
    """Read the SM-like Higgs mass off the canonical point.

    Deliberately has NO default. This repo used to fall back to a hard-coded
    125.13, which meant a point produced under a different mass convention was
    silently rewritten to this repo's assumption when its param_card was
    generated. The mass convention has exactly one owner
    (conventions/physics_conventions.yaml) and travels on the point; a point
    that does not carry it is a contract violation, not a defaulting case.
    """
    return _resolve_numeric_aliases(
        point, M_H_FIELD_ALIASES[0], M_H_FIELD_ALIASES[1:]
    )


def resolve_m_phi_GeV(point: Dict[str, Any], *, require_canonical: bool = False) -> float:
    """Resolve the additional scalar mass, checking every supplied alias."""
    return _resolve_numeric_aliases(
        point,
        "m_phi_GeV",
        ("mH_input_GeV", "mH2_GeV", "mH"),
        require_canonical=require_canonical,
    )


def resolve_point_masses_GeV(point: Dict[str, Any]) -> Tuple[float, float]:
    """Resolve and validate both masses against the point's convention state."""
    has_provenance, valid_v3 = _v3_provenance_state(point)
    if has_provenance and not valid_v3:
        raise ValueError("v3 physics convention provenance is incomplete or mismatched")
    is_v3 = has_provenance
    if is_v3:
        mh = _resolve_numeric_aliases(point, "m_h_GeV", ("mh_input_GeV", "mh"), require_canonical=True)
        mass_text = point.get("m_h_GeV_text", _mass_convention(point).get("m_h_GeV_text"))
        if mh != 125.20 or mass_text != "125.20":
            raise ValueError("v3 new production requires the active decimal m_h value 125.20 GeV")
    else:
        mh = resolve_m_h_GeV(point)
    m_phi = resolve_m_phi_GeV(point, require_canonical=is_v3)
    if mh <= 0 or m_phi <= 0:
        raise ValueError("point masses must be positive")
    return mh, m_phi


def generate_param_card_text(
    template_text: str,
    *,
    mh_GeV: float,
    mH2_GeV: float = 150.0,
    g_hH2H2_GeV: float = 63.59142520075966,
    ctau_mm: float = 4.326221529733112,
    total_width_GeV: Optional[float] = None,
    ghphiphi_GeV: Optional[float] = None,
) -> str:
    """Generate exact point-specific param_card.dat content from default template."""
    ctau_m = ctau_mm / 1000.0
    # Direct legacy callers may still supply only a magnitude. The production
    # driver passes the convention-resolved signed value explicitly.
    gh_phiphi = -abs(g_hH2H2_GeV) if ghphiphi_GeV is None else float(ghphiphi_GeV)
    if not math.isfinite(gh_phiphi):
        raise ValueError("GHphiphi must be finite")

    if total_width_GeV is None or not math.isfinite(total_width_GeV) or total_width_GeV <= 0:
        total_width_GeV = 1.973269804e-16 / ctau_m if ctau_m > 0 else 4.561185e-14

    text = template_text
    # Replace mass block. Anchored to start-of-line so this cannot also match
    # the unrelated "DECAY  25  <width>" line further down the card: the old
    # unanchored `\b25\s+` pattern matched both, silently overwriting the SM
    # Higgs total width with the SM Higgs mass value (see
    # results/pilot_cards/*_param_card.dat for pre-fix corrupted output, e.g.
    # "DECAY  25 1.251300e+02 # WH" -- 125.13 GeV is not a valid decay width).
    # Two independent campaign scripts (mission_runs/20260825_h2_event_yields_v1
    # /scripts/run_200gev_pilot.py and mission_runs/20260826_h2_table_v2_requalification
    # /work/run_madgraph_v2.py) worked around this externally by monkeypatching
    # this function to restore the template's original DECAY 25 line; fixing
    # it here retires both workarounds.
    text = re.sub(r"^(\s*25\s+)\S+", rf"\g<1>{format_slha_float(mh_GeV)}", text, flags=re.M)
    text = re.sub(r"^(\s*9000006\s+)\S+", rf"\g<1>{format_slha_float(mH2_GeV)}", text, flags=re.M)
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
    point_id = str(point.get("point_id", "unknown_point")).strip()
    ghphiphi = resolve_ghphiphi_GeV(point)
    has_provenance, valid_v3 = _v3_provenance_state(point)
    is_v3 = has_provenance and valid_v3
    mh, mH2 = resolve_point_masses_GeV(point)
    g_hH2H2 = _resolve_numeric_aliases(
        point, "g_physical_hphiphi_abs_GeV", ("g_hH2H2_GeV", "g"), require_canonical=is_v3
    )
    ctau = _resolve_numeric_aliases(point, "ctau_mm", ("ctau",), require_canonical=is_v3)
    br_bb = _resolve_numeric_aliases(point, "br_bb", ("BR_bb",), require_canonical=is_v3)
    tan_beta = _resolve_numeric_aliases(point, "tan_beta", ("tan_beta_input",))
    lambda6 = _resolve_numeric_aliases(point, "lambda6_input", ("lambda6",))
    M2 = _resolve_numeric_aliases(point, "M2_input_GeV2", ("M2_GeV2",))
    total_width = _resolve_numeric_aliases(
        point, "total_width_GeV", ("width_GeV",), require_canonical=is_v3
    )

    if min(mh, mH2, g_hH2H2, ctau, total_width, tan_beta, M2) <= 0:
        raise ValueError("masses, coupling magnitude, lifetime, width, tan_beta, and M2 must be positive")
    if not 0.0 <= br_bb <= 1.0:
        raise ValueError("br_bb must be between zero and one")
    expected_ctau = 1.973269804e-13 / total_width
    if not math.isclose(ctau, expected_ctau, rel_tol=1e-4):
        raise ValueError("ctau_mm and total_width_GeV are inconsistent")

    template_param_path = proc_dir / "Cards" / "param_card_default.dat"
    if not template_param_path.exists():
        template_param_path = proc_dir / "Cards" / "param_card.dat"
    template_text = template_param_path.read_text(encoding="utf-8")

    param_card_content = generate_param_card_text(
        template_text,
        mh_GeV=mh,
        mH2_GeV=mH2,
        g_hH2H2_GeV=g_hH2H2,
        ghphiphi_GeV=ghphiphi,
        ctau_mm=ctau,
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
                    timeout=600,
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
                        "point_id": point_id,
                        "mH2_GeV": mH2,
                        "tan_beta": tan_beta,
                        "lambda6": lambda6,
                        "M2_GeV2": M2,
                        "g_hH2H2_GeV": g_hH2H2,
                        "g_physical_hphiphi_GeV": point.get("g_physical_hphiphi_GeV"),
                        "g_physical_hphiphi_abs_GeV": point.get("g_physical_hphiphi_abs_GeV"),
                        "two_hdmc_hphiphi_real_GeV": point.get("two_hdmc_hphiphi_real_GeV"),
                        "two_hdmc_hphiphi_imag_GeV": point.get("two_hdmc_hphiphi_imag_GeV"),
                        "GHphiphi_GeV": ghphiphi,
                        "coupling_prescription": point.get("coupling_prescription", "historical_replay"),
                        "ctau_mm": ctau,
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
        "point_id": point_id,
        "mH2_GeV": mH2,
        "tan_beta": tan_beta,
        "lambda6": lambda6,
        "M2_GeV2": M2,
        "g_hH2H2_GeV": g_hH2H2,
        "g_physical_hphiphi_GeV": point.get("g_physical_hphiphi_GeV"),
        "g_physical_hphiphi_abs_GeV": point.get("g_physical_hphiphi_abs_GeV"),
        "two_hdmc_hphiphi_real_GeV": point.get("two_hdmc_hphiphi_real_GeV"),
        "two_hdmc_hphiphi_imag_GeV": point.get("two_hdmc_hphiphi_imag_GeV"),
        "mass_convention_id": point.get("mass_convention_id", _mass_convention(point).get("convention_id")),
        "m_h_GeV_text": point.get("m_h_GeV_text", _mass_convention(point).get("m_h_GeV_text")),
        "GHphiphi_GeV": ghphiphi,
        "coupling_prescription": point.get("coupling_prescription", "historical_replay"),
        "physics_conventions_schema": point.get("physics_conventions_schema", _mass_convention(point).get("schema_version")),
        "physics_conventions_commit": point.get("physics_conventions_commit", _mass_convention(point).get("source_commit")),
        "physics_conventions_sha256": point.get("physics_conventions_sha256", _mass_convention(point).get("source_sha256")),
        "ctau_mm": ctau,
        "BR_bb": br_bb,
        "sigma_production_fb": sigma_production_fb,
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
            "mH2_GeV",
            "tan_beta",
            "lambda6",
            "M2_GeV2",
            "g_hH2H2_GeV",
            "ctau_mm",
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
