"""Base repository implementation."""

from typing import Generic, TypeVar, Optional, List, Type
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update

T = TypeVar("T")
M = TypeVar("M")


class BaseRepository(Generic[T, M]):
    """Base repository implementation."""

    def __init__(self, session: AsyncSession, model: Type[M], entity_class: Type[T]):
        """Initialize repository with session and model."""
        self.session = session
        self.model = model
        self.entity_class = entity_class

    def _model_to_entity(self, model: M) -> T:
        """Convert database model to domain entity."""
        raise NotImplementedError("Subclasses must implement _model_to_entity")

    def _entity_to_model(self, entity: T) -> M:
        """Convert domain entity to database model."""
        raise NotImplementedError("Subclasses must implement _entity_to_model")

    async def create(self, entity: T) -> T:
        """Create a new entity."""
        model = self._entity_to_model(entity)
        self.session.add(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._model_to_entity(model)

    async def get_by_id(self, entity_id: int) -> Optional[T]:
        """Get entity by ID."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == entity_id)
        )
        model = result.scalar_one_or_none()
        return self._model_to_entity(model) if model else None

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all entities with pagination."""
        result = await self.session.execute(
            select(self.model).offset(skip).limit(limit)
        )
        models = result.scalars().all()
        return [self._model_to_entity(model) for model in models]

    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        if not entity.id:
            raise ValueError("Entity must have an ID to update")
        
        model = self._entity_to_model(entity)
        await self.session.merge(model)
        await self.session.flush()
        await self.session.refresh(model)
        return self._model_to_entity(model)

    async def delete(self, entity_id: int) -> bool:
        """Delete an entity by ID."""
        result = await self.session.execute(
            delete(self.model).where(self.model.id == entity_id)
        )
        await self.session.flush()
        return result.rowcount > 0

