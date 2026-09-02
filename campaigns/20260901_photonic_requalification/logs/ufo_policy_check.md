# UFO policy check (read-only)

Performed 2026-09-01 as part of the photonic requalification. **No UFO was
modified by this campaign, and no MadGraph was run.** Verification record only.

## Finding: the "external GHphiphi" UFO does not yet expose GHphiphi

`~/atlas_dihiggs/dihiggs_ufo/` contains two UFO trees:

```
LLscalar_v3_UFO_original/
LLscalar_v3_UFO_external_GHphiphi/
```

- `diff -rq LLscalar_v3_UFO_original/ LLscalar_v3_UFO_external_GHphiphi/` returns
  **no output**: the trees are byte-identical, file for file.
- `grep -rn "GHphiphi" <tree>/*.py` matches **nothing** in either tree.

So `GHphiphi` is not exposed as an external parameter anywhere, and the directory
named `..._external_GHphiphi` is at present an unmodified copy.

**Weight of this evidence.** Both directories carry mtimes of 18:27:58 and
18:28:41 on 2026-09-01, and every file *inside* them carries a 2021 mtime with
permissions matching `LLscalar_v3_UFO.zip`. The most likely reading is that both
trees were extracted from that same archive minutes apart, in which case
"`diff` is empty" is close to tautological and is weak evidence on its own. The
`grep` result is the load-bearing one: **`GHphiphi` does not appear in either
tree**, so the external-coupling variant has not been built regardless of how the
directories came to exist.

Consequence for the next campaign: the external-`GHphiphi` / `EF_m2` prescription
has **no implementation yet**. This matches `state/CURRENT_CAMPAIGN.yaml`, which
records `PI_simplified` as `allowed: true, implemented: false`. Creating that UFO
is work still to be done, not an existing asset to reuse.

## The coupling actually used for production

`LLscalar_v3_UFO_original/couplings.py:372`:

```python
GC_90 = Coupling(name = 'GC_90', value = '8*complex(0,1)*Mh2**2/vev', ...)
```

attached to `Vertex(particles=[P.H, P.h2, P.h2])`. This is the vertex behind the
reused `sigma_LO`, and it is **not** the coupling the requalified decay point has
— see `validated/REQUALIFICATION_SUMMARY.md` section 5.

## Scope confirmations

- Neither UFO tree was modified by this campaign; no `.py`, `.dat` or `.pkl` file
  in either has a 2026 mtime. Both are untracked (`??`) in `dihiggs_ufo`'s git
  index, along with other local changes there that predate this work.
- `inputs/chris_original/` unmodified (mtimes 18:17:21–18:22:51, all earlier than
  every campaign output at 18:41+).
- `dihiggs` repo working tree is **clean**; the binaries built for this campaign
  land on gitignored paths (`2hdmc/lib/`, `2hdmc/CalcGen`, `2hdmc/CalcLH`,
  `dihiggs/app/`), confirmed with `git check-ignore`.
- Mixed benchmark not regenerated. No MadGraph run (no `MG_h2h2_LO/`,
  `mg5_cards/`, `xsec_mg_h2h2.csv`, `.lhe` or banner anywhere in the campaign).
  `sigma_LO` reused verbatim from Christopher's LaTeX.
