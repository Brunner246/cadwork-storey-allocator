import logging
import sys
from typing import Iterable, Optional, Generator, Any

import attribute_controller  # TODO: move to cwapi_wrapper

import allocation
import models
import visitors
from models import IModelElement
from . import cwapi_wrapper

logger = logging.getLogger(__name__)


def build_model_element_trees(element_ids: Iterable[int]) -> list[models.IModelElement]:
    tree_builder = allocation.ModelElementTreeBuilder(element_ids)
    return tree_builder.build()


def map_model_element_trees_to_buildings(model_element_trees: list[models.IModelElement]) -> dict[
    str, list[models.IModelElement]]:
    """Map each model element tree to its corresponding building name."""
    buildings_to_nodes: dict[str, list[models.IModelElement]] = {}
    for node in model_element_trees:
        element_id: int = cwapi_wrapper.get_element_id_from_cadwork_guid(node.guid.value)
        building_name: str = cwapi_wrapper.get_building_name(element_id) or "UnassignedBuilding"
        buildings_to_nodes.setdefault(building_name, []).append(node)

    return buildings_to_nodes


def filter_valid_elements(element_ids: Iterable[int]) -> Generator[int]:
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

    def __init__(self, registry: allocation.BuildingRegistry, coverage_threshold: float = 0.60) -> None:
        if not (0.0 <= coverage_threshold <= 1.0):
            raise ValueError("coverage_threshold must be in [0,1]")
        self._registry = registry
        self._coverage_threshold = coverage_threshold

    @models.decorators.timeit("Assign elements to storeys")
    def assign_elements(self, element_ids: Iterable[int]) -> None:
        """
        Assign each element in element_ids to a storey if its local bbox overlaps
        at least coverage_threshold fraction with a storey boundary.
        """

        # visitor = visitors.VerticalCoverageAssignmentVisitor(self._coverage_threshold)
        # result = building_element.accept(visitor, boundaries)

        valid_elements = filter_valid_elements(element_ids)

        model_element_trees = build_model_element_trees(valid_elements)
        building_tree_nodes: dict[str, list[models.IModelElement]] = map_model_element_trees_to_buildings(
            model_element_trees)

        for building_name, building in self._registry.items():
            logger.info(f"Processing building: {building_name}")

            # Create storey boundaries (one per vertical span)
            boundaries: list[models.BuildingStoreyBoundary] = allocation.BuildingStoreyBoundaryCreator.from_building(
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
                elements.append(cwapi_wrapper.get_element_id_from_cadwork_guid(building_element.guid.value))
                elements.extend(
                    (cwapi_wrapper.get_element_id_from_cadwork_guid(e.guid.value) for e in
                     building_element.children))

            # Perform assignments batched per storey
            for storey_name, element_ids in to_assign.items():
                try:
                    logger.info(f"Setting {len(element_ids)} elements to {building_name}/{storey_name}")
                    cwapi_wrapper.set_building_storey(element_ids, building_name, storey_name)
                except Exception as e:
                    logger.exception(
                        f"Failed assigning {len(element_ids)} elements to {building_name}/{storey_name}: {e}"
                    )
