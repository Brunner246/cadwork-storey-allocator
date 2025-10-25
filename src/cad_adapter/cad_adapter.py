"""
CAD API Adapter

This module provides an abstraction layer over the cadwork API controllers,
allowing for dependency injection and easier testing.

Usage:
    # Production code:
    adapter = CadworkAdapter()
    builder = ModelElementTreeBuilder(element_ids, adapter)
    
    # Test code:
    mock_adapter = MockCadAdapter()
    builder = ModelElementTreeBuilder(element_ids, mock_adapter)
"""
from enum import Enum
from typing import Protocol, runtime_checkable

from compas.geometry import Point, Vector


class ElementGroupingType(Enum):
    GROUP = 1
    SUBGROUP = 2


@runtime_checkable
class ICadAdapter(Protocol):
    """Protocol defining the interface for CAD API operations.
    
    This protocol can be implemented by production adapters (wrapping real CAD APIs)
    or by mock/stub implementations for testing purposes.
    """

    # Element Controller operations
    def get_element_cadwork_guid(self, element_id: int) -> str:
        """Get the cadwork GUID for an element."""
        ...

    def get_element_from_cadwork_guid(self, guid: str) -> int:
        """Get element ID from cadwork GUID."""
        ...

    def get_all_identifiable_element_ids(self) -> list[int]:
        """Get all identifiable element IDs in the model."""
        ...

    def get_active_identifiable_element_ids(self) -> list[int]:
        """Get active/selected element IDs."""
        ...

    def get_bounding_box_vertices_local(self, element_id: int, reference_ids: list[int]) -> list[Point]:
        """Get bounding box vertices for an element."""
        ...

    # Geometry Controller operations
    def get_p1(self, element_id: int) -> Point:
        """Get reference point P1 of an element."""
        ...

    def get_xl(self, element_id: int) -> Vector:
        """Get X-axis local vector of an element."""
        ...

    def get_yl(self, element_id: int) -> Vector:
        """Get Y-axis local vector of an element."""
        ...

    def get_zl(self, element_id: int) -> Vector:
        """Get Z-axis local vector of an element."""
        ...

    # Attribute Controller operations
    def get_name(self, element_id: int) -> str:
        """Get element name."""
        ...

    def is_wall(self, element_id: int) -> bool:
        """Check if element is a wall."""
        ...

    def is_floor(self, element_id: int) -> bool:
        """Check if element is a floor/slab."""
        ...

    def is_roof(self, element_id: int) -> bool:
        """Check if element is a roof."""
        ...

    def is_container(self, element_id: int) -> bool:
        """Check if element is a container."""
        ...

    def get_subgroup(self, element_id: int) -> str:
        """Get element subgroup."""
        ...

    def get_group(self, element_id: int) -> str:
        """Get element group."""
        ...

    def get_element_grouping_type(self) -> ElementGroupingType:
        """Get current element grouping type (group or subgroup)."""
        ...

    # BIM Controller operations
    def get_building(self, element_id: int) -> str:
        """Get building name for an element."""
        ...

    def get_building_storeys(self, building_name: str) -> list[str]:
        """Get storeys for a given building."""
        ...

    def set_building_and_storey(self, element_ids: list[int], building_name: str, storey_name: str) -> None:
        """Set building and storey for elements."""
        ...

    def get_buildings(self) -> list[str]:
        """Get all building names in the model."""
        ...

    def get_storey_elevation(self, building_name: str, storey_name: str) -> float:
        """Get elevation of a storey in a building."""
        ...


class CadworkAdapter(ICadAdapter):
    """Production adapter wrapping the cadwork API controllers.
    """

    def __init__(self):
        import element_controller as ec
        import geometry_controller as gc
        import attribute_controller as ac
        import bim_controller as bc

        self._ec = ec
        self._gc = gc
        self._ac = ac
        self._bc = bc

    # Element Controller operations
    def get_element_cadwork_guid(self, element_id: int) -> str:
        return self._ec.get_element_cadwork_guid(element_id)

    def get_element_from_cadwork_guid(self, guid: str) -> int:
        return self._ec.get_element_from_cadwork_guid(guid)

    def get_all_identifiable_element_ids(self) -> list[int]:
        return self._ec.get_all_identifiable_element_ids()

    def get_active_identifiable_element_ids(self) -> list[int]:
        return self._ec.get_active_identifiable_element_ids()

    def get_bounding_box_vertices_local(self, element_id: int, reference_ids: list[int]) -> list[Point]:
        vertices = self._ec.get_bounding_box_vertices_local(element_id, reference_ids)
        return [to_point(v) for v in vertices]

    # Geometry Controller operations
    def get_p1(self, element_id: int) -> Point:
        return to_point(self._gc.get_p1(element_id))

    def get_xl(self, element_id: int) -> Vector:
        return to_vector(self._gc.get_xl(element_id))

    def get_yl(self, element_id: int) -> Vector:
        return to_vector(self._gc.get_yl(element_id))

    def get_zl(self, element_id: int) -> Vector:
        return to_vector(self._gc.get_zl(element_id))

    # Attribute Controller operations
    def get_name(self, element_id: int) -> str:
        return self._ac.get_name(element_id)

    def is_wall(self, element_id: int) -> bool:
        return self._ac.is_wall(element_id)

    def is_floor(self, element_id: int) -> bool:
        return self._ac.is_floor(element_id)

    def is_roof(self, element_id: int) -> bool:
        return self._ac.is_roof(element_id)

    def is_container(self, element_id: int) -> bool:
        return self._ac.is_container(element_id)

    def get_subgroup(self, element_id: int) -> str:
        return self._ac.get_subgroup(element_id)

    def get_group(self, element_id: int) -> str:
        return self._ac.get_group(element_id)

    def get_element_grouping_type(self) -> ElementGroupingType:
        return ElementGroupingType(self._ac.get_element_grouping_type().value)

    # BIM Controller operations
    def get_building(self, element_id: int) -> str:
        return self._bc.get_building(element_id)

    def set_building_and_storey(self, element_ids: list[int], building_name: str, storey_name: str) -> None:
        self._bc.set_building_and_storey(element_ids, building_name, storey_name)

    def get_buildings(self) -> list[str]:
        return self._bc.get_all_buildings()

    def get_building_storeys(self, building_name: str) -> list[str]:
        return self._bc.get_all_storeys(building_name)

    def get_storey_elevation(self, building_name: str, storey_name: str) -> float:
        return self._bc.get_storey_height(building_name, storey_name)


# Utility conversion functions
def to_vector(vec3) -> Vector:
    """Convert cadwork point_3d to compas Vector."""
    return Vector(vec3.x, vec3.y, vec3.z)


def to_point(p3) -> Point:
    """Convert cadwork point_3d to compas Point."""
    return Point(p3.x, p3.y, p3.z)


_adapter = CadworkAdapter()


def get_aabb_vertices(element_id: int) -> list[Point]:
    """Get axis-aligned bounding box vertices for an element."""
    bbx_vertices = _adapter.get_bounding_box_vertices_local(element_id, [element_id])
    bbx_pts = [to_point(v) for v in bbx_vertices]
    return bbx_pts


def get_building_name(element_id: int) -> str:
    """Get building name for an element."""
    return _adapter.get_building(element_id)


def set_building_storey(element_ids: list[int], building_name: str, storey_name: str) -> None:
    """Set building and storey for elements."""
    _adapter.set_building_and_storey(element_ids, building_name, storey_name)


def get_element_id_from_cadwork_guid(guid: str) -> int:
    """Get element ID from cadwork GUID."""
    guid = guid if not guid.islower() else guid.upper()
    if not guid.startswith('{') and not guid.endswith('}'):
        guid = '{' + guid + '}'
    return _adapter.get_element_from_cadwork_guid(guid)


def get_all_element_ids() -> list[int]:
    """Get all identifiable element IDs."""
    return _adapter.get_all_identifiable_element_ids()


def get_active_element_ids() -> list[int]:
    """Get active/selected element IDs."""
    return _adapter.get_active_identifiable_element_ids()
