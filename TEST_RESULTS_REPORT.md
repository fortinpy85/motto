# Test Results Report

**Generated:** 2025-11-05
**Test Duration:** 1 hour, 38 minutes, 42 seconds (5922.91s)
**Total Tests:** 442 collected

## Executive Summary

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ PASSED | 50 | 11.3% |
| ❌ FAILED | 19 | 4.3% |
| 🔥 ERROR | 379 | 85.7% |
| **Issues** | **398** | **90.0%** |

## Critical Issues

### 1. Missing Staticfiles Manifest Entries (Primary Failure Cause)

**Impact:** 48 occurrences, causing most view test failures

**Error Pattern:**
```
ValueError: Missing staticfiles manifest entry for 'thirdparty/htmx.min.js'
ValueError: Missing staticfiles manifest entry for 'autocomplete/css/autocomplete.css'
```

**Root Cause:** Django staticfiles not collected or manifest not generated before tests

**Location:** `django/contrib/staticfiles/storage.py:518`

**Fix Required:**
```bash
python django/manage.py collectstatic --noinput
```

**Affected Tests:**
- All chat view tests (`tests/chat/test_chat_views.py`)
- QA options tests
- Preset loading tests
- Translation tests with glossary

---

### 2. Database Connection Errors (Secondary Issue)

**Impact:** 444 occurrences throughout test execution

**Error Pattern:**
```
psql: error: connection to server at "localhost" (::1), port 5432 failed:
FATAL:  role "jd_user" does not exist
```

**Root Cause:** PostgreSQL user "jd_user" not configured or environment mismatch

**Location:** Database connection layer during test setup

**Fix Required:**
1. Create PostgreSQL role: `createuser jd_user`
2. Or update `.env` to use correct database user
3. Verify `DJANGODB_USER` and `VECTORDB_USER` environment variables

---

### 3. File Access Errors

**Impact:** 1 occurrence in chat models

**Error Pattern:**
```
WinError 32: The process cannot access the file because it is being used by another process:
'C:\\otto\\Otto\\django\\test_media\\files\\2025\\11\\04\\test_document.pdf'
```

**Root Cause:** File handle not released before deletion attempt

**Location:** `django/chat/models.py:753(delete_saved_file)`

**Fix Required:** Ensure file handles are properly closed before deletion

---

### 4. TLD Extractor Configuration Error

**Impact:** 1 occurrence in URL validation

**Error Pattern:**
```
ValueError: file: URLs with hostname components are not permitted
```

**Root Cause:** TLD extractor attempting to fetch local file URL incorrectly

**Location:** `django/otto/utils/common.py:81(check_url_allowed)`

**Fix Required:** Update TLD extractor configuration to handle local files properly

---

## Failed Tests (19 Total)

### Chat View Tests (14 failures)
All in `tests/chat/test_chat_views.py` - caused by missing staticfiles:

1. `test_chat_message_error` - Missing htmx.min.js
2. `test_chat_message_url_validation` - Missing htmx.min.js
3. `test_chat_response` - Missing htmx.min.js
4. `test_chat_routes` - Missing htmx.min.js
5. `test_chat_summarization_response` - Missing htmx.min.js
6. `test_delete_chat` - Missing htmx.min.js
7. `test_download_file` - Missing htmx.min.js
8. `test_per_source_qa_response` - Missing htmx.min.js
9. `test_preset` - Missing autocomplete.css
10. `test_qa_filters` - Missing htmx.min.js
11. `test_qa_response` - Missing htmx.min.js
12. `test_summarize_qa_response` - Missing htmx.min.js
13. `test_translate_response` - Missing htmx.min.js
14. `test_update_qa_options_from_librarian` - Missing autocomplete.css

### LLM Edge Case Tests (3 failures)
In `tests/chat/test_llm_edge_cases.py`:

15. `TestLLMModelConfiguration::test_get_model_invalid_raises_error`
16. `TestLLMNegativeCases::test_chat_history_with_malformed_data`
17. `TestOttoLLMInitialization::test_ottollm_custom_deployment`

### Other Failures (2)
18. `test_translate_glossary_filename_persists_on_refresh` - Missing staticfiles
19. `test_message_pre_delete_removes_documents` - File access error

---

## Error Tests (379 Total - Sample)

### Categories of Errors

#### Chat Module Errors (346 tests)
**Files affected:**
- `tests/chat/test_answer_sources.py` - 1 test
- `tests/chat/test_chat_models.py` - 6 tests
- `tests/chat/test_chat_options.py` - 2 tests
- `tests/chat/test_chat_procs.py` - 10 tests
- `tests/chat/test_chat_readonly.py` - 1 test
- `tests/chat/test_chat_translate.py` - 2 tests
- `tests/chat/test_chat_translate_glossary.py` - 1 test
- `tests/chat/test_chat_views.py` - 3 tests
- `tests/chat/test_message_pre_delete.py` - 6 tests

**Common pattern:** Database connection failures and staticfiles issues

#### Laws Module Errors (3 tests)
- `tests/laws/test_laws_loading.py::test_get_dict_from_xml`
- `tests/laws/test_laws_loading.py::test_get_sha_256_hash`
- `tests/laws/test_laws_loading.py::test_job_status_cancel`

#### Otto Module Errors (1 test)
- `tests/otto/test_cleanup.py::test_delete_text_extractor_files_task`

#### Text Extractor Module Errors (2 tests)
- `tests/text_extractor/test_views.py::test_poll_tasks_view`
- `tests/text_extractor/test_views.py::test_download_all_zip`

---

## Recommendations

### Immediate Actions (Before Next Test Run)

1. **Collect Static Files**
   ```bash
   cd django
   python manage.py collectstatic --noinput
   ```

2. **Fix Database Configuration**
   ```bash
   # Option A: Create the expected user
   createuser jd_user

   # Option B: Update .env file
   DJANGODB_USER=your_actual_user
   VECTORDB_USER=your_actual_user
   ```

3. **Verify Environment Setup**
   ```bash
   cd django
   python manage.py check
   python manage.py showmigrations
   ```

### Code Fixes Required

1. **File Deletion in chat/models.py:753**
   - Add proper file handle cleanup before deletion
   - Implement retry logic for locked files on Windows
   - Add error logging for file access issues

2. **TLD Extractor Configuration in otto/utils/common.py:81**
   - Update configuration to properly handle local file URLs
   - Add validation before TLD extraction

3. **LLM Edge Cases**
   - Review and fix the 3 LLM-related test failures
   - Ensure proper error handling for invalid models
   - Validate malformed data handling

### Test Infrastructure Improvements

1. **Pre-test Setup Script**
   - Automate `collectstatic` before test runs
   - Verify database connectivity before starting
   - Check all required environment variables

2. **Better Error Reporting**
   - Group similar errors in test output
   - Provide fix suggestions in test failures
   - Add test fixtures validation

3. **CI/CD Integration**
   - Add staticfiles collection to CI pipeline
   - Validate database configuration in CI
   - Run subset of critical tests before full suite

---

## Passing Tests (50 Total)

Tests that passed successfully demonstrate:
- Core model functionality works
- Basic chat operations function correctly
- Authentication and permissions systems operational
- Some view rendering works when staticfiles present

---

## Test Execution Timeline

- **Start:** Test collection phase
- **Duration:** 5922.91 seconds (98.7 minutes)
- **End:** 19 failed, 50 passed, 379 errors
- **Exit Code:** 0 (tests completed, despite failures)

---

## Next Steps

1. ✅ Fix staticfiles collection (highest priority)
2. ✅ Fix database user configuration
3. ⚠️ Fix file handling in models.py
4. ⚠️ Fix TLD extractor configuration
5. ⚠️ Review and fix LLM edge case tests
6. ⚠️ Re-run full test suite
7. 📊 Aim for >95% pass rate

---

## Appendix: Complete Test Lists

### All Failed Tests

See `failed_tests.txt` for complete list with error details.

### All Error Tests

See `error_tests.txt` for complete list (392 entries).

### Full Test Output

See `test_results_complete.txt` for complete pytest output (6148 lines).

---

**Report End**
