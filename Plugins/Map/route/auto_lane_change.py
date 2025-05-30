import logging
import math

import Plugins.Map.data as data
import Plugins.Map.route.planning as planning

plugin = None

def init(map_plugin):
    """Initialize auto lane change module with main plugin"""
    global plugin
    plugin = map_plugin
    logging.info("Auto lane change initialized")

def _vehicles_in_predicted_path(threshold: float = 6.0) -> bool:
    """Return True if a vehicle is within the prediction path"""
    if plugin is None:
        return False
    traffic = getattr(plugin.modules, "Traffic", None)
    if traffic is None:
        return False
    vehicles = traffic.run()
    if not vehicles:
        return False
    for vehicle in vehicles:
        vx = vehicle.position.x
        vz = vehicle.position.z
        for point in data.prediction_points:
            dist = math.sqrt((vx - point.x) ** 2 + (vz - point.z) ** 2)
            if dist < threshold:
                logging.debug(
                    f"Vehicle {vehicle.id} detected {dist:.1f}m from predicted path"
                )
                return True
    return False

def PerformLaneChange():
    """Automatically execute planned lane changes if safe"""
    if len(data.route_plan) < 2:
        return
    current = data.route_plan[0]
    next_section = data.route_plan[1]
    if current.lane_index == next_section.lane_index:
        return
    distance_left = current.distance_left()
    required = max(
        data.minimum_lane_change_distance,
        data.truck_speed * data.lane_change_distance_per_kph,
    )
    if distance_left < required:
        return
    if _vehicles_in_predicted_path():
        data.plugin.globals.tags.lane_change_status = "waiting_traffic"
        return
    logging.info(
        f"Auto lane change from {current.lane_index} to {next_section.lane_index}"
    )
    current.force_lane_change = True
    current.lane_index = next_section.lane_index
    current.force_lane_change = False
    planning.ResetState()
