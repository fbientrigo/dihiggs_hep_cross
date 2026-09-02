#!/usr/bin/env python3
"""Recover Christopher's event-table conventions from his own published numbers.

Nothing here is assumed: the Z branching fractions and the number-formatting
rule used by `build_deliverables.py` are both *derived* from
`inputs/chris_original/chris_event_yields.tex` and checked against it.
"""
from __future__ import annotations

L = 300.0
SIGMA = {200: 23.51, 250: 13.35, 300: 7.530}

# BRs exactly as Christopher's CSV reports them (4 significant figures).
BR = {200: dict(bb=0.009231, gg=0.003233, Zga=0.3216, gaga=0.6645),
      250: dict(bb=0.004961, gg=0.003035, Zga=0.3801, gaga=0.6111),
      300: dict(bb=0.002939, gg=0.003076, Zga=0.4111, gaga=0.5820)}

# tab:A_fotonico, per mass (200, 250, 300)
TAB_A = {
    ("bb", "bb"): (0.6010, 0.0986, 0.0195), ("bb", "gg"): (0.4210, 0.1206, 0.0408),
    ("bb", "Zga"): (41.88, 15.10, 5.458), ("bb", "gaga"): (86.53, 24.28, 7.728),
    ("gg", "gg"): (0.0737, 0.0369, 0.0214), ("gg", "Zga"): (14.67, 9.240, 5.713),
    ("gg", "gaga"): (30.31, 14.86, 8.088), ("Zga", "Zga"): (730, 579, 382),
    ("Zga", "gaga"): (3.01e3, 1.86e3, 1.08e3), ("gaga", "gaga"): (3.11e3, 1.50e3, 765),
}
# tab:B_fotonico entries needed to solve for the Z branching fractions
TAB_B = {"bb_jjga": (29.28, 10.56, 3.816), "bb_eega": (1.408, 0.5080, 0.1836),
         "bb_mumuga": (1.410, 0.5084, 0.1837)}


def N(m, a, b):
    n = L * SIGMA[m]
    return n * (BR[m][a] ** 2 if a == b else 2 * BR[m][a] * BR[m][b])


def fmt_chris(v: float) -> str:
    if v >= 1000:
        return f"{v:.2e}".replace("e+0", "e+")
    if v >= 100:
        return f"{v:.0f}"
    if v >= 10:
        return f"{v:.2f}"
    if v >= 1:
        return f"{v:.3f}"
    return f"{v:.4f}"


def main() -> int:
    masses = (200, 250, 300)

    print("1. Event-count formula  N_ab = L*sigma*BR_a^2 (a==b) | 2*L*sigma*BR_a*BR_b")
    worst = 0.0
    for (a, b), vals in TAB_A.items():
        for m, tex in zip(masses, vals):
            worst = max(worst, abs(N(m, a, b) / tex - 1))
    print(f"   worst relative disagreement vs tab:A_fotonico: {worst:.2%}")
    print("   (non-zero only because his BRs are quoted to 4 significant figures)")

    print("\n2. Z branching fractions, solved from tab:B_fotonico / tab:A_fotonico")
    got = {}
    for key, vals in TAB_B.items():
        ratios = [tex / N(m, "bb", "Zga") for m, tex in zip(masses, vals)]
        got[key] = sum(ratios) / len(ratios)
        print(f"   {key:12} -> BR(Z->{key.split('_')[1]:7}) = {got[key]:.5f}"
              f"   per-mass: {', '.join(f'{r:.5f}' for r in ratios)}")
    print("   adopted: jj = 0.6991, ee = 0.03363, mumu = 0.03366  (PDG)")

    print("\n3. Number formatting rule")
    exact = diff = 0
    for (a, b), vals in TAB_A.items():
        for m, tex in zip(masses, vals):
            mine = fmt_chris(N(m, a, b))
            theirs = fmt_chris(float(tex))
            if mine == theirs:
                exact += 1
            else:
                diff += 1
                print(f"   last-digit differs: ({a})({b}) @ {m} GeV -> "
                      f"ours {mine}, his {theirs}")
    print(f"   {exact}/{exact + diff} entries reproduce exactly; {diff} differ in the "
          f"last digit only,\n   from his rounding of the BRs before multiplying.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
