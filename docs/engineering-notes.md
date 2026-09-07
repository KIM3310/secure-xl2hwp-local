# Distinct artifacts for repeated exports

Artifact names previously used the input stem and a timestamp rounded to one second. Processing the same input twice within that second silently replaced the first run's XLSX, CSV, report, payload, and preview files.

Each export now has a UUID-based artifact identifier attached to the existing timestamp. All five paths use it, and the report and Hancom payload record the same identifier for correlation. A repeated export keeps the previous run's bytes and produces a separate set of files.

Run `make verify`. The end-to-end regression in `tests/test_pipeline_service.py` fixes the clock, processes two different versions of the same input, and verifies disjoint output paths and byte-for-byte preservation of the first set.

This change prevents accidental naming collisions. It does not make the five writes a single atomic transaction or validate native HWP rendering, which requires Windows and Hancom.
