# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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