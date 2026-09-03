# UFO externalization — validation

## 1. Original UFO verified against its source archive

`~/atlas_dihiggs/dihiggs_ufo/LLscalar_v3_UFO_original/` diffed against the
tracked source archive `~/atlas_dihiggs/dihiggs_ufo/LLscalar_v3_UFO.zip`
(2021-08-19). **All plain-text source files are byte-identical**
(`couplings.py`, `parameters.py`, `vertices.py`, `particles.py`,
`lorentz.py`, etc.). Only `model.pkl` differs — a compiled pickle cache, not
source; expected to differ across Python/MG5 versions and not evidence of
tampering. `py3_model.pkl` matched exactly.

`GC_90` confirmed, read directly from `couplings.py:372-374`:
```python
GC_90 = Coupling(name = 'GC_90', value = '8*complex(0,1)*Mh2**2/vev', order = {'QED':-1})
```
— matching the 2026-08-31 audit's quotation exactly, and used in exactly one
vertex, `V_7 = [P.H, P.h2, P.h2]` (`vertices.py:48-52`). `Mh2` is itself an
external MASS-block parameter (pdg 9000006, `parameters.py:230-236`).

**Also observed (out of scope for this mission, not acted on):** the
`dihiggs_ufo` repo's working tree currently shows `git status --short`
reporting `D CURRENT_PACK_A` and `D PACK_AA_PRESENTATION_EVIDENCE.zip` —
pre-existing deletions, not made by this session, not investigated further
per the mission's restriction against reopening prior provenance work. Noted
here for the record, not remediated.

**`LLscalar_v3_UFO_external_GHphiphi/`** (the pre-existing directory of that
name inside `dihiggs_ufo/`) was diffed against `LLscalar_v3_UFO_original/`
and found **byte-identical** — confirming the 2026-08-31 audit's finding
that this directory, despite its name, does **not** actually expose
`GHphiphi` as an external parameter (`grep -rn GHphiphi` matches nothing in
either tree). It is left untouched; this mission does not treat it as the
externalized model.

## 2. New externalized copy (this campaign only)

Created at `ufo/LLscalar_v3_UFO_GHphiphi_external/` — a copy of
`LLscalar_v3_UFO_original/`, **not** of the misleadingly-named pre-existing
directory above. The original UFO tree (`~/atlas_dihiggs/dihiggs_ufo/`) was
never written to by this mission.

**Diff, exactly 2 files changed** (`ufo/externalization_diff.patch`, full
`diff -ru` output):

1. `couplings.py`: `GC_90`'s value changed from `'8*complex(0,1)*Mh2**2/vev'`
   to `'complex(0,1)*GHphiphi'`. The old expression is left commented out
   immediately above (matching the file's own existing convention — the
   original `2*complex(0,1)*vev` predecessor is preserved as a comment the
   same way).
2. `parameters.py`: one new `Parameter` block added, `GHphiphi` (`nature =
   'external'`, `lhablock = 'FRBlock'`, `lhacode = [3]` — matching the
   block/code the 2026-08-31 audit found in the actual 2026-08-26 production
   param cards, `Block frblock / 3 ... # GHphiphi`), placed immediately
   after `Mh2` for locality. Default value is the exact `M²=m_φ²` coupling,
   `−m_h²/v = −63.459361087483` GeV — a placeholder, not a claim about what
   any future run should use. **Corrected twice**:
   - `validation/SOL_REVIEW.md` "Additional issue #1" found the original
     default (−63.45936155377521) was copied from a theory-**invalid**
     phys-route grid point; replaced with the theory-valid λ1-route mφ=250
     anchor, −63.459361555950252.
   - `validation/SOL_FINAL_REVIEW.md` "Additional issue #4" then found that
     anchor's last ~8 digits were themselves the tanβ=4×10⁷
     `cos(atan(tanβ))` floating-point artefact `COUPLING_STUDY_REPORT.md`
     §5 calls "not real physics" — shipping that as the flagship default
     was internally inconsistent even though numerically harmless for any
     cross section. Replaced with the artefact-free exact value above,
     which needs no particular tanβ to be true.

**Sign convention**: `GHphiphi = Im(c)` where `c` is 2HDMC's
`get_coupling_hhh(1,2,2)` — i.e. `GHphiphi` is the *signed* imaginary part.
**Corrected**: an earlier version of this file claimed
`coupling_comparison/coupling_table.csv`'s `physical_2HDM_GeV` column
"report[ed] the same signed quantity" — that was false (the column was
built with `abs()`, `validation/SOL_REVIEW.md` item 2) and additionally
cited a `physical_2HDM_GeV` column inside `validation/numerical_crosschecks.csv`,
which does not exist. Both are fixed: `run_all_probes.py` no longer takes
`abs()`, so `coupling_table.csv:physical_2HDM_GeV` is now genuinely signed
(−63.459…, matching `GHphiphi`'s sign convention directly) — verify against
that column, not `numerical_crosschecks.csv`, before copying a value into a
param card.

**New finding, not previously stated anywhere in this campaign** (surfaced
by the adversarial review, `SOL_REVIEW.md` item 14): the **frozen original**
UFO's `GC_90 = 8i·Mh2²/vev` is **positive** imaginary, while the actual
physical coupling at every benchmark point tested is **negative** imaginary
(`physical_2HDM_GeV` < 0 throughout `coupling_table.csv`). So the frozen
production UFO's coupling has the wrong **sign**, in addition to being
20–46× the wrong **magnitude** (`COUPLING_STUDY_REPORT.md` §10). Irrelevant
for a single-diagram |M|² (only |coupling|² enters), but relevant the
moment any diagram interferes with this vertex.

**Stale caches removed**, not left to potentially shadow the edited source:
`model.pkl`, `py3_model.pkl`, and the two `*~` backup files were deleted
from the new copy (present in the original only as build/editor artifacts,
confirmed non-source in §1).

## 3. Required validation checklist

| Check | Result |
|---|---|
| Original UFO unchanged | CONFIRMED — `dihiggs_ufo/` never written to this session |
| External UFO imports | PARTIAL — see §4, no full MadGraph import available in this environment |
| All unrelated parameters/couplings unchanged | CONFIRMED — diff touches only the `GC_90` value line and adds one new `Parameter` block; every other line in both files is untouched (`externalization_diff.patch`) |
| Only intended trilinear becomes externally controllable | CONFIRMED — `grep -c "^GC_90\|^GHphiphi"` shows exactly one active definition of each; `V_7`'s vertex definition (`vertices.py`) is byte-identical to the original (diffed directly, §below) since it references `C.GC_90` by name and needs no edit |
| Parameter card exposes the value | CONFIRMED by construction — `lhablock='FRBlock', lhacode=[3]`, matching the block/code the prior audit found in real production param cards |
| Vertex uses external parameter | CONFIRMED — `GC_90` (now `complex(0,1)*GHphiphi`) is still the sole coupling on `V_7 = [H, h2, h2]` |
| UFO/2HDMC normalization is like-for-like (not asserted before the review) | CONFIRMED via `validation/SOL_REVIEW.md` item 14, independently checked: `V_10=[H,H,H]`'s `GC_94 = -6i·lam·vev = -3i·MH²/vev` (UFO's own hhh self-coupling) equals 2HDMC's `get_coupling_hhh(1,1,1) = -3i·v·Z1 = -3i·m_h²/v` at alignment (`Z1 = m_h²/v²` in every campaign CSV row); the UFO's `vev` and 2HDMC's `v` agree to 15 digits (246.2205690734859 vs 246.22056907348588). So `GC_90` and `get_coupling_hhh(1,2,2)` are directly, unit-for-unit comparable — this was previously assumed, not demonstrated, anywhere in the campaign. **Re-confirmed independently by a second, unrelated reviewer pass** (`validation/SOL_FINAL_REVIEW.md` A3/F29, computing `vev` from the UFO's own `aEWM1`/`Gf`/`MZ` rather than reading off `sm.get_v()`): `GC_94 = get_coupling_hhh(1,1,1) = -190.37808326245033i`, digit-for-digit. That second pass additionally anchored the **two**-identical-scalar case (`GC_93 = [G0,G0,H]` vs. the SM Feynman rule with its explicit 2! combinatorial factor, `validation/SOL_FINAL_REVIEW.md` A4) — confirming neither UFO nor 2HDMC carries a hidden identical-particle factor in either direction, a check `ufo/validation.md`'s first pass did not do. |

## 4. Smoke test performed, and what was NOT performed

**No local MadGraph (`mg5_aMC`) installation exists in this environment**
(`which mg5_aMC` → not found; no `MGME` directory under `dihiggs/2hdmc/`).
Per the mission's explicit restriction ("Do not run new MadGraph production
unless necessary to diagnose an actual blocker" / "a tiny import/
process-generation smoke test is allowed" — not required), a full UFO
import / process-generation test was **not performed**.

What **was** performed, as a partial substitute:
- `python3 -m py_compile couplings.py parameters.py` — both files
  syntactically valid.
- A direct Python import of both modules (`import parameters; import
  couplings`) inside the model directory succeeded with no errors, and
  confirmed `parameters.GHphiphi` constructs correctly (`name='GHphiphi',
  value=-63.459..., lhablock='FRBlock', lhacode=[3]`) and
  `couplings.GC_90.value == 'complex(0,1)*GHphiphi'` as a string, correctly
  referencing the new parameter object.

**Disposition:** this confirms the Python source is well-formed and the
object graph constructs correctly, but does **not** confirm MadGraph itself
can parse/import the model or generate a process from it — that check is
explicitly left open for whoever runs a real MadGraph session against this
directory before any production use, consistent with the mission's
instruction not to run a production campaign in this phase.
