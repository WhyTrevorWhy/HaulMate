from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import List, Tuple, Optional
import math

import Plugins.Map.data as data
from Plugins.Map.utils import math_helpers


@dataclass
class Prediction:
    """Container for prediction results."""
    future_points: List[Tuple[float, float]]
    curvature: Optional[float]
    next_stop_light_distance: Optional[float]
    vehicles_ahead: int
    lane_change: bool

    def dict(self) -> dict:
        """Return a serialisable dict representation."""
        return asdict(self)


class Predictor:
    """Simple route based predictor.

    This implementation is intentionally lightweight and is meant to provide
    a foundation for more sophisticated prediction logic.  It looks ahead
    along the current planned route and extracts basic information about the
    road ahead such as curvature, stop light proximity and lane changes.
    """

    def __init__(self, lookahead_distance: float = 200.0) -> None:
        self.lookahead_distance = lookahead_distance

    def update(self) -> Prediction:
        """Generate a prediction snapshot of the upcoming road."""
        points = self._collect_future_points(self.lookahead_distance)
        curvature = self._calculate_curvature(points)
        stop_light_distance = self._find_stop_light_distance(points)

        vehicles_ahead = 0
        if isinstance(data.external_data, dict):
            vehicles = data.external_data.get("vehicles")
            if isinstance(vehicles, list):
                vehicles_ahead = len(vehicles)

        lane_change = False
        if len(data.route_plan) >= 2:
            lane_change = data.route_plan[0].lane_index != data.route_plan[1].lane_index

        return Prediction(
            future_points=points,
            curvature=curvature,
            next_stop_light_distance=stop_light_distance,
            vehicles_ahead=vehicles_ahead,
            lane_change=lane_change,
        )

    def _collect_future_points(self, distance_limit: float) -> List[Tuple[float, float]]:
        """Collect upcoming lane points up to ``distance_limit`` metres."""
        collected: List[Tuple[float, float]] = []
        travelled = 0.0
        previous = (data.truck_x, data.truck_z)

        for section in data.route_plan:
            lane_points = section.lane_points
            for point in lane_points:
                current = (point.x, point.z)
                travelled += math_helpers.DistanceBetweenPoints(previous, current)
                collected.append(current)
                previous = current
                if travelled >= distance_limit:
                    return collected
        return collected

    def _calculate_curvature(self, points: List[Tuple[float, float]]) -> Optional[float]:
        """Estimate average curvature for a list of points."""
        if len(points) < 3:
            return None

        angles: List[float] = []
        for i in range(1, len(points)):
            x0, y0 = points[i - 1]
            x1, y1 = points[i]
            angles.append(math.atan2(y1 - y0, x1 - x0))

        changes = [abs(angles[i] - angles[i - 1]) for i in range(1, len(angles))]
        if not changes:
            return None
        return sum(changes) / len(changes)

    def _find_stop_light_distance(self, points: List[Tuple[float, float]]) -> Optional[float]:
        """Return distance to the nearest stop light along the upcoming path."""
        min_distance: Optional[float] = None
        for prefab in getattr(data, "current_sector_prefabs", []):
            token = str(getattr(prefab, "token", "")).lower()
            if "traffic" in token or "semaphore" in token:
                prefab_pos = (getattr(prefab, "x", 0.0), getattr(prefab, "y", 0.0))
                for point in points:
                    distance = math_helpers.DistanceBetweenPoints(prefab_pos, point)
                    if min_distance is None or distance < min_distance:
                        min_distance = distance
        return min_distance
