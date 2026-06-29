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

## P층 — 메일·엑셀 ↔ Origin (55 L4 설계)

| L0 | 파일 | L4 | 상태 |
|----|------|-----|------|
| **P-REGISTRY** | [P-REGISTRY.md](P-REGISTRY.md) | 55 | P0 **PASS** |
| P0-T,R | [P0-T.md](P0-T.md) · [P0-R.md](P0-R.md) | 10 | 구현 **PASS** |
| P1-P | [P1-P.md](P1-P.md) | 8 | 구현 **PASS** |
| P2 | [P2.md](P2.md) | 6 | 구현 **PASS** |
| P3-S | [P3-S.md](P3-S.md) | 4 | 구현 **PASS** |
| P4 | [P4.md](P4.md) | 6 | 구현 **PASS** |
| P5 | [P5.md](P5.md) | 9 | 구현 **PASS** |
| P6 | [P6.md](P6.md) | 8 | 구현 **PASS** |
| P7 | [P7.md](P7.md) | 4 | 구현 **PASS** |
| P8-B | [P8-B.md](P8-B.md) | 4 | 구현 **PASS** |
| P9-L | [P9-L.md](P9-L.md) | 4 | 구현 **PASS** |
| P10-F,M | [P10.md](P10.md) | 7 | 구현 **PASS** |
| P11-K | [P11.md](P11.md) | 4 | 구현 **PASS** |
| P12-F | [P12.md](P12.md) | 4 | 구현 **PASS** |
| P13-I,M | [P13.md](P13.md) | 8 | 구현 **PASS** |
| P14-R,J | [P14.md](P14.md) | 8 | 구현 **PASS** |
| P15-S,H | [P15.md](P15.md) | 8 | 구현 **PASS** |
| P16-W,H | [P16.md](P16.md) | 8 | 구현 **PASS** |
| P17-E,H | [P17.md](P17.md) | 8 | 구현 **PASS** |
| P18-P,L | [P18.md](P18.md) | 8 | 구현 **PASS** |
| P19-V,R | [P19.md](P19.md) | 8 | 구현 **PASS** |
| P20-M,H | [P20.md](P20.md) | 8 | 구현 **PASS** |
| P21-C,H | [P21.md](P21.md) | 8 | 구현 **PASS** |
| P22-A,H | [P22.md](P22.md) | 8 | 구현 **PASS** |
| P23-G,H | [P23.md](P23.md) | 8 | 구현 **PASS** |
| P24-O,H | [P24.md](P24.md) | 8 | 구현 **PASS** |
| P25-N,H | [P25.md](P25.md) | 8 | 구현 **PASS** |
| P26-W,H | [P26.md](P26.md) | 8 | 구현 **PASS** |
| P27-G,H | [P27.md](P27.md) | 8 | 구현 **PASS** |
| P28-M,H | [P28.md](P28.md) | 8 | 구현 **PASS** |
| P29-G,H | [P29.md](P29.md) | 8 | 구현 **PASS** |
| P30-G,H | [P30.md](P30.md) | 8 | 구현 **PASS** |
| P31-M,H | [P31.md](P31.md) | 8 | 구현 **PASS** |
| P32-G,H | [P32.md](P32.md) | 8 | 구현 **PASS** |
| P33-G,H | [P33.md](P33.md) | 8 | 구현 **PASS** |
| P34-G,H | [P34.md](P34.md) | 8 | 구현 **PASS** |
| P35-G,H | [P35.md](P35.md) | 8 | 구현 **PASS** |
| P36-G,H | [P36.md](P36.md) | 8 | 구현 **PASS** |
| P37-G,H | [P37.md](P37.md) | 8 | 구현 **PASS** |
| P38-G,H | [P38.md](P38.md) | 8 | 구현 **PASS** |

## 구현 포인터

```
DONE: P38 — GitHub refresh P36–P37
verify: python -m data_pc_origin.verify --p38   # 286 gates
P38: python -m data_pc_origin.live_p38_github_refresh [--sync] [--push]
P37: python -m data_pc_origin.live_p37_github_push [--push]
P36: python -m data_pc_origin.live_p36_github_refresh [--sync] [--push]
P35: python -m data_pc_origin.live_p35_github_push [--push]
P34: python -m data_pc_origin.live_p34_github_refresh [--sync] [--push]
P33: python -m data_pc_origin.live_p33_github_push [--push]
P32: python -m data_pc_origin.live_p32_github_refresh [--sync] [--push]
P31: python -m data_pc_origin.live_p31_merge_pr [--pr]
P30: python -m data_pc_origin.live_p30_github_push [--push]
P29: python -m data_pc_origin.live_p29_github_refresh [--sync] [--push]
MERGE: python -m data_pc_origin.live_merge_readiness [--pr]
GITHUB: python -m data_pc_origin.live_github_refresh [--sync] [--push]
WATCH: python -m data_pc_origin.live_watch_resident [--delegate]
OPS: python -m data_pc_origin.live_ops_rollup [--tick]
```
