# Folder Structure

Complete folder structure of the Sports Analytics Backend:

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                          # Application entry point
│   │
│   ├── api/                             # Presentation Layer
│   │   ├── __init__.py
│   │   └── v1/                          # API Version 1
│   │       ├── __init__.py
│   │       ├── router.py                # Main API router
│   │       └── endpoints/               # Route handlers
│   │           ├── __init__.py
│   │           ├── players.py            # Player endpoints
│   │           ├── teams.py              # Team endpoints
│   │           └── matches.py            # Match endpoints
│   │
│   ├── core/                            # Core Configuration
│   │   ├── __init__.py
│   │   ├── config.py                    # Environment settings
│   │   ├── dependencies.py              # Dependency injection
│   │   ├── exceptions.py                # Custom exceptions
│   │   ├── middleware.py                # Middleware setup
│   │   └── rate_limit.py               # Rate limiting utilities
│   │
│   ├── domain/                          # Domain Layer
│   │   ├── __init__.py
│   │   ├── entities/                    # Business entities
│   │   │   ├── __init__.py
│   │   │   ├── player.py                # Player entity
│   │   │   ├── team.py                  # Team entity
│   │   │   └── match.py                 # Match entity
│   │   └── repositories/                # Repository interfaces
│   │       ├── __init__.py
│   │       ├── base_repository.py       # Base repository interface
│   │       ├── player_repository.py      # Player repository interface
│   │       ├── team_repository.py       # Team repository interface
│   │       └── match_repository.py      # Match repository interface
│   │
│   ├── application/                     # Application Layer
│   │   ├── __init__.py
│   │   ├── dto/                         # Data Transfer Objects
│   │   │   ├── __init__.py
│   │   │   ├── player_dto.py            # Player DTOs
│   │   │   ├── team_dto.py              # Team DTOs
│   │   │   └── match_dto.py             # Match DTOs
│   │   └── services/                     # Business logic services
│   │       ├── __init__.py
│   │       ├── player_service.py        # Player service
│   │       ├── team_service.py          # Team service
│   │       └── match_service.py         # Match service
│   │
│   └── infrastructure/                  # Infrastructure Layer
│       ├── __init__.py
│       ├── database/                     # Database configuration
│       │   ├── __init__.py
│       │   ├── base.py                  # Database engine & base
│       │   ├── session.py               # Session management
│       │   └── models/                  # SQLAlchemy ORM models
│       │       ├── __init__.py
│       │       ├── player_model.py      # Player database model
│       │       ├── team_model.py        # Team database model
│       │       └── match_model.py       # Match database model
│       └── repositories/                 # Repository implementations
│           ├── __init__.py
│           ├── base_repository.py       # Base repository implementation
│           ├── player_repository.py     # Player repository implementation
│           ├── team_repository.py       # Team repository implementation
│           └── match_repository.py      # Match repository implementation
│
├── tests/                               # Test files (to be created)
│
├── .env.example                         # Environment variables template
├── .gitignore                           # Git ignore rules
├── requirements.txt                     # Python dependencies
├── README.md                            # Project documentation
├── ARCHITECTURE.md                      # Architecture documentation
└── FOLDER_STRUCTURE.md                  # This file
```

## Module Responsibilities Summary

### Presentation Layer (`app/api/`)
- **Purpose**: Handle HTTP requests/responses
- **Key Files**:
  - `main.py`: Application initialization
  - `api/v1/router.py`: Route aggregation
  - `api/v1/endpoints/*.py`: Individual endpoint handlers

### Core (`app/core/`)
- **Purpose**: Shared configuration and utilities
- **Key Files**:
  - `config.py`: Environment-based settings
  - `dependencies.py`: Dependency injection
  - `middleware.py`: CORS, rate limiting setup
  - `exceptions.py`: Custom error classes

### Domain Layer (`app/domain/`)
- **Purpose**: Core business logic (no dependencies)
- **Key Files**:
  - `entities/*.py`: Business entities
  - `repositories/*.py`: Repository interfaces

### Application Layer (`app/application/`)
- **Purpose**: Use cases and orchestration
- **Key Files**:
  - `dto/*.py`: Data Transfer Objects
  - `services/*.py`: Business logic services

### Infrastructure Layer (`app/infrastructure/`)
- **Purpose**: Technical implementations
- **Key Files**:
  - `database/models/*.py`: ORM models
  - `repositories/*.py`: Repository implementations

## Dependency Flow

```
API Endpoints
    ↓
Application Services
    ↓
Domain Entities & Interfaces
    ↑
Infrastructure Repositories
```

