import math
import Plugins.Map.utils.math_helpers as math_helpers
import Plugins.Map.data as data
import Plugins.Map.classes as c


def GetPredictedPath(point_count: int | None = None) -> list[c.Position]:
    """Generate future path points from the full navigation list."""
    if point_count is None:
        point_count = data.prediction_point_count

    if len(data.navigation_points) == 0:
        data.prediction_points = []
        return []

    # Find the closest navigation point in front of the truck
    start_index = 0
    best_distance = math.inf
    for i, point in enumerate(data.navigation_points):
        dist = math_helpers.DistanceBetweenPoints((point.x, point.z), (data.truck_x, data.truck_z))
        if dist < best_distance and math_helpers.IsInFront((point.x, point.z), data.truck_rotation, (data.truck_x, data.truck_z)):
            best_distance = dist
            start_index = i

    points = data.navigation_points[start_index:start_index + point_count]
    data.prediction_points = points
    return points
