import math
import logging

from compas.geometry import Frame

import models


class BuildingStoreyBoundaryCreator:
    """Factory/service to create BuildingStoreyBoundary instances."""

    @staticmethod
    def from_frames(building_storey: models.BuildingStorey, bottom_frame: "Frame",
                    top_frame: "Frame") -> models.BuildingStoreyBoundary:
        BuildingStoreyBoundaryCreator._validate_frames(bottom_frame, top_frame)
        return models.BuildingStoreyBoundary(building_storey, bottom_frame, top_frame)

    @staticmethod
    def from_building(building: models.Building) -> list[models.BuildingStoreyBoundary]:
        storeys = building.storeys
        # frame low z is storey elevation frame top z is next storey elevation
        boundaries = []
        for i in range(len(storeys) - 1):
            bottom_storey = storeys[i]
            top_storey = storeys[i + 1]
            bottom_frame = Frame([0, 0, bottom_storey.elevation], [1, 0, 0], [0, 1, 0])
            top_frame = Frame([0, 0, top_storey.elevation], [1, 0, 0], [0, 1, 0])
            # identifier = f"{building.name}_{bottom_storey.storey_name}"
            try:
                boundary = BuildingStoreyBoundaryCreator.from_frames(bottom_storey,
                                                                     bottom_frame,
                                                                     top_frame)
                boundaries.append(boundary)
            except ValueError as e:
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Skipping invalid storey pair: {bottom_storey.storey_name} to {top_storey.storey_name} due to non-increasing elevations: {e}")
                continue

        return boundaries

    @staticmethod
    def _validate_frames(bottom_frame: "Frame", top_frame: "Frame") -> None:
        # Same XY and orientation on XY plane required; Z must increase
        if top_frame.point.z <= bottom_frame.point.z:
            raise ValueError("top_frame must be above bottom_frame (z_top > z_bottom)")
        is_close = lambda cl, cr: math.isclose(cl, cr, abs_tol=1e-5)
        # if (is_close(top_frame.point.x, bottom_frame.point.x)) or (
        #     is_close(topFrame.point.y, bottom_frame.point.y)
        # ):
        #     raise ValueError("Frames must be vertically aligned (same x,y)")
