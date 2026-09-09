# Testing Patterns

**Analysis Date:** 2026-09-09

## Framework
The project currently does not use a standardized testing framework (like `pytest` or `unittest` for Python, or `GTest`/`QtTest` for C++). 
Testing relies on standalone execution scripts that serve as manual end-to-end (E2E) sanity checks.

## Structure
- Test scripts use the `test_` prefix (e.g., `test_imap.py`, `test_service.py`, `test_execute.py`).
- Test scripts are placed directly alongside source code or at the root of modules (e.g., `backend/memory/test_execute.py`).
- There are currently no automated tests for the C++ frontend layer.

## Mocking
- **No mocking is used.** 
- Test scripts interact directly with production-like dependencies (real IMAP email servers, real local disk storage).
- Tests output directly to standard out (`print`) for manual visual validation instead of relying on programmatic assertions.

## Coverage
- Test coverage is unknown as there is no coverage tracking or automated execution pipeline.
- Due to the nature of the manual sanity-check scripts, test automation coverage is effectively 0%.

*Testing patterns analysis: 2026-09-09*
<!-- refreshed: 2026-09-09 -->
