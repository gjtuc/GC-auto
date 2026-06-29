# GC1 화면 읽기(눈) — 배율·캘리브레이션

> **상태:** `gc_screen_read.py` 단독 모듈 (gc_autochro **미병합**)  
> GC3 아이디어: [`GC3_SCREEN_REGION_READ.md`](GC3_SCREEN_REGION_READ.md)

---

## 왜 필요한가

Autochro 단계마다 **화면으로만 확인**할 것이 많음:

- 아래 피크 표 숫자 (MTD 적용 / 초기화 후 0)
- 분석목록·제어목록 탭 파란 선택
- 왼쪽 트리 시료명 = 제어목록 데이터명
- 우클릭 메뉴 글자 (초기화, 분석방법 불러오기 …)

`pywinauto`만으로는 「읽었다」는 검증이 약함 → **영역 캡처 + OCR**.

---

## 4배 × 4배 연쇄에 대해

**전체 화면을 4배 → 그걸 다시 4배** 하면 (16배):

- 메모리·파일 커짐
- 픽셀이 뭉개져 OCR이 **더 나빠질** 수 있음

권장: **잘라낸 뒤 단계별 확대** (기본값 `deploy/screen_regions.gc1.json`)

| 단계 | 배율 | 대상 | 예 |
|------|------|------|-----|
| **full** | **1.0×** | Autochro 창 전체 | 탭 글자, 트리 시료명 |
| **panel** | **2.5×** | 패널 크롭 | 시료 표, 아래 피크 표 |
| **fine** | **3.5×** | panel 결과 위 추가 확대 | RT·면적 숫자, 작은 한글 |

한 셀 기준 **실효 배율** ≈ 2.5 × 3.5 ≈ **8.7×** — 4×4(16×)보다 작고 선명.

### 배율 조정 가이드

| 증상 | 조치 |
|------|------|
| 글자 잘림·너무 큼 | `fine` 3.5 → **2.5** |
| 숫자 인식 실패 | `panel` 2.5 → **3.0**, `fine` **4.0** |
| 탭/트리만 읽으면 됨 | `fine` 단계 끄거나 region `stage: panel` 만 |

환경변수로 덮어쓰기: `screen_regions.gc1.json` 의 `zoom_pipeline` 수정.

---

## 설치 (GC1 장비 PC)

```bat
pip install -r requirements-screen.txt
```

[Tesseract Windows](https://github.com/UB-Mannheim/tesseract/wiki) + **kor** 언어팩.

```bat
set TESSERACT_CMD=C:\Program Files\Tesseract-OCR\tesseract.exe
```

---

## 사용법

Autochro 켜 둔 상태:

```bat
gc_screen_read.bat calibrate --region bottom_peak_table
gc_screen_read.bat read --region bottom_peak_table_fine
gc_screen_read.bat task verify_peak_table_has_data
gc_screen_read.bat find --region top_sample_table --text 초기화
gc_screen_read.bat click --region top_sample_table --text 초기화 --button left
gc_screen_read.bat probe
gc_screen_read.bat focus --show-focus --region top_sample_table
```

### 실시간 포커스 네모 (속이 빈 빨간 테두리)

캡처 참고 사진처럼 **지금 읽는 영역**만 화면 위에 잠깐 표시:

```bat
gc_screen_read.bat read --show-focus --region top_sample_table
set GC_SCREEN_SHOW_FOCUS=1
set GC_SCREEN_FOCUS_MS=1200
```

- 빨간 네모 = OCR 직전 영역 (창 전체 → 패널 순)
- 클릭 시 찾은 글자 주위에 더 작은 네모
- 배경 투명, 클릭은 Autochro로 통과
- `--show-focus` 없으면 네모 없이 백그라운드만

캡처 PNG: `%USERPROFILE%\.cursor\gc-screen-capture\`

---

## 영역 정의

`deploy/screen_regions.gc1.json` — 창 안 **상대 좌표** (0~1).

캘리브레이션:

1. `calibrate --region …` 로 PNG 확인
2. 잘리면 해당 region 의 `box` [x,y,w,h] 조정
3. `display_profile` 에 해상도·배율 기록 (1920×1080, 100%)

---

## 클릭 반복 루프 (개념)

1. `read` / `find` 로 글자·숫자 확인  
2. `click --text …` 로 메뉴·항목 클릭  
3. 화면 바뀌면 다음 region `read`  

병합 시 `gc_autochro` 각 단계 뒤에 `task verify_*` 호출.

---

## 관련

- `gc_autochro.py` — 손 (UI 자동화)
- `gc_screen_read.py` — 눈 (OCR·검증·클릭 보조)
