# Test Results - 2026-03-19

## Summary

| Metric | Value |
|--------|-------|
| Total tests | 97 |
| Passed | 97 |
| Failed | 0 |
| Skipped | 0 |
| Duration | 3.46s |
| Python | 3.9.6 |
| Platform | darwin (macOS) |
| pytest | 8.4.2 |
| Ruff lint | All checks passed |

## Test Breakdown by File

| File | Tests | Status |
|------|-------|--------|
| test_api_auth.py | 13 | PASS |
| test_audit_logger.py | 1 | PASS |
| test_auth_service.py | 2 | PASS |
| test_critical_paths.py | 41 | PASS (NEW) |
| test_excel_processor.py | 1 | PASS |
| test_frontend_metadata.py | 3 | PASS |
| test_llm_service.py | 3 | PASS |
| test_pipeline_service.py | 1 | PASS |
| test_runtime_proof_script.py | 2 | PASS |
| test_settings.py | 8 | PASS |
| test_speckit_loader.py | 1 | PASS |
| test_template_engine.py | 3 | PASS |
| test_ui.py | 18 | PASS |

## New Tests Added (test_critical_paths.py - 41 tests)

### JWT Auth Flow (12 tests)
- Token issuance and verification roundtrip
- Expired token rejection
- Missing `sub` claim rejection
- Missing `role` claim rejection
- Wrong secret key rejection
- Token role mismatch with user registry rejection
- Inactive/missing user token rejection
- Wrong password returns None
- Unknown user returns None
- PBKDF2 password verification (correct and incorrect)
- SHA256 password verification (correct and incorrect)
- Malformed PBKDF2 hash returns False

### Login Attempt Guard with Race Condition Awareness (9 tests)
- Basic lockout flow (3 failures triggers lock)
- Success clears failure counter
- Configure resets all state
- Reset clears all state
- Different principals tracked independently
- Concurrent failure registration across 10 threads (thread safety)
- Concurrent failure + success interleaving (no crash)
- Remaining attempts counter accuracy

### Export Signature Verification (4 tests)
- Signing enabled produces valid HMAC-SHA256
- Signing disabled uses "none" algorithm
- Empty payload produces valid SHA256 digest
- Different payloads produce different signatures

### Pipeline Stages - CotOrchestrator (9 tests)
- All three stages complete in deterministic mode
- Schema inference maps contract fields to columns
- Cleanup advice identifies high-missing columns (>=40%)
- Document mapping includes row count
- Document mapping handles empty dataframe
- Stage outputs contain all expected keys
- _normalize strips whitespace and lowercases
- _safe_json handles all primitive and collection types

### Path Guardrails Validation (8 tests)
- Relative path resolution
- Absolute path resolution
- Valid path within base accepted
- Path traversal (`..`) blocked with 400
- Output dir traversal to /tmp blocked
- Deep traversal (`../../../etc/passwd`) blocked
- Template path traversal blocked
- None template path accepted

## Raw Output

```
============================= test session starts ==============================
platform darwin -- Python 3.9.6, pytest-8.4.2, pluggy-1.6.0
rootdir: <repo-root>
configfile: pyproject.toml
testpaths: tests
plugins: anyio-4.12.1, cov-5.0.0
collected 97 items

tests/test_api_auth.py .............                                     [ 13%]
tests/test_audit_logger.py .                                             [ 14%]
tests/test_auth_service.py ..                                            [ 16%]
tests/test_critical_paths.py .........................................   [ 58%]
tests/test_excel_processor.py .                                          [ 59%]
tests/test_frontend_metadata.py ...                                      [ 62%]
tests/test_llm_service.py ...                                            [ 65%]
tests/test_pipeline_service.py .                                         [ 67%]
tests/test_runtime_proof_script.py ..                                    [ 69%]
tests/test_settings.py ........                                          [ 77%]
tests/test_speckit_loader.py .                                           [ 78%]
tests/test_template_engine.py ...                                        [ 81%]
tests/test_ui.py ..................                                      [100%]

============================== 97 passed in 3.46s ==============================
```

## Code Quality

Ruff linter output: **All checks passed** (0 errors, 0 warnings).

Configuration: line-length=100, target-version=py39, rules: E, F, I, UP, B.
