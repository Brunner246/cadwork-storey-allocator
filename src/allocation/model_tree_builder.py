from typing import Iterable, Dict, List, Tuple, Callable

import cadwork
from compas.geometry import Point, Vector

import cad_adapter
import models
import logging

logger = logging.getLogger(__name__)


class ModelElementTreeBuilder:
    """Builds a tree of ModelElements from CAD element IDs.
    
    This builder uses dependency injection to allow for testing without
    a running CAD instance.
    """

    def __init__(self, element_ids: Iterable[int], adapter: cad_adapter.ICadAdapter):
        """Initialize the builder with element IDs and a CAD adapter.
        
        Args:
            element_ids: Iterable of element IDs to process.
            adapter: An implementation of ICadAdapter for accessing CAD data.
        """
        self._all_ids: List[int] = list(element_ids)
        self._adapter = adapter

    def _classify(self, ids: Iterable[int]) -> Tuple[List[int], List[int]]:
        """Classify elements into parents (walls, floors, etc.) and leaves."""
        parents, leaves = [], []
        for i in ids:
            if (self._adapter.is_wall(i) or self._adapter.is_floor(i) or
                    self._adapter.is_roof(i) or self._adapter.is_container(i)):
                parents.append(i)
            else:
                leaves.append(i)
        return parents, leaves

    def _grouping_by(self, element_id: int) -> str:
        """Get grouping key for an element based on current grouping type."""
        if self._adapter.get_element_grouping_type().value == cad_adapter.ElementGroupingType.SUBGROUP.value:
            return self._adapter.get_subgroup(element_id)
        else:
            return self._adapter.get_group(element_id)

    def _group_children(self, leaf_ids: Iterable[int]) -> Dict[str, List[int]]:
        """Group leaf elements by their group/subgroup."""
        groups: Dict[str, List[int]] = {}
        for i in leaf_ids:
            subgroup = self._grouping_by(i) or ""
            groups.setdefault(subgroup, []).append(i)
        return groups

    def build(self) -> list[models.IModelElement]:
        """Build the model element tree."""
        parents, leaves = self._classify(self._all_ids)
        grouping_to_children = self._group_children(leaves)

        composites: list[models.IModelElement] = []
        for pid in parents:
            subgroup = self._grouping_by(pid) or ""
            children_ids = grouping_to_children.get(subgroup, [])
            try:
                parent_el = self._create_typed_parent(pid, [self._create_leaf_element(cid) for cid in children_ids])
                composites.append(parent_el)
            except ValueError as e:
                logger.warning(f"Failed to create parent element for {pid}: {e}")

        # attach orphan leaves (no parent by subgroup) under a generic container
        orphans = self._collect_orphans(grouping_to_children, set(self._grouping_by(p) or "" for p in parents))
        if orphans:
            container = models.OrphanParent(
                guid=models.create_guid(),  # Create a synthetic GUID for the orphan container
                name="Orphans",
                geometry=self._empty_geometry(),
                children=[self._create_leaf_element(i) for i in orphans],
            )
            composites.append(container)

        return composites

    @staticmethod
    def _collect_orphans(groups: Dict[str, List[int]], parent_groups: set[str]) -> set[int]:
        orphans: set[int] = set()
        for subgroup, ids in groups.items():
            if subgroup not in parent_groups:
                orphans.update(ids)
        return orphans

    def _create_typed_parent(self, parent_id: int, children: list[models.IModelElement]) -> models.IModelElement:
        """Create a typed parent element (Wall, Floor, Roof, Container)."""
        guid = models.Guid(self._adapter.get_element_cadwork_guid(parent_id))
        name = self._adapter.get_name(parent_id)
        geom = self._create_element_geometry(parent_id)
        if self._adapter.is_wall(parent_id):
            return models.Wall(guid, name, geom, children)
        if self._adapter.is_floor(parent_id):
            return models.Slab(guid, name, geom, children)
        if self._adapter.is_roof(parent_id):
            return models.Roof(guid, name, geom, children)
        if self._adapter.is_container(parent_id):
            return models.Container(guid, name, geom, children)
        # Fallback
        return models.ModelNodeElement(guid, name, geom, children)

    def _create_leaf_element(self, element_id: int) -> models.ModelLeafElement:
        """Create a leaf element."""
        guid = models.Guid(self._adapter.get_element_cadwork_guid(element_id))
        name = self._adapter.get_name(element_id)
        geom = self._create_element_geometry(element_id)
        return models.ModelLeafElement(guid, name, geom)

    def _create_element_geometry(self, element_id: int) -> models.ModelElementGeometry:
        """Create geometry for an element."""
        lazy_aabb_query: Callable[[], list[Point]] = lambda: self._adapter.get_bounding_box_vertices_local(element_id,
                                                                                                           [element_id])
        return models.ModelElementGeometry(
            cad_adapter.to_point(self._adapter.get_p1(element_id)),
            cad_adapter.to_vector(self._adapter.get_xl(element_id)),
            cad_adapter.to_vector(self._adapter.get_yl(element_id)),
            cad_adapter.to_vector(self._adapter.get_zl(element_id)),
            lazy_aabb_query,
        )

    @staticmethod
    def _empty_geometry() -> models.ModelElementGeometry:
        origin = Point(0, 0, 0)
        x = Vector(1, 0, 0)
        y = Vector(0, 1, 0)
        z = Vector(0, 0, 1)
        bbx = [origin, origin, origin, origin, origin, origin, origin, origin]
        lazy_aabb_query: Callable[[], list[Point]] = lambda: bbx
        return models.ModelElementGeometry(origin, x, y, z, lazy_aabb_query)


def build_model_tree(element_ids: Iterable[int], adapter: cad_adapter.ICadAdapter) -> list[models.IModelElement]:
    """Build a model tree from element IDs using the provided adapter.
    
    Args:
        element_ids: Iterable of element IDs to process.
        adapter: An implementation of ICadAdapter for accessing CAD data.
        
    Returns:
        List of root model elements in the tree.
    """
    return ModelElementTreeBuilder(element_ids, adapter).build()
