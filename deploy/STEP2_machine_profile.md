# Step 2 — PC 식별 (machine_profile)

## 목적

Cursor/에이전트가 **「지금 이 PC가 GC1 장비인지, 데이터 PC인지」** 구분할 수 있게 합니다.

| 파일 | 위치 | GitHub |
|------|------|--------|
| **실제 프로필** | `Desktop\박은규\machine_profile.json` | ❌ 로컬 전용 |
| **GC1 템플릿** | `deploy/machine_profile.template.gc1.json` | ✅ |
| **데이터 PC 템플릿** | `deploy/machine_profile.template.data_pc.json` | ✅ |
| **차헌 참고** | `deploy/machine_profile.reference.chaheon.json` | ✅ |

## GC1 PC (은규) — 완료 checklist

- [x] `Desktop\박은규\machine_profile.json` 작성 (DESKTOP-MBGSSME)
- [x] repo에 템플릿 추가
- [ ] Cursor 채팅 시작 시 `@machine_profile.json` 또는 README 참고

## 다른 PC에서 새로 만들 때

```powershell
Get-CimInstance Win32_ComputerSystemProduct | Select-Object UUID
Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Cryptography' | Select-Object MachineGuid
```

템플릿 복사 → identifiers 채우기 → `machine_profile.json`으로 저장.

## 코드와의 관계

- **장비 PC 분기**: `gc_profiles.py` + `Desktop\...\gc_automation.env`
- **데이터 PC 분기**: `machine_profile.json` + `촉매 반응 계산.py` USER SETTINGS (Step 3)
