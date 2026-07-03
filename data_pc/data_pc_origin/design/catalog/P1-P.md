# P1-P — Stage2 metadata → OriginJobPayload (L4 #11–18)

| gate_id | symbol | assert |
|---------|--------|--------|
| P1-P-01-a-1 | `Stage2Metadata` | frozen; sample_name, identity_key, saved_excel |
| P1-P-02-a-1 | `validate_sample_name` | non-empty strip |
| P1-P-03-a-1 | `validate_identity_key` | 2-tuple str |
| P1-P-04-a-1 | `mapping_subset_for_df` | H2+CO2 in full df |
| P1-P-05-a-1 | partial df | 6/8 mapping cols (DRE live) |
| P1-P-06-a-1 | `skipped_mapping_columns` | CH4 Conv, C2H6 pct missing |
| P1-P-07-a-1 | `assemble_stage2_metadata` | from 촉매-shaped args |
| P1-P-08-a-1 | `build_payload_from_stage2` | → `OriginJobPayload` |

Module: `p1_payload.py`

선행: P0 PASS · O0-M mapping
