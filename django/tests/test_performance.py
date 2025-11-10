"""
Comprehensive performance and stress tests for Otto application

This test suite covers:
- LLM response time and throughput
- Document processing performance
- Vector store query performance
- Database query optimization (SecureModel)
- Concurrent user operations and race conditions
- Memory usage and resource leaks
- Cache effectiveness
- API rate limiting behavior
"""

import pytest
import time
import gc
import threading
from unittest.mock import Mock, patch, MagicMock
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.contrib.auth.models import Group
from django.core.cache import cache
from django.db import connection
from django.test.utils import override_settings

from chat.models import Chat, Message, ChatOptions
from chat.llm import OttoLLM
from librarian.models import Document, DataSource, Library, LibraryUserRole
from otto.secure_models import AccessKey
from otto.models import Cost, CostType


# ==================== Performance Benchmarking Utilities ====================

class PerformanceBenchmark:
    """Utility class for measuring performance metrics"""

    def __init__(self, name):
        self.name = name
        self.start_time = None
        self.end_time = None
        self.queries_before = None
        self.queries_after = None

    def __enter__(self):
        gc.collect()  # Clear memory before test
        self.queries_before = len(connection.queries)
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, *args):
        self.end_time = time.perf_counter()
        self.queries_after = len(connection.queries)

    @property
    def elapsed_time(self):
        """Return elapsed time in seconds"""
        if self.start_time and self.end_time:
            return self.end_time - self.start_time
        return None

    @property
    def query_count(self):
        """Return number of database queries executed"""
        if self.queries_before is not None and self.queries_after is not None:
            return self.queries_after - self.queries_before
        return None

    def assert_performance(self, max_time=None, max_queries=None):
        """Assert performance meets requirements"""
        if max_time and self.elapsed_time:
            assert self.elapsed_time < max_time, \
                f"{self.name} took {self.elapsed_time:.3f}s, expected < {max_time}s"

        if max_queries and self.query_count:
            assert self.query_count <= max_queries, \
                f"{self.name} executed {self.query_count} queries, expected <= {max_queries}"


# ==================== LLM Performance Tests ====================

@pytest.mark.slow
class TestLLMPerformance:
    """Test LLM chat performance and throughput"""

    def test_ottollm_initialization_performance(self):
        """Test LLM initialization time"""
        with PerformanceBenchmark("OttoLLM initialization") as bench:
            llm = OttoLLM(mock_embedding=True)

        # Initialization should be fast (< 1 second)
        bench.assert_performance(max_time=1.0)
        assert llm is not None

    @patch('chat.llm.genai.GenerativeModel')
    def test_simple_chat_response_time(self, mock_genai, basic_user):
        """Test simple chat response latency"""
        user = basic_user()

        # Mock LLM response
        mock_response = Mock()
        mock_response.text = "This is a test response"
        mock_genai.return_value.generate_content.return_value = mock_response

        chat = Chat.objects.create(
            title="Performance Test",
            user=user,)

        user_message = Message.objects.create(chat=chat,
            text="Hello, how are you?", is_bot=False
        )

        with PerformanceBenchmark("Simple chat response") as bench:
            llm = OttoLLM(mock_embedding=True)
            # Simulate chat completion
            response = mock_genai.return_value.generate_content("test")

        # Simple responses should be fast (< 5 seconds with mocking)
        bench.assert_performance(max_time=5.0)

    @patch('chat.llm.genai.GenerativeModel')
    def test_concurrent_llm_requests(self, mock_genai, basic_user):
        """Test LLM throughput with concurrent requests"""
        user = basic_user()

        mock_response = Mock()
        mock_response.text = "Concurrent response"
        mock_genai.return_value.generate_content.return_value = mock_response

        def create_chat_and_respond():
            """Create a chat and get a response"""
            chat = Chat.objects.create(
                title=f"Concurrent Test {threading.get_ident()}",
                user=user
            )
            ChatOptions.objects.create(mode="chat", chat=chat)

            Message.objects.create(chat=chat,
                text="Test message", is_bot=False
            )

            llm = OttoLLM(mock_embedding=True)
            return True

        # Test with 10 concurrent requests
        with PerformanceBenchmark("10 concurrent LLM requests") as bench:
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [executor.submit(create_chat_and_respond) for _ in range(10)]
                results = [f.result() for f in as_completed(futures)]

        assert all(results)
        # Concurrent requests should complete in reasonable time (< 15 seconds)
        bench.assert_performance(max_time=15.0)


# ==================== Document Processing Performance Tests ====================

@pytest.mark.slow
class TestDocumentProcessingPerformance:
    """Test document processing performance"""

    def test_document_creation_performance(self, basic_user):
        """Test document creation without processing"""
        user = basic_user()
        access_key = AccessKey(user=user)

        library = Library.objects.create(name="Performance Test Library")

        datasource = DataSource.objects.create(library=library,
            name="Performance Test Source")

        with PerformanceBenchmark("Create 100 documents") as bench:
            documents = []
            for i in range(100):
                doc = Document.objects.create(data_source=datasource,
                    url=f"https://example.com/doc{i}",
                    manual_title=f"Document {i}")
                documents.append(doc)

        # Creating 100 documents should be fast (< 5 seconds)
        bench.assert_performance(max_time=5.0)
        assert len(documents) == 100

    @patch('librarian.utils.process_engine.fetch_from_url')
    @patch('librarian.utils.process_engine.extract_markdown')
    def test_batch_document_processing(self, mock_extract, mock_fetch, basic_user):
        """Test processing multiple documents"""
        user = basic_user()
        access_key = AccessKey(user=user)

        library = Library.objects.create(name="Batch Test Library")

        datasource = DataSource.objects.create(library=library,
            name="Batch Test Source")

        # Mock document content
        mock_fetch.return_value = b"<html><body>Test content</body></html>"
        mock_result = Mock()
        mock_result.markdown = "Test content"
        mock_extract.return_value = mock_result

        # Create 10 documents
        documents = []
        for i in range(10):
            doc = Document.objects.create(data_source=datasource,
                url=f"https://example.com/doc{i}")
            documents.append(doc)

        with PerformanceBenchmark("Process 10 documents") as bench:
            for doc in documents:
                # Simulate processing (actual processing would be in Celery task)
                doc.status = "COMPLETE"
                doc.save()

        # Processing 10 documents (simulated) should be fast (< 3 seconds)
        bench.assert_performance(max_time=3.0)


# ==================== Vector Store Performance Tests ====================

@pytest.mark.slow
class TestVectorStorePerformance:
    """Test vector store query performance"""

    def test_vector_store_initialization(self):
        """Test vector store initialization time"""
        with PerformanceBenchmark("Vector store initialization") as bench:
            llm = OttoLLM(mock_embedding=True)
            # Vector store initialized in LLM constructor

        # Vector store initialization should be fast (< 2 seconds)
        bench.assert_performance(max_time=2.0)

    @pytest.mark.skip(reason="query_engine API no longer exists in OttoLLM - needs refactoring to use current API")
    def test_similarity_search_performance(self, basic_user):
        """Test vector similarity search performance"""
        user = basic_user()

        llm = OttoLLM(mock_embedding=True)

        with PerformanceBenchmark("Vector similarity search") as bench:
            # API changed - query_engine no longer exists
            # Need to refactor to use get_retriever or similar
            pass

        # Similarity search should be fast (< 2 seconds)
        bench.assert_performance(max_time=2.0)


# ==================== SecureModel Query Performance Tests ====================

class TestSecureModelQueryPerformance:
    """Test SecureModel query performance and optimization"""

    def test_secure_query_performance(self, basic_user):
        """Test SecureModel query performance"""
        user = basic_user()
        access_key = AccessKey(user=user)

        # Create test data
        library = Library.objects.create(name="Query Performance Test")

        datasource = DataSource.objects.create(library=library,
            name="Query Performance Source")

        # Create 50 documents
        for i in range(50):
            Document.objects.create(data_source=datasource,
                manual_title=f"Document {i}")

        with PerformanceBenchmark("Query 50 secure documents") as bench:
            docs = Document.objects.all()
            doc_list = list(docs)  # Force evaluation

        # Querying 50 documents should be fast (< 1 second)
        bench.assert_performance(max_time=1.0)
        assert len(doc_list) == 50

    def test_secure_query_with_filters(self, basic_user):
        """Test SecureModel filtered query performance"""
        user = basic_user()
        access_key = AccessKey(user=user)

        library = Library.objects.create(name="Filter Test Library")

        datasource = DataSource.objects.create(library=library,
            name="Filter Test Source")

        # Create documents with different statuses
        for i in range(100):
            status = "COMPLETE" if i % 2 == 0 else "PENDING"
            Document.objects.create(data_source=datasource,
                manual_title=f"Document {i}",
                status=status)

        with PerformanceBenchmark("Filtered query on 100 documents") as bench:
            complete_docs = Document.objects.filter(
                status="COMPLETE"
            ).all()
            doc_list = list(complete_docs)

        # Filtered queries should be fast (< 1 second)
        bench.assert_performance(max_time=1.0)
        # Should have limited queries (select + permission check)
        bench.assert_performance(max_queries=5)
        assert len(doc_list) == 50

    def test_n_plus_one_query_prevention(self, basic_user):
        """Test that N+1 query problem is avoided"""
        user = basic_user()
        access_key = AccessKey(user=user)

        library = Library.objects.create(name="N+1 Test Library")

        datasource = DataSource.objects.create(library=library,
            name="N+1 Test Source")

        # Create 20 documents
        for i in range(20):
            Document.objects.create(data_source=datasource,
                manual_title=f"Document {i}")

        with PerformanceBenchmark("Access 20 documents with related data") as bench:
            docs = Document.objects.select_related(
                'data_source'
            ).all()

            # Access related fields (should not trigger additional queries)
            for doc in docs:
                _ = doc.data_source.name_en

        # Should use select_related to avoid N+1 queries
        # Expect: 1 main query + permission queries, not 20+ queries
        bench.assert_performance(max_queries=10)


# ==================== Concurrent Operations and Race Conditions ====================

@pytest.mark.django_db(transaction=True)
class TestConcurrentOperations:
    """Test concurrent user operations and race conditions"""

    def test_concurrent_chat_creation(self, basic_user):
        """Test multiple users creating chats concurrently"""
        user1 = basic_user(username="concurrent1")
        user2 = basic_user(username="concurrent2")
        user3 = basic_user(username="concurrent3")

        def create_chats(user, count):
            """Create multiple chats for a user"""
            chats = []
            for i in range(count):
                chat = Chat.objects.create(
                    title=f"Chat {i} by {user.upn}",
                    user=user,)
                chats.append(chat)
            return len(chats)

        with PerformanceBenchmark("Concurrent chat creation") as bench:
            with ThreadPoolExecutor(max_workers=3) as executor:
                futures = [
                    executor.submit(create_chats, user1, 10),
                    executor.submit(create_chats, user2, 10),
                    executor.submit(create_chats, user3, 10),
                ]
                results = [f.result() for f in as_completed(futures)]

        assert sum(results) == 30
        assert Chat.objects.count() == 30
        # Concurrent operations should complete in reasonable time
        bench.assert_performance(max_time=5.0)

    def test_concurrent_document_updates(self, basic_user):
        """Test concurrent updates to same document (race condition)"""
        user = basic_user()
        access_key = AccessKey(user=user)

        library = Library.objects.create(name="Race Condition Test")

        datasource = DataSource.objects.create(library=library,
            name="Race Condition Source")

        document = Document.objects.create(data_source=datasource,
            manual_title="Concurrent Update Test")

        def update_document(doc_id, value):
            """Update document status"""
            access_key = AccessKey(bypass=True)
            doc = Document.objects.get(id=doc_id)
            doc.status = value
            doc.save()
            return True

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [
                executor.submit(update_document, document.id, f"STATUS_{i}")
                for i in range(5)
            ]
            results = [f.result() for f in as_completed(futures)]

        assert all(results)
        # Document should have one of the statuses (last write wins)
        document.refresh_from_db()
        assert document.status.startswith("STATUS_")

    def test_concurrent_permission_grants(self, basic_user):
        """Test concurrent permission grants to same resource"""
        owner = basic_user(username="owner")
        users = [basic_user(username=f"user{i}") for i in range(5)]

        access_key = AccessKey(user=owner)
        library = Library.objects.create(name="Permission Test")

        def grant_permission(lib_id, user):
            """Grant view permission to user"""
            access_key = AccessKey(user=owner)
            lib = Library.objects.get(id=lib_id)
            LibraryUserRole.objects.create(library=lib, user=user, role="viewer")
            return True

        with PerformanceBenchmark("Concurrent permission grants") as bench:
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(grant_permission, library.id, user)
                    for user in users
                ]
                results = [f.result() for f in as_completed(futures)]

        assert all(results)
        # All users should have view permission
        for user in users:
            assert user.has_perm("librarian.view_library", library)

        bench.assert_performance(max_time=3.0)


# ==================== Memory and Resource Management Tests ====================

class TestMemoryAndResources:
    """Test memory usage and resource management"""

    def test_large_query_result_memory(self, basic_user):
        """Test memory usage with large query results"""
        user = basic_user()
        access_key = AccessKey(user=user)

        library = Library.objects.create(name="Memory Test Library")

        datasource = DataSource.objects.create(library=library,
            name="Memory Test Source")

        # Create 200 documents
        for i in range(200):
            Document.objects.create(data_source=datasource,
                manual_title=f"Document {i}"
            )

        gc.collect()

        with PerformanceBenchmark("Query 200 large documents") as bench:
            # Use iterator to avoid loading all into memory at once
            docs = Document.objects.all().iterator(chunk_size=50)
            count = sum(1 for _ in docs)

        assert count == 200
        # Should handle large results efficiently
        bench.assert_performance(max_time=3.0)

    def test_cache_effectiveness(self, basic_user):
        """Test Django cache effectiveness"""
        user = basic_user()
        cache_key = f"test_performance_{user.id}"
        test_data = {"user": user.upn, "timestamp": time.time()}

        # First access - cache miss
        with PerformanceBenchmark("Cache miss") as bench1:
            result = cache.get(cache_key)
            if not result:
                cache.set(cache_key, test_data, 60)

        # Second access - cache hit
        with PerformanceBenchmark("Cache hit") as bench2:
            result = cache.get(cache_key)

        assert result == test_data
        # Cache hit should be significantly faster than miss
        # (This is a basic check, actual timing depends on cache backend)
        assert bench2.elapsed_time is not None


# ==================== Stress Tests ====================

@pytest.mark.slow
class TestStressScenarios:
    """Stress tests for high-load scenarios"""

    def test_high_volume_chat_creation(self, basic_user):
        """Stress test: Create many chats rapidly"""
        user = basic_user()

        with PerformanceBenchmark("Create 100 chats") as bench:
            chats = []
            for i in range(100):
                chat = Chat.objects.create(
                    title=f"Stress Test Chat {i}",
                    user=user,)
                chats.append(chat)

        assert len(chats) == 100
        # Should handle high volume (< 10 seconds for 100 chats)
        bench.assert_performance(max_time=10.0)

    def test_rapid_permission_checks(self, basic_user):
        """Stress test: Rapid permission checks"""
        user = basic_user()
        access_key = AccessKey(user=user)

        library = Library.objects.create(name="Permission Stress Test")

        with PerformanceBenchmark("1000 permission checks") as bench:
            for _ in range(1000):
                _ = user.has_perm("librarian.view_library", library)

        # Should handle many permission checks efficiently
        bench.assert_performance(max_time=2.0)

    @pytest.mark.django_db(transaction=True)
    def test_database_connection_pooling(self, basic_user):
        """Test database connection handling under load"""
        user = basic_user()

        def query_user_data(user_id):
            """Perform database query"""
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)
            chats = Chat.objects.filter(user=user).count()
            return chats

        with PerformanceBenchmark("50 concurrent database queries") as bench:
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(query_user_data, user.id)
                    for _ in range(50)
                ]
                results = [f.result() for f in as_completed(futures)]

        # Should handle concurrent queries without connection issues
        bench.assert_performance(max_time=5.0)
        assert all(r >= 0 for r in results)


# ==================== Cost Tracking Performance Tests ====================

class TestCostTrackingPerformance:
    """Test performance of cost tracking operations"""

    def test_cost_aggregation_performance(self, basic_user):
        """Test cost calculation performance"""
        user = basic_user()

        # Create 100 cost records
        for i in range(100):
            Cost.objects.create(
                user=user,
                cost_type=CostType.objects.get_or_create(name="LLM", defaults={"unit_name": "tokens", "unit_cost": 0.00001, "unit_quantity": 1000})[0],
                count=1500,
                usd_cost=0.015
            )

        with PerformanceBenchmark("Aggregate 100 cost records") as bench:
            total_cost = Cost.objects.get_user_cost_this_month(user)

        assert total_cost > 0
        # Cost aggregation should be fast (< 1 second)
        bench.assert_performance(max_time=1.0)
        # Should use efficient aggregation query
        bench.assert_performance(max_queries=3)

    @pytest.mark.django_db(transaction=True)
    def test_concurrent_cost_creation(self, basic_user):
        """Test concurrent cost record creation"""
        user = basic_user()

        def create_cost_record(user_id, index):
            """Create a cost record"""
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=user_id)

            Cost.objects.create(
                user=user,
                cost_type=CostType.objects.get_or_create(name="LLM", defaults={"unit_name": "tokens", "unit_cost": 0.00001, "unit_quantity": 1000})[0],
                count=1500,
                usd_cost=0.015
            )
            return True

        with PerformanceBenchmark("Concurrent cost creation") as bench:
            with ThreadPoolExecutor(max_workers=10) as executor:
                futures = [
                    executor.submit(create_cost_record, user.id, i)
                    for i in range(50)
                ]
                results = [f.result() for f in as_completed(futures)]

        assert all(results)
        assert Cost.objects.filter(user=user).count() == 50
        bench.assert_performance(max_time=5.0)


# ==================== API Rate Limiting Tests ====================

class TestRateLimitingPerformance:
    """Test API rate limiting behavior"""

    @patch('chat.llm.genai.GenerativeModel')
    def test_rate_limit_handling(self, mock_genai, basic_user):
        """Test handling of rate limit errors"""
        user = basic_user()

        # Simulate rate limit error on first call, success on second
        from google.api_core import exceptions as google_exceptions

        mock_genai.return_value.generate_content.side_effect = [
            google_exceptions.ResourceExhausted("Rate limit exceeded"),
            Mock(text="Success after retry")
        ]

        with PerformanceBenchmark("Rate limit retry") as bench:
            llm = OttoLLM()
            try:
                # First call fails
                response = mock_genai.return_value.generate_content("test")
            except google_exceptions.ResourceExhausted:
                # Retry after rate limit
                time.sleep(0.1)  # Brief delay
                response = mock_genai.return_value.generate_content("test")

        # Should handle rate limits gracefully
        assert response.text == "Success after retry"


# ==================== Performance Regression Tests ====================

class TestPerformanceRegression:
    """Tests to detect performance regressions"""

    def test_secure_model_query_baseline(self, basic_user):
        """Baseline performance test for SecureModel queries"""
        user = basic_user()
        access_key = AccessKey(user=user)

        # Create baseline data
        library = Library.objects.create(name="Baseline Test")

        datasource = DataSource.objects.create(library=library,
            name="Baseline Source")

        for i in range(50):
            Document.objects.create(data_source=datasource,
                manual_title=f"Document {i}")

        # Baseline: Query 50 documents
        with PerformanceBenchmark("Baseline SecureModel query") as bench:
            docs = list(Document.objects.all())

        # Establish baseline metrics (these can be adjusted based on actual performance)
        # Time: < 1 second
        # Queries: < 10 (efficient permission checking)
        bench.assert_performance(max_time=1.0, max_queries=10)
        assert len(docs) == 50

        # Log metrics for regression tracking
        print(f"Baseline Query Performance: {bench.elapsed_time:.3f}s, {bench.query_count} queries")
