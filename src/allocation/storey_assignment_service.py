import logging
import sys
from typing import Iterable, Optional, Generator

import models
import visitors
from models import IModelElement, ElementKind
import cad_adapter
from .model_tree_builder import ModelElementTreeBuilder
from .building_registry import BuildingRegistry
from .building_storey_boundary_creator import BuildingStoreyBoundaryCreator

logger = logging.getLogger(__name__)


def _log_boundary_details(boundaries: list[models.BuildingStoreyBoundary]) -> None:
    """Log details about each storey boundary."""
    for b in boundaries:
        bz0, bz1 = b.z_range()
        logger.debug(
            f"Boundary {b.storey.building_name} - {b.storey.storey_name}: "
            f"z_range=({bz0:.3f}, {bz1:.3f}), height={b.height():.3f}"
        )


def _extend_topmost_storey(boundaries: list[models.BuildingStoreyBoundary]) -> None:
    """Extend the topmost storey boundary to infinite height."""
    top_most_storey = boundaries[-1]
    top_most_storey.top_frame = top_most_storey.top_frame.translated([0, 0, sys.float_info.max])
    logger.debug(
        f"Extended topmost storey {top_most_storey.storey.building_name} - "
        f"{top_most_storey.storey.storey_name} to infinite height."
    )


def _flatten_element_tree(element_nodes: list[models.IModelElement]) -> list[models.IModelElement]:
    """Flatten the element tree into a list containing parents and all children."""
    flattened: list[models.IModelElement] = []
    for element_node in element_nodes:
        flattened.append(element_node)
        if element_node.children:
            flattened.extend(element_node.children)
    return flattened


def element_id_valid(element_id: int) -> bool:
    return element_id > 0


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
        valid_elements = self.filter_valid_elements(element_ids)
        model_element_trees = self.build_model_element_tree_nodes(valid_elements)
        building_tree_nodes = self.map_model_element_trees_to_buildings(model_element_trees)

        for building_name, building in self._registry.items():
            self._process_building(building_name, building, building_tree_nodes)

    def _process_building(self,
                          building_name: str,
                          building: models.Building,
                          building_tree_nodes: dict[str, list[models.IModelElement]]
                          ) -> None:
        """Process a single building and assign its elements to storeys."""
        logger.info(f"Processing building: {building_name}")

        boundaries = self._create_and_validate_boundaries(building, building_name)
        if not boundaries:
            return

        building_element_nodes = building_tree_nodes.get(building_name)
        if not building_element_nodes:
            logger.warning(f"No building elements for building {building_name}")
            return

        to_assign = self._assign_elements_to_storeys(building_element_nodes, boundaries)
        self._batch_assign_to_cad(building_name, to_assign)

    @staticmethod
    def _create_and_validate_boundaries(building: models.Building,
                                        building_name: str
                                        ) -> Optional[list[models.BuildingStoreyBoundary]]:
        """Create storey boundaries for a building and extend the topmost storey to infinity."""
        boundaries = BuildingStoreyBoundaryCreator.from_building(building)
        if not boundaries:
            logger.warning(f"No boundaries for building {building_name}")
            return None

        _log_boundary_details(boundaries)
        _extend_topmost_storey(boundaries)
        return boundaries

    def _assign_elements_to_storeys(self,
                                    building_element_nodes: list[models.IModelElement],
                                    boundaries: list[models.BuildingStoreyBoundary]
                                    ) -> dict[str, list[int]]:
        """Assign elements to storeys based on vertical coverage."""
        to_assign: dict[str, list[int]] = {}
        all_elements = _flatten_element_tree(building_element_nodes)

        for building_element in all_elements:
            self._assign_single_element(building_element, boundaries, to_assign)

        return to_assign

    def _assign_single_element(self,
                               building_element: models.IModelElement,
                               boundaries: list[models.BuildingStoreyBoundary],
                               to_assign: dict[str, list[int]]
                               ) -> None:
        """Assign a single element to its appropriate storey."""
        visitor = visitors.VerticalCoverageAssignmentVisitor(self._coverage_threshold)
        storey_coverage = building_element.accept(visitor, boundaries)

        if not storey_coverage:
            logger.warning(
                f"Element {building_element.name} ({building_element.guid.value}) "
                f"not assigned to any storey"
            )
            return

        element_ids = self._collect_element_and_children_ids(building_element)
        to_assign.setdefault(storey_coverage.storey_name, []).extend(element_ids)

    def _collect_element_and_children_ids(self, building_element: models.IModelElement) -> list[int]:
        """Collect element ID and all its children's IDs.
        
        For OrphanParent nodes, only collect children IDs since the parent doesn't
        correspond to a real CAD element.
        """
        element_ids = []

        # OrphanParent doesn't have a real CAD element ID, only collect children
        if building_element.kind != ElementKind.ORPHAN_PARENT:
            element_id = self._cad_adapter.get_element_from_cadwork_guid(building_element.guid)
            if element_id_valid(element_id):  # Filter out invalid IDs
                element_ids.append(element_id)

        try:
            if children := building_element.children:
                for child in children:
                    child_id = self._cad_adapter.get_element_from_cadwork_guid(child.guid)
                    if element_id_valid(child_id):  # Filter out invalid IDs
                        element_ids.append(child_id)
        except NotImplementedError:
            # Leaf element, no children
            pass

        return element_ids

    def _batch_assign_to_cad(self, building_name: str, to_assign: dict[str, list[int]]) -> None:
        """Perform batch assignments to CAD system."""
        for storey_name, element_ids in to_assign.items():
            try:
                logger.info(f"Setting {len(element_ids)} elements to {building_name}/{storey_name}")
                self._cad_adapter.set_building_and_storey(element_ids, building_name, storey_name)
            except Exception as e:
                logger.exception(
                    f"Failed assigning {len(element_ids)} elements to "
                    f"{building_name}/{storey_name}: {e}"
                )

    def map_model_element_trees_to_buildings(self, model_element_trees: list[models.IModelElement]) -> dict[
        str, list[models.IModelElement]]:
        """Map each model element tree to its corresponding building name.
        
        For OrphanParent nodes (which don't have real CAD elements), we map each child
        individually to its building instead of the parent.
        """
        buildings_to_nodes: dict[str, list[models.IModelElement]] = {}
        logger.debug(f"Mapping {len(model_element_trees)} model element trees to buildings")

        for node in model_element_trees:
            logger.debug(f"Processing node: {node.name}, GUID: {node.guid}, Kind: {node.kind}")

            # Special handling for OrphanParent
            if node.kind == ElementKind.ORPHAN_PARENT:
                logger.debug(f"  -> OrphanParent detected, mapping {len(node.children)} children individually")
                for child in node.children:
                    child_element_id = self._cad_adapter.get_element_from_cadwork_guid(child.guid)
                    child_building_name = self._cad_adapter.get_building(child_element_id) or "UnassignedBuilding"
                    logger.debug(f"    -> Child {child.name} mapped to building: {child_building_name}")

                    orphan_wrapper = models.OrphanParent(
                        guid=node.guid,
                        name=node.name,
                        geometry=node.geometry,
                        children=[child]
                    )
                    buildings_to_nodes.setdefault(child_building_name, []).append(orphan_wrapper)
                continue

            # Normal handling for real CAD elements
            element_id: int = self._cad_adapter.get_element_from_cadwork_guid(node.guid)
            logger.debug(f"  -> element_id from GUID lookup: {element_id}")
            building_name: str = self._cad_adapter.get_building(element_id) or "UnassignedBuilding"
            logger.debug(f"  -> building_name: {building_name}")
            buildings_to_nodes.setdefault(building_name, []).append(node)

        logger.debug(f"Buildings mapped: {list(buildings_to_nodes.keys())}")
        return buildings_to_nodes

    def filter_valid_elements(self, element_ids: Iterable[int]) -> Generator[
        int, None, None]:
        """Filter out non-standard elements like nodes, lines, and dimensions.

        Args:
            element_ids: Iterable of element IDs to filter.
            adapter: An implementation of ICadAdapter for checking element types.

        Returns:
            Generator of valid element IDs.
        """
        valid_elements = (eid for eid in element_ids if
                          not self._cad_adapter.is_node(eid)
                          and not self._cad_adapter.is_line(eid)
                          and not self._cad_adapter.is_dimension(eid)
                          )
        return valid_elements

    def build_model_element_tree_nodes(self, element_ids: Iterable[int]) -> list[models.IModelElement]:
        """Build model element trees using the provided adapter.

        Args:
            element_ids: Iterable of element IDs to process.
            adapter: An implementation of ICadAdapter for accessing CAD data.

        Returns:
            List of root model elements in the tree.
        """
        tree_builder = ModelElementTreeBuilder(element_ids, self._cad_adapter)
        return tree_builder.build()
