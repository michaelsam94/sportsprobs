# Sports Analytics Backend

FastAPI backend for sports analytics mobile app with clean architecture.

## Architecture Overview

This backend follows **Clean Architecture** principles with clear separation of concerns:

```
backend/
├── app/
│   ├── api/              # Presentation Layer (API routes, middleware)
│   ├── core/             # Core configuration and utilities
│   ├── domain/           # Domain Layer (entities, interfaces)
│   ├── application/      # Application Layer (use cases, DTOs)
│   └── infrastructure/   # Infrastructure Layer (database, external services)
├── tests/                # Test files
└── requirements.txt      # Python dependencies
```

## Layer Responsibilities

### 1. Domain Layer (`app/domain/`)
- **Entities**: Core business objects (Player, Team, Match, etc.)
- **Interfaces**: Abstract repository and service interfaces
- **Value Objects**: Immutable domain values
- **No dependencies** on other layers

### 2. Application Layer (`app/application/`)
- **Use Cases**: Business logic orchestration
- **DTOs**: Data Transfer Objects for API communication
- **Services**: Application-level services
- **Depends on**: Domain layer only

### 3. Infrastructure Layer (`app/infrastructure/`)
- **Repositories**: Concrete implementations of domain interfaces
- **Database**: Database models, connections, migrations
- **External Services**: Third-party API integrations
- **Depends on**: Domain and Application layers

### 4. Presentation Layer (`app/api/`)
- **Routes**: API endpoints organized by version
- **Middleware**: Rate limiting, CORS, authentication
- **Dependencies**: FastAPI dependencies for DI
- **Depends on**: Application layer

## Key Features

- ✅ **REST API** with OpenAPI documentation
- ✅ **Async endpoints** for better performance
- ✅ **Rate limiting** per endpoint/user
- ✅ **API versioning** (v1, v2, etc.)
- ✅ **Environment-based configuration** (.env files)
- ✅ **Dependency injection** for testability
- ✅ **Type hints** throughout
- ✅ **Error handling** with custom exceptions

## Dependency Flow

```
Presentation (API) 
    ↓ depends on
Application (Use Cases)
    ↓ depends on
Domain (Entities/Interfaces)
    ↑ implemented by
Infrastructure (Repositories)
```

## Getting Started

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

3. Run the application:
```bash
uvicorn app.main:app --reload
```

4. Access API documentation:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Environment Variables

See `.env.example` for all available configuration options.

