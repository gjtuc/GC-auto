# Gate Leaf Catalog — 색인

> L7/L8 전개. 상위: [`DESIGN_LEPTON.md`](../../DESIGN_LEPTON.md)

## O0 Pure (61 L4) — ✅ 전량

| L1 | 파일 | L4 | L7≈ | L8≈ |
|----|------|-----|-----|-----|
| T | [O0-T.md](O0-T.md) | 6 | 18 | 12 |
| K | [O0-K.md](O0-K.md) | 9 | 36 | 27 |
| I | [O0-I.md](O0-I.md) | 9 | 45 | 36 |
| C | [O0-C.md](O0-C.md) | 11 | 44 | 33 |
| S | [O0-S.md](O0-S.md) | 16 | 64 | 48 |
| M | [O0-M.md](O0-M.md) | 10 | 40 | 30 |

## O5 Worksheet — ✅ **117 L4 전량 설계**

| 파일 | L4 | L7/L8 |
|------|-----|-------|
| **[O5-REGISTRY.md](O5-REGISTRY.md)** | **117** | **마스터 순서 #1–117** |
| [O5-I.md](O5-I.md) | 24 | I-01(12)+I-02(12) |
| [O5-T.md](O5-T.md) | 27 | T-01..04 |
| [O5-M.md](O5-M.md) | 59 | M-01..04 + DEBUG + E2E |
| [FX-O5-opju-mock.yaml](FX-O5-opju-mock.yaml) | — | L8 shared |
| [gates/O5/](gates/O5/) | 2+ | YAML per L4 목표 |

## O1–O9 (기타)

| L0 | 파일 | L4 | 상태 |
|----|------|-----|------|
| O1-P | [O1-P.md](O1-P.md) | 18 | L7/L8 전량 |
| O1-W,I / O2–O4 / O6–O9 | [_TEMPLATE.md](_TEMPLATE.md) | ~200 | 양식만 |

## O5 rollup

| rollup_id | gates | count |
|-----------|-------|-------|
| O5-L2-I01 | O5-I-01-* | 12 |
| O5-L2-I02 | O5-I-02-* | 12 |
| O5-L1-I | #1–24 | 24 |
| O5-L2-T01..T04 | | 27 |
| O5-L1-T | #25–51 | 27 |
| O5-L2-M01..M04 | | 54 |
| O5-L1-M | #52–105 | 54 |
| O5-DEBUG | #106–110 | 5 (opt) |
| O5-E2E | #111–113 | 3 |
| O5-R | #114–117 | 4 |
| **O5 core** | #1–105 | **105** |

## 구현 포인터

```
NEXT code: O5-I-01-a-1  (registry #1)
설계: O5-REGISTRY.md 형제 순서 = verify 체인
```
