# GC3 실데이터 — GC8860에서 검증 후 zip 재배포

GC3 PC에서 cmd가 닫히거나 `[건너뜀] ... 패턴 불일치` 가 수백 줄 나오면,  
**Chem32 폴더를 구글 드라이브로 보내서 여기(GC8860)에서 먼저 고칩니다.**

---

## GC3에서 보낼 것 (구글 드라이브)

**방법 A — 권장 (용량 작음)**  
Chem32에서 지금 돌리는 **시료 폴더 하나**만 zip:

```
C:\Chem32\1\Data\{시료 폴더 이름}\
```

예: `20260620 DRME(1.5) 600C NI5_CE5_AL2O3` 폴더 전체  
→ 안에 `REACTION 2026-...` / `001F0101.D` / `Report.TXT` 가 포함되어야 함.

**방법 B**  
`C:\Chem32\1\Data` 전체 (용량 크면 A 권장)

---

## GC8860에서 받는 위치

```
C:\Users\User\chemstation-gc-automation\testdata\gc3_real\
```

드라이브에서 zip 받은 뒤 위 폴더에 **압축 해제**  
(시료 폴더가 `gc3_real\20260620 DRME...\` 로 보이면 OK)

---

## 검증 실행 (Cursor / GC8860)

```bat
cd C:\Users\User\chemstation-gc-automation
gc_chem32_validate.bat --data-path testdata\gc3_real
```

엑셀까지 테스트:

```bat
gc_chem32_validate.bat --data-path testdata\gc3_real --run-pipeline
```

로그 파일 (항상 저장):

`Desktop\KCH\gc3_validate_log.txt`

---

## “불일치”가 많을 때 (지금 GC3에서 본 현상)

코드는 **시료 폴더 안 모든 REACTION 시퀀스·주입**을 시간순으로 모은 뒤,  
**첫 TCD 주입 패턴**만 기준으로 나머지를 맞춥니다.

→ 예전에 돌린 REACTION 이 같은 시료 폴더에 남아 있으면  
→ `[건너뜀] 패턴 불일치` 가 **대량**으로 나옵니다 (오류가 아니라 제외 로그).

여기서 로그 보고 **최신 시퀀스만 처리**하도록 코드를 고친 뒤,  
`gc3_make_deploy_zip.bat` → 드라이브 → GC3 에 **한 번만** 다시 배포합니다.

---

## GC3에 다시 넘길 때

1. `gc3_make_deploy_zip.bat`
2. 구글 드라이브 업로드
3. GC3: zip 덮어쓰기 (**`gc_automation.env` 는 유지**)
4. `gc_run_force.bat` 또는 `gc_start_watch.bat`

GC3에서 디버깅할 필요 없음.
