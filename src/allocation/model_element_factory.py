import attribute_controller as ac
import cadwork
import element_controller as ec
import geometry_controller as gc
from compas.geometry import Point, Vector

import models
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
        bbx_vertices = ec.get_bounding_box_vertices_local(element_id, [element_id])
        bbx_pts = [cls.to_point(v) for v in bbx_vertices]

        geometry = ModelElementGeometry(
            cls.to_point(gc.get_p1(element_id)),
            cls.to_vector(gc.get_xl(element_id)),
            cls.to_vector(gc.get_yl(element_id)),
            cls.to_vector(gc.get_zl(element_id)),
            bbx_pts,
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


def to_vector(vector3d: cadwork.point_3d) -> Vector:
    return ModelElementFactory.to_vector(vector3d)


def to_point(point3d: cadwork.point_3d) -> Point:
    return ModelElementFactory.to_point(point3d)


def create_model_element(element_id: int) -> IModelElement:
    return ModelElementFactory.create(element_id)
