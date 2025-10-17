import logging
from typing import Iterable

import bim_controller as bc
import element_controller as ec
from bim_controller import set_building_and_storey
from compas.geometry import Point

import allocation
import models
from allocation.building_registry import BuildingRegistry
from allocation.building_storey_boundary_creator import BuildingStoreyBoundaryCreator
from allocation.model_element_factory import ModelElementFactory
from models.building_storey_boundary import BuildingStoreyBoundary

logger = logging.getLogger(__name__)


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

    def __init__(self, registry: BuildingRegistry, coverage_threshold: float = 0.60) -> None:
        if not (0.0 <= coverage_threshold <= 1.0):
            raise ValueError("coverage_threshold must be in [0,1]")
        self._registry = registry
        self._coverage_threshold = coverage_threshold

    def assign_elements(self, element_ids: Iterable[int]) -> None:
        """
        Assign each element in element_ids to a storey if its local bbox overlaps
        at least coverage_threshold fraction with a storey boundary.
        """

        model_element_trees = build_model_element_trees(element_ids)
        building_tree_nodes = map_model_element_trees_to_buildings(model_element_trees)

        for building_name, building in self._registry.items():
            logger.info(f"Processing building: {building_name}")

            # Create storey boundaries (one per vertical span)
            boundaries: list[BuildingStoreyBoundary] = BuildingStoreyBoundaryCreator.from_building(building)
            if not boundaries:
                logger.warning(f"No boundaries for building {building_name}")
                continue

            # Pre-log boundaries
            for b in boundaries:
                bz0, bz1 = b.z_range()
                logger.debug(f"Boundary {b.identifier}: z_range=({bz0:.3f}, {bz1:.3f}), height={b.height():.3f}")

            to_assign: dict[str, list[int]] = {}  # storey_name -> element ids

            for eid in element_ids:
                try:
                    me = ModelElementFactory.create(eid)
                except Exception as e:
                    logger.exception(f"Failed to create model element for id={eid}: {e}")
                    continue

                # Get bbox points (compas Points) from geometry (we stored them in the BoundingBox)
                # We reconstruct from local bbox vertices again to avoid exposing internals
                try:
                    bbx_vertices = ec.get_bounding_box_vertices_local(eid, [eid])
                    bbox_pts = [ModelElementFactory.to_point(v) for v in bbx_vertices]
                except Exception as e:
                    logger.exception(f"Failed to get bbox for id={eid}: {e}")
                    continue

                chosen_storey = None
                chosen_coverage = 0.0

                # Evaluate coverage for each boundary
                for boundary in boundaries:
                    covered = self._vertical_coverage(boundary, bbox_pts)
                    logger.debug(
                        f"Element {eid} vs {boundary.identifier}: coverage={covered:.3%}"
                    )
                    if covered > chosen_coverage:
                        chosen_storey = boundary.identifier.split("_", 1)[-1]  # "<building>_<storey>"
                        chosen_coverage = covered

                if chosen_storey and chosen_coverage >= self._coverage_threshold:
                    to_assign.setdefault(chosen_storey, []).append(eid)
                    logger.info(
                        f"Element {eid} assigned to {building_name}/{chosen_storey} "
                        f"(coverage={chosen_coverage:.3%} thr={self._coverage_threshold:.3%})"
                    )
                else:
                    logger.warning(
                        f"Element {eid} not assigned in {building_name} "
                        f"(best={chosen_coverage:.3%} thr={self._coverage_threshold:.3%})"
                    )

            # Perform assignments batched per storey
            for storey_name, eids in to_assign.items():
                try:
                    logger.info(f"Setting {len(eids)} elements to {building_name}/{storey_name}")
                    set_building_and_storey(eids, building_name, storey_name)
                except Exception as e:
                    logger.exception(
                        f"Failed assigning {len(eids)} elements to {building_name}/{storey_name}: {e}"
                    )

    @staticmethod
    def _vertical_coverage(boundary: BuildingStoreyBoundary, bbox_points: Iterable[Point]) -> float:
        """Return fraction of bbox height overlapped by boundary along Z."""
        zs = [p.z for p in bbox_points]
        z_min, z_max = min(zs), max(zs)
        if z_max <= z_min:
            return 0.0

        b_min, b_max = boundary.z_range()
        overlap_low = max(z_min, b_min)
        overlap_high = min(z_max, b_max)
        overlap = max(0.0, overlap_high - overlap_low)
        return overlap / (z_max - z_min)

    @staticmethod
    def _create_node_elements(element_ids: Iterable[int]) -> list[int]:
        """Create ModelNodeElement instances from element ids."""
        node_elements = []
        for eid in element_ids:
            me = ModelElementFactory.create(eid)
            # if isinstance(me, models.ModelNodeElement):
            #     node_elements.append(me)
        return node_elements
