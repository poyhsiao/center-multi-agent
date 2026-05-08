# Center Multi-Agent

A multi-agent orchestration system with authentication, RBAC, and knowledge management.

## Architecture

```
center-multi-agent/
├── backend/              # FastAPI backend (Python)
│   └── app/
│       ├── api/          # API endpoints
│       ├── core/         # Security, exceptions, config
│       ├── db/           # Database connections (Redis, PostgreSQL)
│       ├── models/       # Data models
│       ├── schemas/      # Pydantic schemas
│       └── services/     # Business logic
└── client/               # Tauri desktop client (Rust/TypeScript/React)
│   ├── src/              # React frontend
│   │   ├── components/   # UI components (Login, Dashboard, Settings, etc.)
│   │   ├── context/      # React context (AuthContext)
│   │   ├── hooks/        # Custom hooks
│   │   ├── lib/          # API client, auth utilities
│   │   └── pages/        # Page components
│   └── e2e/              # Playwright E2E tests
```

## Features

### Phase 1-4: Core Services (TDD)
- **Token Service** - JWT authentication with fingerprint-based device binding
- **Auth Service** - bcrypt password hashing + TOTP 2FA
- **Tenant Service** - Organization/Department/User CRUD with RBAC
- **Gateway Service** - Model router with failover chain
- **Knowledge Service** - Knowledge workflow with RAG pipeline

### Phase 5: BDD E2E Tests
- 4 Gherkin features with 24 scenarios
- Login flow, Agent operations, Knowledge contribution, Client sync

### Phase 6: Production Hardening
- Structured logging with structlog (JSON format, correlation IDs)
- Request logging middleware with timing
- Security middleware (TrustedHost, CORS)
- Redis-based rate limiting (60 req/min)
- WebSocket endpoint for real-time communication
- Enhanced health check with service status

## Quick Start

### Prerequisites
- Python 3.11+
- Docker (for PostgreSQL and Redis)

### Backend Setup

```bash
cd backend
poetry install
docker compose up -d  # Start PostgreSQL and Redis
poetry run pytest     # Run unit tests
poetry run behave tests/bdd/features  # Run BDD tests
```

### Environment Variables

```bash
# Backend (.env)
REDIS_URL=redis://localhost:6380/0
DATABASE_URL=postgresql://postgres:postgres@localhost:5433/center_multi_agent
JWT_SECRET=your-secret-key
```

## Testing

```bash
# Unit tests (124 tests)
poetry run pytest tests/unit/ -v

# Integration tests (4 tests, requires Redis)
REDIS_URL="redis://localhost:6380/0" poetry run pytest tests/integration/ -v

# BDD acceptance tests (24 scenarios)
poetry run behave tests/bdd/features -v

# All tests
REDIS_URL="redis://localhost:6380/0" poetry run pytest tests/ -v
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | 5433 | Primary database |
| Redis | 6380 | Cache and token storage |

## API Endpoints

### Authentication
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Token refresh
- `POST /api/v1/auth/logout` - Logout

### Tenant Management
- `GET/POST /api/v1/organizations` - Organization CRUD
- `GET/POST /api/v1/departments` - Department CRUD
- `GET/POST /api/v1/users` - User CRUD

### Knowledge
- `POST /api/v1/knowledge` - Submit knowledge
- `PUT /api/v1/knowledge/{id}/submit` - Submit for review
- `PUT /api/v1/knowledge/{id}/approve` - Approve knowledge
- `PUT /api/v1/knowledge/{id}/reject` - Reject knowledge
- `PUT /api/v1/knowledge/{id}/publish` - Publish knowledge

## License

MIT