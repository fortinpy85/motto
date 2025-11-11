# CI Test Failures Analysis - Updated After Fixes

**Latest CI Run**: 19217097965 (Workflow completed successfully)

**Progress Summary**:
- **Initial State** (Run 19210072528): 36 failed, 399 passed, 8 skipped (90.0% pass rate)
- **After First Fix** (Commit 21308c05): 31 failed, 404 passed, 8 skipped (92.9% pass rate)
- **After Second Fix** (Commit 0cb606ce): **29 failed, 406 passed, 8 skipped (93.3% pass rate)**

**Net Improvement**: Fixed 7 tests, +7 passing tests, +3.3% pass rate

---

## Fixes Applied

### Commit 21308c05: Initial Model API Updates
1. Changed Document `title=` to `manual_title=` (6 instances in test_performance.py, 1 in test_e2e_workflows.py)
2. Fixed Message model: `content` → `text`, `role` → `is_bot`, removed `created_by` (7 tests)
3. Fixed ChatOptions: removed `model_id` parameter, use mode-specific fields (1 test)
4. Fixed ChatFile: changed `chat` → `message` parameter (1 test)
5. Fixed DataSource: removed `created_by` parameter (4 instances)
6. Added LibraryUserRole import (1 test)

### Commit 0cb606ce: Corrective Access Key Fixes
1. Removed invalid `.all(access_key=access_key)` calls (5 occurrences)
2. Removed invalid `.save(access_key=access_key)` call (1 occurrence)
3. Removed invalid `doc.text` assignment (1 occurrence)
4. Removed non-existent `text=` and `created_by=` parameters from Document.objects.create()

**Tests Fixed by These Commits**: 7 tests now passing (36 → 29 failures)

---

## Remaining 29 Test Failures - Categorized

### Category 1: Document Model API Issues (3 failures)

**Document.title property still has issues**:
1. `test_e2e_workflows.py::TestLibraryManagementWorkflow::test_library_collaboration_workflow`
   - Error: `AttributeError: property 'title' of 'Document' object has no setter`
   - Location: Missed instance in test_e2e_workflows.py

2. `test_e2e_workflows.py::TestMultiUserCollaboration::test_team_library_workflow`
   - Error: `AttributeError: property 'title' of 'Document' object has no setter`
   - Location: Another missed instance in test_e2e_workflows.py

**Document.created_by parameter**:
3. `test_e2e_workflows.py::TestErrorRecoveryWorkflows::test_document_processing_error_recovery`
   - Error: `TypeError: Document() got unexpected keyword arguments: 'created_by'`
   - Fix: Remove `created_by=` parameter from Document.objects.create()

---

### Category 2: Message Model Field Issues (3 failures)

**Message.created_by field in queries**:
1. `test_e2e_workflows.py::TestUserOnboardingWorkflow::test_new_user_complete_onboarding`
   - Error: `django.core.exceptions.FieldError: Cannot resolve keyword 'created_by' into field`
   - Fix: Remove `created_by` from Message query filters/ordering

2. `test_e2e_workflows.py::TestSessionManagementWorkflow::test_user_session_continuity`
   - Error: `django.core.exceptions.FieldError: Cannot resolve keyword 'created_by' into field`
   - Fix: Remove `created_by` from Message query filters/ordering

**Message.content vs text**:
3. `test_e2e_workflows.py::TestCostBudgetWorkflow::test_cost_tracking_workflow`
   - Error: `TypeError: Message() got unexpected keyword arguments: 'content'`
   - Fix: Change `content=` to `text=` in Message.objects.create()

---

### Category 3: Preset Model API Changes (5 failures)

**Preset constructor signature changes**:
1. `test_otto/test_auth_integration.py::TestChatAccessAuthorization::test_preset_sharing_everyone`
   - Error: `TypeError: Preset() got unexpected keyword arguments: 'name'`

2. `test_otto/test_auth_integration.py::TestChatAccessAuthorization::test_preset_sharing_specific_users`
   - Error: `TypeError: Preset() got unexpected keyword arguments: 'name'`

3. `test_otto/test_auth_integration.py::TestChatAccessAuthorization::test_preset_edit_permissions`
   - Error: `TypeError: Preset() got unexpected keyword arguments: 'name'`

4. `test_otto/test_auth_integration.py::TestChatAccessAuthorization::test_global_default_preset_restrictions`
   - Error: `TypeError: Preset() got unexpected keyword arguments: 'name'`

5. `test_e2e_workflows.py::TestPresetSharingWorkflow::test_preset_creation_and_sharing`
   - Error: `TypeError: Preset() got unexpected keyword arguments: 'is_public'`

**Fix Strategy**: Review Preset model in chat/models.py to understand current constructor signature

---

### Category 4: Document ORM Query Issues (1 failure)

**Document.select_related with invalid field**:
1. `test_performance.py::TestSecureModelQueryPerformance::test_n_plus_one_query_prevention`
   - Error: `django.core.exceptions.FieldError: Invalid field name(s) given in select_related: 'created_by'. Choices are: data_source, saved_file`
   - Fix: Remove `created_by` from `.select_related()` call for Document queries

---

### Category 5: CostType Test Data Issues (4 failures)

**CostType.DoesNotExist**:
1. `test_librarian/test_document_loading.py::test_extract_pdf_gemini_read`
2. `test_librarian/test_document_loading.py::test_extract_pdf_gemini_layout`
3. `test_otto/test_manage_users.py::test_get_cost_dashboard`

**CostType.MultipleObjectsReturned**:
4. `test_performance.py::TestCostTrackingPerformance::test_concurrent_cost_creation`
   - Error: `otto.models.CostType.MultipleObjectsReturned: get() returned more than one CostType -- it returned 4!`

**Fix Strategy**: These are test data setup issues. Tests need to properly initialize or filter CostType objects.

---

### Category 6: Test Data Setup Issues (2 failures)

1. `test_librarian/test_librarian_models.py::test_create_data_source`
   - Error: `chat.models.Preset.MultipleObjectsReturned: get() returned more than one Preset -- it returned 2!`
   - Fix: Test needs more specific Preset query or proper test isolation

2. `test_celery_tasks.py::TestProcessDocumentHelper::test_process_document_helper_url_success`
   - Error: `ValueError: too many values to unpack (expected 2)`
   - Fix: Return value structure changed, test needs to match new signature

---

### Category 7: Authorization Test Failures (3 failures)

1. `test_otto/test_auth_integration.py::TestGroupBasedAuthorization::test_otto_admin_group_membership`
   - Error: `assert False`
   - Fix: Review authorization logic, test assertions may be outdated

2. `test_otto/test_auth_integration.py::TestGroupBasedAuthorization::test_data_steward_permissions`
   - Error: `AssertionError: assert False`
   - Fix: Review authorization logic and test expectations

3. `test_otto/test_auth_integration.py::TestLibraryAccessAuthorization::test_manage_library_users_permission`
   - Error: `AssertionError: assert False`
   - Fix: Review library authorization rules

---

### Category 8: Performance Test Query Count Assertions (3 failures)

1. `test_performance.py::TestSecureModelQueryPerformance::test_secure_query_performance`
   - Error: `assert 55 == 50`
   - Issue: Query count changed (expected 50, got 55)

2. `test_performance.py::TestMemoryAndResources::test_large_query_result_memory`
   - Error: `assert 205 == 200`
   - Issue: Query count changed (expected 200, got 205)

3. `test_performance.py::TestPerformanceRegression::test_secure_model_query_baseline`
   - Error: `assert 55 == 50`
   - Issue: Query count baseline changed

**Fix Strategy**: These may need assertion updates if the query count changes are expected/acceptable, or investigation if they indicate a performance regression.

---

### Category 9: Workflow and Integration Test Issues (4 failures)

1. `test_e2e_workflows.py::TestDocumentRAGWorkflow::test_complete_document_rag_workflow`
   - Error: `AssertionError: assert 'chat' == 'qa'`
   - Issue: Mode value mismatch in test expectations

2. `test_negative_cases.py::TestFileUploadValidation::test_file_size_limits`
   - Error: `AssertionError: assert False`
   - Issue: Test logic or assertions need review

3. `text_extractor/test_tasks.py::test_process_ocr_document_pdf`
   - Error: `AssertionError: assert 'RIF drawing' == 'Page 1\nPage 2\nPage 3'`
   - Issue: OCR output expectations don't match actual behavior

4. `test_performance.py::TestLLMPerformance::test_concurrent_llm_requests`
   - Error: `django.db.utils.IntegrityError: insert or update on table "chat_chat" violates foreign key constraint "chat_chat_user_id_bbe8a5b9_fk_otto_user_id"`
   - Issue: Test data setup or user reference issue in concurrent test

---

## Priority Fixes for Next Round

### High Priority (Quick Wins - 7 tests):
1. **Document.title in test_e2e_workflows.py** (2 tests) - Same fix as before, just missed instances
2. **Document.created_by parameter** (1 test) - Remove from Document.objects.create()
3. **Message.content vs text** (1 test) - Change to `text=`
4. **Message.created_by in queries** (2 tests) - Remove from filters/ordering
5. **Document.select_related('created_by')** (1 test) - Remove from select_related()

### Medium Priority (Require Model Investigation - 5 tests):
6. **Preset constructor changes** (5 tests) - Investigate Preset model API

### Lower Priority (Test Data/Logic Issues - 17 tests):
7. **CostType issues** (4 tests) - Test data setup
8. **Authorization tests** (3 tests) - Logic review needed
9. **Performance query counts** (3 tests) - May be expected changes
10. **Workflow/integration issues** (4 tests) - Various test logic updates
11. **Test isolation issues** (2 tests) - Proper test setup
12. **OCR expectations** (1 test) - Output validation update

---

## Next Steps

1. Apply high-priority fixes for Document and Message issues (7 tests)
2. Investigate Preset model and fix constructor calls (5 tests)
3. Review and fix test data setup for CostType (4 tests)
4. Address remaining authorization, performance, and integration test issues (13 tests)
5. Target: Get to 100% test pass rate (443/443 passing)

**Current Status**: 29 failures remaining out of 443 total tests (93.3% pass rate)
**Goal**: 0 failures (100% pass rate)
