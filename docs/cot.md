# CoT Pipeline Guide

이 서비스의 CoT 방식은 모델의 장문 추론 텍스트를 직접 저장하는 방식이 아니라,
단계를 분리하고 각 단계 산출물을 구조화(JSON)하는 운영 방식입니다.

## Stages
1. `schema_inference`
2. `cleanup_advice`
3. `document_mapping`

## 장점
- 단계별 실패 원인 분리
- LLM 실패 시 결정론적 fallback 유지
- 감사 로그(`report_json`)에 단계별 결과 기록
