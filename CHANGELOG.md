# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-05-09

### Added
- **LLM Gateway Model Router** - TaskType-based model selection with failover chains
- **Embedding Service** - OpenAI text-embedding-3-small integration
- **PGVector Operations** - VectorStore for knowledge chunk storage and similarity search
- **RBAC MANAGER Role** - Full 4-role system with spec-compliant permissions

### Changed
- **RBAC Permission Matrix** - Fixed MEMBER/VIEWER permissions per spec Section 3.2
- **Departments Router** - Registered in main.py with RBAC enforcement
- **Integration Tests** - Redis RT rotation/blacklist tests, auth flow tests
- **Dashboard Placeholder Components** - Improved UI structure with proper CSS classes

### Fixed
- **MANAGER Role Missing** - Added to Role enum, ROLE_HIERARCHY, and PERMISSIONS
- **Member Permissions** - Removed users:read/write per spec
- **Viewer Permissions** - Removed knowledge:write per spec
- **TaskSubmit Button Text** - Changed from "Cancel" to "Close" for test compatibility

## [0.3.0] - 2026-05-08

### Added
- **Tauri Desktop Client** - Cross-platform desktop app with WebView2/WebKit
- **React Frontend** - Dashboard, Login, Settings, Knowledge, and Task components
- **E2E Test Suite** - Playwright-based end-to-end tests for auth flows
- **WebSocket Client** - Real-time communication support in Tauri client
- **Sync Engine** - Background synchronization with retry logic

### Changed
- **Auth Flow** - Added JSON-based `/api/v1/auth/login` endpoint for client apps
- **RouteGuard** - Added loading state to prevent premature auth redirects
- **Docker Compose** - IPv4 proxy target for backend (192.168.155.4:8000)

### Fixed
- **Login Redirect Issue** - RouteGuard now waits for auth restoration before checking authentication
- **UUID Serialization** - JWT encoder handles UUID objects correctly
- **CORS Configuration** - Added localhost:1420 to allowed origins

## [0.2.1] - 2026-05-08

### Added
- **Structured Logging** - structlog-based JSON logging with timestamps, service info, and correlation IDs
- **Request Logging Middleware** - HTTP request/response logging with timing and X-Request-ID headers
- **Security Headers Middleware** - TrustedHostMiddleware and CORS middleware stack
- **Rate Limiting Middleware** - Redis-based rate limiting (60 req/min default, configurable)
- **WebSocket Endpoint** - Real-time bidirectional communication at `/api/v1/ws`
- **Enhanced Health Check** - Health endpoint with detailed status reporting

### Changed
- **Dependencies** - Added structlog ^24.1 for production-ready structured logging

## [0.2.0] - 2026-05-07

### Added
- **BDD E2E Tests** - Behave-based acceptance tests for 4 features:
  - Login flow (7 scenarios) - authentication, token refresh, device fingerprint
  - Agent operations (5 scenarios) - task queue, failover, timeout handling
  - Knowledge contribution (7 scenarios) - draft, review, approve/reject, publish
  - Client sync (5 scenarios) - MCP sync, settings, offline support
- **Docker Compose** - PostgreSQL and Redis services for local development
- **Behave Configuration** - BDD framework integration in pyproject.toml

### Changed
- **Token Service** - Fixed flaky access token comparison in integration tests
- **Test Coverage** - 144 unit/integration tests + 24 BDD scenarios

### Fixed
- Thread-safety issue in gateway service (random.seed → rng = random.Random(seed))
- Removed dead code (_MODELS unused variable)

## [0.1.0] - 2026-05-07

### Added
- **Token Service** - JWT creation/verification, fingerprint-based auth, Redis RT storage
- **Auth Service** - bcrypt password hashing, TOTP 2FA, login flow integration
- **Tenant Service** - Organization/Department/User CRUD, RBAC engine (member/manager/admin)
- **Gateway Service** - Model router, failover chain, cost metrics
- **Knowledge Service** - KnowledgeStatus state machine, RAG pipeline, SSE events

### Features
- RS256 JWT with access token (15min) and refresh token (7 days)
- Sliding window token refresh with fingerprint validation
- Device registration and management
- Role-based permissions (RBAC) with 8 permission categories
- Model failover with priority-based routing
- Knowledge workflow: draft → pending_review → approved → published