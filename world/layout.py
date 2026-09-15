from collections import deque
from dataclasses import dataclass, field
from pathlib import Path


Position = tuple[int, int]


@dataclass
class GridLayout:
    name: str
    grid: tuple[str, ...]
    defender_start: Position
    intruder_start: Position
    critical_nodes: frozenset[Position]
    _distance_cache: dict[tuple[Position, Position], int | float] = field(
        default_factory=dict, init=False, repr=False
    )

    @classmethod
    def load(cls, path: str | Path) -> "GridLayout":
        source = Path(path)
        rows = tuple(
            line.rstrip("\n")
            for line in source.read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        if not rows or len({len(row) for row in rows}) != 1:
            raise ValueError("El layout adversario debe ser rectangular y no vacío")
        defenders = cls._find(rows, "D")
        intruders = cls._find(rows, "I")
        critical = frozenset(cls._find(rows, "C"))
        if len(defenders) != 1 or len(intruders) != 1 or not critical:
            raise ValueError("El layout requiere exactamente un D, un I y al menos un C")
        return cls(source.stem, rows, defenders[0], intruders[0], critical)

    @staticmethod
    def _find(rows: tuple[str, ...], symbol: str) -> list[Position]:
        return [
            (row, col)
            for row, line in enumerate(rows)
            for col, value in enumerate(line)
            if value == symbol
        ]

    @property
    def height(self) -> int:
        return len(self.grid)

    @property
    def width(self) -> int:
        return len(self.grid[0])

    def is_open(self, position: Position) -> bool:
        row, col = position
        return 0 <= row < self.height and 0 <= col < self.width and self.grid[row][col] != "%"

    def distance(self, start: Position, goal: Position) -> int | float:
        key = (start, goal)
        if key in self._distance_cache:
            return self._distance_cache[key]
        queue: deque[Position] = deque([start])
        distances = {start: 0}
        while queue:
            current = queue.popleft()
            if current == goal:
                break
            row, col = current
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (row + dr, col + dc)
                if self.is_open(nxt) and nxt not in distances:
                    distances[nxt] = distances[current] + 1
                    queue.append(nxt)
        value = distances.get(goal, float("inf"))
        self._distance_cache[key] = value
        self._distance_cache[(goal, start)] = value
        return value
