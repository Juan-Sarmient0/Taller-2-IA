from dataclasses import dataclass, field


Configuration = tuple[int, ...]


@dataclass(slots=True)
class OptimizationResult:
    """Resultado uniforme para los tres algoritmos de optimización."""

    best_configuration: Configuration
    best_score: float
    evaluations: int
    iterations: int
    history: list[Configuration] = field(default_factory=list)
    score_history: list[float] = field(default_factory=list)
    metadata: dict[str, float | int | str] = field(default_factory=dict)
    _visualization_details: list[dict[str, object]] = field(
        default_factory=list, init=False, repr=False
    )
