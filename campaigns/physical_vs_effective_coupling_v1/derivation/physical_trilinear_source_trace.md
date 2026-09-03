# Source-level trace: the physical h-φ-φ trilinear in 2HDMC

**Status: line-by-line reconstruction, personally read from
`~/atlas_dihiggs/dihiggs/2hdmc/src/THDM.cpp` for this mission (not copied
from the 2026-08-31 audit's prose, though the audit independently arrived at
the same alignment-limit formula and its numbers are used below as a
cross-check).** Every claim here cites a file:line in the canonical,
unmodified 2HDMC copy at `~/atlas_dihiggs/dihiggs`. No 2HDMC source file was
edited to produce this trace.

Convention: 2HDMC neutral-scalar **index 1 is the lighter of the two
CP-even eigenstates** (`set_param_phys`/`get_param_phys`, `THDM.cpp:322-326,
1094-1095` — 2HDMC refuses m_h > m_H and always assigns the smaller mass²
eigenvalue to index 1); it **coincides with "SM-like" only at exact
alignment** (corrected after `SOL_REVIEW.md` item 1 — an earlier version of
this file wrote "index 1 = 'h' = SM-like" unconditionally, which is wrong at
the non-aligned points used to validate the general closed-form formula in
`physical_trilinear_derivation.md` §1). With m_h=125 GeV fixed < m_φ ∈
{200,250,300} in this project's benchmark family, index 1 is in fact the
125 GeV state there and index 2 is m_φ (per `DihiggsPointV2Evaluator.cpp` /
`physics_conventions.yaml`, unchanged from the prior audit and the photonic
campaign) — but this is a fact about the benchmark's mass ordering, not a
general property of the index. The coupling audited throughout is 2HDMC's
own `get_coupling_hhh(1,2,2)`.

---

## 1. Entry point

`THDM::get_coupling_hhh(int h1,int h2,int h3, complex<double> &c)` —
`THDM.cpp:1574-1629`. Header comment: "Conventions are according to
hep-ph/0602242" (line 1575).

```cpp
double Z1,Z2,Z3,Z4,Z5,l6,l7,m_Hp;
get_param_higgs(Z1,Z2,Z3,Z4,Z5,l6,l7,m_Hp);
double Z6=-l6, Z7=-l7;
double v=sm.get_v();
```
(`THDM.cpp:1578-1581`) — the function's own Z1..Z7 are the Higgs-basis
quartic couplings, obtained by calling `get_param_higgs`, with a **sign
flip applied to positions 6 and 7 only** (Z6=-Lambda6, Z7=-Lambda7; Z1..Z5
keep the sign `get_param_higgs` returns). This sign flip is a **CONVENTION**
internal to `get_coupling_hhh`, not a property of the Higgs basis itself —
`get_param_higgs`'s own Lambda6/Lambda7 outputs are used unflipped
elsewhere (e.g. `get_param_hybrid`, `THDM.cpp:1160-1162`).

For three neutral indices (h1,h2,h3 all < 4), the function sums over all 6
permutations of the sorted triple via `gsl_permutation`, accumulating
(`THDM.cpp:1613-1622`):

```cpp
c += -I*v/2.*( qki(h0,1)*conj(qki(h1,1))*real(qki(h2,1))*Z1
             + qki(h0,2)*conj(qki(h1,2))*real(qki(h2,1))*(Z3+Z4)
             + real(conj(qki(h0,1))*qki(h1,2)*qki(h2,2)*Z5)
             + real((2.*qki(h0,1)+conj(qki(h0,1)))*conj(qki(h1,1))*qki(h2,2)*Z6)
             + real(conj(qki(h0,2))*qki(h1,2)*qki(h2,2)*Z7) );
```
(indices `h[0],h[1],h[2]` are the current permutation of `{h1,h2,h3}`).

## 2. The mixing matrix `qki`

`THDM::get_qki(int k,int i)` — `THDM.cpp:1201-1220`:

```cpp
double sba = get_sba();   // sin(beta-alpha)
double cba = get_cba();   // cos(beta-alpha)
complex<double> qki[4][2] = {{ sba, -cba },   // k=1 ("h")
                              { cba,  sba },   // k=2 ("H")
                              { 0  ,  I   },   // k=3 ("A")
                              { I  ,  0   }};  // k=4 ("H+")
return qki[k-1][i-1];
```

For the neutral CP-even states (k=1,2) this matrix is real; `i` indexes the
two Higgs-doublet components in the Higgs basis. This is the rotation from
the (SM-like, exotic) mass basis into the two-doublet Higgs basis, and is
**the entire carrier of the alignment angle** in `get_coupling_hhh`.

**Scope limitation (added after `SOL_REVIEW.md` item 2):** `get_cba()`
(`THDM.cpp:2828-2831`) returns `+sqrt(1-sba²)` — **always the non-negative
root**. 2HDMC's own `qki` therefore cannot represent `cos(β−α) < 0`; the
general closed-form coupling formula derived in
`physical_trilinear_derivation.md` §1, and its numerical validation, cover
only the `cba ≥ 0` branch. (Contrast `get_param_hybrid`, which uses
`sign(sinba)·sqrt(1-sba²)` and can be negative.)

## 3. `get_param_higgs`: Higgs-basis Z's and `M22²`

`THDM::get_param_higgs` — `THDM.cpp:1105-1138`. Inputs: the generic-basis
members `lambda[1..7]` and `beta` (i.e. this is a **pure basis rotation**,
no new physics input). Header comment cites hep-ph/0504050.

```cpp
double lambda345 = lambda[3]+lambda[4]+lambda[5];
Lambda1 = lambda[1]*cb4 + lambda[2]*sb4 + 0.5*lambda345*s2b2 + 2.*s2b*(cb2*lambda[6]+sb2*lambda[7]);
Lambda2 = lambda[1]*sb4 + lambda[2]*cb4 + 0.5*lambda345*s2b2 - 2.*s2b*(sb2*lambda[6]+cb2*lambda[7]);
Lambda3 = 0.25*s2b2*(lambda[1]+lambda[2]-2*lambda345) + lambda[3] - s2b*c2b*(lambda[6]-lambda[7]);
Lambda4 = 0.25*s2b2*(lambda[1]+lambda[2]-2*lambda345) + lambda[4] - s2b*c2b*(lambda[6]-lambda[7]);
Lambda5 = 0.25*s2b2*(lambda[1]+lambda[2]-2*lambda345) + lambda[5] - s2b*c2b*(lambda[6]-lambda[7]);
Lambda6 = -0.5*s2b*(lambda[1]*cb2-lambda[2]*sb2-lambda345*c2b) + cb*c3b*lambda[6] + sb*s3b*lambda[7];
Lambda7 = -0.5*s2b*(lambda[1]*sb2-lambda[2]*cb2+lambda345*c2b) + sb*s3b*lambda[6] + cb*c3b*lambda[7];

double m12_2 = get_m12_2();
double m11_2 = m12_2*tb - 0.5*v2*(lambda[1]*cb2+(lambda[3]+lambda[4]+lambda[5])*sb2+3.*lambda[6]*sb*cb+lambda[7]*sb2*tb);
double M22_2 = m11_2*sb2 + m22_2*cb2 + m12_2*s2b;
m_Hp = sqrt(M22_2 + 0.5*v2*Lambda3);
```
(`THDM.cpp:1125-1137`). Note **`M22_2` is a *local variable computed here*,
never returned or exposed by any public THDM accessor** — it exists only
inside this function's stack frame to compute `m_Hp`. Any use of "M22²"
elsewhere in this project (including the 2026-08-31 audit's own analysis) is
necessarily a **re-derivation from public quantities using this same
verbatim formula**, not a call into 2HDMC's own state. `m22_2` (lower-case,
the class member fed in) is itself private; the project's `AuditProbe.cpp`
independently re-derives it too, via the public `set_param_phys` formula at
`THDM.cpp:359` (see `AuditProbe.cpp:163-171`).

**Key line for `m_Hp`:** `m_Hp² = M22² + ½v²·Z3` — a direct source
identity, `GENERAL IDENTITY` (holds for any beta, any lambdas, no alignment
assumed).

## 4. Where `M2` (this project's convention) actually enters

This project's own `M2 = m12²/(sinβ cosβ)` (used throughout
`DihiggsPointV2Evaluator.cpp`, `M2PointEvaluator.cpp`,
`Lambda1EvaluatorV2.cpp`) is **not** a 2HDMC-native symbol; grep of
`THDM.cpp` and `THDM.h` for `M2` finds no such quantity defined inside
2HDMC itself. It is entirely this project's construction, built from the
2HDMC-native `m12_2` (the soft-breaking mass² in the generic basis,
`THDM.h`'s private member) divided by `sinβ cosβ`.

**Caveat on `get_m12_2()`** (`THDM.cpp:2774-2792`, added after
`SOL_REVIEW.md` "Additional issue #2"): this accessor does **not** return
the value that was fed into `set_param_phys`/`set_param_gen` — it
*re-derives* m12² from the private `m22_2` member and the λ's via a
different formula. At tanβ=4×10⁷ this round trip is wrong by **4.5%**
(`m12_2_out` columns throughout this campaign's CSVs are the *re-derived*,
unusable value, not the true input — `GeneralProbe` always uses
`m12_2_exact_used`/`m12_2_in` instead, never `get_m12_2()`'s output, for
exactly this reason).

`THDM::set_param_phys` (`THDM.cpp:317-360`, masses+m12²+tanβ route) takes
`m12_2` as a **direct numerical input** — it is not derived from anything
else inside this route; the caller supplies it. So "`M2`" is, mechanically,
a convenience rescaling of whatever `m12_2` value the caller chose. **But
this does not mean M2=m_φ² is optional at this project's tanβ** — see
`derivation/assumptions_and_limits.md` §4 (corrected after `SOL_REVIEW.md`
item 6): perturbativity forces `|λ1| ≲ 4π`, and at alignment
`λ1 = (m_φ²−M²)/(v²cos²β) − 1.5λ6·tanβ + 0.5λ7·tan³β`, so at tanβ=4×10⁷
(`v²cos²β ≈ 3.79×10⁻¹¹ GeV²`) any construction route is pinned to
`M² = m_φ² − 1.5v²λ6/tanβ` to within **relative ~10⁻¹⁴–10⁻¹⁵**, regardless
of which coordinates the caller thinks they are choosing independently. See
`m2_study/m2_variation.csv` for the numerical demonstration (the
`exact_via_star_identity_lambda1eq1` rows) and
`derivation/assumptions_and_limits.md` §2/§4 for the full derivation.

## 5. `set_param_phys_lam1` and the λ1 route

`THDM::set_param_phys_lam1` — `THDM.cpp:398-424` (reconstructs `m12_2` from
an input λ1, then calls `set_param_phys`):

```cpp
double m12_2 = (m_H*m_H*ca2 + m_h*m_h*sa2
                - v2*cb2*(lambda1_in + 1.5*lambda6*tb - 0.5*lambda7*tb*tb*tb)) / tb;
```
(`THDM.cpp:414-416`, exact copy verified against source — matches the
2026-08-31 audit's quotation verbatim). This is the *inverse* of the λ1
branch of `set_param_phys`'s own `get_param_gen` formula
(`THDM.cpp:354`: `lambda[1] = (m_H²ca²+m_h²sa² - m12_2·tb)/v2/cb2 - 1.5λ6·tb + 0.5λ7·tb³`).
Differentiating the forward map:

```
d(m12_2)/d(lambda1) = -v² cb² / tb = -v² cos³β / sinβ
```

`GENERAL IDENTITY` (pure calculus on the closed-form map above) — this term
is suppressed by `1/tan³β` and is the algebraic root of the λ1
ill-conditioning already established in the photonic campaign
(`tanbeta-1e7-spectrum-has-no-significant-digits` memory) and in the
2026-08-31 audit. **`set_param_phys_lam1` and `set_param_phys` are related
by an explicit, invertible, but numerically ill-conditioned map at large
tanβ — they are not interchangeable coordinate systems at the tanβ this
project's benchmarks use**, per this mission's explicit instruction.

## 6. Independent hand-verification (this mission)

I re-derived `get_coupling_hhh(1,2,2)` by hand directly from §1-§2's source
lines (not from the prior audit's prose), for **general** `sba=s, cba=c`
(not assuming alignment), and separately specialized to `s=1,c=0`. Full
algebra is in `physical_trilinear_derivation.md`. Result, reduced at exact
alignment:

```
get_coupling_hhh(1,2,2) = -i·v·(Z3+Z4+Z5)        [s=1, c=0 exactly]
```

This is **independently confirmed** by the 2026-08-31 audit's own
`AuditProbe.cpp` (`g_from_Z345 = -v*Z345` column, `AuditProbe.cpp:215`, its
own note: "matches get_coupling_hhh(1,2,2)... to 13 sig figs"). Two
independent code paths (my by-hand permutation sum vs. the audit's compiled,
numerically executed comparison) now agree — this satisfies the mission's
"reject any conclusion supported only by one code path" bar for the
alignment-limit formula specifically.

The **general, non-aligned** closed form I derived (§ below) has **not**
yet been executed against a compiled 2HDMC point away from alignment — this
is flagged as a to-be-verified numeric task, not asserted as confirmed. See
`physical_trilinear_derivation.md` §3 and `m2_study/` for the verification
status.
