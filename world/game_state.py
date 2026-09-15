from dataclasses import dataclass

from world.layout import GridLayout, Position


DIRECTION_VECTORS: dict[str, tuple[int, int]] = {
    "North": (-1, 0),
    "South": (1, 0),
    "East": (0, 1),
    "West": (0, -1),
    "Stop": (0, 0),
}
ACTION_ORDER = tuple(DIRECTION_VECTORS)


@dataclass(frozen=True, slots=True)
class GameState:
    layout: GridLayout
    defender_position: Position
    intruder_position: Position
    pending_terminals: frozenset[Position]
    score: float = 0.0
    turns: int = 0

    @classmethod
    def initial(cls, layout: GridLayout) -> "GameState":
        return cls(
            layout=layout,
            defender_position=layout.defender_start,
            intruder_position=layout.intruder_start,
            pending_terminals=layout.critical_nodes,
        )

    def is_lose(self) -> bool:
        return self.defender_position == self.intruder_position

    def is_win(self) -> bool:
        return not self.pending_terminals and not self.is_lose()

    def get_num_agents(self) -> int:
        return 2

    def get_score(self) -> float:
        return self.score

    def get_legal_actions(self, agent_index: int) -> list[str]:
        if self.is_win() or self.is_lose():
            return []
        if agent_index not in (0, 1):
            raise ValueError("Los agentes válidos son 0 (defensor) y 1 (intruso)")
        position = self.defender_position if agent_index == 0 else self.intruder_position
        actions: list[str] = []
        for action in ACTION_ORDER:
            dr, dc = DIRECTION_VECTORS[action]
            nxt = (position[0] + dr, position[1] + dc)
            if self.layout.is_open(nxt):
                actions.append(action)
        return actions

    def generate_successor(self, agent_index: int, action: str) -> "GameState":
        if action not in self.get_legal_actions(agent_index):
            raise ValueError(f"Acción ilegal para el agente {agent_index}: {action}")
        dr, dc = DIRECTION_VECTORS[action]
        defender = self.defender_position
        intruder = self.intruder_position
        pending = self.pending_terminals
        score = self.score
        turns = self.turns

        if agent_index == 0:
            defender = (defender[0] + dr, defender[1] + dc)
            score -= 1.0
            if defender in pending:
                pending = frozenset(position for position in pending if position != defender)
                score += 100.0
        else:
            intruder = (intruder[0] + dr, intruder[1] + dc)
            turns += 1

        successor = GameState(self.layout, defender, intruder, pending, score, turns)
        if successor.is_lose():
            return GameState(self.layout, defender, intruder, pending, -1000.0, turns)
        if successor.is_win():
            return GameState(self.layout, defender, intruder, pending, 1000.0, turns)
        return successor
