# SpecKit Guide

## contracts/default.yaml
데이터 계약(필드 정의, 제약조건, 템플릿 placeholder 기준)을 정의합니다.

## profiles/default.yaml
실제 수집 엑셀마다 다른 컬럼명을 표준화하고 정제 규칙을 적용합니다.

## templates/default.yaml
한컴 문서 매핑 규칙을 정의합니다.
- `placeholder_rules`: source + transform 기반 단일 값 매핑
- `table_sections`: 다건 row를 단일 placeholder 텍스트로 렌더링
- `include_unmapped_placeholders`: 템플릿에서 감지된 미매핑 placeholder 보강

## security/users.yaml
로컬 인증 사용자 레지스트리입니다.
- `user_id`, `role`, `password_hash`, `active`
- 비밀번호 해시는 `scripts/hash_password.py`로 생성합니다.

## 운영 패턴
1. 신규 엑셀 양식은 `profiles/*.yaml` 추가로 대응
2. 문서 템플릿 변경은 `templates/*.yaml`만 수정
3. 보안 정책 변경은 `security/users.yaml`와 `.env` 키 교체
4. 코드 변경 없이 스펙 중심으로 운영
