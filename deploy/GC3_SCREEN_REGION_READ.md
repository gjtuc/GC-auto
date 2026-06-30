# GC3 — 화면 영역 캡처·확대·글자 읽기 (미구현 아이디어)

> **상태:** **스켈레톤** (T83) — `gc3_screen_read.py` + `deploy/screen_regions.gc3.json` + `--dry-run`.  
> live OCR·GC3 PC 캘리브레이션은 GC3 앞에서 이어서.
> **목적:** 나중에 GC3 PC 앞에 앉았을 때 / Cursor로 다시 작업할 때 이 문서만 보면 방향을 잡을 수 있게.

---

## 왜 필요할 수 있는가

GC3는 **Chem32 `Report.TXT` 파일 파싱**이 주 경로 (`gc_chem32.py` → `gc_automation.py`).

그래도 아래처럼 **화면에서만 보이는 정보**가 필요해질 수 있음:

- Chem32 UI 상태·경고·진행 중 여부 (파일 생성 전)
- `Report.TXT` 형식과 UI 표시 불일치 검증
- Win7 + Chem32 환경에서 **원격 디버깅** (GC8860/Cursor는 GC3 화면을 직접 못 봄)
- Cursor 에이전트에게 “이 화면 읽어”를 **사용자 수동 스크린샷 없이** 돌리고 싶을 때

**전체 화면을 비전(이미지)으로 보내는 방식**은:

- 글씨가 작으면 **정확도 낮음**
- 이미지 토큰 **비용 큼**

→ **관심 영역만 자동 캡처 → (필요 시 2~3배 확대) → OCR 또는 작은 이미지만 분석**이 낫다.

---

## 중요: 수동이 아니라 자동화

| ❌ 이렇게 하면 의미 없음 | ✅ 이렇게 해야 함 |
|------------------------|------------------|
| 사용자가 Snipping Tool로 잘라서 채팅에 붙임 | 스크립트/bat가 **영역 캡처 → 크롭 → (확대) → 텍스트/PNG**까지 실행 |
| Cursor가 OS 화면에 직접 접근 | 에이전트는 **터미널 명령 한 번**만 실행하고 **출력(텍스트·파일 경로)**만 읽음 |

사용자는 “범례 읽어”, “상태창 확인”처럼 **말만** 하고,  
캡처·좌표·확대는 **로컬 도구**가 매번 처리.

---

## 전용 올인원 툴은 없음 — 레고 조립

**파이썬을 처음부터 큰 프로그램으로 짤 필요는 없음.**  
역할별로 이미 있는 것들을 `winget` / `pip` / Windows 기본으로 받아 **짧게 이어 붙이면** 됨.

| 단계 | 후보 | 비고 |
|------|------|------|
| 영역 캡처 | PowerShell + .NET, `mss` (pip), ShareX CLI | GC3는 **Win7** — 도구·Python 버전 호환 먼저 확인 |
| 크롭·확대 | ImageMagick (`magick -crop … -resize 200%`) | PNG 권장 |
| 글자 추출 | **Tesseract** CLI, Windows OCR API | 선명한 UI·로그·표는 **OCR이 비전보다 저렴·정확**한 경우 많음 |
| 에이전트 연동 | `gc_screen_read.bat legend` 같은 **고정 진입점** | Cursor는 이 명령만 호출 |

**접착제** (bat 10줄, PowerShell 20줄, 또는 Python 30줄)는 **반드시 한 번** 필요.  
“다운로드만 하면 Cursor가 알아서 화면 본다”는 제품은 **없다**고 보면 됨.

---

## GC3 PC에 붙일 때 제약

| 항목 | GC3 |
|------|-----|
| OS | Windows 7 |
| Cursor / Git | **없음** (USB zip 배포 — [`GC3_PC_SETUP.md`](GC3_PC_SETUP.md)) |
| 주 파이프라인 | `Report.TXT` — 화면 읽기는 **보조·검증·fallback** |
| 개발·테스트 | **GC8860**에서 mock/실데이터 검증 후 zip 재배포 |

구현 위치(안):

```
chemstation-gc-automation/
  gc3_screen_read.py              # T83 스켈레톤 (--dry-run list/read/probe)
  gc_screen_read.py               # GC1 Autochro (별도)
  deploy/screen_regions.gc3.json  # 창 제목 + 상대 좌표
```

GC3 zip에 포함 → `gc_automation.py` watch 루프에서 호출하거나,  
디버그용 `gc_screen_read.bat`만 바탕화면에 두는 식.

---

## 좌표 설계 (나중에 GC3 앞에서 1회)

1. **창 제목** (예: Chem32 메인) + **창 안 상대 (x, y, w, h)** — 절대 화면 픽셀만 두지 말 것  
2. DPI·해상도·창 위치 기록 (`1920×1080`, 배율 100% 등)  
3. `screen_regions.gc3.json` 예시:

```json
{
  "chem32_status_bar": {
    "window_title_contains": "ChemStation",
    "box": [0, 700, 800, 80],
    "scale": 2.0,
    "method": "ocr"
  }
}
```

4. 영역 이름으로 호출: `python gc_screen_read.py --region chem32_status_bar`

---

## OCR vs 비전 (Cursor 이미지)

| | OCR (로컬) | 크롭 PNG → 비전 |
|--|------------|-----------------|
| 비용 | 거의 0 | 작은 PNG면 전체 화면보다 ↓ |
| 자동화 | ✅ | ✅ |
| 적합 | 표·로그·상태 문자열 | 레이아웃·그래프·애매한 UI |
| GC3 무인 운영 | **우선 검토** | 에이전트 디버그·예외 시 |

---

## 구현 순서 (나중에)

1. GC3 PC 앞에서 **읽어야 할 UI 1~2곳** 확정 (Report로 안 되는 것만)  
2. GC8860에서 PowerShell/`mss` + Tesseract로 **프로토타입** (Win7 호환 확인)  
3. `gc_chem32_validate.bat` 옆에 `--screen-check` 같은 옵션으로 **로그만** 남기기  
4. 통과하면 `gc3_make_deploy_zip.bat`에 포함  

---

## 관련 문서

- [`GC3_PC_SETUP.md`](GC3_PC_SETUP.md) — GC3 배포·운영  
- [`GC3_DATA_HANDOFF.md`](GC3_DATA_HANDOFF.md) — 실데이터는 파일로 넘겨 GC8860에서 고침  
- [`docs/PC_NAMING.md`](../docs/PC_NAMING.md) — GC3 **장비 PC** vs **차헌 PC** 구분  
- 코드: `gc_chem32.py` (Report 파싱 — **주 경로**)

---

## 대화 메모 (2026-06-27)

- “픽셀 영역 지정 → 확대 → 읽기” 아이디어는 **맞음**. 다만 **사용자가 수동 캡처**하면 자동화가 아님.  
- Cursor 에이전트는 화면을 직접 못 보고, **로컬 스크립트 출력**만 읽을 수 있음.  
- 기능은 흩어진 CLI/OCR로 충분; **짧은 접착 + 영역 설정 JSON**이 핵심.
