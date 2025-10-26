import pytest
from tests.mock_cad_adapter import MockCadAdapter
from src.allocation.model_element_factory import ModelElementFactory
from models import Guid


class TestModelElementFactory:
    """Test ModelElementFactory with mock adapter."""

    def test_create_simple_element(self):
        """Test creating a simple element."""
        # Arrange
        mock = MockCadAdapter()
        mock.add_element(
            element_id=1,
            name="TestBeam",
            guid=Guid("a710a36f-2211-4b51-b2a8-30725eafddad"),
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
        assert element.guid == Guid("a710a36f-2211-4b51-b2a8-30725eafddad")
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
