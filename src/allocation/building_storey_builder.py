import dataclasses
from typing import Iterable

import bim_controller
import models


def get_buildings() -> list[str]:
    """Get a list of all building IDs in the BIM data."""
    buildings = bim_controller.get_all_buildings()
    return buildings if buildings is not None else []


def get_building_for_element(element_id: int) -> str | None:
    """Get the building ID associated with an element, if any."""
    building_name = bim_controller.get_building(element_id)
    return building_name if building_name is not None else None


def get_storey_for_element(element_id: int) -> str | None:
    """Get the storey ID associated with an element, if any."""
    storey_name = bim_controller.get_storey(element_id)
    return storey_name if storey_name is not None else None


def get_building_storeys(building_name: str) -> list[str]:
    """Get a list of storeys for a given building."""
    storeys = bim_controller.get_all_storeys(building_name)
    return storeys if storeys is not None else []


def build_building_storey_hierarchy() -> dict[str, models.Building]:
    """Build a hierarchy of buildings and their storeys from the BIM data."""
    building_storey_hierarchy: dict[str, models.Building] = {}

    for building_name in get_buildings():
        storeys = set()
        for storey_name in get_building_storeys(building_name):  # TODO: refactor to wrapper function
            elevation = bim_controller.get_storey_height(building_name, storey_name)
            # if elevation is not None:
            storey = models.BuildingStorey(building_name=building_name, storey_name=storey_name, elevation=elevation)
            storeys.add(storey)

        building_storey_hierarchy[building_name] = models.Building(name=building_name, storeys=list(storeys))

    return building_storey_hierarchy
