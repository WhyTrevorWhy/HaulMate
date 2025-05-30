import logging
import Plugins.Map.data as data
import Plugins.Map.utils.math_helpers as mh
import Plugins.Map.route.planning as planning

plugin = None
traffic_module = None

def init(plugin_obj):
    """Initialize auto lane change module with plugin reference."""
    global plugin, traffic_module
    plugin = plugin_obj
    try:
        traffic_module = plugin.modules.Traffic
    except Exception as e:
        logging.error(f"Auto lane change failed to get Traffic module: {e}")
        traffic_module = None


def _vehicle_on_path(vehicle, path, threshold=4.0):
    for point in path:
        if mh.DistanceBetweenPoints((vehicle.position.x, vehicle.position.z), (point.x, point.z)) < threshold:
            return True
    return False


def PerformLaneChange():
    """Automatically perform lane changes ahead of intersections."""
    if plugin is None or traffic_module is None:
        return

    if len(data.route_plan) < 2:
        return

    current = data.route_plan[0]
    upcoming = data.route_plan[1]

    if current.lane_index == upcoming.lane_index:
        return

    next_point = upcoming.get_points()[0]
    dist = mh.DistanceBetweenPoints((data.truck_x, data.truck_z), (next_point.x, next_point.z))
    if dist > 100:
        return

    vehicles = traffic_module.run() or []
    path = data.prediction_points[:20]
    for vehicle in vehicles:
        if _vehicle_on_path(vehicle, path):
            logging.info("Auto lane change: vehicle detected, waiting for gap")
            plugin.globals.tags.lane_change_status = "waiting_for_gap"
            return

    logging.info(f"Auto lane change from {current.lane_index} to {upcoming.lane_index}")
    plugin.globals.tags.lane_change_status = "auto_executing"
    current.force_lane_change = True
    current.lane_index = upcoming.lane_index
    current.force_lane_change = False
    data.route_plan = [current]
