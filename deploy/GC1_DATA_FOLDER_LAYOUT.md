# GC1 `Desktop\박은규` 폴더 레이아웃

은규 사용자는 **데이터만** 보면 됩니다. 자동화·Cursor 연동 파일은 하위 폴더에 둡니다.

## 구조

```
Desktop\박은규\
  *.xlsx, *.pdf          … 실험 데이터 (은규 확인)
  _GC자동화\             … watch·env·로그·bat (운영/에이전트)
```

## `_GC자동화` 안에 있는 것

| 종류 | 예 |
|------|-----|
| env | `gc_automation.env` |
| watch | `.gc_watch_status.json`, `GC_감시_상태.txt`, `GC_대기_*.txt` |
| 핫스팟 에이전트 | `.gc_hotspot_agent_*.log/json` |
| 오류 복구 | `GC_오류_최근.txt`, `.gc_error_*` |
| 바로가기 bat | `GC1_동작해줘.bat`, `GC1_감시시작.bat` |

## 코드에서의 규칙

- `EXCEL_OUTPUT_DIR` = 데이터 루트 (`박은규`) — xlsx·pdf·PDF glob
- `gc_runtime_dir()` / `paths_for_output_dir()["runtime_dir"]` = `_GC자동화` — 상태·env·watch
- `gc_automation.py` 시작 시 `migrate_gc1_runtime_layout()` — 루트·바탕화면 `KCH` 잔여 파일 자동 정리
- GC1 PC에 `Desktop\KCH` 가 생기면 (env 미로드 등) 내용을 `_GC자동화`로 합친 뒤 빈 폴더 삭제 — **GC2/GC3 장비 PC의 KCH 폴더와 무관**

## OCR·학습 (PC 전역, 박은규 밖)

- `%USERPROFILE%\.cursor\gc-ocr-learnings\` — overlay·run_journal
- `%USERPROFILE%\.cursor\gc-ocr-case-study\` — 실패 케이스 JSON

변경일: 2026-06-30
