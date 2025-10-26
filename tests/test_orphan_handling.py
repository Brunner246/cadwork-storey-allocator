"""Test handling of orphan elements with synthetic parent nodes."""

import pytest
from mock_cad_adapter import MockCadAdapter
from allocation.storey_assignment_service import StoreyAssignmentService
from allocation.building_registry import BuildingRegistry
from models import Building, BuildingStorey, Guid, create_guid


def test_orphan_elements_are_mapped_to_correct_buildings():
    """Test that orphan elements (without matching parents) are correctly mapped to their buildings."""
    # Setup mock adapter
    mock_adapter = MockCadAdapter()
    
    # Add parent element for Building1
    mock_adapter.add_element(
        element_id=1,
        name="Wall-001",
        guid=Guid("{00000000-0000-0000-0000-000000000001}"),
        is_wall=True,
        subgroup="SG1",
        building="Building1"
    )
    
    # Add child element for the wall
    mock_adapter.add_element(
        element_id=2,
        name="Beam-001",
        guid=Guid("{00000000-0000-0000-0000-000000000002}"),
        subgroup="SG1",
        building="Building1"
    )
    
    # Add orphan elements (no parent) - one for Building1, one for Building2
    mock_adapter.add_element(
        element_id=3,
        name="Orphan-Building1",
        guid=Guid("{00000000-0000-0000-0000-000000000003}"),
        subgroup="ORPHAN_GROUP",
        building="Building1"
    )
    
    mock_adapter.add_element(
        element_id=4,
        name="Orphan-Building2",
        guid=Guid("{00000000-0000-0000-0000-000000000004}"),
        subgroup="ORPHAN_GROUP",
        building="Building2"
    )
    
    # Create registry with both buildings
    registry = BuildingRegistry()
    registry.register(Building(
        name="Building1",
        storeys=[
            BuildingStorey("Building1", "Ground", 0.0),
            BuildingStorey("Building1", "First", 3.0),
        ]
    ))
    registry.register(Building(
        name="Building2",
        storeys=[
            BuildingStorey("Building2", "Ground", 0.0),
            BuildingStorey("Building2", "First", 3.0),
        ]
    ))
    
    # Create service
    service = StoreyAssignmentService(registry, mock_adapter, coverage_threshold=0.6)
    
    # Build model tree
    element_ids = [1, 2, 3, 4]
    model_trees = service.build_model_element_trees(element_ids)
    
    # Map to buildings
    building_mapping = service.map_model_element_trees_to_buildings(model_trees)
    
    # Verify the mapping
    assert "Building1" in building_mapping, "Building1 should be in mapping"
    assert "Building2" in building_mapping, "Building2 should be in mapping"
    
    # Building1 should have the wall parent and an orphan parent wrapper
    building1_nodes = building_mapping["Building1"]
    assert len(building1_nodes) == 2, f"Building1 should have 2 nodes (wall + orphan wrapper), got {len(building1_nodes)}"
    
    # Building2 should have one orphan parent wrapper
    building2_nodes = building_mapping["Building2"]
    assert len(building2_nodes) == 1, f"Building2 should have 1 node (orphan wrapper), got {len(building2_nodes)}"
    
    print("✓ Orphan elements correctly mapped to their buildings")


def test_orphan_parent_does_not_generate_invalid_element_ids():
    """Test that OrphanParent nodes don't try to get element IDs from synthetic GUIDs."""
    mock_adapter = MockCadAdapter()
    
    # Add only orphan elements
    mock_adapter.add_element(
        element_id=1,
        name="Orphan-001",
        guid=Guid("{00000000-0000-0000-0000-000000000001}"),
        subgroup="NO_PARENT",
        building="TestBuilding"
    )
    
    registry = BuildingRegistry()
    registry.register(Building(
        name="TestBuilding",
        storeys=[
            BuildingStorey("TestBuilding", "Ground", 0.0),
            BuildingStorey("TestBuilding", "First", 3.0),
        ]
    ))
    
    service = StoreyAssignmentService(registry, mock_adapter, coverage_threshold=0.6)
    
    # Build model tree - should create an OrphanParent
    model_trees = service.build_model_element_trees([1])
    assert len(model_trees) == 1, "Should have one tree (OrphanParent)"
    
    orphan_parent = model_trees[0]
    assert orphan_parent.kind.name == "ORPHAN_PARENT", "Should be an OrphanParent"
    
    # Try to collect element IDs - should not fail even though parent GUID is synthetic
    element_ids = service._collect_element_and_children_ids(orphan_parent)
    
    # Should only contain the child element ID (1), not the synthetic parent ID
    assert element_ids == [1], f"Should contain only child element ID [1], got {element_ids}"
    
    print("✓ OrphanParent with synthetic GUID handled correctly")


if __name__ == "__main__":
    test_orphan_elements_are_mapped_to_correct_buildings()
    test_orphan_parent_does_not_generate_invalid_element_ids()
    print("\nAll tests passed!")
