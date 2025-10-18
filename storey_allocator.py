import logging
import os
import sys
from pathlib import Path

import element_controller

base_dir = Path(__file__).absolute().parent
src_dir = base_dir / "src"
dep_dir = base_dir / ".venv" / "Lib" / "site-packages"

for p in {str(src_dir), str(base_dir), str(dep_dir)}:
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

[print(path) for path in sys.path]  # if os.path.isdir(path)

import allocation
import models

models.setup_colored_logging(logging.DEBUG)

logger = logging.getLogger(__name__)


# logger.info("Hello colored world")
#
# logging.basicConfig(level=logging.DEBUG,
#                     format="%(asctime)s [%(levelname)s] %(message)s",
#                     datefmt="%Y-%m-%d %H:%M:%S")
# logger = logging.getLogger(__name__)


def main():
    logger.info("Starting building storey allocation example")

    # TODO: Refactor following to a function SOLID
    registry = allocation.BuildingRegistry()

    # registry.register("MyBuilding")(make_boundaries())
    building_nodes = allocation.build_building_storey_hierarchy()
    for b_name, building in building_nodes.items():
        logger.info(f"Building {b_name}")

        boundaries = allocation.BuildingStoreyBoundaryCreator.from_building(building)
        registry.upsert(building)

        for b in boundaries:
            logger.info(f"Boundary: {id(b)}, Bottom Z: {b.bottom_frame.point.z}, Top Z: {b.top_frame.point.z}")

        logger.info(f"Building: {b_name}")
        for storey in building.storeys:
            logger.info(f"  Storey: {storey.storey_name}, Elevation: {storey.elevation}")

    [logger.info(f"Registered {key}") for key in registry.names()]


    element_ids = element_controller.get_all_identifiable_element_ids()
    storey_assigner = allocation.StoreyAssignmentService(registry, coverage_threshold=0.6)
    storey_assigner.assign_elements(element_ids)


if __name__ == "__main__":
    main()
