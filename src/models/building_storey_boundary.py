from typing import Iterable, Tuple

import compas
from compas.geometry import Frame

from .spatial_element import Building, BuildingStorey


class BuildingStoreyBoundary:
    """Building storey boundary is defined by a bottom and top frame."""

    def __init__(self, building_storey: BuildingStorey, bottom_frame: Frame, top_frame: Frame):
        self._storey: BuildingStorey = building_storey
        self.bottom_frame = bottom_frame
        self.top_frame = top_frame

    @property
    def storey(self) -> BuildingStorey:
        return self._storey

    def height(self) -> float:
        """Height of the storey boundary."""
        return self.top_frame.point.z - self.bottom_frame.point.z

    def z_range(self) -> Tuple[float, float]:
        """Return (z_min, z_max) of the boundary in world Z."""
        return self.bottom_frame.point.z, self.top_frame.point.z

    def contains_bbox_fully(self, bbox_points: Iterable[compas.geometry.Point]) -> bool:  # Iterable[Iterable[float]]
        """
        Check if the entire axis-aligned bounding box (given as its 8 corner points)
        is inside the vertical extent of this storey boundary.
        """
        z_min, z_max = self._bbox_z_minmax(bbox_points)
        b_min, b_max = self.z_range()
        return z_min >= b_min and z_max <= b_max

    def contains_bbox_fraction(self, bbox_points: Iterable[compas.geometry.Point], fraction: float) -> bool:
        """
        Check if at least `fraction` (0..1) of the bbox vertical height is inside the storey boundary.

        The check is done along Z (since boundaries are defined by bottom/top frames at Z levels).
        """
        if not (0.0 <= fraction <= 1.0):
            raise ValueError("fraction must be between 0 and 1")

        z_min, z_max = self._bbox_z_minmax(bbox_points)
        if z_max <= z_min:
            return False

        b_min, b_max = self.z_range()

        # Overlap of [z_min, z_max] with [b_min, b_max]
        overlap_low = max(z_min, b_min)
        overlap_high = min(z_max, b_max)
        overlap = max(0.0, overlap_high - overlap_low)

        bbox_height = z_max - z_min
        covered = overlap / bbox_height
        return covered >= fraction

    @staticmethod
    def _bbox_z_minmax(points: Iterable[compas.geometry.Point]) -> Tuple[float, float]:
        zs = [p.z for p in points]
        return min(zs), max(zs)

    def __repr__(self) -> str:
        return (f"BuildingStoreyBoundary(storey_name={self._storey.storey_name}, "
                f"building_name={self._storey.building_name}, "
                f"bottom_frame={self.bottom_frame}, "
                f"top_frame={self.top_frame})")
