"""
Example mock adapter for testing CAD-dependent code without a running CAD instance.

This demonstrates how to create mock implementations of ICadAdapter for unit testing.
"""

from typing import Dict

from compas.geometry import Point, Vector

from src.cad_adapter import cad_adapter
from models import create_guid


class MockCadAdapter(cad_adapter.ICadAdapter):
    """Mock implementation of ICadAdapter for testing.
    
    This mock stores element data in memory and provides predictable responses
    for testing purposes.
    
    Example usage:
        # Setup test data
        mock = MockCadAdapter()
        mock.add_element(1, "Wall-001", is_wall=True, guid="{GUID-001}")
        mock.add_element(2, "Beam-001", is_wall=False, guid="{GUID-002}")
        
        # Use in tests
        factory = ModelElementFactory(mock)
        element = factory.create(1)
        assert element.name == "Wall-001"
    """

    def __init__(self):
        """Initialize the mock adapter with empty data structures."""
        self._elements: Dict[int, dict] = {}
        self._guids_to_ids: Dict[str, int] = {}
        self._grouping_type = cad_adapter.ElementGroupingType.SUBGROUP  # subgroup
        self._all_element_ids: list[int] = []
        self._active_element_ids: list[int] = []

    def add_element(
            self,
            element_id: int,
            name: str = "TestElement",
            guid: str = None,
            is_wall: bool = False,
            is_floor: bool = False,
            is_roof: bool = False,
            is_container: bool = False,
            group: str = "",
            subgroup: str = "",
            p1: tuple[float, float, float] = (0, 0, 0),
            xl: tuple[float, float, float] = (1, 0, 0),
            yl: tuple[float, float, float] = (0, 1, 0),
            zl: tuple[float, float, float] = (0, 0, 1),
            building: str = "TestBuilding"
    ):

        if guid is None:
            guid = create_guid()  # f"{{GUID-{element_id:04d}}}"

        self._elements[element_id] = {
            'name': name,
            'guid': guid,
            'is_wall': is_wall,
            'is_floor': is_floor,
            'is_roof': is_roof,
            'is_container': is_container,
            'group': group,
            'subgroup': subgroup,
            'p1': Point(*p1),
            'xl': Vector(*xl),
            'yl': Vector(*yl),
            'zl': Vector(*zl),
            'building': building,
            'storey': '',
        }
        self._guids_to_ids[guid] = element_id
        self._all_element_ids.append(element_id)

    def set_active_elements(self, element_ids: list[int]):
        """Set which elements are considered 'active' (selected)."""
        self._active_element_ids = element_ids

    # Element Controller operations
    def get_element_cadwork_guid(self, element_id: int) -> str:
        return self._elements.get(element_id, {}).get('guid', '')

    def get_element_from_cadwork_guid(self, guid: str) -> int:
        return self._guids_to_ids.get(guid, 0)

    def get_all_identifiable_element_ids(self) -> list[int]:
        return self._all_element_ids.copy()

    def get_active_identifiable_element_ids(self) -> list[int]:
        return self._active_element_ids.copy()

    def get_bounding_box_vertices_local(self, element_id: int, reference_ids: list[int]) -> list[Point]:
        # Return a simple box for testing
        return [
            Point(0, 0, 0),
            Point(1, 0, 0),
            Point(1, 1, 0),
            Point(0, 1, 0),
            Point(0, 0, 1),
            Point(1, 0, 1),
            Point(1, 1, 1),
            Point(0, 1, 1),
        ]

    # Geometry Controller operations
    def get_p1(self, element_id: int) -> Point:
        return self._elements.get(element_id, {}).get('p1', Point(0, 0, 0))

    def get_xl(self, element_id: int) -> Vector:
        return self._elements.get(element_id, {}).get('xl', Vector(1, 0, 0))

    def get_yl(self, element_id: int) -> Vector:
        return self._elements.get(element_id, {}).get('yl', Vector(0, 1, 0))

    def get_zl(self, element_id: int) -> Vector:
        return self._elements.get(element_id, {}).get('zl', Vector(0, 0, 1))

    # Attribute Controller operations
    def get_name(self, element_id: int) -> str:
        return self._elements.get(element_id, {}).get('name', '')

    def is_wall(self, element_id: int) -> bool:
        return self._elements.get(element_id, {}).get('is_wall', False)

    def is_floor(self, element_id: int) -> bool:
        return self._elements.get(element_id, {}).get('is_floor', False)

    def is_roof(self, element_id: int) -> bool:
        return self._elements.get(element_id, {}).get('is_roof', False)

    def is_container(self, element_id: int) -> bool:
        return self._elements.get(element_id, {}).get('is_container', False)

    def get_subgroup(self, element_id: int) -> str:
        return self._elements.get(element_id, {}).get('subgroup', '')

    def get_group(self, element_id: int) -> str:
        return self._elements.get(element_id, {}).get('group', '')

    def get_element_grouping_type(self) -> cad_adapter.ElementGroupingType:
        return self._grouping_type

    def set_element_grouping_type(self, grouping_type: cad_adapter.ElementGroupingType):
        """Set the grouping type for testing."""
        self._grouping_type = grouping_type

    # BIM Controller operations
    def get_building(self, element_id: int) -> str:
        return self._elements.get(element_id, {}).get('building', '')

    def set_building_and_storey(self, element_ids: list[int], building_name: str, storey_name: str) -> None:
        for eid in element_ids:
            if eid in self._elements:
                self._elements[eid]['building'] = building_name
                self._elements[eid]['storey'] = storey_name

    def get_building_storeys(self, building_name: str) -> list[str]:
        return [storey_info['storey'] for storey_info in self._elements.values()
                if storey_info['building'] == building_name and storey_info['storey']]

    def get_buildings(self) -> list[str]:
        return list(set(info['building'] for info in self._elements.values()))

    def get_storey_elevation(self, building_name: str, storey_name: str) -> float:
        elevations = {('TestBuilding', 'GroundFloor'): 0.0,
                      ('TestBuilding', 'FirstFloor'): 3000.0}
        return elevations.get((building_name, storey_name), 0.0)
