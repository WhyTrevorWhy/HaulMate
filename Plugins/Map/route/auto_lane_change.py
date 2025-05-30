import logging
import Plugins.Map.data as data
import Plugins.Map.route.prediction as prediction
import Plugins.Map.utils.math_helpers as math_helpers
import Plugins.Map.classes as c

traffic_module = None


def init(plugin):
    """Initialize auto lane change module with references to other modules."""
    global traffic_module
    traffic_module = plugin.modules.Traffic
    logging.info("Auto lane change module initialized")


def _vehicles_in_path(points: list[c.Position], distance: float = 15) -> bool:
    """Return True if any traffic vehicle is within `distance` of a point."""
    if traffic_module is None:
        return False
    try:
        vehicles = traffic_module.run()
    except Exception:
        logging.exception("Failed to read traffic data")
        return False
    if not vehicles:
        return False
    for vehicle in vehicles:
        pos = (vehicle.position.x, vehicle.position.z)
        for point in points:
            if math_helpers.DistanceBetweenPoints(pos, (point.x, point.z)) < distance:
                return True
    return False


def PerformLaneChange() -> None:
    """Automatically perform lane changes when safe."""
    if not data.calculate_steering or len(data.route_plan) < 2:
        return

    current = data.route_plan[0]
    next_section = data.route_plan[1]

    if current.is_lane_changing:
        return

    if current.lane_index == next_section.lane_index:
        return

    distance_left = current.distance_left()
    required = current.get_planned_lane_change_distance(
        lane_count=abs(next_section.lane_index - current.lane_index)
    )

    if distance_left < required:
        return

    points = prediction.GetPredictedPath()
    if _vehicles_in_path(points):
        logging.info("Auto lane change blocked by traffic, slowing down")
        try:
            data.controller.brake = 1
            data.controller.throttle = 0
        except Exception:
            logging.exception("Failed to issue stop commands")
        return

    logging.info(
        "Auto lane change from %s to %s", current.lane_index, next_section.lane_index
    )
    current.target_lanes = [next_section.lane_index]
