# secure-xl2hwp-local

로컬 보안 환경에서 엑셀 데이터를 자동 추출/정제하고, 한컴 문서 템플릿으로 넘기는 `SpecKit + CoT` 서비스입니다.

## 이번 버전 핵심 기능
- `SpecKit`: 계약/프로필/템플릿 스펙 기반으로 파이프라인 제어
- `CoT 파이프라인`: 스키마 추론 -> 정제 조언 -> 문서 매핑 단계 분리
- `한컴 템플릿 고도화`: 템플릿 placeholder 감지 + 변환 규칙 + 표 섹션 자동 생성
- `JWT 인증`: `/auth/login`, `/auth/me`, 보호된 처리 API
- `감사로그`: 로그인/처리 시작/성공/실패를 `jsonl`로 기록
- `오프라인 배포`: wheel 번들 생성 및 air-gapped 설치 스크립트 제공

## 모델 추천 (기본값)
- Primary SLM: `qwen2.5:7b`
- Fallback SLM: `qwen2.5:14b`

LLM이 내려가도 결정론적 파이프라인이 계속 동작합니다.
또한 `LLM_UNAVAILABLE_COOLDOWN_SECONDS`(기본 20초)로 일시적인 연결 실패 시 재시도 폭주를 줄입니다.

## 프로젝트 구조
```text
app/
  api/                 # API schemas
  connectors/          # Optional Hancom Windows COM connector
  core/                # Settings, logging
  pipeline/            # CoT orchestrator
  services/            # Auth/Audit/SpecKit/Template/Export/Pipeline
specs/
  contracts/           # Data contract YAML
  profiles/            # Cleanup profile YAML
  templates/           # Hancom template mapping profile YAML
  security/            # Local users registry YAML
scripts/
examples/
docs/
```

## 빠른 시작
```bash
cd secure-xl2hwp-local
python3 -m venv .venv
source .venv/bin/activate
pip install '.[dev]'
cp .env.example .env
python scripts/create_sample_excel.py
```

### Ollama 모델 준비 (선택)
```bash
ollama pull qwen2.5:7b
ollama pull qwen2.5:14b
```

Ollama를 쓰지 않으면 `.env`에서 `ENABLE_LLM=false`로 설정합니다.

## 인증 (JWT)

### 기본 계정 제거됨
- 저장소 기본 `specs/security/users.yaml`은 비어 있습니다.
- 서비스 사용 전, 조직 정책에 맞는 계정을 직접 등록해야 합니다.

운영 전 필수:
1. `.env`의 `JWT_SECRET_KEY`, `AUTH_PASSWORD_PEPPER`, `EXPORT_SIGNING_KEY`를 강한 값으로 설정
2. `scripts/hash_password.py`(기본 pbkdf2)로 비밀번호 해시 생성 후 `specs/security/users.yaml` 작성
3. 처리 권한 역할은 `PROCESS_ALLOWED_ROLES`로 제한
4. 로그인 보호 정책(`AUTH_LOGIN_MAX_FAILURES`, `AUTH_LOGIN_WINDOW_SECONDS`, `AUTH_LOGIN_LOCK_SECONDS`) 점검
5. 경로 제한 정책(`ALLOWED_INPUT_BASE_DIR`, `ALLOWED_OUTPUT_BASE_DIR`, `ALLOWED_TEMPLATE_BASE_DIR`) 점검

### 계정 등록 예시
```bash
# 1) 해시 생성 (기본: pbkdf2_sha256)
python scripts/hash_password.py --password 'StrongPassword!' --pepper 'YOUR_AUTH_PASSWORD_PEPPER'

# 2) specs/security/users.yaml 작성
cat > specs/security/users.yaml <<'YAML'
users:
  - user_id: "local-admin"
    role: "Admin"
    password_hash: "PASTE_HASH_HERE"
    active: true
YAML
```

### 로그인
```bash
curl -sS -X POST http://127.0.0.1:8080/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"user_id":"local-admin","password":"StrongPassword!"}' | jq
```

### 내 정보 확인
```bash
TOKEN="<access_token>"
curl -sS http://127.0.0.1:8080/auth/me \
  -H "Authorization: Bearer $TOKEN" | jq
```

### 로그인 보호 상태 확인 (Admin/Auditor)
```bash
TOKEN="<access_token>"
curl -sS http://127.0.0.1:8080/auth/guard/state \
  -H "Authorization: Bearer $TOKEN" | jq
```

### 비밀번호 해시 생성
```bash
# default: pbkdf2_sha256
python scripts/hash_password.py --password 'StrongPassword!' --pepper 'your-pepper'

# optional: legacy sha256
python scripts/hash_password.py --algo sha256 --password 'StrongPassword!' --pepper 'your-pepper'
```

## 실행

### API 실행
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8080
```

### 웹 스튜디오 UI
- URL: `http://127.0.0.1:8080/`
- 기능:
  - 서비스 브리프 패널(처리 스키마, 인증/서명 모드, trust boundary, review flow)
  - 첫 진입 관리자 온보딩 카드(계정 미구성 시 생성 단계 안내, `한국어/English` 토글 반영)
  - 로그인/JWT 세션 관리
  - Path/File 모드 실행
  - 메트릭/아티팩트/응답 JSON 시각화
  - 최근 감사 이벤트 타임라인
  - 언어 토글(`한국어/English`)
  - 테마 토글(`Light/Dark`)
  - 브랜드 프리셋(`Aqua/Ember/Slate`)
  - 운영 차트(상태 분포/시간대 처리량/상위 실행자)
  - 운영 필터(기간/상태/이벤트 타입/실행자 검색) + 자동 새로고침 + 이상징후 플래그
  - 서명된 운영 데이터 내보내기 ZIP(원본 + `.sig.json` 매니페스트)
  - 서명 검증 센터(원본 파일 + `.sig.json` 업로드 검증)
  - 시스템 레디니스 점검(스펙/감사저장소/서명설정/LLM 연결)

### 보호된 처리 API 호출
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
  }' | jq
```

에러 응답은 `request_id`를 포함하며, 파일 미존재는 `404`, 권한 부족은 `403`, 업로드 용량 초과는 `413`을 반환합니다.

### CLI 실행
```bash
secure-xl2hwp \
  --input examples/input/sample_projects.xlsx \
  --output-dir examples/output \
  --template-name default \
  --template-path examples/input/sample_report_template.txt
```

## 한컴 템플릿 매핑 고도화

### 템플릿 스펙
- 위치: `specs/templates/default.yaml`
- 기능:
  - `placeholder_rules`: source + transform
  - `table_sections`: 여러 row를 한 placeholder로 렌더링
  - `include_unmapped_placeholders`: 템플릿에만 있고 규칙이 없는 placeholder 처리

### 지원 transform 예시
- `identity`
- `currency_krw`
- `percent`
- `date:%Y-%m-%d`
- `upper`, `lower`, `json`

### 템플릿 placeholder 자동 감지
- 텍스트 템플릿: `.txt/.xml/.html`
- 한컴 문서: `.hwpx`(zip 내부 XML 스캔)

## 출력 아티팩트
- `*.normalized.*.xlsx`
- `*.normalized.*.csv`
- `*.report.*.json`
- `*.hancom_payload.*.json`
- `*.hancom_preview.*.txt`

## 감사로그
- 경로: `logs/audit/YYYY-MM-DD.jsonl`
- 이벤트:
  - `auth.login`
  - `pipeline.process` (`started/succeeded/failed`)
- 운영 조회 API:
  - `GET /ops/audit/recent`
  - `GET /ops/audit/summary` (차트/대시보드 집계 + anomaly)
  - `GET /ops/audit/export/summary` (서명 헤더 포함 JSON)
  - `GET /ops/audit/export/recent.csv` (서명 헤더 포함 CSV)
  - `GET /ops/audit/export/summary.bundle.zip` (원본+서명 매니페스트 ZIP)
  - `GET /ops/audit/export/recent.bundle.zip` (원본+서명 매니페스트 ZIP)
  - `POST /ops/audit/export/verify` (payload + manifest 서명 검증)
  - `GET /ops/readiness` (운영 전 레디니스 점검)
  - `GET /ops/service-brief` (운영 계약, trust boundary, review flow)
  - `GET /ops/runtime-scorecard` (compact runtime score, audit flow, auth bootstrap posture)
  - `GET /ops/review-pack` (signed export evidence, approval gate, reviewer handoff)
  - `GET /ops/schema/process-report` (처리 결과 contract)
- 필터 쿼리:
  - `since_hours`, `status`, `event_type`, `actor_contains`

## 2-Minute Review Path
- `/health`에서 bootstrap state, signing posture, path guardrails를 먼저 확인합니다.
- `/ops/runtime-scorecard`에서 runtime score, audit event count, latest process posture를 확인합니다.
- `/ops/service-brief`에서 allowed roles, failed checks, trust boundary를 확인합니다.
- `/ops/readiness`를 실행한 뒤 regulated spreadsheet processing을 열어야 합니다.
- reviewer handoff 전에는 signed summary or audit bundle과 `/ops/audit/export/verify`를 확인합니다.

## Proof Assets
- `Health Envelope` -> `/health`: bootstrap state, signing posture, path guardrails를 먼저 확인합니다.
- `Runtime Scorecard` -> `/ops/runtime-scorecard`: auth bootstrap, recent audit flow, runtime readiness를 압축해서 보여줍니다.
- `Service Brief` -> `/ops/service-brief`: allowed roles, failed checks, trust boundary, process contract를 한 번에 확인합니다.
- `Readiness Check` -> `/ops/readiness`: regulated spreadsheet processing 전에 선행 검증을 강제합니다.
- `Process Schema` -> `/ops/schema/process-report`: 처리 결과 envelope가 어떤 contract를 따르는지 고정합니다.
- `Signed Summary Bundle` -> `/ops/audit/export/summary.bundle.zip`: reviewer handoff 전에 서명된 요약 증거를 묶습니다.
- `Verify Bundle` -> `/ops/audit/export/verify`: export bundle의 hash/signature를 사후 검증합니다.

### 서명 검증(옵션)
- 응답 헤더:
  - `X-Export-SHA256`
  - `X-Export-Signature`
  - `X-Export-Signature-Alg` (`hmac-sha256` or `none`)
  - `X-Export-Signature-Key-Id`
- `.env` 설정:
  - `EXPORT_SIGNING_ENABLED`
  - `EXPORT_SIGNING_KEY_ID`
  - `EXPORT_SIGNING_KEY`

## 오프라인(폐쇄망) 배포
가이드: `docs/offline-deploy.md`

### 번들 생성 (인터넷 가능한 빌드 머신)
```bash
bash scripts/build_offline_bundle.sh
```

생성물:
- `dist/secure-xl2hwp-offline-bundle.tar.gz`

## 품질 체크
```bash
pytest
ruff check app tests scripts
```

## Docker 실행
```bash
docker compose up --build
```

## GitHub Actions
- `.github/workflows/ci.yml`
- Push/PR 시 `ruff + pytest` 자동 실행

## 문서
- 사용 가이드 (KO): `docs/usage-ko.md`
- User Guide (EN): `docs/usage-en.md`
- 아키텍처: `docs/architecture.md`
- SpecKit 운영: `docs/speckit.md`
- CoT 단계 설계: `docs/cot.md`
- 오프라인 배포: `docs/offline-deploy.md`

## 라이선스
MIT

<!-- codex:local-verification:start -->
## Local Verification
```bash
/Library/Developer/CommandLineTools/usr/bin/python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e '.[dev]'
python -m pip install pytest
python -m pytest -q
python scripts/exercise_runtime_scorecard.py
```

## Repository Hygiene
- Keep runtime artifacts out of commits (`.codex_runs/`, cache folders, temporary venvs).
- Prefer running verification commands above before opening a PR.

_Last updated: 2026-03-04_
<!-- codex:local-verification:end -->
