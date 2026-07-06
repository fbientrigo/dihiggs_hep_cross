# Contract — minimal recast output schema

Required columns for a first scalar LLP recast table:

| Column | Meaning | Status |
|---|---|---|
| `mass_gev` | LLP scalar mass | required |
| `total_width_gev` | total decay width | required or derived |
| `ctau_mm` | proper decay length | required or derived |
| `beta_gamma` | boost proxy or event-level value | proxy until MC |
| `lab_decay_length_mm` | beta_gamma * ctau | derived |
| `br_bb` | BR to bb | optional |
| `br_gg` | BR to gg | optional |
| `br_WW` | BR to WW | optional |
| `br_ZZ` | BR to ZZ | optional |
| `br_hadronic_proxy` | hadronic decay proxy | required |
| `p_single_decay_ID_4_300mm` | one-LLP ID decay probability | derived |
| `p_event_at_least_one_ID` | event-level ID probability | derived |
| `eps_vertex_proxy` | public/table efficiency or placeholder | required with quality flag |
| `eps_event_proxy` | public/table efficiency or placeholder | required with quality flag |
| `aeff_proxy` | acceptance times efficiency proxy | derived |
| `xsec_fb` | signal production cross section | required for yield |
| `nsig_139fb_proxy` | expected signal yield | derived |
| `quality_flag` | e.g. `TRUTH_PROXY`, `TABLE_INTERPOLATED`, `FULL_MC_REQUIRED` | required |
