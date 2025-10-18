import logging
from typing import Iterable, Optional

import bim_controller as bc
import element_controller as ec
from bim_controller import set_building_and_storey

import allocation
import models
import visitors

logger = logging.getLogger(__name__)


def get_element_id_from_cadwork_guid(guid: str) -> int:
    return ec.get_element_from_cadwork_guid(guid)


def build_model_element_trees(element_ids: Iterable[int]) -> list[models.IModelElement]:
    tree_builder = allocation.ModelElementTreeBuilder(element_ids)
    return tree_builder.build()


def map_model_element_trees_to_buildings(model_element_trees: list[models.IModelElement]) -> dict[
    str, models.IModelElement]:
    buildings_to_nodes: dict[str, models.IModelElement] = {}
    for node in model_element_trees:
        element_id: int = ec.get_element_from_cadwork_guid(node.guid.value)
        building_name: str = bc.get_building(element_id) or "UnassignedBuilding"
        buildings_to_nodes.setdefault(building_name, node)

    return buildings_to_nodes


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

    def assign_elements(self, element_ids: Iterable[int]) -> None:
        """
        Assign each element in element_ids to a storey if its local bbox overlaps
        at least coverage_threshold fraction with a storey boundary.
        """

        # visitor = visitors.VerticalCoverageAssignmentVisitor(self._coverage_threshold)
        # result = building_element.accept(visitor, boundaries)

        model_element_trees = build_model_element_trees(element_ids)
        building_tree_nodes: dict[str, models.IModelElement] = map_model_element_trees_to_buildings(model_element_trees)

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

            building_element_nodes = building_tree_nodes.setdefault(building_name, None)
            if not building_element_nodes:
                logger.warning(f"No building elements for building {building_name}")
                continue

            to_assign: dict[str, list[int]] = {}  # storey_name -> element ids

            for building_element in building_element_nodes.children:
                visitor = visitors.VerticalCoverageAssignmentVisitor(self._coverage_threshold)
                storey_name_coverage: Optional[models.StoreyCoverage] = building_element.accept(visitor, boundaries)

                elements = to_assign.setdefault(storey_name_coverage.storey_name, [])
                elements.append(get_element_id_from_cadwork_guid(building_element.guid.value))
                elements.extend((get_element_id_from_cadwork_guid(e.guid.value) for e in building_element.children))

            # Perform assignments batched per storey
            for storey_name, element_ids in to_assign.items():
                try:
                    logger.info(f"Setting {len(element_ids)} elements to {building_name}/{storey_name}")
                    set_building_and_storey(element_ids, building_name, storey_name)
                except Exception as e:
                    logger.exception(
                        f"Failed assigning {len(element_ids)} elements to {building_name}/{storey_name}: {e}"
                    )
