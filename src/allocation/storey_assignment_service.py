import logging
import sys
from typing import Iterable, Optional, Generator

import attribute_controller  # TODO: move to cwapi_wrapper

import models
import visitors
from models import IModelElement
import cad_adapter
from .model_tree_builder import ModelElementTreeBuilder
from .building_registry import BuildingRegistry
from .building_storey_boundary_creator import BuildingStoreyBoundaryCreator

logger = logging.getLogger(__name__)


def build_model_element_trees(element_ids: Iterable[int], adapter: cad_adapter.ICadAdapter) -> list[
    models.IModelElement]:
    """Build model element trees using the provided adapter.
    
    Args:
        element_ids: Iterable of element IDs to process.
        adapter: An implementation of ICadAdapter for accessing CAD data.
        
    Returns:
        List of root model elements in the tree.
    """
    tree_builder = ModelElementTreeBuilder(element_ids, adapter)
    return tree_builder.build()


def filter_valid_elements(element_ids: Iterable[int]) -> Generator[int, None, None]:
    valid_elements = (eid for eid in element_ids if
                      not attribute_controller.is_node(eid)
                      and not attribute_controller.is_line(eid)
                      and not ((t := attribute_controller.get_element_type(eid)) and t.is_dimension())
                      )
    return valid_elements


class StoreyAssignmentService:
    """
    Service that:
      - Builds boundaries for each registered building
      - Checks element bbox against boundaries
      - Assigns the element to the first storey with >= threshold coverage
      - Logs decisions
    """

    def __init__(self, registry: BuildingRegistry, cad_adapter: cad_adapter.ICadAdapter,
                 coverage_threshold: float = 0.60) -> None:
        if not (0.0 <= coverage_threshold <= 1.0):
            raise ValueError("coverage_threshold must be in [0,1]")
        self._registry = registry
        self._coverage_threshold = coverage_threshold
        self._cad_adapter = cad_adapter

    @models.decorators.timeit("Assign elements to storeys")
    def assign_elements(self, element_ids: Iterable[int]) -> None:
        """
        Assign each element in element_ids to a storey if its local bbox overlaps
        at least coverage_threshold fraction with a storey boundary.
        """

        # visitor = visitors.VerticalCoverageAssignmentVisitor(self._coverage_threshold)
        # result = building_element.accept(visitor, boundaries)

        valid_elements = filter_valid_elements(element_ids)

        model_element_trees = build_model_element_trees(valid_elements, self._cad_adapter)
        building_tree_nodes: dict[str, list[models.IModelElement]] = self.map_model_element_trees_to_buildings(
            model_element_trees)

        for building_name, building in self._registry.items():
            logger.info(f"Processing building: {building_name}")

            # Create storey boundaries (one per vertical span)
            boundaries: list[models.BuildingStoreyBoundary] = BuildingStoreyBoundaryCreator.from_building(
                building)
            if not boundaries:
                logger.warning(f"No boundaries for building {building_name}")
                continue

            for b in boundaries:
                bz0, bz1 = b.z_range()
                logger.debug(
                    f"Boundary {b.storey.building_name} - {b.storey.storey_name}: z_range=({bz0:.3f}, {bz1:.3f}), height={b.height():.3f}")

            top_most_storey = boundaries[-1]
            top_most_storey.top_frame = top_most_storey.top_frame.translated([0, 0, sys.float_info.max])
            logger.debug(
                f"Extended topmost storey {top_most_storey.storey.building_name} - {top_most_storey.storey.storey_name} to infinite height."
            )

            building_element_nodes = building_tree_nodes.setdefault(building_name, None)
            if not building_element_nodes:
                logger.warning(f"No building elements for building {building_name}")
                continue

            to_assign: dict[str, list[int]] = {}  # storey_name -> element ids

            node_children: list[IModelElement] = list()
            for element_node in building_element_nodes:
                node_children.append(element_node)
                if element_node.children:
                    node_children.extend(element_node.children)

            for building_element in node_children:
                visitor = visitors.VerticalCoverageAssignmentVisitor(self._coverage_threshold)
                storey_name_coverage: Optional[models.StoreyCoverage] = building_element.accept(visitor, boundaries)
                if not storey_name_coverage:
                    logger.warning(
                        f"Element {building_element.name} ({building_element.guid.value}) not assigned to any storey")
                    continue

                elements = to_assign.setdefault(storey_name_coverage.storey_name, [])
                elements.append(self._cad_adapter.get_element_from_cadwork_guid(building_element.guid.value))
                elements.extend(
                    (self._cad_adapter.get_element_from_cadwork_guid(e.guid.value) for e in
                     building_element.children))

            # Perform assignments batched per storey
            for storey_name, element_ids in to_assign.items():
                try:
                    logger.info(f"Setting {len(element_ids)} elements to {building_name}/{storey_name}")
                    self._cad_adapter.set_building_and_storey(element_ids, building_name, storey_name)
                except Exception as e:
                    logger.exception(
                        f"Failed assigning {len(element_ids)} elements to {building_name}/{storey_name}: {e}"
                    )

    def map_model_element_trees_to_buildings(self, model_element_trees: list[models.IModelElement]) -> dict[
        str, list[models.IModelElement]]:
        """Map each model element tree to its corresponding building name."""
        buildings_to_nodes: dict[str, list[models.IModelElement]] = {}
        for node in model_element_trees:
            element_id: int = self._cad_adapter.get_element_from_cadwork_guid(node.guid.value)
            building_name: str = self._cad_adapter.get_building(element_id) or "UnassignedBuilding"
            buildings_to_nodes.setdefault(building_name, []).append(node)

        return buildings_to_nodes
