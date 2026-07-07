# MadGraph input-deck templates (the basis)

These are **placeholder templates**, not runnable cards. They define the shape of
the MadGraph input decks that `scripts/12_prepare_madgraph_runs.py` renders, one
deck per 2HDMC priority point, into `outputs/madgraph_runs/<run_tag>/`.

This repository intentionally:

- does **not** ship a UFO/model (`{{MODEL}}` is a placeholder), and
- does **not** install MadGraph, and
- does **not** invent any cross section.

## Placeholders

Rendered by simple `{{KEY}}` substitution (see `llp_recast.madgraph.render_template`):

| Placeholder | Source |
|---|---|
| `{{POINT_ID}}` | priority-point id |
| `{{RUN_NAME}}` | sanitized run tag (`mg_<point_id>`) |
| `{{MODEL}}` | UFO/model name — placeholder until supplied |
| `{{PROCESS}}` | production process, default `g g > h2` |
| `{{SQRT_S_TEV}}` / `{{EBEAM_GEV}}` | collider energy and per-beam energy |
| `{{MH_GEV}}` / `{{WIDTH_GEV}}` / `{{BR_GAGA}}` | heavy-scalar mass, total width, and BR(gamma gamma) from the point |
| `{{GENERATED_AT}}` | UTC timestamp of generation |

## Files

- `proc_card.dat.tmpl` — production-only process card (no `H -> gamma gamma`; the
  branching ratio is applied downstream in `scripts/10_apply_sigma_inputs.py`).
- `run_card_fragment.dat.tmpl` — beam-energy fragment to merge into a default run card.
- `param_card_fragment.dat.tmpl` — mass/width fragment to map onto the real UFO's blocks.
- `run_commands.sh.tmpl` — documents the exact `mg5_aMC` command; runs nothing by default.

See `docs/contracts/madgraph_run_preparation_contract.md` for the full workflow.
