#!/usr/bin/env python3
"""Write the official ATLAS Trackless model-independent threshold for R9.

Primary source:
ATLAS Collaboration, JHEP 06 (2023) 200, arXiv:2301.13866v3,
Table 6 (paper page 22), Trackless jet signal region.

The local HEPData YAML record is still inventoried for region provenance, but
the model-independent counting limit is taken from the publication table.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTDIR = REPO_ROOT / "results" / "r9_h2_sensitivity_threshold"
BASELINE_PATH = OUTDIR / "baseline.json"

OBSERVED_EVENTS = 0
EXPECTED_BACKGROUND = 0.83
EXPECTED_BACKGROUND_UP = 0.51
EXPECTED_BACKGROUND_DOWN = 0.53
OBSERVED_S95 = 3.0
EXPECTED_S95 = 3.4
EXPECTED_S95_UP = 1.3
EXPECTED_S95_DOWN = 0.3
PUBLISHED_VISIBLE_SIGMA_LIMIT_FB = 0.022
LUMINOSITY_FB_INVERSE = 139.0


def main() -> int:
    baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    n0 = baseline["recomputed"]["Trackless_expected_events"]
    g0 = baseline["frozen_inputs"]["g_hH2H2_GeV"]["value"]

    exact_visible_sigma = OBSERVED_S95 / LUMINOSITY_FB_INVERSE
    rate_multiplier = OBSERVED_S95 / n0
    required_kappa = math.sqrt(rate_multiplier)
    required_abs_g = required_kappa * g0

    payload = {
        "schema": "hep_cross.r9.atlas_threshold.v2",
        "publication": {
            "reference": "ATLAS, JHEP 06 (2023) 200",
            "arxiv": "2301.13866v3",
            "table": 6,
            "paper_page": 22,
            "signal_region": "Trackless jet SR",
            "hepdata_doi": "10.17182/hepdata.137762",
        },
        "status": "OFFICIAL_THRESHOLD_RESOLVED",
        "region_mapping": {
            "recast_region": "Trackless",
            "official_region": "Trackless jet SR",
            "region_mapping_status": "UNAMBIGUOUS",
            "basis": [
                "R_DV > 4 mm",
                "|d0| > 2 mm",
                "n_tracks(DV) >= 5",
                "m_DV > 10 GeV",
                "Trackless jet selection",
            ],
        },
        "numerical_threshold": {
            "observed_events": OBSERVED_EVENTS,
            "expected_background": EXPECTED_BACKGROUND,
            "expected_background_up": EXPECTED_BACKGROUND_UP,
            "expected_background_down": EXPECTED_BACKGROUND_DOWN,
            "observed_S95": OBSERVED_S95,
            "expected_S95": EXPECTED_S95,
            "expected_S95_up": EXPECTED_S95_UP,
            "expected_S95_down": EXPECTED_S95_DOWN,
            "published_model_independent_visible_sigma_limit_fb": (
                PUBLISHED_VISIBLE_SIGMA_LIMIT_FB
            ),
            "exact_visible_sigma_from_S95_over_lumi_fb": exact_visible_sigma,
            "published_rounding_check_pass": (
                round(exact_visible_sigma, 3)
                == PUBLISHED_VISIBLE_SIGMA_LIMIT_FB
            ),
            "integrated_luminosity_fb_inverse": LUMINOSITY_FB_INVERSE,
        },
        "required_visible_sigma_fb": exact_visible_sigma,
        "required_rate_multiplier": rate_multiplier,
        "required_kappa_g": required_kappa,
        "required_abs_g_hH2H2_GeV": required_abs_g,
        "interpretation": (
            "The official observed Trackless limit corresponds to 3.0 signal "
            "events. The R8 benchmark predicts 0.2884 events, so the rate must "
            "increase by 10.4017 and |g_hH2H2| by kappa_g=3.22516 under the "
            "structurally exact single-diagram scaling."
        ),
    }

    OUTDIR.mkdir(parents=True, exist_ok=True)
    out = OUTDIR / "atlas_threshold.json"
    out.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"{out.name}: {payload['status']}")
    print(f"observed S95: {OBSERVED_S95}")
    print(f"required kappa_g: {required_kappa:.12f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
