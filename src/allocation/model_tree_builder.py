from typing import Iterable, Dict, List, Tuple, Callable

import attribute_controller as ac
import cadwork
import element_controller as ec
import geometry_controller as gc
from compas.geometry import Point, Vector

import models
import logging

logger = logging.getLogger(__name__)


def _classify(ids: Iterable[int]) -> Tuple[List[int], List[int]]:
    parents, leaves = [], []
    for i in ids:
        if ac.is_wall(i) or ac.is_floor(i) or ac.is_roof(i) or ac.is_container(i):
            parents.append(i)
        else:
            leaves.append(i)
    return parents, leaves


grouping_by: Callable[[int], str] = lambda x: ac.get_subgroup(x) \
    if ac.get_element_grouping_type() == cadwork.element_grouping_type.subgroup \
    else lambda y: ac.get_group(y)


def _group_children(leaf_ids: Iterable[int]) -> Dict[str, List[int]]:
    groups: Dict[str, List[int]] = {}
    for i in leaf_ids:
        subgroup = grouping_by(i) or ""
        groups.setdefault(subgroup, []).append(i)
    return groups


class ModelElementTreeBuilder:
    def __init__(self, element_ids: Iterable[int]):
        self._all_ids: List[int] = list(element_ids)

    def build(self) -> list[models.IModelElement]:
        parents, leaves = _classify(self._all_ids)
        grouping_to_children = _group_children(leaves)

        composites: list[models.IModelElement] = []
        for pid in parents:
            subgroup = grouping_by(pid) or ""
            children_ids = grouping_to_children.get(subgroup, [])
            try:
                parent_el = self._create_typed_parent(pid, [self._create_leaf_element(cid) for cid in children_ids])
                composites.append(parent_el)
            except ValueError as e:
                logger.warning(f"Failed to create parent element for {pid}: {e}")

        # attach orphan leaves (no parent by subgroup) under a generic container
        orphans = self._collect_orphans(leaves, grouping_to_children, set(grouping_by(p) or "" for p in parents))
        if orphans:
            container = models.ModelNodeElement(
                guid=models.create_guid(),  # stable but arbitrary
                name="Orphans",
                geometry=self._empty_geometry(),
                children=[self._create_leaf_element(i) for i in orphans],
            )
            composites.append(container)

        return composites

    @staticmethod
    def _collect_orphans(leaf_ids: Iterable[int], groups: Dict[str, List[int]], parent_groups: set[str]) -> set[int]:
        orphans: set[int] = set()
        for subgroup, ids in groups.items():
            if subgroup not in parent_groups:
                orphans.update(ids)
        return orphans

    def _create_typed_parent(self, parent_id: int, children: list[models.IModelElement]) -> models.IModelElement:
        guid = models.Guid(ec.get_element_cadwork_guid(parent_id))
        name = ac.get_name(parent_id)
        geom = self._create_element_geometry(parent_id)
        if ac.is_wall(parent_id):
            return models.Wall(guid, name, geom, children)
        if ac.is_floor(parent_id):
            return models.Slab(guid, name, geom, children)
        if ac.is_roof(parent_id):
            return models.Roof(guid, name, geom, children)
        if ac.is_container(parent_id):
            return models.Container(guid, name, geom, children)
        # Fallback
        return models.ModelNodeElement(guid, name, geom, children)

    def _create_leaf_element(self, element_id: int) -> models.ModelLeafElement:
        guid = models.Guid(ec.get_element_cadwork_guid(element_id))
        name = ac.get_name(element_id)
        geom = self._create_element_geometry(element_id)
        return models.ModelLeafElement(guid, name, geom)

    @staticmethod
    def _create_element_geometry(element_id: int) -> models.ModelElementGeometry:
        bbx_vertices = ec.get_bounding_box_vertices_local(element_id, [element_id])
        bbx_pts = [Point(v.x, v.y, v.z) for v in bbx_vertices]
        return models.ModelElementGeometry(
            Point(gc.get_p1(element_id).x, gc.get_p1(element_id).y, gc.get_p1(element_id).z),
            Vector(gc.get_xl(element_id).x, gc.get_xl(element_id).y, gc.get_xl(element_id).z),
            Vector(gc.get_yl(element_id).x, gc.get_yl(element_id).y, gc.get_yl(element_id).z),
            Vector(gc.get_zl(element_id).x, gc.get_zl(element_id).y, gc.get_zl(element_id).z),
            bbx_pts,
        )

    @staticmethod
    def _empty_geometry() -> models.ModelElementGeometry:
        origin = Point(0, 0, 0)
        x = Vector(1, 0, 0)
        y = Vector(0, 1, 0)
        z = Vector(0, 0, 1)
        bbx = [origin, origin, origin, origin, origin, origin, origin, origin]
        return models.ModelElementGeometry(origin, x, y, z, bbx)


# Convenience function
def build_model_tree(element_ids: Iterable[int]) -> list[models.IModelElement]:
    return ModelElementTreeBuilder(element_ids).build()
