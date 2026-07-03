# P0-T — Workflow types (L4 #1–6)

| gate_id | symbol | assert |
|---------|--------|--------|
| P0-T-01-a-1 | `WorkflowMode` | OPJU_ONLY, CALC_ONLY, FULL_ARCHIVE |
| P0-T-02-a-1 | `WorkflowOptions` | frozen; opju_path, auto_archive, skip_stage4 |
| P0-T-03-a-1 | `Stage2Artifacts` | df, saved_excel, warnings, feed_source_desc |
| P0-T-04-a-1 | `OriginJobPayload` | opju_path, sample_name, identity_key, save_in_place, df |
| P0-T-05-a-1 | `build_origin_payload` | OPJU_ONLY → save_in_place False |
| P0-T-06-a-1 | `payload_row_count` | len(df) via O8 helper |

Module: `p0_types.py`
