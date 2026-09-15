from optimization.problem import SmartGridOptimizationProblem
from optimization.result import OptimizationResult
from world.game_state import GameState


class NullDisplay:
    def show_optimization(
        self, problem: SmartGridOptimizationProblem, result: OptimizationResult
    ) -> None:
        return

    def show_game(self, trace: list[GameState], labels: list[str], stats: dict[str, object]) -> None:
        return
