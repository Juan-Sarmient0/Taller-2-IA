from collections import deque
import json
from pathlib import Path
import random

from optimization.result import Configuration


Position = tuple[int, int]


class SmartGridOptimizationProblem:
    """Problema de ubicar exactamente k módulos en sitios candidatos."""

    def __init__(self, layout_path: str | Path) -> None:
        path = Path(layout_path)
        data = json.loads(path.read_text(encoding="utf-8"))
        self.name = str(data.get("name", path.stem))
        self.grid = tuple(str(row) for row in data["grid"])
        if not self.grid or len({len(row) for row in self.grid}) != 1:
            raise ValueError("El grid debe ser rectangular y no vacío")

        self.height = len(self.grid)
        self.width = len(self.grid[0])
        self.candidates = tuple(self._positions("N"))
        self.critical_nodes = tuple(self._positions("C"))
        self.module_count = int(data["modules"])
        self.coverage_radius = int(data.get("coverage_radius", 4))
        self.redundancy_distance = int(data.get("redundancy_distance", 2))
        self.redundancy_penalty = float(data.get("redundancy_penalty", 2.0))

        weights = data.get("critical_weights", [1] * len(self.critical_nodes))
        risks = data.get("candidate_risks", [0] * len(self.candidates))
        if len(weights) != len(self.critical_nodes):
            raise ValueError("critical_weights debe tener un valor por nodo C")
        if len(risks) != len(self.candidates):
            raise ValueError("candidate_risks debe tener un valor por sitio N")
        if not 0 < self.module_count <= len(self.candidates):
            raise ValueError("modules debe estar entre 1 y el número de sitios N")

        self.critical_weights = tuple(float(value) for value in weights)
        self.candidate_risks = tuple(float(value) for value in risks)
        self._distances: dict[tuple[Position, Position], int | float] = {}
        relevant = self.candidates + self.critical_nodes
        for start in relevant:
            found = self._bfs_distances(start)
            for goal in relevant:
                self._distances[(start, goal)] = found.get(goal, float("inf"))

    def _positions(self, symbol: str) -> list[Position]:
        return [
            (row, col)
            for row, line in enumerate(self.grid)
            for col, value in enumerate(line)
            if value == symbol
        ]

    def _bfs_distances(self, start: Position) -> dict[Position, int]:
        queue: deque[Position] = deque([start])
        distances = {start: 0}
        while queue:
            row, col = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (row + dr, col + dc)
                if not self.is_open(nxt) or nxt in distances:
                    continue
                distances[nxt] = distances[(row, col)] + 1
                queue.append(nxt)
        return distances

    def is_open(self, position: Position) -> bool:
        row, col = position
        return 0 <= row < self.height and 0 <= col < self.width and self.grid[row][col] != "%"

    def distance(self, first: Position, second: Position) -> int | float:
        return self._distances.get((first, second), float("inf"))

    def is_valid(self, configuration: Configuration) -> bool:
        return (
            len(configuration) == len(self.candidates)
            and all(bit in (0, 1) for bit in configuration)
            and sum(configuration) == self.module_count
        )

    def random_configuration(self, rng: random.Random) -> Configuration:
        selected = set(rng.sample(range(len(self.candidates)), self.module_count))
        return tuple(1 if index in selected else 0 for index in range(len(self.candidates)))

    def neighbors(self, configuration: Configuration) -> list[Configuration]:
        if not self.is_valid(configuration):
            raise ValueError("La configuración debe ser válida")
        active = [index for index, bit in enumerate(configuration) if bit]
        inactive = [index for index, bit in enumerate(configuration) if not bit]
        result: list[Configuration] = []
        for remove in active:
            for add in inactive:
                child = list(configuration)
                child[remove] = 0
                child[add] = 1
                result.append(tuple(child))
        return result

    def repair_configuration(self, configuration: Configuration, rng: random.Random) -> Configuration:
        bits = [1 if value else 0 for value in configuration[: len(self.candidates)]]
        bits.extend([0] * (len(self.candidates) - len(bits)))
        active = [index for index, bit in enumerate(bits) if bit]
        inactive = [index for index, bit in enumerate(bits) if not bit]
        while len(active) > self.module_count:
            index = rng.choice(active)
            bits[index] = 0
            active.remove(index)
            inactive.append(index)
        while len(active) < self.module_count:
            index = rng.choice(inactive)
            bits[index] = 1
            inactive.remove(index)
            active.append(index)
        return tuple(bits)

    def initial_population(self, size: int, rng: random.Random) -> list[Configuration]:
        if size < 2:
            raise ValueError("La población debe tener al menos dos individuos")
        return [self.random_configuration(rng) for _ in range(size)]

    def tournament_select(
        self,
        population: list[Configuration],
        scores: list[float],
        rng: random.Random,
        tournament_size: int = 3,
    ) -> Configuration:
        count = min(tournament_size, len(population))
        indices = rng.sample(range(len(population)), count)
        winner = max(indices, key=lambda index: scores[index])
        return population[winner]

    def score_components(self, configuration: Configuration) -> tuple[float, float, float]:
        """Retorna cobertura, redundancia y exposición sin combinarlas."""
        if not self.is_valid(configuration):
            return float("-inf"), 0.0, 0.0
        selected = [index for index, bit in enumerate(configuration) if bit]
        coverage = 0.0
        for critical, weight in zip(self.critical_nodes, self.critical_weights):
            nearest = min(self.distance(self.candidates[index], critical) for index in selected)
            if nearest <= self.coverage_radius:
                coverage += weight * (self.coverage_radius + 1 - nearest)

        redundancy = 0.0
        for offset, first_index in enumerate(selected):
            for second_index in selected[offset + 1 :]:
                distance = self.distance(self.candidates[first_index], self.candidates[second_index])
                if distance <= self.redundancy_distance:
                    redundancy += self.redundancy_penalty * (
                        self.redundancy_distance + 1 - distance
                    )

        exposure = sum(self.candidate_risks[index] for index in selected)
        return coverage, redundancy, exposure
