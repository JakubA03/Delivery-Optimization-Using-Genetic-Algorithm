"""Sample data and helpers for the delivery optimization problem."""

from __future__ import annotations

import math
from typing import Iterable, List, Sequence, Tuple

Point = Tuple[float, float]

# Point 0 is the depot. Remaining points are customers/locations.
DEFAULT_POINTS: List[Point] = [
    (0.0, 0.0),   # Depot
    (1.0, 5.0),
    (2.5, 1.5),
    (4.5, 4.0),
    (5.0, 1.0),
    (6.5, 3.0),
    (7.0, 6.5),
    (8.0, 2.5),
    (9.5, 5.5),
    (3.5, 7.0),
    (6.0, 8.0),
    (9.0, 0.5),
]


def build_distance_matrix(points: Sequence[Point]) -> List[List[float]]:
    """Return a symmetric distance matrix using Euclidean distances."""
    matrix: List[List[float]] = []
    for i, (x1, y1) in enumerate(points):
        row: List[float] = []
        for j, (x2, y2) in enumerate(points):
            dx = x1 - x2
            dy = y1 - y2
            row.append(math.hypot(dx, dy))
        matrix.append(row)
    return matrix


def route_distance(
    permutation: Iterable[int], distance_matrix: Sequence[Sequence[float]]
) -> float:
    """Calculate the total distance of a route starting/ending at the depot."""
    depot = 0
    total = 0.0
    current = depot
    for nxt in permutation:
        total += distance_matrix[current][nxt]
        current = nxt
    total += distance_matrix[current][depot]
    return total
