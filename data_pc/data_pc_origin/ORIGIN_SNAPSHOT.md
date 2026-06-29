# Origin 자동화 스냅샷 — `feat/data-pc-origin`

> **main에 병합하지 않은 백업 브랜치**. 문제 시 이 브랜치에서 복구.

## 포함 (P23 sync 2026-06-29 01:41 UTC)

- `data_pc/data_pc_origin/` — O0..O9 + P층 (158 gates)
- `data_pc/data_pc_runtime/` — L0..L4 supervisor
- `data_pc/data_pc_watch.py` · `data_pc_watchdog.py` · autostart bat/VBS
- `data_pc/촉매 반응 계산.py` — origin pipeline 위임

## 검증 (repo `data_pc` 기준)

```bash
cd data_pc
python -m data_pc_origin.verify --p26
python -m data_pc_origin.live_ops_rollup
```

## 운영 PC

차헌 PC 실사용: `Desktop\.cursor\` — P23 harness가 GC-auto-push로 sync.
