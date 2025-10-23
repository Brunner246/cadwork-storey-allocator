import bim_controller as bc
import cadwork
import element_controller as ec
from compas.geometry import Point, Vector


def get_aabb_vertices(element_id: int) -> list[Point]:
    bbx_vertices = ec.get_bounding_box_vertices_local(element_id, [element_id])
    bbx_pts = [to_point(v) for v in bbx_vertices]
    return bbx_pts


# TODO: utility.py
def to_vector(vec3: cadwork.point_3d) -> Vector:
    return Vector(vec3.x, vec3.y, vec3.z)


def to_point(point3d: cadwork.point_3d) -> Point:
    return Point(point3d.x, point3d.y, point3d.z)


# def create_model_element(element_id: int) -> models.IModelElement:
#     return ModelElementFactory.create(element_id)


def get_building_name(element_id: int) -> str:
    return bc.get_building(element_id)


def set_building_storey(element_ids: list[int], building_name: str, storey_name: str) -> None:
    bc.set_building_and_storey(element_ids, building_name, storey_name)


def get_element_id_from_cadwork_guid(guid: str) -> int:
    guid = guid if not guid.islower() else guid.upper()
    if not guid.startswith('{') and not guid.endswith('}'):
        guid = '{' + guid + '}'
    return ec.get_element_from_cadwork_guid(guid)


def get_all_element_ids() -> list[int]:
    return ec.get_all_identifiable_element_ids()


def get_active_element_ids() -> list[int]:
    return ec.get_active_identifiable_element_ids()
