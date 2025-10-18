from abc import ABC, abstractmethod
from typing import Optional
import models


class IElementAssignmentVisitor(ABC):
    """Visitor that determines storey assignment for different element types."""

    @abstractmethod
    def visit_wall(self, wall: models.Wall, boundaries: list[models.BuildingStoreyBoundary]) -> Optional[
        models.StoreyCoverage]:
        """Returns (storey_name, coverage) or None."""
        pass

    @abstractmethod
    def visit_slab(self, slab: models.Slab, boundaries: list[models.BuildingStoreyBoundary]) -> Optional[
        models.StoreyCoverage]:
        pass

    @abstractmethod
    def visit_roof(self, roof: models.Roof, boundaries: list[models.BuildingStoreyBoundary]) -> Optional[
        models.StoreyCoverage]:
        pass

    @abstractmethod
    def visit_container(self, container: models.Container, boundaries: list[models.BuildingStoreyBoundary]) -> Optional[
        models.StoreyCoverage]:
        pass

    @abstractmethod
    def visit_leaf(self, leaf: models.ModelLeafElement, boundaries: list[models.BuildingStoreyBoundary]) -> Optional[
        models.StoreyCoverage]:
        pass
