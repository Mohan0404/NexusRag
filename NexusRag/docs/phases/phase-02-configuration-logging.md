# Phase 2 — Configuration & Logging

## 1. Objective

Phase 2 establishes the centralized configuration and logging infrastructure for **NexusRAG**. In production RAG systems, configuration and telemetry are foundational:
- Without centralized configuration, application components scatter calls to `os.getenv()`, making runtime configurations brittle, untestable, and prone to silent failures when missing or misconfigured.
- Without strict separation between secrets and non-secret hyperparameters, sensitive credentials (like LLM API keys) risk accidental commit to version control or leakage in log aggregators.
- Without structured and sanitized logging, developers lack visibility into system execution, or worse, inadvertently leak API keys, authorization tokens, or passwords to log files and observability platforms.

This phase equips the backend with a robust, type-safe settings foundation and an automated log redaction filter that safeguards system secrets while providing clear operational visibility.

---

## 2. Files Created / Modified

| File | Purpose | What was implemented |
| :--- | :--- | :--- |
| `backend/app/core/config.py` | Centralized configuration engine | Implemented `Settings` (Pydantic Settings) and submodels `RAGConfig`, `CacheConfig`, `LLMConfig`. Added YAML parsing, alias mapping, secret protections with `SecretStr`, and `@lru_cache` accessor. |
| `backend/app/core/logging.py` | Centralized logging engine | Created `setup_logging`, `get_logger`, `SensitiveDataFilter`, and `SensitiveDataFormatter` to redact Gemini keys, OpenRouter keys, Bearer tokens, and credential key-value pairs. |
| `backend/config.yaml` | Non-secret system parameters | Configured algorithm hyperparameters: `chunk_size`, `chunk_overlap`, `top_k`, `cache_ttl`, and LLM `temperature`. |
| `backend/.env` | Local environment variables & secrets | Defined server variables, provider selections, and local secret placeholders (`GEMINI_API_KEY`, `OPENROUTER_API_KEY`, `REDIS_URL`, `CHROMA_PATH`). |
| `backend/.env.example` | Environment template | Documented all required and optional environment keys for onboarding and deployment. |
| `.env.example` | Root environment template | Synchronized workspace-level template matching backend settings. |
| `backend/app/main.py` | Application entry point | Cleaned temporary debug prints, retaining clean lifecycle logging using the centralized logger and settings. |
| `backend/tests/test_config.py` | Configuration test suite | Created 6 test cases verifying default settings, YAML loading, validation bounds, invalid overlap errors, secret masking with `SecretStr`, and prevention of secrets in YAML. |
| `backend/tests/test_logging.py` | Logging test suite | Created 4 test cases verifying level configuration, pattern-based secret redaction, normal log preservation, and stream handler integration. |
| `backend/tests/test_health.py` | Health endpoint tests | Updated project name assertion to support `NexusRAG`. |
| `.gitignore` | Git ignore rules | Ignored `.env`, `.venv`, `logs/`, `*.log`, `__pycache__`, and test caches. |

---

## 3. Configuration Architecture

### The Dual-Source Configuration Hierarchy

NexusRAG employs a strict dual-source architecture that cleanly separates **secrets & deployment environments** from **algorithmic hyperparameters**:

```text
       .env / Environment Variables               config.yaml
   (Secrets, Ports, Hosts, Provider Names)    (Chunking, TTL, Top-K, Temperature)
                      │                                    │
                      ▼                                    ▼
       ┌─────────────────────────────────────────────────────────────┐
       │                Pydantic Settings (Settings)                 │
       │  - Type Validation & Coercion (int, bool, float)            │
       │  - Boundary Validation (chunk_overlap < chunk_size)         │
       │  - Secret Masking (SecretStr)                               │
       │  - Security Checks (Rejects secrets in YAML)                │
       └─────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
                      Centralized Singleton (get_settings)
                                      │
           ┌──────────────────────────┼──────────────────────────┐
           ▼                          ▼                          ▼
     FastAPI App / Router       Future RAG Pipeline        Future Vector / Cache
    (CORS, Prefixes, Port)    (Chunker, Embedder, LLM)       (ChromaDB, Redis)
```

### Separation Rules

| Setting Type | Destination | Reason |
| :--- | :--- | :--- |
| **Secrets & Keys** (`GEMINI_API_KEY`, `OPENROUTER_API_KEY`) | `.env` or Host Environment | Must never be committed to Git. Varies per environment (Dev, Staging, Prod). |
| **Infrastructure Endpoints** (`REDIS_URL`, `CHROMA_PATH`, `HOST`, `PORT`) | `.env` or Host Environment | Specific to host networking and container topology. |
| **Algorithm Hyperparameters** (`chunk_size`, `chunk_overlap`, `top_k`) | `config.yaml` | Algorithmic tuning parameters that should be tracked in version control. |
| **Execution Controls** (`temperature`, `cache_ttl`) | `config.yaml` | Non-sensitive defaults shared across development team and reproducibility benchmarks. |

---

## 4. File-by-File Walkthrough

### `backend/app/core/config.py`
- **Responsibility**: Single source of truth for all application configuration.
- **Important Classes & Functions**:
  - `RAGConfig(BaseModel)`: Validates `chunk_size > 0`, `chunk_overlap >= 0`, `top_k > 0`, and enforces `chunk_overlap < chunk_size` via `@model_validator(mode="after")`.
  - `CacheConfig(BaseModel)`: Validates `cache_ttl >= 0`.
  - `LLMConfig(BaseModel)`: Validates `0.0 <= temperature <= 2.0`.
  - `Settings(BaseSettings)`: Main configuration class reading `.env` and merging `config.yaml`.
  - `get_settings() -> Settings`: Decorated with `@lru_cache` to ensure a singleton instance across requests while allowing test mocking.
- **Key Fields**: `PROJECT_NAME`, `DEBUG`, `LOG_LEVEL`, `GEMINI_API_KEY` (as `SecretStr`), `OPENROUTER_API_KEY` (as `SecretStr`), `LLM_PROVIDER`, `LLM_MODEL`, `CHROMA_PATH`, `REDIS_URL`.
- **Security Check**: `_load_yaml_config()` inspects `config.yaml` and throws a `ValueError` if keys containing `api_key`, `secret`, `password`, or `token` are found.
- **Future Use**: Ingestion services query `settings.chunk_size` and `settings.chunk_overlap`. Vector stores consume `settings.CHROMA_PATH`. LLM services read `settings.LLM_PROVIDER` and unpack `settings.GEMINI_API_KEY.get_secret_value()`.

### `backend/app/core/logging.py`
- **Responsibility**: Application-wide structured logging and automated secret redaction.
- **Important Classes & Functions**:
  - `SensitiveDataFilter(logging.Filter)`: Inspects log record messages and arguments using compiled regular expressions to identify and mask tokens.
  - `SensitiveDataFormatter(logging.Formatter)`: Guarantees that the final rendered log string has all secret patterns replaced with `[REDACTED]`.
  - `setup_logging(log_level, log_file_path)`: Configures console (`sys.stdout`) and persistent file handlers with the redaction formatter and filter.
  - `get_logger(name)`: Provides named logger instances.
- **Future Use**: Ingestion, cache hits/misses, vector search latencies, and LLM completions log through `get_logger(__name__)` without fear of exposing raw bearer tokens or API keys.

### `backend/config.yaml`
- **Responsibility**: Human-readable, non-secret parameters maintained in Git.
- **Contents**:
  ```yaml
  rag:
    chunk_size: 500
    chunk_overlap: 50
    top_k: 4

  cache:
    cache_ttl: 3600

  llm:
    temperature: 0.2
  ```
- **Future Use**: Modifying chunk size or retrieval depth during evaluation requires updating this single file without touching code.

### `backend/.env` & `backend/.env.example`
- **Responsibility**: Local developer environment configuration.
- **Contents**: Application metadata, local server port/host, active LLM provider selection, placeholder API keys, and local Redis/Chroma endpoints.
- **Future Use**: Developers copy `.env.example` to `.env` and populate their local API keys.

### `backend/app/main.py`
- **Responsibility**: Application bootstrap and middleware setup.
- **Updates**: Removed temporary debug prints. Integrates cleanly with `setup_logging` and `get_settings()` during FastAPI lifespan startup and shutdown events.

### `backend/tests/test_config.py`
- **Responsibility**: Unit testing configuration parsing, boundary validation, YAML integration, and security guardrails.
- **Test Cases**:
  1. `test_default_settings_instantiation`: Verifies clean defaults without external services.
  2. `test_yaml_config_parameters`: Confirms YAML hyperparameters are loaded and accessible.
  3. `test_invalid_rag_overlap_validation`: Confirms `chunk_overlap >= chunk_size` raises `ValidationError`.
  4. `test_invalid_llm_temperature_validation`: Confirms temperatures outside `[0.0, 2.0]` raise `ValidationError`.
  5. `test_prohibited_secrets_in_yaml`: Confirms adding an API key to `config.yaml` throws a security `ValueError`.
  6. `test_secret_masking`: Confirms `SecretStr` masks raw keys in string and repr forms.

### `backend/tests/test_logging.py`
- **Responsibility**: Unit testing logging setup and automated redaction.
- **Test Cases**:
  1. `test_sensitive_data_filter_redaction`: Tests regex redaction on Gemini keys, OpenRouter keys, Bearer headers, and key-value formats.
  2. `test_sensitive_data_filter_preserves_normal_messages`: Confirms standard logs remain unchanged.
  3. `test_logging_level_configuration`: Verifies dynamic log level configuration.
  4. `test_logger_redaction_stream`: Confirms end-to-end redaction through a stream handler.

### `backend/tests/test_health.py`
- **Responsibility**: Regression testing Phase 1 health check.
- **Updates**: Updated assertion to validate `settings.PROJECT_NAME in ("NexusRAG", "GenWorx RAG")`.

---

## 5. Important Implementation Decisions

1. **Pydantic Settings over Raw `os.getenv`**:
   - `os.getenv` returns untyped strings or `None`, forcing type casts (`int(os.getenv(...))`) everywhere, which fail unpredictably at runtime. Pydantic Settings parses types, validates ranges, provides sensible defaults, and fails fast at startup.
2. **`SecretStr` for API Keys**:
   - Accidental logging of settings (e.g. `logger.info("Config: %s", settings.dict())`) is a leading cause of credential exposure. Wrapping keys in `SecretStr` ensures their `__str__` and `__repr__` output `**********`. Accessing raw values requires calling `.get_secret_value()`.
3. **Dedicated YAML Security Guard**:
   - Developers sometimes mistakenly commit secrets into configuration files. `config.py` explicitly parses YAML keys for prohibited substrings (`api_key`, `secret`, `password`, `token`) and aborts startup if detected.
4. **Custom Redaction Formatter + Filter in Logging**:
   - Filters alone can be bypassed if records are formatted irregularly. Coupling a `SensitiveDataFilter` with a `SensitiveDataFormatter` guarantees that any rendered log message passing through standard streams or log files is sanitized.
5. **Separation of Secrets (`.env`) from Hyperparameters (`config.yaml`)**:
   - In ML/RAG development, hyperparameters are iterated upon frequently and should be version-controlled with code. Secrets belong strictly in environment variables and container secrets.

---

## 6. Data & Control Flow

### Configuration Flow

```text
[ Developer / Deployment System ]
               │
      ┌────────┴────────┐
      ▼                 ▼
   [.env]         [config.yaml]
      │                 │
      ▼                 ▼
  Pydantic BaseSettings Ingestion
      │
      ├─► Validate types (str, int, bool, float)
      ├─► Validate boundary invariants (overlap < chunk_size)
      ├─► Mask secrets in SecretStr
      ├─► Verify no secrets present in YAML
      ▼
  @lru_cache get_settings() Singleton
      │
      ├─► app.main (Title, CORS, Host, Port)
      ├─► app.api (API version prefixes)
      └─► Future modules (Ingestion, Retriver, LLM)
```

### Logging Flow

```text
Application Component (e.g., app.api.routes_chat)
      │
      ▼
logger.info("User query processed with key: %s", raw_key)
      │
      ▼
SensitiveDataFilter
      │ (Filters record.msg & record.args via regex)
      ▼
SensitiveDataFormatter
      │ (Applies final regex sweep on formatted string)
      ▼
Replaces secrets with [REDACTED]
      │
      ├──► stdout / Terminal
      └──► logs/app.log
```

---

## 7. Security Considerations

- **Secret Handling**: All API keys use `pydantic.SecretStr`. Plaintext values are never held in untyped strings.
- **Version Control Protection**: `.env` is listed in `.gitignore`. Only `.env.example` containing dummy placeholders is tracked in Git.
- **Zero Raw Secrets in Logs**: Dual-layered redaction ensures that accidental log statements (e.g., logging headers, query params, or error responses) have sensitive patterns redacted before being written.
- **Fail-Fast Invariants**: Invalid hyperparameters (e.g., negative chunk sizes or overlap greater than chunk size) abort application startup immediately rather than failing silently during document processing.

---

## 8. Testing

### Test Suite Summary

Tests were run in the activated virtual environment using `pytest`:

```powershell
.venv\Scripts\Activate.ps1; cd NexusRag/backend; python -m pytest -v
```

### Results
```text
============================= test session starts =============================
platform win32 -- Python 3.11.0, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\Academic-Projects\RAG\NexusRag\backend
plugins: anyio-4.15.1
collected 13 items

tests/test_config.py::test_default_settings_instantiation PASSED         [  7%]
tests/test_config.py::test_yaml_config_parameters PASSED                 [ 15%]
tests/test_config.py::test_invalid_rag_overlap_validation PASSED         [ 23%]
tests/test_config.py::test_invalid_llm_temperature_validation PASSED     [ 30%]
tests/test_config.py::test_prohibited_secrets_in_yaml PASSED             [ 38%]
tests/test_config.py::test_secret_masking PASSED                         [ 46%]
tests/test_health.py::test_health_check_returns_200_and_healthy PASSED   [ 53%]
tests/test_health.py::test_health_check_content_type PASSED              [ 61%]
tests/test_health.py::test_app_operates_without_external_dependencies PASSED [ 69%]
tests/test_logging.py::test_sensitive_data_filter_redaction PASSED       [ 76%]
tests/test_logging.py::test_sensitive_data_filter_preserves_normal_messages PASSED [ 84%]
tests/test_logging.py::test_logging_level_configuration PASSED           [ 92%]
tests/test_logging.py::test_logger_redaction_stream PASSED               [100%]

======================= 13 passed, 2 warnings in 0.89s ========================
```

---

## 9. How This Connects to Future Phases

| Future Component | Phase | How Phase 2 Configuration & Logging is Consumed |
| :--- | :---: | :--- |
| **Document Ingestion** | Phase 3 | Reads `settings.chunk_size` and `settings.chunk_overlap` for chunking documents. Logs document parsing errors via `get_logger(__name__)`. |
| **Embeddings** | Phase 4 | Injects model dimension and embedding parameters. Ingestion logs embedding latencies. |
| **ChromaDB Store** | Phase 5 | Connects to `settings.CHROMA_PATH` to persist vector collections. |
| **Gemini / OpenRouter LLM Services** | Phase 6 | Reads `settings.LLM_PROVIDER`, `settings.LLM_MODEL`, `settings.llm_temperature`, and safely unpacks `settings.GEMINI_API_KEY.get_secret_value()`. |
| **Redis Cache** | Phase 7 | Connects using `settings.REDIS_URL` and manages cache invalidation using `settings.cache_ttl`. |
| **RAG Pipeline** | Phase 8 | Retrieves `settings.top_k` documents to assemble the contextual prompt for the LLM. |

---

## 10. Interview Knowledge (Applied to NexusRAG)

- **Dependency Injection**: Instead of instantiating settings inside individual functions, components declare `settings: Settings = Depends(get_settings)`. This allows test fixtures to inject custom settings without modifying source code.
- **Configuration Management**: Splitting environment variables from configuration files is an industry standard (12-Factor App methodology). Environment variables adapt the app to its deployment environment; config files govern application behavior.
- **Pydantic Settings**: Provides type coercion, validation, and error reporting on startup. If an environment variable is invalid (e.g., `DEBUG=notabool`), the server stops immediately with clear diagnostic logs.
- **Secret Management (`SecretStr`)**: Prevents accidental data leaks. In Python, logging an object calls `__str__` or `__repr__`. `SecretStr` overrides both methods to display `**********`.
- **Log Sanitation**: Defends against log-injection and credential leakage vulnerabilities. Even if an unhandled exception or third-party error contains an API key, the logging filter strips the key before it hits disk or stdout.
- **Separation of Concerns**: `config.py` does not initialize the web app; `main.py` does not parse configuration files; routes do not read `.env` directly.

---

## 11. Verification Checklist

- [x] Application starts (`python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload`)
- [x] Configuration loads from `.env` and `config.yaml`
- [x] Health endpoint works (`GET /api/v1/health` returns `200` with `{"status": "healthy"}`)
- [x] All 13 pytest tests pass
- [x] Secrets are masked with `SecretStr` and redacted by logging filters
- [x] Existing Phase 1 functionality remains completely operational and regression-free
