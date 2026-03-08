# secure-xl2hwp-local Service-Grade SPECKIT

Last updated: 2026-03-08

## S - Scope
- 대상: air-gapped document automation pipeline
- 이번 iteration 목표: reviewer가 첫 화면과 API surface만 보고도 trust boundary, processing contract, operator review flow를 이해하게 만든다.

## P - Product Thesis
- 이 repo는 단순 변환기가 아니라 `폐쇄망용 문서 자동화 파이프라인`이어야 한다.
- 입력 파일 경계, output contract, offline posture가 가장 먼저 보여야 한다.

## E - Execution
- `/ops/service-brief`로 auth bootstrap, signed export posture, readiness 결과, review flow를 고정한다.
- `/ops/schema/process-report`로 처리 결과 contract를 명시해 metrics/artifacts review 기준을 고정한다.
- 웹 스튜디오 첫 화면에 service brief panel을 올려 schema, auth mode, signing mode, failed checks를 바로 보여준다.
- `/health`에도 같은 readiness contract와 reviewer links를 연결한다.

## C - Criteria
- local verification green
- README에서 trust boundary와 운영 가치가 즉시 이해됨
- `/health`, `/ops/service-brief`, `/ops/schema/process-report` contract가 일관된다.
- 첫 화면에서 review flow와 trust boundary가 보인다.

## K - Keep
- air-gapped posture
- deterministic file pipeline

## I - Improve
- sample redacted fixtures 추가
- operator checklist / error catalog 강화
- signed export evidence를 runbook과 release checklist에 연결

## T - Trace
- `README.md`
- `app/`
- `tests/`
- `.github/workflows/`
