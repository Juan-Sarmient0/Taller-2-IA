from optimization.problem import SmartGridOptimizationProblem
from optimization.result import Configuration, OptimizationResult
from world.game_state import GameState


def _optimization_grid(
    problem: SmartGridOptimizationProblem, configuration: Configuration
) -> str:
    rows = [list(row) for row in problem.grid]
    for index, position in enumerate(problem.candidates):
        row, col = position
        rows[row][col] = "O" if configuration[index] else "N"
    return "\n".join("".join(row) for row in rows)


def _game_grid(state: GameState) -> str:
    rows = [list(row) for row in state.layout.grid]
    for row, col in state.layout.critical_nodes:
        rows[row][col] = "C" if (row, col) in state.pending_terminals else "A"
    dr, dc = state.defender_position
    ir, ic = state.intruder_position
    rows[dr][dc] = "X" if (dr, dc) == (ir, ic) else "D"
    if (dr, dc) != (ir, ic):
        rows[ir][ic] = "I"
    return "\n".join("".join(row) for row in rows)


class TextDisplay:
    def show_optimization(
        self, problem: SmartGridOptimizationProblem, result: OptimizationResult
    ) -> None:
        print("\n=== CONFIGURACIÓN FINAL ===")
        print(_optimization_grid(problem, result.best_configuration))
        print(
            f"Puntaje={result.best_score:.2f} | Evaluaciones={result.evaluations} "
            f"| Iteraciones={result.iterations}"
        )

    def show_game(self, trace: list[GameState], labels: list[str], stats: dict[str, object]) -> None:
        for index, state in enumerate(trace):
            print(f"\n=== PASO {index}: {labels[index]} ===")
            print(_game_grid(state))
            print(
                f"Pendientes={len(state.pending_terminals)} | Puntaje={state.score:.1f}"
            )
        print("\n=== MÉTRICAS ===")
        print(" | ".join(f"{key}={value}" for key, value in stats.items()))
