"""
Example test demonstrating how to test CAD-dependent code using the mock adapter.

This test shows how the adapter pattern enables testing without a running CAD instance.
"""

import pytest
from tests.mock_cad_adapter import MockCadAdapter
from src.allocation.model_element_factory import ModelElementFactory
from src.allocation.model_tree_builder import ModelElementTreeBuilder
import models


class TestModelElementFactory:
    """Test ModelElementFactory with mock adapter."""

    def test_create_simple_element(self):
        """Test creating a simple element."""
        # Arrange
        mock = MockCadAdapter()
        mock.add_element(
            element_id=1,
            name="TestBeam",
            guid=models.create_guid().value,
            p1=(10, 20, 30),
            xl=(5, 0, 0),
            yl=(0, 2, 0),
            zl=(0, 0, 1)
        )
        factory = ModelElementFactory(mock)

        # Act
        element = factory.create(1)

        # Assert
        assert element.name == "TestBeam"
        assert element.guid.value != ""
        assert element.geometry.local_origin().x == 10
        assert element.geometry.local_origin().y == 20
        assert element.geometry.local_origin().z == 30

    def test_create_wall_element(self):
        """Test creating a wall element."""
        # Arrange
        mock = MockCadAdapter()
        mock.add_element(
            element_id=100,
            name="ExteriorWall",
            is_wall=True,
            p1=(0, 0, 0),
        )
        factory = ModelElementFactory(mock)

        # Act
        element = factory.create(100)

        # Assert
        assert element.name == "ExteriorWall"
        # TODO: Currently factory returns ModelLeafElement, not Wall
        # This has to be be enhanced in the factory implementation


class TestModelElementTreeBuilder:
    """Test ModelElementTreeBuilder with mock adapter."""

    def test_build_simple_tree(self):
        """Test building a simple tree with one wall and children."""
        # Arrange
        mock = MockCadAdapter()

        # Add a wall (parent)
        mock.add_element(
            element_id=1,
            name="Wall-1",
            is_wall=True,
            subgroup="G1"
        )

        # Add child elements in the same subgroup
        mock.add_element(
            element_id=2,
            name="Beam-1",
            subgroup="G1"
        )
        mock.add_element(
            element_id=3,
            name="Beam-2",
            subgroup="G1"
        )

        builder = ModelElementTreeBuilder([1, 2, 3], mock)

        # Act
        trees = builder.build()

        # Assert
        assert len(trees) == 1
        wall_node = trees[0]
        assert isinstance(wall_node, models.Wall)
        assert wall_node.name == "Wall-1"
        assert len(wall_node.children) == 2
        assert wall_node.children[0].name == "Beam-1"
        assert wall_node.children[1].name == "Beam-2"

    def test_build_tree_with_orphans(self):
        """Test building a tree with orphaned elements."""
        # Arrange
        mock = MockCadAdapter()

        # Add a wall with subgroup "G1"
        mock.add_element(
            element_id=1,
            name="Wall-1",
            is_wall=True,
            subgroup="G1"
        )

        # Add orphan elements with different subgroup
        mock.add_element(
            element_id=2,
            name="Orphan-1",
            subgroup="G2"
        )

        builder = ModelElementTreeBuilder([1, 2], mock)

        # Act
        trees = builder.build()

        # Assert
        assert len(trees) == 2

        # Find the wall and orphans container
        wall = next((t for t in trees if t.name == "Wall-1"), None)
        orphans = next((t for t in trees if t.name == "Orphans"), None)

        assert wall is not None
        assert orphans is not None
        assert len(wall.children) == 0  # Wall has no children in its group
        assert len(orphans.children) == 1  # Orphan container has 1 child
        assert orphans.children[0].name == "Orphan-1"

    def test_classify_elements_by_type(self):
        """Test that elements are correctly classified."""
        # Arrange
        mock = MockCadAdapter()
        mock.add_element(1, "Wall-1", is_wall=True, subgroup="G1")
        mock.add_element(2, "Floor-1", is_floor=True, subgroup="G2")
        mock.add_element(3, "Roof-1", is_roof=True, subgroup="G3")
        mock.add_element(4, "Beam-1", subgroup="G4")

        builder = ModelElementTreeBuilder([1, 2, 3, 4], mock)

        # Act
        trees = builder.build()

        # Assert
        assert len(trees) == 4  # 3 typed parents + 1 orphan container

        types_found = {type(t).__name__ for t in trees}
        assert "Wall" in types_found
        assert "Slab" in types_found
        assert "Roof" in types_found
        assert "ModelNodeElement" in types_found  # Orphans container


class TestGroupingBehavior:
    """Test grouping behavior with different grouping types."""

    def test_subgroup_grouping(self):
        """Test that elements are grouped by subgroup when subgroup mode is active."""
        # Arrange
        mock = MockCadAdapter()
        mock.set_element_grouping_type(2)  # cadwork.element_grouping_type.subgroup

        mock.add_element(1, "Wall-1", is_wall=True, group="GroupA", subgroup="SubA")
        mock.add_element(2, "Beam-1", group="GroupA", subgroup="SubA")
        mock.add_element(3, "Beam-2", group="GroupB", subgroup="SubA")  # Same subgroup

        builder = ModelElementTreeBuilder([1, 2, 3], mock)

        # Act
        trees = builder.build()

        # Assert
        wall = trees[0]
        assert len(wall.children) == 2  # Both beams have same subgroup as wall

    def test_group_grouping(self):
        """Test that elements are grouped by group when group mode is active."""
        # Arrange
        mock = MockCadAdapter()
        mock.set_element_grouping_type(1)

        mock.add_element(1, "Wall-1", is_wall=True, group="GroupA", subgroup="SubA")
        mock.add_element(2, "Beam-1", group="GroupA", subgroup="SubB")  # Different subgroup, same group
        mock.add_element(3, "Beam-2", group="GroupB", subgroup="SubA")  # Different group

        builder = ModelElementTreeBuilder([1, 2, 3], mock)

        # Act
        trees = builder.build()

        # Assert
        wall = trees[0]
        # In group mode, Beam-1 should be grouped with Wall-1 (same group)
        assert len(wall.children) == 1
        assert wall.children[0].name == "Beam-1"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
