import math

from compas.geometry import Frame

from allocation.building_storey_builder import Building
from models.building_storey_boundary import BuildingStoreyBoundary


class BuildingStoreyBoundaryCreator:
    """Factory/service to create BuildingStoreyBoundary instances."""

    @staticmethod
    def from_frames(identifier: str, bottom_frame: "Frame", top_frame: "Frame") -> BuildingStoreyBoundary:
        BuildingStoreyBoundaryCreator._validate_frames(bottom_frame, top_frame)
        return BuildingStoreyBoundary(identifier, bottom_frame, top_frame)

    @staticmethod
    def from_building(building: Building) -> list[BuildingStoreyBoundary]:
        storeys = building.storeys
        # frame low z is storey elevation frame top z is next storey elevation
        boundaries = []
        for i in range(len(storeys) - 1):
            bottom_storey = storeys[i]
            top_storey = storeys[i + 1]
            bottom_frame = Frame([0, 0, bottom_storey.elevation], [1, 0, 0], [0, 1, 0])
            top_frame = Frame([0, 0, top_storey.elevation], [1, 0, 0], [0, 1, 0])
            identifier = f"{building.name}_{bottom_storey.storey_name}"
            boundary = BuildingStoreyBoundaryCreator.from_frames(identifier, bottom_frame, top_frame)
            boundaries.append(boundary)

        return boundaries

    @staticmethod
    def _validate_frames(bottom_frame: "Frame", top_frame: "Frame") -> None:
        # Same XY and orientation on XY plane required; Z must increase
        if top_frame.point.z <= bottom_frame.point.z:
            raise ValueError("top_frame must be above bottom_frame (z_top > z_bottom)")
        is_close = lambda cl, cr: math.isclose(cl, cr, abs_tol=1e-5)
        # if (is_close(top_frame.point.x, bottom_frame.point.x)) or (
        #     is_close(top_frame.point.y, bottom_frame.point.y)
        # ):
        #     raise ValueError("Frames must be vertically aligned (same x,y)")
