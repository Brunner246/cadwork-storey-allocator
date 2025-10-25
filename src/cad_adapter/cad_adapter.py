"""
CAD API Adapter

This module provides an abstraction layer over the cadwork API controllers.
"""
from enum import Enum
from typing import Protocol, runtime_checkable

from compas.geometry import Point, Vector

from models import Guid


class ElementGroupingType(Enum):
    """Element grouping types for CAD systems."""
    GROUP = 1
    SUBGROUP = 2


# ============================================================================
# Segregated Interface Protocols (ISP - Interface Segregation Principle)
# ============================================================================

@runtime_checkable
class IElementIdentifier(Protocol):
    """Protocol for element identification operations."""
    
    def get_element_cadwork_guid(self, element_id: int) -> str:
        """Get the cadwork GUID for an element."""
        ...

    def get_element_from_cadwork_guid(self, guid: Guid) -> int:
        """Get element ID from cadwork GUID."""
        ...

    def get_all_identifiable_element_ids(self) -> list[int]:
        """Get all identifiable element IDs in the model."""
        ...

    def get_active_identifiable_element_ids(self) -> list[int]:
        """Get active/selected element IDs."""
        ...


@runtime_checkable
class IElementGeometry(Protocol):
    """Protocol for element geometry operations."""
    
    def get_bounding_box_vertices_local(self, element_id: int, reference_ids: list[int]) -> list[Point]:
        """Get bounding box vertices for an element."""
        ...

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


@runtime_checkable
class IElementClassification(Protocol):
    """Protocol for element type classification operations."""
    
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
    
    def is_node(self, element_id: int) -> bool:
        """Check if element is a node."""
        ...
        
    def is_line(self, element_id: int) -> bool:
        """Check if element is a line."""
        ...
        
    def is_dimension(self, element_id: int) -> bool:
        """Check if element is a dimension."""
        ...


@runtime_checkable
class IElementGrouping(Protocol):
    """Protocol for element grouping operations."""
    
    def get_subgroup(self, element_id: int) -> str:
        """Get element subgroup."""
        ...

    def get_group(self, element_id: int) -> str:
        """Get element group."""
        ...

    def get_element_grouping_type(self) -> ElementGroupingType:
        """Get current element grouping type (group or subgroup)."""
        ...


@runtime_checkable
class IBuildingInformation(Protocol):
    """Protocol for BIM building and storey operations."""
    
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


# ============================================================================
# Composite Interface for Full CAD Adapter (for backward compatibility)
# ============================================================================

@runtime_checkable
class ICadAdapter(
    IElementIdentifier,
    IElementGeometry,
    IElementClassification,
    IElementGrouping,
    IBuildingInformation,
    Protocol
):
    """Composite protocol combining all CAD adapter interfaces.
    
    This interface provides backward compatibility while allowing
    clients to depend on smaller, focused interfaces when needed.
    
    Clients should prefer depending on the specific interfaces they need:
    - IElementIdentifier: For GUID and element ID operations
    - IElementGeometry: For geometric queries
    - IElementClassification: For type checking (wall, floor, etc.)
    - IElementGrouping: For group/subgroup operations
    - IBuildingInformation: For BIM data operations
    """
    pass


# ============================================================================
# Specialized Adapter Implementations (Composition over Inheritance)
# ============================================================================

class ElementIdentifierAdapter(IElementIdentifier):
    """Specialized adapter for element identification operations.
    
    This class implements only IElementIdentifier, following SRP.
    It wraps the cadwork element_controller for ID and GUID operations.
    """
    
    def __init__(self, element_controller):
        self._ec = element_controller
    
    def get_element_cadwork_guid(self, element_id: int) -> str:
        return self._ec.get_element_cadwork_guid(element_id)

    def get_element_from_cadwork_guid(self, guid: Guid) -> int:
        return self._ec.get_element_from_cadwork_guid(guid.value_with_braces.upper())

    def get_all_identifiable_element_ids(self) -> list[int]:
        return self._ec.get_all_identifiable_element_ids()

    def get_active_identifiable_element_ids(self) -> list[int]:
        return self._ec.get_active_identifiable_element_ids()


class ElementGeometryAdapter(IElementGeometry):
    """Specialized adapter for element geometry operations.
    
    This class implements only IElementGeometry, following SRP.
    It wraps cadwork element_controller and geometry_controller.
    """
    
    def __init__(self, element_controller, geometry_controller):
        self._ec = element_controller
        self._gc = geometry_controller
    
    def get_bounding_box_vertices_local(self, element_id: int, reference_ids: list[int]) -> list[Point]:
        vertices = self._ec.get_bounding_box_vertices_local(element_id, reference_ids)
        return [to_point(v) for v in vertices]

    def get_p1(self, element_id: int) -> Point:
        return to_point(self._gc.get_p1(element_id))

    def get_xl(self, element_id: int) -> Vector:
        return to_vector(self._gc.get_xl(element_id))

    def get_yl(self, element_id: int) -> Vector:
        return to_vector(self._gc.get_yl(element_id))

    def get_zl(self, element_id: int) -> Vector:
        return to_vector(self._gc.get_zl(element_id))


class ElementClassificationAdapter(IElementClassification):
    """Specialized adapter for element type classification.
    
    This class implements only IElementClassification, following SRP.
    It wraps the cadwork attribute_controller for type checking.
    """
    
    def __init__(self, attribute_controller):
        self._ac = attribute_controller
    
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
    
    def is_node(self, element_id: int) -> bool:
        return self._ac.is_node(element_id)
    
    def is_line(self, element_id: int) -> bool:
        return self._ac.is_line(element_id)
    
    def is_dimension(self, element_id: int) -> bool:
        element_type = self._ac.get_element_type(element_id)
        return element_type is not None and element_type.is_dimension()


class ElementGroupingAdapter(IElementGrouping):
    """Specialized adapter for element grouping operations.
    
    This class implements only IElementGrouping, following SRP.
    It wraps the cadwork attribute_controller for group operations.
    """
    
    def __init__(self, attribute_controller):
        self._ac = attribute_controller
    
    def get_subgroup(self, element_id: int) -> str:
        return self._ac.get_subgroup(element_id)

    def get_group(self, element_id: int) -> str:
        return self._ac.get_group(element_id)

    def get_element_grouping_type(self) -> ElementGroupingType:
        return ElementGroupingType(self._ac.get_element_grouping_type().value)


class BuildingInformationAdapter(IBuildingInformation):
    """Specialized adapter for BIM building and storey operations.
    
    This class implements only IBuildingInformation, following SRP.
    It wraps the cadwork bim_controller for BIM data operations.
    """
    
    def __init__(self, bim_controller):
        self._bc = bim_controller
    
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


# ============================================================================
# Facade Adapter (Composition-based)
# ============================================================================

class CadworkAdapter(ICadAdapter):
    """Facade adapter providing unified access to all CAD operations.
    
    This adapter uses composition to delegate to specialized adapters,
    following the Facade Pattern and Composition over Inheritance.
    
    Design benefits:
    - Each specialized adapter has a single responsibility (SRP)
    - Easy to test individual adapters in isolation
    - Can inject different implementations per interface
    - Clients can use specialized adapters directly if needed
    - Follows Dependency Inversion Principle (DIP)
    
    Usage:
        # Use facade for convenience
        adapter = CadworkAdapter()
        
        # Or use specialized adapters directly
        identifier = adapter.identifier
        geometry = adapter.geometry
    """

    def __init__(self):
        import element_controller as ec
        import geometry_controller as gc
        import attribute_controller as ac
        import bim_controller as bc

        # Create specialized adapters (composition)
        self.identifier = ElementIdentifierAdapter(ec)
        self.geometry = ElementGeometryAdapter(ec, gc)
        self.classification = ElementClassificationAdapter(ac)
        self.grouping = ElementGroupingAdapter(ac)
        self.building_info = BuildingInformationAdapter(bc)

    # ========================================================================
    # IElementIdentifier - Delegate to specialized adapter
    # ========================================================================
    
    def get_element_cadwork_guid(self, element_id: int) -> str:
        return self.identifier.get_element_cadwork_guid(element_id)

    def get_element_from_cadwork_guid(self, guid: Guid) -> int:
        return self.identifier.get_element_from_cadwork_guid(guid)

    def get_all_identifiable_element_ids(self) -> list[int]:
        return self.identifier.get_all_identifiable_element_ids()

    def get_active_identifiable_element_ids(self) -> list[int]:
        return self.identifier.get_active_identifiable_element_ids()

    # ========================================================================
    # IElementGeometry - Delegate to specialized adapter
    # ========================================================================
    
    def get_bounding_box_vertices_local(self, element_id: int, reference_ids: list[int]) -> list[Point]:
        return self.geometry.get_bounding_box_vertices_local(element_id, reference_ids)

    def get_p1(self, element_id: int) -> Point:
        return self.geometry.get_p1(element_id)

    def get_xl(self, element_id: int) -> Vector:
        return self.geometry.get_xl(element_id)

    def get_yl(self, element_id: int) -> Vector:
        return self.geometry.get_yl(element_id)

    def get_zl(self, element_id: int) -> Vector:
        return self.geometry.get_zl(element_id)

    # ========================================================================
    # IElementClassification - Delegate to specialized adapter
    # ========================================================================
    
    def get_name(self, element_id: int) -> str:
        return self.classification.get_name(element_id)

    def is_wall(self, element_id: int) -> bool:
        return self.classification.is_wall(element_id)

    def is_floor(self, element_id: int) -> bool:
        return self.classification.is_floor(element_id)

    def is_roof(self, element_id: int) -> bool:
        return self.classification.is_roof(element_id)

    def is_container(self, element_id: int) -> bool:
        return self.classification.is_container(element_id)
    
    def is_node(self, element_id: int) -> bool:
        return self.classification.is_node(element_id)
    
    def is_line(self, element_id: int) -> bool:
        return self.classification.is_line(element_id)
    
    def is_dimension(self, element_id: int) -> bool:
        return self.classification.is_dimension(element_id)

    # ========================================================================
    # IElementGrouping - Delegate to specialized adapter
    # ========================================================================
    
    def get_subgroup(self, element_id: int) -> str:
        return self.grouping.get_subgroup(element_id)

    def get_group(self, element_id: int) -> str:
        return self.grouping.get_group(element_id)

    def get_element_grouping_type(self) -> ElementGroupingType:
        return self.grouping.get_element_grouping_type()

    # ========================================================================
    # IBuildingInformation - Delegate to specialized adapter
    # ========================================================================
    
    def get_building(self, element_id: int) -> str:
        return self.building_info.get_building(element_id)

    def set_building_and_storey(self, element_ids: list[int], building_name: str, storey_name: str) -> None:
        self.building_info.set_building_and_storey(element_ids, building_name, storey_name)

    def get_buildings(self) -> list[str]:
        return self.building_info.get_buildings()

    def get_building_storeys(self, building_name: str) -> list[str]:
        return self.building_info.get_building_storeys(building_name)

    def get_storey_elevation(self, building_name: str, storey_name: str) -> float:
        return self.building_info.get_storey_elevation(building_name, storey_name)


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
