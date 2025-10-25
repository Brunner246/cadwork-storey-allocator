import logging
import os
import sys
from pathlib import Path

base_dir = Path(__file__).absolute().parent
src_dir = base_dir / "src"
dep_dir = base_dir / ".venv" / "Lib" / "site-packages"

for p in {str(src_dir), str(base_dir), str(dep_dir)}:
    if os.path.isdir(p) and p not in sys.path:
        sys.path.insert(0, p)

[print(path) for path in sys.path]  # if os.path.isdir(path)

import allocation
import models
from models.events import events
from cad_adapter.cad_adapter import ICadAdapter, CadworkAdapter

models.setup_colored_logging(logging.DEBUG)

logger = logging.getLogger(__name__)


@models.decorators.timeit("Storey allocation and event publishing")
def run_allocation_and_publish_events():
    """Run the storey allocation logic synchronously and publish events to the global publisher.
    """
    try:
        registry = allocation.BuildingRegistry()

        cad_adapter: ICadAdapter = CadworkAdapter()
        builder_conf = allocation.BuildingStoreyHierarchyBuilder.Config(cad_adapter)
        building_storey_builder = allocation.BuildingStoreyHierarchyBuilder(config=builder_conf)
        building_nodes = building_storey_builder.build()
        for b_name, building in building_nodes.items():
            logger.info(f"Building {b_name}")

            boundaries = allocation.BuildingStoreyBoundaryCreator.from_building(building)
            registry.upsert(building)

            for boundary in boundaries:
                logger.info(
                    f"Boundary: {id(boundary)}, Bottom Z: {boundary.bottom_frame.point.z}, Top Z: {boundary.top_frame.point.z}"
                )

            logger.info(f"Building: {b_name}")
            for storey in building.storeys:
                logger.info(f"  Storey: {storey.storey_name}, Elevation: {storey.elevation}")

        [logger.info(f"Registered {key}") for key in registry.names()]

        storey_assigner = allocation.StoreyAssignmentService(registry, cad_adapter, coverage_threshold=0.6)

        element_ids = cad_adapter.get_active_identifiable_element_ids()  # .get_all_element_ids()
        storey_assigner.assign_elements(element_ids)
        events.publisher.publish(events.SuccessEvent("Storey assignment completed for all elements"))
    except Exception as exc:
        logger.exception("Error during processing")
        events.publisher.publish(events.ErrorEvent(str(exc)))


def _print_events_to_console():
    # fallback when PyQt5 isn't available or when running headless
    print("\nStorey allocation events:\n")
    for ev in events.publisher.events:
        if isinstance(ev, events.ErrorEvent):
            print(f"ERROR: {ev.message}")
        elif isinstance(ev, events.SuccessEvent):
            print(f"SUCCESS: {ev.message}")
        else:
            print(f"EVENT: {ev.message}")


def main():
    logger.info("Starting building storey allocation example")

    DEBUG_MODE = True
    if debug := DEBUG_MODE:
        logger.info(f"Debug mode enabled {debug=}, connecting to PyCharm debugger...")
        try:
            import pydevd_pycharm
            pydevd_pycharm.settrace('localhost', port=9000, stdout_to_server=True, stderr_to_server=True)
        except ModuleNotFoundError as exception:
            logger.exception(f"Failed to connect to PyCharm debugger {exception=}")

    # Run allocation logic synchronously (no threads). This will populate events.publisher.events
    run_allocation_and_publish_events()
    _print_events_to_console()


if __name__ == "__main__":
    main()
