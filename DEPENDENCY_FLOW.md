# Dependency Flow Documentation

## Overview

This document explains the dependency flow and data transformation through the clean architecture layers.

## Request Flow Example: Creating a Player

### 1. HTTP Request
```
POST /api/v1/players
Body: { "name": "John Doe", "position": "Forward", ... }
```

### 2. Presentation Layer (`app/api/v1/endpoints/players.py`)

**Responsibilities:**
- Receive HTTP request
- Validate input via Pydantic DTO
- Apply rate limiting
- Get database session via dependency injection
- Create service instance
- Call service method
- Return HTTP response

**Code Flow:**
```python
@router.post("", response_model=PlayerResponseDTO, status_code=201)
@limiter.limit("60/minute")
async def create_player(
    request: Request,
    player_data: PlayerCreateDTO,  # Pydantic validation
    db: AsyncSession = Depends(get_db),
):
    repository = get_player_repository(db)
    service = PlayerService(repository)
    return await service.create_player(player_data)
```

**Dependencies:**
- `PlayerCreateDTO` (Application Layer)
- `PlayerService` (Application Layer)
- `get_db` (Core - Infrastructure)
- `get_player_repository` (Core - Infrastructure)

### 3. Application Layer (`app/application/services/player_service.py`)

**Responsibilities:**
- Business logic orchestration
- Entity validation
- Convert DTO to Domain Entity
- Call repository
- Convert Domain Entity to DTO
- Handle business exceptions

**Code Flow:**
```python
async def create_player(self, dto: PlayerCreateDTO) -> PlayerResponseDTO:
    # Convert DTO to Domain Entity
    player = Player(
        name=dto.name,
        position=dto.position,
        ...
    )
    
    # Call repository (Domain interface)
    created = await self.repository.create(player)
    
    # Convert Entity to DTO
    return self._entity_to_dto(created)
```

**Dependencies:**
- `PlayerCreateDTO` (Application Layer)
- `Player` (Domain Layer)
- `IPlayerRepository` (Domain Layer)
- `PlayerResponseDTO` (Application Layer)

### 4. Domain Layer (`app/domain/entities/player.py`)

**Responsibilities:**
- Define business entity
- Business rules validation
- No external dependencies

**Code Flow:**
```python
@dataclass
class Player:
    id: Optional[int] = None
    name: str = ""
    position: str = ""
    ...
    
    def __post_init__(self):
        if not self.name:
            raise ValueError("Player name is required")
```

**Dependencies:**
- None (pure Python types)

### 5. Infrastructure Layer (`app/infrastructure/repositories/player_repository.py`)

**Responsibilities:**
- Implement domain repository interface
- Convert Domain Entity to Database Model
- Execute database queries
- Convert Database Model to Domain Entity

**Code Flow:**
```python
async def create(self, entity: Player) -> Player:
    # Convert Entity to Model
    model = self._entity_to_model(entity)
    
    # Database operation
    self.session.add(model)
    await self.session.flush()
    await self.session.refresh(model)
    
    # Convert Model to Entity
    return self._model_to_entity(model)
```

**Dependencies:**
- `Player` (Domain Layer)
- `PlayerModel` (Infrastructure Layer)
- `AsyncSession` (SQLAlchemy)

## Data Transformation Flow

```
HTTP Request
    ↓
PlayerCreateDTO (Pydantic) - Input validation
    ↓
Player (Domain Entity) - Business logic
    ↓
PlayerModel (SQLAlchemy) - Database persistence
    ↓
Database
    ↓
PlayerModel (SQLAlchemy) - Database retrieval
    ↓
Player (Domain Entity) - Business logic
    ↓
PlayerResponseDTO (Pydantic) - Output serialization
    ↓
HTTP Response (JSON)
```

## Dependency Rules

### ✅ Allowed Dependencies

1. **Presentation → Application**: ✅ Allowed
   - API endpoints use services and DTOs

2. **Presentation → Core**: ✅ Allowed
   - Configuration, dependencies, middleware

3. **Application → Domain**: ✅ Allowed
   - Services use entities and repository interfaces

4. **Infrastructure → Domain**: ✅ Allowed
   - Repositories implement domain interfaces

5. **Infrastructure → Application**: ✅ Allowed (for DTOs if needed)

### ❌ Forbidden Dependencies

1. **Domain → Any Layer**: ❌ Forbidden
   - Domain layer must remain pure

2. **Application → Infrastructure**: ❌ Forbidden
   - Application layer should depend on interfaces, not implementations

3. **Presentation → Domain**: ❌ Forbidden (directly)
   - Should go through Application layer

4. **Presentation → Infrastructure**: ❌ Forbidden (directly)
   - Should use dependency injection from Core

## Dependency Injection

FastAPI's dependency injection system is used throughout:

```python
# Core dependencies
async def get_db() -> AsyncSession:
    """Database session dependency."""
    async for session in get_db_session():
        yield session

def get_player_repository(db: AsyncSession) -> PlayerRepository:
    """Repository dependency."""
    return PlayerRepository(db)

# Usage in endpoints
async def create_player(
    db: AsyncSession = Depends(get_db),
):
    repository = get_player_repository(db)
    service = PlayerService(repository)
    ...
```

## Benefits of This Architecture

1. **Testability**: Each layer can be tested independently
2. **Maintainability**: Clear separation of concerns
3. **Flexibility**: Easy to swap implementations (e.g., different database)
4. **Scalability**: Can add new features without affecting existing code
5. **Type Safety**: Full type hints throughout

## Example: Adding a New Feature

To add a new feature (e.g., "Statistics"):

1. **Domain Layer**: Add `Statistic` entity and `IStatisticRepository` interface
2. **Application Layer**: Add `StatisticService` and DTOs
3. **Infrastructure Layer**: Implement `StatisticRepository` and `StatisticModel`
4. **Presentation Layer**: Add endpoints in `api/v1/endpoints/statistics.py`

Each layer remains independent and testable!

