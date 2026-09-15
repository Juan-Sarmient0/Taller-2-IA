import time

from algorithms.adversarial import AlphaBetaAgent, MinimaxAgent
from algorithms.evaluation import evaluation_function
from world.game_state import GameState
from world.layout import GridLayout


def _intruder_action(state: GameState, depth: int) -> tuple[str | None, int]:
    """Selecciona la respuesta MIN usando el mismo modelo adversario del taller."""
    actions = state.get_legal_actions(1)
    if not actions:
        return None, 0

    nodes = 1

    def value(
        node: GameState,
        agent_index: int,
        plies_left: int,
        alpha: float,
        beta: float,
    ) -> float:
        nonlocal nodes
        nodes += 1
        if node.is_win() or node.is_lose() or plies_left == 0:
            return evaluation_function(node)
        legal = node.get_legal_actions(agent_index)
        if not legal:
            return evaluation_function(node)
        next_agent = (agent_index + 1) % node.get_num_agents()

        if agent_index == 0:
            result = float("-inf")
            for action in legal:
                result = max(
                    result,
                    value(
                        node.generate_successor(agent_index, action),
                        next_agent,
                        plies_left - 1,
                        alpha,
                        beta,
                    ),
                )
                if result >= beta:
                    return result
                alpha = max(alpha, result)
            return result

        result = float("inf")
        for action in legal:
            result = min(
                result,
                value(
                    node.generate_successor(agent_index, action),
                    next_agent,
                    plies_left - 1,
                    alpha,
                    beta,
                ),
            )
            if result <= alpha:
                return result
            beta = min(beta, result)
        return result

    best_action = actions[0]
    best_value = float("inf")
    alpha = float("-inf")
    beta = float("inf")
    remaining_depth = max(0, int(depth) - 1)
    for action in actions:
        action_value = value(
            state.generate_successor(1, action),
            0,
            remaining_depth,
            alpha,
            beta,
        )
        if action_value < best_value:
            best_value = action_value
            best_action = action
        beta = min(beta, best_value)
    return best_action, nodes


def run_game(
    layout: GridLayout,
    agent_name: str,
    depth: int,
    max_rounds: int = 60,
) -> tuple[list[GameState], list[str], dict[str, object]]:
    if agent_name == "MinimaxAgent":
        agent = MinimaxAgent(depth)
    elif agent_name == "AlphaBetaAgent":
        agent = AlphaBetaAgent(depth)
    else:
        raise ValueError(f"Agente desconocido: {agent_name}")

    state = GameState.initial(layout)
    trace = [state]
    labels = ["Estado inicial"]
    total_nodes = 0
    total_intruder_nodes = 0
    defender_actions: list[str] = []
    intruder_actions: list[str] = []
    step_metrics: list[dict[str, int | str]] = [
        {
            "actor": "inicio",
            "nodes": 0,
            "intruder_nodes": 0,
        }
    ]
    start = time.perf_counter()

    for _ in range(max_rounds):
        if state.is_win() or state.is_lose():
            break
        defender_action = agent.get_action(state)
        total_nodes += agent.nodes_evaluated
        if defender_action is None:
            break
        defender_actions.append(defender_action)
        state = state.generate_successor(0, defender_action)
        trace.append(state)
        labels.append(f"Defensor MAX: {defender_action}")
        step_metrics.append(
            {
                "actor": "MAX",
                "nodes": total_nodes,
                "intruder_nodes": total_intruder_nodes,
            }
        )
        if state.is_win() or state.is_lose():
            break

        intruder_action, intruder_nodes = _intruder_action(state, depth)
        total_intruder_nodes += intruder_nodes
        if intruder_action is None:
            break
        intruder_actions.append(intruder_action)
        state = state.generate_successor(1, intruder_action)
        trace.append(state)
        labels.append(f"Intruso MIN: {intruder_action}")
        step_metrics.append(
            {
                "actor": "MIN",
                "nodes": total_nodes,
                "intruder_nodes": total_intruder_nodes,
            }
        )

    result = "victoria" if state.is_win() else "derrota" if state.is_lose() else "límite"
    termination = (
        "activación completa"
        if state.is_win()
        else "intercepción"
        if state.is_lose()
        else "límite de rondas"
    )
    stats: dict[str, object] = {
        "agent": agent_name,
        "depth": depth,
        "result": result,
        "termination": termination,
        "rounds": state.turns,
        "initial_action": defender_actions[0] if defender_actions else None,
        "defender_actions": tuple(defender_actions),
        "intruder_actions": tuple(intruder_actions),
        "step_metrics": step_metrics,
        "nodes": total_nodes,
        "intruder_nodes": total_intruder_nodes,
        "intruder_policy": "adversarial_min",
        "time": round(time.perf_counter() - start, 6),
    }
    return trace, labels, stats
