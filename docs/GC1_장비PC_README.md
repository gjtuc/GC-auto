# GC1 장비 PC — `gc_automation.py` 안내

## 이 PC의 역할

**ChemStation이 설치된 GC1 장비 PC**입니다.  
여기서는 **KCH 원본 엑셀을 만들고 메일로 보내는 것**까지만 합니다.

수율/전환율 계산, G: 드라이브 정리, Origin 업데이트는 **은규 PC**에서 합니다.

---

## 동작 요약

1. ChemStation 시퀀스 완료 후 `Data` 폴더에 생성된 `F-....D` 주입 폴더들을 스캔
2. 각 폴더의 `sequence.acam_` 에서 피크 Area·RT 추출
3. KCH 형식 엑셀 (`YYYYMMDD 시료이름.xlsx`) 생성
4. 네이버 SMTP로 **은규 PC 메일**에 첨부 발송

---

## 은규가 GC1에서 수정할 항목

| 위치 | 내용 |
|------|------|
| `DEFAULT_CHEMSTATION_DATA` | GC1 ChemStation Data 경로 (보통 `C:\Users\Public\Documents\ChemStation\1\Data`) |
| `EXCEL_OUTPUT_DIR` | KCH 엑셀 임시 저장 경로 |
| `TARGET_EMAIL` (약 70행) | **은규 PC 네이버 메일** (현재 차헌 주소로 되어 있음) |
| `.env` | 발송용 `NAVER_EMAIL`, `NAVER_APP_PASSWORD` — 은규 또는 장비 PC 전용 계정 |

---

## 실행 예

```powershell
# 시퀀스 날짜·시료명 지정
python gc_automation.py --sequence-date 20260613 --sample-name "Ni10-Al2O3 DRE@600"

# 메일 없이 엑셀만
python gc_automation.py --sequence-date 20260613 --sample-name "시료" --no-email
```

---

## 아직 구현되지 않은 것 (GC2/GC3 장비 PC 참고)

차헌 GC2 쪽에서 논의된 **Post-run 매크로·폴더 감시**는 이 사본에 없습니다.  
시퀀스 종료 후 지금은 **수동으로** 위 명령을 실행합니다.

---

## 다음 단계

1. 본 README와 `gc_automation.py` 주석으로 1단계 이해
2. `00_먼저_읽기_인수인계_설명.md` 로 전체 구조 확인
3. `02_데이터PC_은규/` 내용을 **은규 PC**로 옮겨 2~4단계 세팅
