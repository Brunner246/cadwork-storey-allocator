from __future__ import annotations
from typing import Dict, Iterable, Optional
from models import Building


class BuildingRegistry:
    """Simple registry to store and retrieve buildings by name."""

    def __init__(self) -> None:
        self._buildings: Dict[str, Building] = {}

    def register(self, building: Building) -> None:
        """Register a building by its name (must be unique)."""
        if not isinstance(building, Building):
            raise TypeError("Expected Building")
        name = building.name
        if not name:
            raise ValueError("Building must have a non-empty name")

        if self._buildings.__contains__(name):
            raise ValueError(f"Building already registered: {name!r}")
        self._buildings[name] = building

    def upsert(self, building: Building) -> None:
        """Register or replace a building by name."""
        if not isinstance(building, Building):
            raise TypeError("Expected Building")
        name = building.name
        if not name:
            raise ValueError("Building must have a non-empty name")
        self._buildings[name] = building

    def get(self, name: str) -> Building:
        """Get a building by name."""
        try:
            return self._buildings[name]
        except KeyError as e:
            raise KeyError(f"Building not found: {name!r}") from e

    def try_get(self, name: str) -> Optional[Building]:
        """Get a building by name or None."""
        return self._buildings.get(name)

    def contains(self, name: str) -> bool:
        return name in self._buildings

    def unregister(self, name: str) -> None:
        if name in self._buildings:
            del self._buildings[name]
        else:
            raise KeyError(f"Building not found: {name!r}")

    def clear(self) -> None:
        self._buildings.clear()

    def names(self) -> Iterable[str]:
        return self._buildings.keys()

    def values(self) -> Iterable[Building]:
        return self._buildings.values()

    def items(self) -> Iterable[tuple[str, Building]]:
        return self._buildings.items()

# registry = BuildingRegistry()

# Usage:
# building = build_building_storey_hierarchy()
# registry.register(building)
# b = registry.get(building.name)
