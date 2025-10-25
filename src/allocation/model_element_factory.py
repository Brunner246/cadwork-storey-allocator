from collections.abc import Callable

from compas.geometry import Point

import models
import cad_adapter
from models.model_element import ModelLeafElement, IModelElement
from models.model_element_geometry import ModelElementGeometry


class ModelElementFactory:
    """Factory for creating ModelElements from CAD element IDs.
    
    This factory uses dependency injection to allow for testing without
    a running CAD instance.
    """

    def __init__(self, adapter: cad_adapter.ICadAdapter):
        """Initialize the factory with a CAD adapter.
        
        Args:
            adapter: An implementation of ICadAdapter for accessing CAD data.
        """
        self._adapter = adapter

    def create(self, element_id: int) -> IModelElement:
        """Create a ModelElement from an element id."""

        lazy_aabb_query: Callable[[], list[Point]] = lambda: cad_adapter.get_aabb_vertices(element_id)

        geometry = ModelElementGeometry(
            cad_adapter.to_point(self._adapter.get_p1(element_id)),
            cad_adapter.to_vector(self._adapter.get_xl(element_id)),
            cad_adapter.to_vector(self._adapter.get_yl(element_id)),
            cad_adapter.to_vector(self._adapter.get_zl(element_id)),
            lazy_aabb_query,
        )

        # if is_wall := self._adapter.is_wall(element_id):
        #     return models.Wall(
        #         models.Guid(self._adapter.get_element_cadwork_guid(element_id)),
        #         self._adapter.get_name(element_id),
        #         geometry,
        #     )

        return ModelLeafElement(
            models.Guid(self._adapter.get_element_cadwork_guid(element_id)),
            self._adapter.get_name(element_id),
            geometry,
        )
