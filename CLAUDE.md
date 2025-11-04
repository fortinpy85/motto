# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## AI Assistant Guidance

This repository contains guidance files for AI assistants to help them understand the project and its conventions. 

- `GEMINI.md`: Provides guidance for Google's Gemini model.
- `CLAUDE.md`: Provides guidance for Anthropic's Claude model.

These files contain information about the project's architecture, development commands, and best practices.

## Project Overview

Otto is a Django-based platform for hosting AI tools, data visualizations, and legal research applications at Justice Canada. The platform provides:
- **Chat/AI Assistant**: Multi-mode chat interface (chat, Q&A, summarize, translate) using **Google Gemini** as the primary LLM provider via llama-index
- **Legislation Search**: Vector-based search across Canadian laws and regulations with XML processing
- **Librarian**: Document management and RAG (retrieval-augmented generation) system with pgvector
- **Text Extractor**: Document processing and format conversion utilities using Gemini OCR
- **SecureModel Framework**: Row-level security system for fine-grained access control

The application runs on Django with Celery for async processing, PostgreSQL with pgvector for embeddings, and Redis for caching/sessions.

**LLM Migration Status**: Otto has fully migrated from Azure OpenAI to Google Gemini for all LLM operations including chat, translation, summarization, and document processing.

## Development Commands

### Initial Setup
```bash
# Run initial dev environment setup (creates .env, runs migrations, loads fixtures)
bash dev_setup.sh

# Apply migrations and load all initial data
bash django/initial_setup.sh
```

### Running the Application
```bash
# Start Django development server (from django/)
python manage.py runserver

# Start Celery worker for async tasks (from django/)
celery -A otto worker -l INFO --pool=gevent --concurrency=256

# Start Celery beat scheduler for periodic tasks (from django/)
celery -A otto beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Run both Django and Celery using VSCode debug configuration:
# "Django: Run Server & Celery Worker"
```

### Testing
```bash
# Collect static files before running tests (from repo root)
python django/manage.py collectstatic --noinput

# Run all tests with coverage (from repo root)
python -m coverage run --source=django -m pytest django/tests
python -m coverage html
python -m coverage report

# Run specific test file
python -m pytest django/tests/test_file.py

# Run tests with specific marker
python -m pytest -m "not slow"

# View coverage report
# Open htmlcov/index.html in browser
```

### Database Management
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Reset specific app data (from django/)
python manage.py reset_app_data apps groups

# Reset libraries and vector store (WARNING: deletes all vector data)
python manage.py reset_app_data libraries

# Complete database reset (WARNING: deletes all data)
python manage.py reset_database
```

### Data Loading
```bash
# Load corporate Q&A library (generates LLM costs)
python manage.py load_corporate_library

# Load minimal laws (1 act, 1 regulation) - fast for testing
python manage.py load_laws_xml --reset --small --start

# Load ~50 laws (~30 min, ~$2 cost)
python manage.py load_laws_xml --reset --start

# Load all laws (~8 hours, ~$20 cost)
python manage.py load_laws_xml --reset --start --full

# Incrementally add laws (without --reset)
python manage.py load_laws_xml --start
```

### Translations
```bash
# Generate/update translations (requires gettext binaries)
python manage.py load_app_localization
```

### User Management
```bash
# Set user as Otto admin (after logging in at least once)
python manage.py set_admin_user <firstname.lastname@justice.gc.ca>

# Sync users from Azure
python manage.py sync_users
```

## Architecture and Key Concepts

### Django Apps Structure
- **otto/**: Core app with User model, SecureModel framework, shared utilities, authentication
- **chat/**: AI chat interface with LLM integration (llm.py, llm_models.py, prompts.py, responses.py)
- **librarian/**: Document management, RAG system, vector store operations
- **laws/**: Legislation search with XML processing and vector embeddings
- **text_extractor/**: Document format conversion and text extraction
- **search_history/**: User search history tracking
- **template_wizard/**: Template generation utilities

### SecureModel Row-Level Security

**Critical**: Most models inherit from `SecureModel` or `SecureReadOnlyModel` in `otto/secure_models.py`.

**Key concepts**:
- **AccessKey**: Required for all CRUD operations - `AccessKey(user=request.user)` or `AccessKey(bypass=True)`
- **Permissions**: `grant_view_to()`, `grant_change_to()`, `grant_delete_to()`, `grant_ownership_to()` (instance methods)
- **Create permission**: `Model.grant_create_to(access_key)` (class method)
- **Querying**: `Model.objects.all(access_key=access_key)` - filters by user permissions
- **Creating**: `Model.objects.create(access_key=access_key, ...)`
- **Saving**: `instance.save(access_key=access_key)`
- **Deleting**: `instance.delete(access_key=access_key)`

**Example**:
```python
from otto.secure_models import AccessKey

access_key = AccessKey(user=request.user)
# Query respects permissions
docs = Document.objects.all(access_key=access_key)
# Create with automatic permission grant
doc = Document.objects.create(access_key=access_key, title="...")
# Grant permissions
doc.grant_view_to(AccessKey(user=other_user))
```

See `django/otto/README.md` for complete SecureModel documentation.

### LLM Integration (chat app)

**Architecture**:
- **llm_models.py**: Model definitions, configurations, pricing (MODELS_BY_ID dict)
- **llm.py**: LlamaIndex integration, vector store setup, retrieval logic
- **prompts.py**: System prompts and prompt templates
- **responses.py**: Response generation logic for different modes
- **tasks.py**: Celery tasks for async LLM operations

**Key models**:
- Chat modes: `chat`, `qa`, `summarize`, `translate`
- Q&A modes: `rag` (top excerpts) vs `summarize` (full documents)
- Models managed via `get_model(model_id)` and `MODELS_BY_ID`

**Vector store**: Uses pgvector via `PGVectorStore` from llama-index

### Document Processing (librarian app)

**Key utilities** (in `librarian/utils/`):
- **process_engine.py**: Main document processing orchestration
- **process_document.py**: Individual document processing logic
- **markdown_splitter.py**: Text chunking for embeddings
- **extract_emails.py**, **extract_zip.py**: Specialized extractors

**Models**:
- Library: Container for documents/datasources with permissions
- DataSource: Folder-like organization within libraries
- Document: Individual documents with vector embeddings
- SavedFile: File storage references

### Celery Tasks

**Task locations**:
- `chat/tasks.py`: LLM processing tasks
- `librarian/tasks.py`: Document ingestion, embedding generation
- `laws/tasks.py`: Law loading and processing
- `text_extractor/tasks.py`: Document conversion tasks

**Important**: Celery requires manual restart when code changes. Not hot-reloaded like Django.

### Authentication and Authorization

**Authentication** (`otto/utils/auth.py`):
- Uses Microsoft Entra ID (Azure AD) for SSO
- Custom User model with `upn` (User Principal Name) as username
- Groups: "Otto admin", "Operations admin" for role-based access

**Authorization**:
- Django `rules` library for object-level permissions
- SecureModel for row-level security
- Group-based admin checks: `user.is_admin`, `user.is_operations_admin`

### Logging

**Required**: Use structlog for all user actions and important events.

```python
from structlog import get_logger

logger = get_logger(__name__)

# Log user actions
logger.info("User uploaded document", document_id=doc.id, user=request.user.upn)

# Log errors
logger.error("Document processing failed", document_id=doc.id, error=str(e))

# Debug logs (only visible when LOG_LEVEL=DEBUG)
logger.debug("Processing started", context=data)
```

### Translations

**Three levels** (see README.md Translations section):
1. **Model-level**: Use django-modeltranslation, register in `translation.py` files
2. **Python code**: Import `gettext as _`, wrap strings: `_("Text to translate")`
3. **Templates**: Load `{% load i18n %}`, use `{% trans "..." %}` or `{% blocktrans %}`

**Always** run `python manage.py load_app_localization` before creating PRs if you've added/modified translatable text.

### Environment Configuration

**Environment variables** (`.env` file):
- Database: `DJANGODB_*` vars for PostgreSQL connection
- Vector DB: `VECTORDB_*` vars (can be same as DJANGODB)
- Redis: `REDIS_HOST`, `REDIS_PORT`
- **LLM (Required)**: `GEMINI_API_KEY` for Google Gemini models
- Azure (Optional/Legacy):
  - `AZURE_STORAGE_ACCOUNT_NAME`, `AZURE_STORAGE_CONTAINER` - if using Azure Blob Storage
  - `AZURE_KEYVAULT_URL` - if using Azure Key Vault for secrets
  - Entra ID vars - for SSO authentication
- `DEBUG`, `LOG_LEVEL`, `CELERY_LOG_LEVEL`

**Important**: Otto now uses Google Gemini for all LLM operations. Azure Cognitive Services (translation) is no longer used.

**See** `.env.example` for full list and defaults.

## Common Patterns and Best Practices

### Working with SecureModel
1. **Always** use `AccessKey` for queries: `Model.objects.all(access_key=access_key)`
2. **Always** check permissions before operations
3. Use `grant_ownership_to()` for full permissions (view, change, delete)
4. Use `AccessKey(bypass=True)` only for system operations, never for user requests

### LLM Operations
1. **Always** track costs: Use `Cost.objects.create()` or `set_costs()`
2. Use appropriate model for task (see `chat/llm_models.py`)
3. Handle streaming responses for better UX
4. Implement proper error handling for LLM failures

### Async Processing
1. Use Celery tasks for long-running operations (>5 seconds)
2. Always return task IDs for status tracking
3. Implement proper error handling and retries
4. Log all task executions and failures

### Testing
1. Tests located in `django/tests/` (not scattered across apps)
2. Use pytest with `@pytest.mark.django_db` for DB access
3. Use fixtures in `tests/conftest.py` for common test data
4. Test views: check status codes and key content
5. Test models: unit test business logic separately

## Development Workflow

### Branch Strategy
1. **Never** commit directly to `main`
2. Create feature branches: `git checkout -b feature-name`
3. Merge `main` before opening PR: `git merge origin/main`
4. Use conventional commits: `feat:`, `fix:`, `chore:`, `refactor:`

### Pull Request Checklist
1. Run tests and ensure they pass locally
2. Generate translations if text was added/modified
3. Write tests for new functionality
4. Get code review before merging
5. Use draft PRs for work-in-progress

### Docker Development
- Uses Dev Containers (`.devcontainer/`)
- Services: PostgreSQL (pgvector), Redis, Django, Celery
- **Important**: VPN required for Azure resources
- First setup takes 5-10 minutes

## Deployment

### Build Docker Image
```powershell
.\build_and_push_image.ps1
```
Prompts for subscription ID and registry name, builds and pushes to Azure Container Registry.

### Infrastructure
See [otto-infrastructure repo](https://github.com/justicecanada/otto-infrastructure) for AKS deployment.

## Important Notes

- **Celery restart required**: Code changes don't hot-reload in Celery workers
- **VPN required**: For Azure resource access during development
- **Cost tracking**: LLM operations generate real costs - track everything
- **Security**: Never commit `.env` or credentials
- **Migrations**: Always create and commit migrations for model changes
- **PgBouncer**: Can be enabled locally for connection pooling (see `.env.example`)
