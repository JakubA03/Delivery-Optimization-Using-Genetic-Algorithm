"""Genetic algorithm for optimizing delivery routes."""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Sequence, Tuple

from .data import route_distance


@dataclass
class GAConfig:
    population_size: int | None = None
    elite_size: int = 2
    mutation_rate: float = 0.05
    generations: int = 400
    tournament_size: int = 5
    seed: int | None = 42


@dataclass
class GeneticAlgorithmResult:
    best_route: List[int]
    best_distance: float
    best_per_generation: List[float]
    avg_per_generation: List[float]


class GeneticRouteOptimizer:
    """Optimize delivery routes (TSP-like) using a genetic algorithm."""

    def __init__(
        self,
        distance_matrix: Sequence[Sequence[float]],
        config: GAConfig | None = None,
    ) -> None:
        self.distance_matrix = distance_matrix
        self.num_locations = len(distance_matrix)
        self.customers = list(range(1, self.num_locations))
        self.config = config or GAConfig()
        self.population_size = self._resolve_population_size()
        if self.config.seed is not None:
            random.seed(self.config.seed)

    # --- Core public API -------------------------------------------------
    def run(self) -> GeneticAlgorithmResult:
        population = self._initial_population()
        fitnesses = [self._fitness(individual) for individual in population]

        best_per_gen: List[float] = []
        avg_per_gen: List[float] = []

        for _ in range(self.config.generations):
            best_per_gen.append(min(fitnesses))
            avg_per_gen.append(sum(fitnesses) / len(fitnesses))

            population = self._next_generation(population, fitnesses)
            fitnesses = [self._fitness(individual) for individual in population]

        # Capture final generation stats
        best_idx = min(range(len(fitnesses)), key=lambda i: fitnesses[i])
        best_route = population[best_idx]
        best_distance = fitnesses[best_idx]
        best_per_gen.append(best_distance)
        avg_per_gen.append(sum(fitnesses) / len(fitnesses))

        return GeneticAlgorithmResult(
            best_route=best_route,
            best_distance=best_distance,
            best_per_generation=best_per_gen,
            avg_per_generation=avg_per_gen,
        )

    # --- GA mechanics ----------------------------------------------------
    def _initial_population(self) -> List[List[int]]:
        """Create the initial population using random permutations."""
        return [
            random.sample(self.customers, len(self.customers))
            for _ in range(self.population_size)
        ]

    def _fitness(self, individual: Sequence[int]) -> float:
        """Lower distance is better."""
        return route_distance(individual, self.distance_matrix)

    def _select_parent(self, population: Sequence[List[int]], fitnesses: Sequence[float]) -> List[int]:
        """Tournament selection."""
        participants = random.sample(range(len(population)), self.config.tournament_size)
        winner_idx = min(participants, key=lambda idx: fitnesses[idx])
        return population[winner_idx]

    def _order_crossover(self, parent_a: Sequence[int], parent_b: Sequence[int]) -> List[int]:
        """Order crossover (OX) maintains valid permutations."""
        size = len(parent_a)
        start, end = sorted(random.sample(range(size), 2))

        child = [None] * size  # type: ignore[list-item]
        child[start:end] = parent_a[start:end]

        pos = end
        for gene in parent_b:
            if gene not in child:
                if pos == size:
                    pos = 0
                child[pos] = gene
                pos += 1

        # mypy cannot infer the None elimination here
        return [g for g in child if g is not None]

    def _mutate(self, individual: List[int]) -> None:
        """Swap mutation in-place."""
        if random.random() < self.config.mutation_rate:
            a, b = random.sample(range(len(individual)), 2)
            individual[a], individual[b] = individual[b], individual[a]

    def _next_generation(
        self, population: List[List[int]], fitnesses: List[float]
    ) -> List[List[int]]:
        # Preserve elites
        sorted_indices = sorted(range(len(population)), key=lambda i: fitnesses[i])
        elites = [population[i][:] for i in sorted_indices[: self.config.elite_size]]

        children: List[List[int]] = elites
        while len(children) < self.population_size:
            parent1 = self._select_parent(population, fitnesses)
            parent2 = self._select_parent(population, fitnesses)
            child = self._order_crossover(parent1, parent2)
            self._mutate(child)
            children.append(child)
        return children

    def _resolve_population_size(self) -> int:
        """Allow dynamic population sizing when user passes None or <=0."""
        if self.config.population_size and self.config.population_size > 0:
            return self.config.population_size

        # Heuristic: scale with number of customers, cap to keep runtime sane.
        auto_size = min(max(6 * len(self.customers), 40), 500)
        self.config.population_size = auto_size
        return auto_size
