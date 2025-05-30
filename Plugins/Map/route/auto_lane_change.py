import Plugins.Map.data as data
import Plugins.Map.route.prediction as prediction
import Plugins.Map.utils.math_helpers as math_helpers
import Plugins.Map.classes as c
import logging


def _get_vehicles() -> list:
    """Fetch vehicles from Traffic module if available."""
    vehicles = []
    try:
        vehicles = data.plugin.modules.Traffic.run()
        if vehicles is None:
            vehicles = []
    except Exception as e:
        logging.debug(f"AutoLaneChange: could not fetch vehicles: {e}")
    return vehicles


def _path_is_clear(points: list[c.Position], vehicles: list, radius: float = 5.0) -> bool:
    """Return True if no vehicle is within radius of any point."""
    for vehicle in vehicles:
        for point in points:
            d = math_helpers.DistanceBetweenPoints(
                (vehicle.position.x, vehicle.position.z),
                (point.x, point.z),
            )
            if d < radius:
                return False
    return True


def PerformLaneChange():
    """Automatically perform lane changes based on predicted path."""
    if len(data.route_plan) < 2:
        return

    current = data.route_plan[0]
    next_section = data.route_plan[1]

    if current.is_lane_changing or type(current.items[0].item) != c.Road:
        return

    if next_section.lane_index == current.lane_index:
        return

    next_point = next_section.get_points()[0]
    distance_to_next = math_helpers.DistanceBetweenPoints(
        (data.truck_x, data.truck_z), (next_point.x, next_point.z)
    )

    planned_distance = current.get_planned_lane_change_distance()
    if distance_to_next > planned_distance + 20:
        return

    points = prediction.GetPredictedPath()[:20]
    vehicles = _get_vehicles()
    if not _path_is_clear(points, vehicles):
        logging.info("AutoLaneChange: traffic detected, slowing down")
        try:
            data.controller.aforward = 0.0
            data.controller.abackward = 1.0
        except Exception as e:
            logging.debug(f"AutoLaneChange: failed to brake - {e}")
        return

    logging.info(
        f"AutoLaneChange: changing lane {current.lane_index} -> {next_section.lane_index}"
    )
    current.force_lane_change = True
    current.lane_index = next_section.lane_index
    current.force_lane_change = False
    data.route_plan = [current] + data.route_plan[1:]

