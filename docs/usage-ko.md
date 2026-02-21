# Secure XL2HWP Local - 사용 가이드 (KO)

이 문서는 로컬 또는 폐쇄망 환경에서 서비스를 설치하고 사용하는 방법을 안내합니다.

## 1. 이 서비스가 하는 일
- 엑셀 데이터를 구조화된 결과물과 한컴 연계용 페이로드로 변환합니다.
- `contracts`, `profiles`, `templates` 스펙 기반으로 같은 입력에 같은 결과를 재현합니다.
- JWT 인증, 역할 기반 권한, 감사로그, 서명 내보내기, 경로 제한을 제공합니다.

## 2. 준비 사항
- Python `3.10+`
- macOS/Linux 쉘 환경 (`zsh/bash` 예시 사용)
- 선택: Ollama (로컬 LLM 기능이 필요할 때)

## 3. 설치
```bash
cd secure-xl2hwp-local
python3 -m venv .venv
source .venv/bin/activate
pip install '.[dev]'
cp .env.example .env
python scripts/create_sample_excel.py
```

## 4. 보안 설정
`.env`에서 아래 값을 강한 값으로 변경하세요.
- `JWT_SECRET_KEY`
- `AUTH_PASSWORD_PEPPER`
- `EXPORT_SIGNING_KEY`

정책값도 함께 점검하세요.
- `PROCESS_ALLOWED_ROLES`
- `AUTH_LOGIN_MAX_FAILURES`, `AUTH_LOGIN_WINDOW_SECONDS`, `AUTH_LOGIN_LOCK_SECONDS`
- `ALLOWED_INPUT_BASE_DIR`, `ALLOWED_OUTPUT_BASE_DIR`, `ALLOWED_TEMPLATE_BASE_DIR`

## 5. 첫 관리자 계정 생성
보안상 기본 `specs/security/users.yaml`은 비어 있습니다.

비밀번호 해시 생성:
```bash
python scripts/hash_password.py \
  --password 'StrongPassword!' \
  --pepper 'YOUR_AUTH_PASSWORD_PEPPER'
```

`specs/security/users.yaml`에 사용자 등록:
```yaml
users:
  - user_id: "local-admin"
    role: "Admin"
    password_hash: "PASTE_HASH_HERE"
    active: true
```

역할 설명:
- `Admin`: 처리 + 감사 + 내보내기
- `Auditor`: 감사 + 내보내기
- `Analyst`: 처리 전용 (`PROCESS_ALLOWED_ROLES` 설정에 따름)

## 6. 서비스 실행
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8080
```

UI 접속:
- `http://127.0.0.1:8080/`

## 7. UI 사용 흐름 (권장)
1. 관리자 계정으로 로그인합니다.
2. `Path Mode` 또는 `File Mode`를 선택합니다.
3. 파이프라인을 실행합니다.
4. 메트릭, 아티팩트, 응답 JSON을 확인합니다.
5. 감사/운영 패널을 확인합니다.
6. 서명된 ZIP 내보내기 후 검증 센터에서 무결성 검증을 수행합니다.

첫 실행에서는 로그인 패널 상단에 관리자 계정 생성 온보딩 카드가 표시되며, 한국어/영어 토글을 지원합니다.

## 8. API 빠른 확인
로그인:
```bash
curl -sS -X POST http://127.0.0.1:8080/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"local-admin","password":"StrongPassword!"}'
```

경로 기반 처리:
```bash
TOKEN="<access_token>"
curl -sS -X POST http://127.0.0.1:8080/process/path \
  -H "Authorization: Bearer $TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{
    "input_path":"examples/input/sample_projects.xlsx",
    "output_dir":"examples/output",
    "contract_name":"default",
    "profile_name":"default",
    "template_name":"default",
    "template_path":"examples/input/sample_report_template.txt"
  }'
```

## 9. Ollama 설정 (선택)
```bash
ollama pull qwen2.5:7b
ollama pull qwen2.5:14b
```

Ollama를 사용하지 않으면 `.env`에서 `ENABLE_LLM=false`로 설정하세요.

## 10. 문제 해결
- `401 Invalid credentials`
  - `users.yaml`에 활성 사용자(`active: true`)가 있는지, 같은 `AUTH_PASSWORD_PEPPER`로 해시를 만들었는지 확인하세요.
- `429 Too many failed login attempts`
  - 잠금 시간(`AUTH_LOGIN_LOCK_SECONDS`) 후 재시도하거나 정책값을 조정하세요.
- `400 ... must stay under configured base directory`
  - `input_path`, `output_dir`, `template_path`가 허용된 기준 디렉터리 밖입니다.
- `403 Insufficient role`
  - 해당 API를 호출할 권한 역할이 아닙니다.
- `413 exceeds max size limit`
  - `MAX_UPLOAD_MB`를 늘리거나 업로드 파일 크기를 줄이세요.

## 11. 관련 문서
- 아키텍처: `docs/architecture.md`
- SpecKit 운영: `docs/speckit.md`
- CoT 단계 설계: `docs/cot.md`
- 오프라인 배포: `docs/offline-deploy.md`
