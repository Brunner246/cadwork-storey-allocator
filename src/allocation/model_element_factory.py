from collections.abc import Callable

import attribute_controller as ac
import cadwork
import element_controller as ec
import geometry_controller as gc
from compas.geometry import Point, Vector

import models
from . import cwapi_wrapper
from models.model_element import ModelLeafElement, IModelElement
from models.model_element_geometry import ModelElementGeometry


class ModelElementFactory:

    @staticmethod
    def to_vector(vec3: cadwork.point_3d) -> Vector:
        return Vector(vec3.x, vec3.y, vec3.z)

    @staticmethod
    def to_point(p3: cadwork.point_3d) -> Point:
        return Point(p3.x, p3.y, p3.z)

    @classmethod
    def create(cls, element_id: int) -> IModelElement:
        """Create a ModelElement from an element id."""

        lazy_aabb_query: Callable[[], list[Point]] = lambda: cwapi_wrapper.get_aabb_vertices(element_id)

        geometry = ModelElementGeometry(
            cls.to_point(gc.get_p1(element_id)),
            cls.to_vector(gc.get_xl(element_id)),
            cls.to_vector(gc.get_yl(element_id)),
            cls.to_vector(gc.get_zl(element_id)),
            lazy_aabb_query,
        )

        # if is_wall := ac.is_wall(element_id):
        #     return models.Wall(
        #         models.Guid(ec.get_element_cadwork_guid(element_id)),
        #         ac.get_name(element_id),
        #         geometry,
        #     )

        return ModelLeafElement(
            models.Guid(ec.get_element_cadwork_guid(element_id)),
            ac.get_name(element_id),
            geometry,
        )


