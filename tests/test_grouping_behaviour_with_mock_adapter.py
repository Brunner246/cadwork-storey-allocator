from allocation import ModelElementTreeBuilder
from cad_adapter import ElementGroupingType
from mock_cad_adapter import MockCadAdapter


class TestGroupingBehavior:
    """Test grouping behavior with different grouping types."""

    def test_subgroup_grouping(self):
        """Test that elements are grouped by subgroup when subgroup mode is active."""
        # Arrange
        mock = MockCadAdapter()
        mock.set_element_grouping_type(ElementGroupingType.SUBGROUP)  # cadwork.element_grouping_type.subgroup

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
        mock.set_element_grouping_type(ElementGroupingType.GROUP)

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
