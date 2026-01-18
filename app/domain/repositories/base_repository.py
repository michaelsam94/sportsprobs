"""Base repository interface."""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, Optional, List

T = TypeVar("T")


class IBaseRepository(ABC, Generic[T]):
    """Base repository interface for CRUD operations."""

    @abstractmethod
    async def create(self, entity: T) -> T:
        """Create a new entity."""
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: int) -> Optional[T]:
        """Get entity by ID."""
        pass

    @abstractmethod
    async def get_all(
        self, skip: int = 0, limit: int = 100
    ) -> List[T]:
        """Get all entities with pagination."""
        pass

    @abstractmethod
    async def update(self, entity: T) -> T:
        """Update an existing entity."""
        pass

    @abstractmethod
    async def delete(self, entity_id: int) -> bool:
        """Delete an entity by ID."""
        pass

