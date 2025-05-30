import Plugins.Map.utils.math_helpers as math_helpers
import Plugins.Map.route.driving as driving
import Plugins.Map.data as data
import Plugins.Map.classes as c


def GetPredictedPath(point_count: int | None = None) -> list[c.Position]:
    """Generate future path points based on the current route plan."""
    if point_count is None:
        point_count = data.prediction_point_count

    if len(data.route_plan) == 0:
        data.prediction_points = []
        return []

    points: list[c.Position] = []
    for section in data.route_plan:
        if len(points) >= point_count:
            break
        if section is None:
            continue
        section_points = section.get_points()
        for point in section_points:
            if len(points) >= point_count:
                break
            if len(points) == 0:
                points.append(point)
                continue
            distance = math_helpers.DistanceBetweenPoints(point.tuple(), points[-1].tuple())
            if distance >= driving.GetPointDistance(len(points), point_count):
                if distance <= 20 and point not in points:
                    points.append(point)
    data.prediction_points = points
    return points
