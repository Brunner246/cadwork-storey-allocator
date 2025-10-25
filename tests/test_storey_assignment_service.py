"""
Tests element assignment to building storeys with various element types
(beams, plates, walls) and edge cases (elements on boundaries, spanning
multiple storeys, etc.).
"""

import pytest
from compas.geometry import Point, Vector

from mock_cad_adapter import MockCadAdapter
from allocation.storey_assignment_service import StoreyAssignmentService
from allocation.building_registry import BuildingRegistry
from models import Building, BuildingStorey, Guid, create_guid


class EnhancedMockCadAdapter(MockCadAdapter):

    def add_beam(self,
                 element_id: int,
                 name: str,
                 guid: Guid,
                 width: float,  # x-direction (mm)
                 height: float,  # y-direction (mm)
                 length: float,  # z-direction (mm)
                 position: tuple[float, float, float],  # Bottom center position
                 building: str = "TestBuilding"
                 ):
        x, y, z = position
        self.add_element(element_id=element_id,
                         name=name,
                         guid=guid,
                         p1=(x, y, z),
                         xl=(width / 1000.0, 0, 0),  # Convert mm to m
                         yl=(0, height / 1000.0, 0),
                         zl=(0, 0, length / 1000.0),
                         building=building
                         )
        # Store custom bounding box
        self._elements[element_id]['bbox'] = [
            Point(x - width / 2000.0, y - height / 2000.0, z),
            Point(x + width / 2000.0, y - height / 2000.0, z),
            Point(x + width / 2000.0, y + height / 2000.0, z),
            Point(x - width / 2000.0, y + height / 2000.0, z),
            Point(x - width / 2000.0, y - height / 2000.0, z + length / 1000.0),
            Point(x + width / 2000.0, y - height / 2000.0, z + length / 1000.0),
            Point(x + width / 2000.0, y + height / 2000.0, z + length / 1000.0),
            Point(x - width / 2000.0, y + height / 2000.0, z + length / 1000.0),
        ]

    def add_plate(self,
                  element_id: int,
                  name: str,
                  guid: Guid,
                  width: float,  # x-direction (mm)
                  length: float,  # y-direction (mm)
                  thickness: float,  # z-direction (mm)
                  position: tuple[float, float, float],  # Bottom corner position
                  building: str = "TestBuilding"
                  ):
        x, y, z = position
        self.add_element(element_id=element_id,
                         name=name,
                         guid=guid,
                         is_floor=True,
                         p1=(x, y, z),
                         xl=(width / 1000.0, 0, 0),
                         yl=(0, length / 1000.0, 0),
                         zl=(0, 0, thickness / 1000.0),
                         building=building
                         )
        self._elements[element_id]['bbox'] = [
            Point(x, y, z),
            Point(x + width / 1000.0, y, z),
            Point(x + width / 1000.0, y + length / 1000.0, z),
            Point(x, y + length / 1000.0, z),
            Point(x, y, z + thickness / 1000.0),
            Point(x + width / 1000.0, y, z + thickness / 1000.0),
            Point(x + width / 1000.0, y + length / 1000.0, z + thickness / 1000.0),
            Point(x, y + length / 1000.0, z + thickness / 1000.0),
        ]

    def add_wall(self,
                 element_id: int,
                 name: str,
                 guid: Guid,
                 width: float,  # x-direction (mm)
                 thickness: float,  # y-direction (mm)
                 height: float,  # z-direction (mm)
                 position: tuple[float, float, float],  # Bottom corner position
                 building: str = "TestBuilding"
                 ):
        x, y, z = position
        self.add_element(element_id=element_id,
                         name=name,
                         guid=guid,
                         is_wall=True,
                         p1=(x, y, z),
                         xl=(width / 1000.0, 0, 0),
                         yl=(0, thickness / 1000.0, 0),
                         zl=(0, 0, height / 1000.0),
                         building=building
                         )

        self._elements[element_id]['bbox'] = [
            Point(x, y, z),
            Point(x + width / 1000.0, y, z),
            Point(x + width / 1000.0, y + thickness / 1000.0, z),
            Point(x, y + thickness / 1000.0, z),
            Point(x, y, z + height / 1000.0),
            Point(x + width / 1000.0, y, z + height / 1000.0),
            Point(x + width / 1000.0, y + thickness / 1000.0, z + height / 1000.0),
            Point(x, y + thickness / 1000.0, z + height / 1000.0),
        ]

    def get_bounding_box_vertices_local(self, element_id: int, reference_ids: list[int]) -> list[Point]:
        """Return custom bounding box if available, otherwise default."""
        element = self._elements.get(element_id)
        if element and 'bbox' in element:
            return element['bbox']
        # Fallback to simple box
        return super().get_bounding_box_vertices_local(element_id, reference_ids)


def create_test_building_with_four_storeys(storey_height: float = 3.0) -> Building:
    """Create a test building with 4 storeys.
    
    Args:
        storey_height: Height of each storey in meters (default: 3.0 m)
        
    Returns:
        Building with storeys 1-4
    """
    return Building(
        name="TestBuilding",
        storeys=[
            BuildingStorey(building_name="TestBuilding", storey_name="Storey1", elevation=0.0),
            BuildingStorey(building_name="TestBuilding", storey_name="Storey2", elevation=storey_height),
            BuildingStorey(building_name="TestBuilding", storey_name="Storey3", elevation=2 * storey_height),
            BuildingStorey(building_name="TestBuilding", storey_name="Storey4", elevation=3 * storey_height),
        ]
    )


class TestStoreyAssignmentService:
    """Test suite for StoreyAssignmentService."""

    def test_beam_fully_within_single_storey(self):
        """Test beam completely within a single storey - standard case."""
        # Arrange
        mock = EnhancedMockCadAdapter()
        building = create_test_building_with_four_storeys(storey_height=3.0)
        registry = BuildingRegistry()
        registry.register(building)

        # Beam at 1.5m elevation (middle of Storey1: 0-3m), 2.5m long vertically
        mock.add_beam(
            element_id=1,
            name="Beam-S1-01",
            guid=create_guid(),
            width=120,  # mm
            height=200,  # mm
            length=2500,  # mm
            position=(5.0, 5.0, 0.5),  # Bottom at 0.5m, top at 3.0m
            building="TestBuilding"
        )

        service = StoreyAssignmentService(registry, mock, coverage_threshold=0.60)

        # Act
        service.assign_elements([1])

        # Assert
        assigned_storey = mock._elements[1]['storey']
        assert assigned_storey == "Storey1", f"Expected Storey1, got {assigned_storey}"

    def test_beam_spanning_two_storeys_assigned_to_lower(self):
        """Test beam spanning two storeys - should assign to storey with most coverage."""
        # Arrange
        mock = EnhancedMockCadAdapter()
        building = create_test_building_with_four_storeys(storey_height=3.0)
        registry = BuildingRegistry()
        registry.register(building)

        # Beam from 2.0m to 4.0m (spans Storey1 [0-3m] and Storey2 [3-6m])
        # 1.0m in Storey1, 1.0m in Storey2 - equal coverage
        mock.add_beam(
            element_id=2,
            name="Beam-S1-S2",
            guid=create_guid(),
            width=120,
            height=200,
            length=2000,
            position=(5.0, 5.0, 2.0),  # Bottom at 2m, top at 4m
            building="TestBuilding"
        )

        service = StoreyAssignmentService(registry, mock, coverage_threshold=0.40)

        # Act
        service.assign_elements([2])

        # Assert
        assigned_storey = mock._elements[2]['storey']
        # With equal coverage, should assign to first matching storey
        assert assigned_storey == "Storey1", f"Expected Storey1, got {assigned_storey}"

    def test_beam_mostly_in_upper_storey(self):
        """Test beam with 70% in upper storey, 30% in lower."""
        # Arrange
        mock = EnhancedMockCadAdapter()
        building = create_test_building_with_four_storeys(storey_height=3.0)
        registry = BuildingRegistry()
        registry.register(building)

        # Beam from 2.5m to 5.5m (3m total)
        # 0.5m in Storey1, 2.5m in Storey2 -> 83% in Storey2
        mock.add_beam(
            element_id=3,
            name="Beam-S2-Dominant",
            guid=create_guid(),
            width=120,
            height=200,
            length=3000,
            position=(5.0, 5.0, 2.5),
            building="TestBuilding"
        )

        service = StoreyAssignmentService(registry, mock, coverage_threshold=0.60)

        # Act
        service.assign_elements([3])

        # Assert
        assigned_storey = mock._elements[3]['storey']
        assert assigned_storey == "Storey2", f"Expected Storey2, got {assigned_storey}"

    def test_plate_at_storey_boundary(self):
        """Test plate (slab) positioned exactly at storey elevation."""
        # Arrange
        mock = EnhancedMockCadAdapter()
        building = create_test_building_with_four_storeys(storey_height=3.0)
        registry = BuildingRegistry()
        registry.register(building)

        # Plate at exactly 3.0m (boundary between Storey1 and Storey2)
        # 200mm thick, so from 3.0m to 3.2m
        mock.add_plate(
            element_id=10,
            name="Slab-S2",
            guid=create_guid(),
            width=6000,
            length=8000,
            thickness=200,
            position=(0.0, 0.0, 3.0),  # Exactly at storey boundary
            building="TestBuilding"
        )

        service = StoreyAssignmentService(registry, mock, coverage_threshold=0.60)

        # Act
        service.assign_elements([10])

        # Assert
        assigned_storey = mock._elements[10]['storey']
        # Plate starts at 3.0m (Storey2 elevation), so should be assigned to Storey2
        assert assigned_storey == "Storey2", f"Expected Storey2, got {assigned_storey}"

    def test_wall_full_height_single_storey(self):
        """Test wall with standard storey height (3m)."""
        # Arrange
        mock = EnhancedMockCadAdapter()
        building = create_test_building_with_four_storeys(storey_height=3.0)
        registry = BuildingRegistry()
        registry.register(building)

        # Wall from 0m to 3m (exactly one storey height)
        mock.add_wall(
            element_id=20,
            name="Wall-S1",
            guid=create_guid(),
            width=5000,
            thickness=200,
            height=3000,
            position=(0.0, 0.0, 0.0),
            building="TestBuilding"
        )

        service = StoreyAssignmentService(registry, mock, coverage_threshold=0.60)

        # Act
        service.assign_elements([20])

        # Assert
        assigned_storey = mock._elements[20]['storey']
        assert assigned_storey == "Storey1", f"Expected Storey1, got {assigned_storey}"

    def test_wall_spanning_multiple_storeys(self):
        """Test wall spanning from Storey1 to Storey3."""
        # Arrange
        mock = EnhancedMockCadAdapter()
        building = create_test_building_with_four_storeys(storey_height=3.0)
        registry = BuildingRegistry()
        registry.register(building)

        # Wall from 0m to 8m (spans Storey1, 2, and part of 3)
        # Coverage: Storey1=3m, Storey2=3m, Storey3=2m
        mock.add_wall(
            element_id=21,
            name="Wall-MultiStorey",
            guid=create_guid(),
            width=5000,
            thickness=200,
            height=8000,
            position=(0.0, 0.0, 0.0),
            building="TestBuilding"
        )

        service = StoreyAssignmentService(registry, mock, coverage_threshold=0.30)

        # Act
        service.assign_elements([21])

        # Assert
        assigned_storey = mock._elements[21]['storey']
        # Should assign to first storey with >= 30% coverage
        assert assigned_storey == "Storey1", f"Expected Storey1, got {assigned_storey}"

    def test_multiple_elements_different_storeys(self):
        """Test batch assignment of multiple elements to different storeys."""
        # Arrange
        mock = EnhancedMockCadAdapter()
        building = create_test_building_with_four_storeys(storey_height=3.0)
        registry = BuildingRegistry()
        registry.register(building)

        # Elements in different storeys
        mock.add_beam(1, "Beam-S1", create_guid(), 120, 200, 2000, (5.0, 5.0, 0.5), "TestBuilding")  # Storey1
        mock.add_beam(2, "Beam-S2", create_guid(), 120, 200, 2000, (5.0, 5.0, 3.5), "TestBuilding")  # Storey2
        mock.add_beam(3, "Beam-S3", create_guid(), 120, 200, 2000, (5.0, 5.0, 6.5), "TestBuilding")  # Storey3
        mock.add_beam(4, "Beam-S4", create_guid(), 120, 200, 2000, (5.0, 5.0, 9.5), "TestBuilding")  # Storey4

        service = StoreyAssignmentService(registry, mock, coverage_threshold=0.60)

        # Act
        service.assign_elements([1, 2, 3, 4])

        # Assert
        assert mock._elements[1]['storey'] == "Storey1"
        assert mock._elements[2]['storey'] == "Storey2"
        assert mock._elements[3]['storey'] == "Storey3"
        assert mock._elements[4]['storey'] == "Storey4"

    def test_element_below_all_storeys(self):
        """Test element positioned below the lowest storey - edge case."""
        # Arrange
        mock = EnhancedMockCadAdapter()
        building = create_test_building_with_four_storeys(storey_height=3.0)
        registry = BuildingRegistry()
        registry.register(building)

        # Beam completely below Storey1 (which starts at 0m)
        mock.add_beam(
            element_id=30,
            name="Beam-Underground",
            guid=create_guid(),
            width=120,
            height=200,
            length=2000,
            position=(5.0, 5.0, -3.0),  # From -3m to -1m
            building="TestBuilding"
        )

        service = StoreyAssignmentService(registry, mock, coverage_threshold=0.60)

        # Act
        service.assign_elements([30])

        # Assert
        # Element below all storeys might not be assigned or assigned to Storey1
        # This depends on implementation - check what happens
        assigned_storey = mock._elements[30]['storey']
        # Should not be assigned as it's below all storeys
        assert assigned_storey == "", f"Expected no assignment, got {assigned_storey}"

    def test_element_above_top_storey(self):
        """Test element positioned above the topmost storey."""
        # Arrange
        mock = EnhancedMockCadAdapter()
        building = create_test_building_with_four_storeys(storey_height=3.0)
        registry = BuildingRegistry()
        registry.register(building)

        # Beam starting at 13m (well above Storey4 which starts at 9m)
        mock.add_beam(
            element_id=31,
            name="Beam-Roof",
            guid=create_guid(),
            width=120,
            height=200,
            length=2000,
            position=(5.0, 5.0, 13.0),
            building="TestBuilding"
        )

        service = StoreyAssignmentService(registry, mock, coverage_threshold=0.60)

        # Act
        service.assign_elements([31])

        # Assert
        # According to the code, topmost storey is extended to infinite height
        assigned_storey = mock._elements[31]['storey']
        assert assigned_storey == "Storey4", f"Expected Storey4 (infinite top), got {assigned_storey}"

    def test_threshold_0_percent_assigns_to_any_overlap(self):
        """Test with 0% threshold - any overlap should assign."""
        # Arrange
        mock = EnhancedMockCadAdapter()
        building = create_test_building_with_four_storeys(storey_height=3.0)
        registry = BuildingRegistry()
        registry.register(building)

        # Beam with minimal overlap in Storey2 (just 1mm)
        mock.add_beam(
            element_id=40,
            name="Beam-MinOverlap",
            guid=create_guid(),
            width=120,
            height=200,
            length=3000,
            position=(5.0, 5.0, 2.999),  # From 2.999m to 5.999m
            building="TestBuilding"
        )

        service = StoreyAssignmentService(registry, mock, coverage_threshold=0.0)

        # Act
        service.assign_elements([40])

        # Assert
        assigned_storey = mock._elements[40]['storey']
        assert assigned_storey in ["Storey1", "Storey2"], f"Expected Storey1 or Storey2, got {assigned_storey}"

    def test_threshold_100_percent_requires_full_coverage(self):
        """Test with 100% threshold - requires complete coverage."""
        # Arrange
        mock = EnhancedMockCadAdapter()
        building = create_test_building_with_four_storeys(storey_height=3.0)
        registry = BuildingRegistry()
        registry.register(building)

        # Beam that spans two storeys (won't have 100% in either)
        mock.add_beam(
            element_id=41,
            name="Beam-Spanning",
            guid=create_guid(),
            width=120,
            height=200,
            length=2000,
            position=(5.0, 5.0, 2.0),  # From 2m to 4m
            building="TestBuilding"
        )

        # Beam fully within one storey
        mock.add_beam(
            element_id=42,
            name="Beam-FullyCovered",
            guid=create_guid(),
            width=120,
            height=200,
            length=2000,
            position=(5.0, 5.0, 0.5),  # From 0.5m to 2.5m (fully in Storey1: 0-3m)
            building="TestBuilding"
        )

        service = StoreyAssignmentService(registry, mock, coverage_threshold=1.0)

        # Act
        service.assign_elements([41, 42])

        # Assert
        # Element 41 spans storeys, won't reach 100% in either
        assert mock._elements[41]['storey'] == "", f"Element 41 should not be assigned"
        # Element 42 is fully within Storey1
        assert mock._elements[42]['storey'] == "Storey1", f"Element 42 should be assigned to Storey1"

    def test_very_thin_plate_at_boundary(self):
        """Test very thin plate (20mm) at storey boundary."""
        # Arrange
        mock = EnhancedMockCadAdapter()
        building = create_test_building_with_four_storeys(storey_height=3.0)
        registry = BuildingRegistry()
        registry.register(building)

        # Very thin plate at 6m boundary (between Storey2 and Storey3)
        mock.add_plate(
            element_id=50,
            name="ThinSlab-S3",
            guid=create_guid(),
            width=6000,
            length=8000,
            thickness=20,  # Only 20mm thick
            position=(0.0, 0.0, 6.0),
            building="TestBuilding"
        )

        service = StoreyAssignmentService(registry, mock, coverage_threshold=0.60)

        # Act
        service.assign_elements([50])

        # Assert
        assigned_storey = mock._elements[50]['storey']
        assert assigned_storey == "Storey3", f"Expected Storey3, got {assigned_storey}"

    def test_element_with_zero_height(self):
        """Test edge case: element with zero height (degenerate geometry)."""
        # Arrange
        mock = EnhancedMockCadAdapter()
        building = create_test_building_with_four_storeys(storey_height=3.0)
        registry = BuildingRegistry()
        registry.register(building)

        # Plate with zero thickness (should still be at a Z position)
        mock.add_plate(
            element_id=60,
            name="ZeroThicknessPlate",
            guid=create_guid(),
            width=1000,
            length=1000,
            thickness=0,  # Zero thickness
            position=(0.0, 0.0, 1.5),
            building="TestBuilding"
        )

        service = StoreyAssignmentService(registry, mock, coverage_threshold=0.60)

        # Act
        service.assign_elements([60])

        # Assert
        # Zero-height element at 1.5m should still be processed
        assigned_storey = mock._elements[60]['storey']
        # Might not assign due to zero height, or might assign based on position
        # This tests implementation robustness

    def test_invalid_threshold_raises_error(self):
        """Test that invalid threshold values raise ValueError."""
        # Arrange
        mock = EnhancedMockCadAdapter()
        building = create_test_building_with_four_storeys()
        registry = BuildingRegistry()
        registry.register(building)

        # Act & Assert
        with pytest.raises(ValueError, match="coverage_threshold must be in"):
            StoreyAssignmentService(registry, mock, coverage_threshold=-0.1)

        with pytest.raises(ValueError, match="coverage_threshold must be in"):
            StoreyAssignmentService(registry, mock, coverage_threshold=1.5)

    def test_empty_element_list(self):
        """Test assignment with empty element list."""
        # Arrange
        mock = EnhancedMockCadAdapter()
        building = create_test_building_with_four_storeys()
        registry = BuildingRegistry()
        registry.register(building)
        service = StoreyAssignmentService(registry, mock, coverage_threshold=0.60)

        # Act
        service.assign_elements([])  # Empty list

        # Assert - should complete without error
        # No elements to verify, just ensuring no exceptions

    def test_column_spanning_all_storeys(self):
        """Test vertical column spanning all four storeys."""
        # Arrange
        mock = EnhancedMockCadAdapter()
        building = create_test_building_with_four_storeys(storey_height=3.0)
        registry = BuildingRegistry()
        registry.register(building)

        # Column from 0m to 12m (all four storeys)
        # Each storey gets 3m of the 12m total = 25% coverage
        mock.add_beam(
            element_id=70,
            name="Column-FullHeight",
            guid=create_guid(),
            width=300,  # Square column
            height=300,
            length=12000,  # 12m tall
            position=(2.0, 2.0, 0.0),
            building="TestBuilding"
        )

        service = StoreyAssignmentService(registry, mock, coverage_threshold=0.20)

        # Act
        service.assign_elements([70])

        # Assert
        assigned_storey = mock._elements[70]['storey']
        # Should assign to first storey that meets threshold
        assert assigned_storey == "Storey1", f"Expected Storey1, got {assigned_storey}"

    def test_multiple_buildings(self):
        """Test assignment with multiple buildings."""
        # Arrange
        mock = EnhancedMockCadAdapter()

        building1 = Building(
            name="Building-A",
            storeys=[
                BuildingStorey(building_name="Building-A", storey_name="Ground", elevation=0.0),
                BuildingStorey(building_name="Building-A", storey_name="First", elevation=3.0),
            ]
        )

        building2 = Building(
            name="Building-B",
            storeys=[
                BuildingStorey(building_name="Building-B", storey_name="Level1", elevation=0.0),
                BuildingStorey(building_name="Building-B", storey_name="Level2", elevation=3.5),
            ]
        )

        registry = BuildingRegistry()
        registry.register(building1)
        registry.register(building2)

        # Add elements to different buildings
        mock.add_beam(80, "Beam-A1", create_guid(), 120, 200, 2000, (0.0, 0.0, 0.5), "Building-A")
        mock.add_beam(81, "Beam-B1", create_guid(), 120, 200, 2000, (10.0, 10.0, 0.5), "Building-B")

        service = StoreyAssignmentService(registry, mock, coverage_threshold=0.60)

        # Act
        service.assign_elements([80, 81])

        # Assert
        assert mock._elements[80]['building'] == "Building-A"
        assert mock._elements[80]['storey'] == "Ground"
        assert mock._elements[81]['building'] == "Building-B"
        assert mock._elements[81]['storey'] == "Level1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
