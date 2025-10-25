import models
from allocation import ModelElementTreeBuilder
from mock_cad_adapter import MockCadAdapter


class TestModelElementTreeBuilder:
    """Test ModelElementTreeBuilder with mock adapter."""

    def test_build_simple_tree(self):
        """Test building a simple tree with one wall and children."""
        # Arrange
        mock = MockCadAdapter()

        # Add a wall (parent)
        mock.add_element(element_id=1,
                         name="Wall-1",
                         is_wall=True,
                         subgroup="G1"
                         )

        # Add child elements in the same subgroup
        mock.add_element(element_id=2,
                         name="Beam-1",
                         subgroup="G1"
                         )
        mock.add_element(element_id=3,
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

        mock.add_element(element_id=1,
                         name="Wall-1",
                         is_wall=True,
                         subgroup="G1"
                         )

        # orphan elements with different subgroup
        mock.add_element(element_id=2,
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
