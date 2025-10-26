import logging
from typing import Optional

import models
from visitors.element_assignment_visitors import IElementAssignmentVisitor

logger = logging.getLogger(__name__)


class VerticalCoverageAssignmentVisitor(IElementAssignmentVisitor):
    """Assigns elements based on vertical coverage of their bounding box."""

    def __init__(self, coverage_threshold: float):
        self._coverage_threshold = coverage_threshold

    def visit_wall(self, wall: models.Wall, boundaries: list[models.BuildingStoreyBoundary]) -> Optional[
        models.StoreyCoverage]:
        return self._assign_by_vertical_coverage(wall, boundaries)

    def visit_slab(self, slab: models.Slab, boundaries: list[models.BuildingStoreyBoundary]) -> Optional[
        models.StoreyCoverage]:
        # Slabs might use centroid Z instead of coverage
        return self._assign_by_centroid(slab, boundaries)

    def visit_roof(self, roof: models.Roof, boundaries: list[models.BuildingStoreyBoundary]) -> Optional[
        models.StoreyCoverage]:
        # Roofs might always go to top storey
        return self._assign_to_top_storey(roof, boundaries)

    def visit_container(self, container: models.Container, boundaries: list[models.BuildingStoreyBoundary]) -> Optional[
        models.StoreyCoverage]:
        # Containers might not be assigned
        return None

    @models.decorators.log_calls
    def visit_leaf(self, leaf: models.ModelLeafElement, boundaries: list[models.BuildingStoreyBoundary]) -> Optional[
        models.StoreyCoverage]:
        # Generic fallback
        return self._assign_by_vertical_coverage(leaf, boundaries)

    def _assign_by_vertical_coverage(self, element: models.IModelElement,
                                     boundaries: list[models.BuildingStoreyBoundary]) -> Optional[
        models.StoreyCoverage]:
        bbox_points = element.geometry.bbx().to_list()
        best_storey: models.BuildingStorey | None = None
        best_coverage: float = 0.0

        for boundary in boundaries:
            coverage = self._vertical_coverage(boundary, bbox_points)
            if coverage > best_coverage:
                best_storey = boundary.storey
                best_coverage = coverage

        if best_coverage >= self._coverage_threshold and best_storey is not None:
            return models.StoreyCoverage(building_name=best_storey.building_name,
                                         storey_name=best_storey.storey_name,
                                         coverage=best_coverage)  # best_storey, best_coverage
        return None

    def visit_orphan(self, orphan: models.OrphanParent, boundaries: list[models.BuildingStoreyBoundary]) -> Optional[
        models.StoreyCoverage]:
        return self._assign_by_vertical_coverage(orphan, boundaries)

    def _assign_by_centroid(self, element: models.IModelElement,
                            boundaries: list[models.BuildingStoreyBoundary]) -> Optional[models.StoreyCoverage]:
        centroid = element.geometry.bbx().centroid()
        centroid_z = centroid.z
        best_storey: models.BuildingStorey | None = None
        best_coverage: float = 0.0

        for boundary in boundaries:
            b_min, b_max = boundary.z_range()
            # For a point: coverage is 1.0 if the centroid Z lies within the storey range, else 0.0
            coverage = 1.0 if (b_min <= centroid_z <= b_max) else 0.0
            if coverage > best_coverage:
                best_storey = boundary.storey
                best_coverage = coverage

        if best_coverage >= self._coverage_threshold and best_storey is not None:
            return models.StoreyCoverage(building_name=best_storey.building_name,
                                         storey_name=best_storey.storey_name,
                                         coverage=best_coverage)
        return None

    def _assign_to_top_storey(self, element: models.IModelElement, boundaries: list[models.BuildingStoreyBoundary]) -> \
            Optional[models.StoreyCoverage]:
        # Implementation for top storey assignment
        pass

    @staticmethod
    def _vertical_coverage(boundary, bbox_points) -> float:
        # bbox_points can be either Point objects or list[float] depending on source
        # Normalize to get z coordinates
        zs = []
        for p in bbox_points:
            if hasattr(p, 'z'):
                zs.append(p.z)
            elif isinstance(p, (list, tuple)) and len(p) >= 3:
                zs.append(p[2])
            else:
                raise TypeError(f"Expected Point or list/tuple with 3 elements, got {type(p)}")
        
        z_min, z_max = min(zs), max(zs)
        if z_max <= z_min:
            return 0.0

        b_min, b_max = boundary.z_range()
        overlap_low = max(z_min, b_min)
        overlap_high = min(z_max, b_max)
        overlap = max(0.0, overlap_high - overlap_low)
        return overlap / (z_max - z_min)
