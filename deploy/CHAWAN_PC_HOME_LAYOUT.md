# 차완 PC 운영 폴더 레이아웃

> **script_dir:** `%USERPROFILE%\gc-data-pc-chawan\`  
> **실험 데이터:** `Desktop\kier\촉매 반응 결과\` (G: 미사용)

## 구조

```
gc-data-pc-chawan\
├── 촉매 반응 계산.py       ← repo data_pc/ 에서 Copy-Item
├── runtime_paths.py
└── KCH\
    ├── processed\          ← 계산완료 xlsx 검토용
    └── machine_profile.json← reaction_roots, origin_seed (Git 제외)

Desktop\kier\촉매 반응 결과\
├── DRE\                    ← 실험 폴더 체인
├── DRM\
└── DRME\
```

## 차헌 PC와 차이

| | 차헌 PC | 차완 PC |
|---|---------|---------|
| script_dir | `Desktop\.cursor\` | `gc-data-pc-chawan\` |
| [1단계] 입력 | IMAP 메일 | **Downloads** xlsx |
| [3단계] 저장 | G: 드라이브 | **kier\촉매 반응 결과** |
| env | `gc_automation.env` (IMAP) | **불필요** (메일 없음) |

## 설치 스크립트

[`docs/차완PC_Cursor_시작.md`](../docs/차완PC_Cursor_시작.md) §2 참고.
