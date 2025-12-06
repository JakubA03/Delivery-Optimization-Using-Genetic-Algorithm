"""Plotting helpers for delivery routes and GA progress."""

from __future__ import annotations

from typing import Iterable, List, Sequence

import matplotlib.pyplot as plt

from .data import Point


def plot_route(
    points: Sequence[Point],
    permutation: Iterable[int],
    distance: float,
    show: bool = True,
    save_path: str | None = None,
) -> None:
    """Plot the depot, delivery points, and the chosen route."""
    depot = points[0]
    route: List[int] = [0, *permutation, 0]
    xs = [points[i][0] for i in route]
    ys = [points[i][1] for i in route]

    plt.figure(figsize=(8, 6))
    plt.plot(xs, ys, "-o", lw=2, color="#1f78b4")
    plt.scatter(depot[0], depot[1], color="#e31a1c", zorder=5, label="Depot")
    for idx, (x, y) in enumerate(points[1:], start=1):
        plt.scatter(x, y, color="#33a02c", zorder=4)
        plt.text(x + 0.05, y + 0.05, str(idx), fontsize=9)

    plt.title(f"Najlepsza trasa (długość: {distance:.2f})")
    plt.xlabel("X")
    plt.ylabel("Y")
    plt.legend()
    plt.grid(True, alpha=0.3)
    if save_path:
        plt.savefig(save_path, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close()


def plot_history(
    best_history: Sequence[float],
    avg_history: Sequence[float],
    show: bool = True,
    save_path: str | None = None,
) -> None:
    """Plot best and average distances across generations."""
    generations = range(len(best_history))
    plt.figure(figsize=(8, 4))
    plt.plot(generations, best_history, label="Najlepsza trasa", color="#1b9e77")
    plt.plot(generations, avg_history, label="Średnia populacji", color="#d95f02")
    plt.xlabel("Pokolenie")
    plt.ylabel("Długość trasy")
    plt.title("Postęp algorytmu genetycznego")
    plt.legend()
    plt.grid(True, alpha=0.3)
    if save_path:
        plt.savefig(save_path, bbox_inches="tight")
    if show:
        plt.show()
    else:
        plt.close()
