# Audit: event-efficiency values above 1

**Trigger:** a request to audit reports of a trackless event-efficiency value
around 1.52 in `fig02_trackless_event_efficiency.png` (this repo's current
figure is `outputs/figures/fig2_event_efficiency_vs_sumpt.png`).

## Result

**No value of 1.52 exists anywhere in this pipeline's data.** The maximum
value found, in the raw HEPData YAML, the tidy CSV, and the plotted figure
alike, is **1.1851**. The 1.52 figure from the request does not match this
repo's current data or figures — flagging this mismatch rather than
silently substituting a number, since it means the report was either from a
stale run, a different figure, or a misremembered value.

## Full trace (source YAML -> radial region -> Sumpt bin -> value)

| Stage | Value |
|---|---|
| Source YAML | `event_efficiency_trackless_r_1150_mm.yaml`, line 12: `value: 1.1851` |
| Radial region | `R < 1150 mm` (filename-encoded; see `EVENT_EFFICIENCY_RADIAL_CATEGORIES` in `src/llp_recast/plots.py`) |
| Dependent variable | `header: {name: Efficiency}` |
| Qualifiers | `Luminosity=139 fb^-1; Energy=13 TeV` |
| Sumpt bin | `[0.6, 0.8)` GeV (7th independent-variable bin, 0-indexed: 3) |
| Raw value | `1.1851` (stat error `0.016449`) |
| Tidy value (`outputs/hepdata_tidy/event_efficiency_trackless.csv`, row 3) | `1.185100` — exact match |
| Plotted value (`outputs/figures/fig2_event_efficiency_vs_sumpt.png`, orange curve peak) | `1.1851` — exact match, visually confirmed |

A second table also exceeds 1: `event_efficiency_highpt_r_1150_mm.yaml`
peaks at `1.0149`. All other event-efficiency tables (`_1150_3870_mm`,
`_3870_mm`, both trackless and highpt) stay within [0, 1]. A full sweep of
every tidy CSV in `outputs/hepdata_tidy/` confirms no other `value` column
labeled as an efficiency/probability exceeds 1; the only other columns with
values above 1 are `excl_xsec_ewk.csv` (cross sections in fb, expected to be
large) and the yield tables (event counts, expected to be large) — neither
is a probability or efficiency and both are correctly unbounded.

## Root cause

None of options 3-5 from the audit brief apply: no duplication, no
misparsed `Sumpt` bins, no incorrectly collapsed qualifiers. The tidy
extraction (`scripts/02_hepdata_tidy_extract.py`) and the plot data-prep
(`prepare_fig2_event_efficiency` in `src/llp_recast/plots.py`) both pass the
raw HEPData `value` through unmodified — no summation, no renormalization.

Option 1 applies: **HEPData's `Efficiency` column here is a published
reinterpretation-recipe weight, not a pure pass/total probability.** The
submission metadata (`submission.yaml`) explicitly labels these tables
`description: 'Reinterpretation Material: Event-level Efficiency for
Trackless SR selections, R < 1150 mm'` and lists SUSY EWK reactions
(gluino/chargino/neutralino pair production) as the associated physics
process. What mechanism produces values above 1 (a correction factor,
overlapping-selection double-counting in ATLAS's own definition, a
per-event weight normalized to something other than a simple denominator)
is not stated in the local YAML/submission metadata we have, and is not
asserted here — only that the value is genuinely published as >1, and is
not a plotting or data-prep artifact on our side.

## Action taken

- No clipping. Raw values preserved exactly through tidy CSV and plot.
- Figure 2 in `outputs/figures/` already carries the
  `HEPDATA_DERIVED_SHAPE; EWK_BENCHMARK_NOT_SCALAR_S; NEEDS_REAL_SIGNAL_MC`
  flags. The new audited figure (`outputs/figures_v2/figB_...`, see
  `scripts/05_make_interpretation_figures.py`) adds an explicit annotation
  on the >1 point plus the label `HEPData benchmark parameterization, not
  universal probability`.
- This document and `docs/recast/efficiency_semantics.md` are the permanent
  record of the audit; see also
  `outputs/chat_summaries/anomalies_and_caveats.json`.
