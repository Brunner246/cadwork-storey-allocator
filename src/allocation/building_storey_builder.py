import dataclasses
from typing import Iterable

import models
from cad_adapter import ICadAdapter


class BuildingStoreyHierarchyBuilder:
    """Builder for creating a hierarchy of buildings and their storeys from BIM data."""

    @dataclasses.dataclass
    class Config:
        adapter: ICadAdapter  # type: ignore

    def __init__(self, config: Config) -> None:
        self.config = config

    def build(self) -> dict[str, models.Building]:
        """Build a hierarchy of buildings and their storeys from the BIM data."""
        building_storey_hierarchy: dict[str, models.Building] = {}

        for building_name in self.config.adapter.get_buildings():
            storeys = set()
            for storey_name in self.config.adapter.get_building_storeys(building_name):
                # get_building_storeys(building_name):  # TODO: refactor to wrapper function
                elevation = self.config.adapter.get_storey_elevation(building_name, storey_name)
                # if elevation is not None:
                storey = models.BuildingStorey(building_name=building_name, storey_name=storey_name,
                                               elevation=elevation)
                storeys.add(storey)

            building_storey_hierarchy[building_name] = models.Building(name=building_name, storeys=list(storeys))

        return building_storey_hierarchy

# def build_building_storey_hierarchy() -> dict[str, models.Building]:
#     """Build a hierarchy of buildings and their storeys from the BIM data."""
#     building_storey_hierarchy: dict[str, models.Building] = {}
#
#     for building_name in get_buildings_names():
#         storeys = set()
#         for storey_name in get_building_storeys(building_name):  # TODO: refactor to wrapper function
#             elevation = bim_controller.get_storey_height(building_name, storey_name)
#             # if elevation is not None:
#             storey = models.BuildingStorey(building_name=building_name, storey_name=storey_name, elevation=elevation)
#             storeys.add(storey)
#
#         building_storey_hierarchy[building_name] = models.Building(name=building_name, storeys=list(storeys))
#
#     return building_storey_hierarchy
