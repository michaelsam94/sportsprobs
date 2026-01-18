# Architecture Documentation

## Overview

This backend follows **Clean Architecture** principles, ensuring separation of concerns, testability, and maintainability. The architecture is divided into four main layers, each with distinct responsibilities.

## Folder Structure

```
backend/
├── app/
│   ├── api/                    # Presentation Layer
│   │   └── v1/                 # API Version 1
│   │       ├── endpoints/      # Route handlers
│   │       └── router.py       # API router
│   ├── core/                   # Core Configuration
│   │   ├── config.py           # Environment settings
│   │   ├── dependencies.py     # Dependency injection
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── middleware.py       # Middleware setup
│   ├── domain/                 # Domain Layer
│   │   ├── entities/           # Business entities
│   │   └── repositories/       # Repository interfaces
│   ├── application/            # Application Layer
│   │   ├── dto/                # Data Transfer Objects
│   │   └── services/           # Business logic services
│   ├── infrastructure/         # Infrastructure Layer
│   │   ├── database/           # Database models & session
│   │   └── repositories/       # Repository implementations
│   └── main.py                 # Application entry point
├── tests/                      # Test files
├── requirements.txt            # Python dependencies
└── README.md                   # Project documentation
```

## Layer Responsibilities

### 1. Domain Layer (`app/domain/`)

**Purpose**: Contains core business logic and entities. No dependencies on other layers.

**Components**:
- **Entities** (`entities/`): Core business objects
  - `Player`: Player domain entity
  - `Team`: Team domain entity
  - `Match`: Match domain entity
- **Repository Interfaces** (`repositories/`): Abstract contracts for data access
  - `IBaseRepository`: Generic CRUD operations
  - `IPlayerRepository`: Player-specific queries
  - `ITeamRepository`: Team-specific queries
  - `IMatchRepository`: Match-specific queries

**Key Principles**:
- Pure business logic
- No framework dependencies
- Immutable where possible
- Self-validating entities

### 2. Application Layer (`app/application/`)

**Purpose**: Orchestrates business logic and defines use cases. Depends only on Domain layer.

**Components**:
- **DTOs** (`dto/`): Data Transfer Objects for API communication
  - `PlayerCreateDTO`, `PlayerUpdateDTO`, `PlayerResponseDTO`
  - `TeamCreateDTO`, `TeamUpdateDTO`, `TeamResponseDTO`
  - `MatchCreateDTO`, `MatchUpdateDTO`, `MatchResponseDTO`
- **Services** (`services/`): Application services that orchestrate use cases
  - `PlayerService`: Player business logic
  - `TeamService`: Team business logic
  - `MatchService`: Match business logic

**Key Principles**:
- Use cases orchestration
- Input validation
- Error handling
- Entity-to-DTO conversion

### 3. Infrastructure Layer (`app/infrastructure/`)

**Purpose**: Implements technical details and external integrations. Depends on Domain and Application layers.

**Components**:
- **Database** (`database/`):
  - `base.py`: Database engine and session factory
  - `session.py`: Session management
  - `models/`: SQLAlchemy ORM models
    - `PlayerModel`: Database model for players
    - `TeamModel`: Database model for teams
    - `MatchModel`: Database model for matches
- **Repositories** (`repositories/`): Concrete implementations of domain interfaces
  - `BaseRepository`: Generic repository implementation
  - `PlayerRepository`: Player data access
  - `TeamRepository`: Team data access
  - `MatchRepository`: Match data access

**Key Principles**:
- Framework-specific implementations
- Database abstraction
- External service integrations
- Entity-to-model conversion

### 4. Presentation Layer (`app/api/`)

**Purpose**: Handles HTTP requests and responses. Depends on Application layer.

**Components**:
- **API Routes** (`v1/endpoints/`):
  - `players.py`: Player endpoints
  - `teams.py`: Team endpoints
  - `matches.py`: Match endpoints
- **Router** (`v1/router.py`): Aggregates all endpoint routers
- **Middleware** (`core/middleware.py`): CORS, rate limiting, etc.

**Key Principles**:
- Request/response handling
- Input validation (via Pydantic)
- Error handling
- Rate limiting
- API versioning

## Dependency Flow

```
┌─────────────────────────────────────┐
│   Presentation Layer (API)          │
│   - Routes                          │
│   - Middleware                      │
└──────────────┬──────────────────────┘
               │ depends on
               ▼
┌─────────────────────────────────────┐
│   Application Layer                  │
│   - Services                        │
│   - DTOs                            │
└──────────────┬──────────────────────┘
               │ depends on
               ▼
┌─────────────────────────────────────┐
│   Domain Layer                      │
│   - Entities                        │
│   - Repository Interfaces           │
└──────────────┬──────────────────────┘
               ▲
               │ implemented by
┌──────────────┴──────────────────────┐
│   Infrastructure Layer              │
│   - Repositories                    │
│   - Database Models                 │
└─────────────────────────────────────┘
```

## Key Features

### 1. API Versioning

API versioning is implemented through folder structure:
- `/api/v1/` - Version 1 endpoints
- Future versions: `/api/v2/`, etc.

### 2. Rate Limiting

Rate limiting is configured per endpoint using `slowapi`:
- Configurable per-minute and per-hour limits
- Based on client IP address
- Can be disabled via environment variable

### 3. Async Endpoints

All endpoints are async for better performance:
- Async database operations
- Non-blocking I/O
- Better concurrency handling

### 4. Environment-Based Configuration

Configuration is managed through:
- `.env` file for local development
- Environment variables for production
- Type-safe settings via Pydantic

### 5. Dependency Injection

FastAPI's dependency injection system is used for:
- Database sessions
- Repository instances
- Service instances

## Data Flow Example

### Creating a Player

1. **Request** → `POST /api/v1/players`
2. **Presentation Layer** (`players.py`):
   - Validates input via `PlayerCreateDTO`
   - Gets database session via dependency
   - Creates repository and service instances
3. **Application Layer** (`PlayerService`):
   - Converts DTO to domain entity
   - Validates business rules
   - Calls repository
4. **Infrastructure Layer** (`PlayerRepository`):
   - Converts entity to database model
   - Executes SQL query
   - Converts model back to entity
5. **Response** → Returns `PlayerResponseDTO`

## Testing Strategy

- **Unit Tests**: Test services and repositories in isolation
- **Integration Tests**: Test API endpoints with test database
- **Mocking**: Mock external dependencies (database, external APIs)

## Future Enhancements

- Authentication & Authorization
- Caching layer (Redis)
- Background task processing
- WebSocket support for real-time updates
- GraphQL API option
- API v2 with enhanced features

