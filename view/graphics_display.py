import math
import tkinter as tk

from algorithms.optimization import configuration_score
from optimization.problem import SmartGridOptimizationProblem
from optimization.result import Configuration, OptimizationResult
from world.game_state import GameState


COLORS = {
    "background": "#e8eef5",
    "wall": "#1f2933",
    "floor": "#f8fafc",
    "grid": "#b8c4d0",
    "candidate": "#7b8794",
    "selected": "#2e9d62",
    "critical": "#f2b134",
    "covered": "#34a853",
    "activated": "#5abf72",
    "risk": "#d64545",
    "redundancy": "#f08c46",
    "defender": "#2563b8",
    "intruder": "#c93434",
    "text": "#17365d",
    "muted": "#617184",
}


ALGORITHM_NAMES = {
    "hillClimbing": "Ascenso de colina",
    "simulatedAnnealing": "Recocido simulado",
    "geneticAlgorithm": "Algoritmo genético",
}


class GraphicsDisplay:
    """Visualización pedagógica; no forma parte del código del estudiante."""

    def __init__(self, frame_time: float = 0.55) -> None:
        self.frame_time = max(0.08, frame_time)

    @staticmethod
    def _window(title: str) -> tuple[tk.Tk, tk.Canvas, tk.Frame]:
        root = tk.Tk()
        root.title(title)
        root.configure(bg=COLORS["background"])
        root.minsize(1120, 780)
        canvas = tk.Canvas(
            root,
            width=770,
            height=735,
            bg=COLORS["background"],
            highlightthickness=0,
        )
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        panel = tk.Frame(root, bg="#f8fafc", width=350)
        panel.pack(side=tk.RIGHT, fill=tk.Y)
        panel.pack_propagate(False)
        tk.Label(
            panel,
            text="RED CENTINELA",
            bg="#17365d",
            fg="#ffffff",
            anchor="w",
            padx=20,
            pady=15,
            font=("Segoe UI", 17, "bold"),
        ).pack(fill=tk.X)
        content = tk.Frame(panel, bg="#f8fafc")
        content.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)
        return root, canvas, content

    @staticmethod
    def _card(parent: tk.Widget, title: str) -> tk.Frame:
        card = tk.Frame(
            parent,
            bg="#ffffff",
            highlightbackground="#d8e0e8",
            highlightthickness=1,
        )
        card.pack(fill=tk.X, pady=(0, 8))
        tk.Label(
            card,
            text=title,
            bg="#ffffff",
            fg=COLORS["text"],
            anchor="w",
            font=("Segoe UI", 9, "bold"),
        ).pack(fill=tk.X, padx=12, pady=(8, 3))
        body = tk.Frame(card, bg="#ffffff")
        body.pack(fill=tk.X, padx=12, pady=(0, 9))
        return body

    @staticmethod
    def _scrollable_card(parent: tk.Widget, title: str) -> tk.Frame:
        """Tarjeta que muestra desplazamiento solo cuando su contenido no cabe."""
        card = tk.Frame(
            parent,
            bg="#ffffff",
            highlightbackground="#d8e0e8",
            highlightthickness=1,
        )
        card.pack(fill=tk.BOTH, expand=True)
        tk.Label(
            card,
            text=title,
            bg="#ffffff",
            fg=COLORS["text"],
            anchor="w",
            font=("Segoe UI", 9, "bold"),
        ).pack(fill=tk.X, padx=12, pady=(8, 3))

        holder = tk.Frame(card, bg="#ffffff")
        holder.pack(fill=tk.BOTH, expand=True, padx=12, pady=(0, 9))
        holder.grid_rowconfigure(0, weight=1)
        holder.grid_columnconfigure(0, weight=1)
        viewport = tk.Canvas(
            holder,
            height=120,
            bg="#ffffff",
            highlightthickness=0,
            bd=0,
        )
        viewport.grid(row=0, column=0, sticky="nsew")
        scrollbar = tk.Scrollbar(
            holder,
            orient=tk.VERTICAL,
            command=viewport.yview,
            relief=tk.FLAT,
            width=11,
        )
        scrollbar.grid(row=0, column=1, sticky="ns", padx=(4, 0))
        scrollbar.grid_remove()
        content = tk.Frame(viewport, bg="#ffffff")
        content_window = viewport.create_window((0, 0), window=content, anchor="nw")

        def refresh(_event=None) -> None:
            requested = content.winfo_reqheight()
            available = viewport.winfo_height()
            viewport.itemconfigure(content_window, width=max(1, viewport.winfo_width()))
            viewport.configure(scrollregion=(0, 0, viewport.winfo_width(), requested))
            if available > 1 and requested > available + 1:
                scrollbar.grid()
                viewport.configure(yscrollcommand=scrollbar.set)
            else:
                scrollbar.grid_remove()
                viewport.configure(yscrollcommand="")
                viewport.yview_moveto(0)

        def wheel(event: tk.Event) -> str | None:
            if not scrollbar.winfo_ismapped() or not event.delta:
                return None
            viewport.yview_scroll(-1 if event.delta > 0 else 1, "units")
            return "break"

        def bind_wheel(widget: tk.Widget) -> None:
            widget.bind("<MouseWheel>", wheel)
            for child in widget.winfo_children():
                bind_wheel(child)

        content.bind("<Configure>", refresh)
        viewport.bind("<Configure>", refresh)
        parent.after_idle(refresh)
        parent.after_idle(lambda: bind_wheel(content))
        return content

    @staticmethod
    def _metric_grid(parent: tk.Widget, rows: list[tuple[str, str]]) -> dict[str, tk.StringVar]:
        variables: dict[str, tk.StringVar] = {}
        for row, (key, label) in enumerate(rows):
            tk.Label(
                parent,
                text=label,
                bg="#ffffff",
                fg=COLORS["muted"],
                anchor="w",
                font=("Segoe UI", 9),
            ).grid(row=row, column=0, sticky="w", pady=1)
            variable = tk.StringVar(value="—")
            variables[key] = variable
            tk.Label(
                parent,
                textvariable=variable,
                bg="#ffffff",
                fg="#172b4d",
                anchor="e",
                font=("Segoe UI", 9, "bold"),
            ).grid(row=row, column=1, sticky="e", pady=1)
        parent.grid_columnconfigure(1, weight=1)
        return variables

    @staticmethod
    def _legend_row(parent: tk.Widget, text: str, draw) -> None:
        row = tk.Frame(parent, bg="#ffffff")
        row.pack(fill=tk.X, pady=1)
        icon = tk.Canvas(row, width=42, height=24, bg="#ffffff", highlightthickness=0)
        icon.pack(side=tk.LEFT)
        draw(icon)
        tk.Label(
            row,
            text=text,
            bg="#ffffff",
            fg="#34495e",
            anchor="w",
            font=("Segoe UI", 8),
        ).pack(side=tk.LEFT, fill=tk.X, expand=True)

    def _build_sidebar(self, parent: tk.Frame, mode: str) -> dict[str, object]:
        execution = self._card(parent, "EJECUCIÓN")
        algorithm = tk.StringVar()
        tk.Label(
            execution,
            textvariable=algorithm,
            bg="#ffffff",
            fg="#172b4d",
            anchor="w",
            font=("Segoe UI", 12, "bold"),
        ).pack(fill=tk.X)
        event = tk.Label(
            execution,
            text="Estado inicial",
            bg="#dbeafe",
            fg="#174c83",
            anchor="w",
            padx=8,
            pady=4,
            font=("Segoe UI", 9, "bold"),
        )
        event.pack(fill=tk.X, pady=(5, 3))
        progress = tk.StringVar()
        tk.Label(
            execution,
            textvariable=progress,
            bg="#ffffff",
            fg=COLORS["muted"],
            anchor="w",
            font=("Segoe UI", 8),
        ).pack(fill=tk.X)

        metrics_body = self._card(parent, "MÉTRICAS DEL FOTOGRAMA")
        metric_rows = (
            [
                ("score", "Puntaje"),
                ("coverage", "Cobertura"),
                ("redundancy", "Redundancia"),
                ("exposure", "Exposición"),
                ("best", "Mejor global"),
                ("evaluations", "Evaluaciones"),
            ]
            if mode == "optimization"
            else [
                ("depth", "Profundidad"),
                ("rounds", "Rondas"),
                ("pending", "Terminales pendientes"),
                ("score", "Puntaje"),
                ("max_nodes", "Nodos MAX"),
                ("min_nodes", "Nodos MIN"),
            ]
        )
        metrics = self._metric_grid(metrics_body, metric_rows)

        detail_body = self._card(parent, "DETALLE DEL PASO")
        detail = tk.StringVar()
        tk.Label(
            detail_body,
            textvariable=detail,
            bg="#ffffff",
            fg="#334155",
            justify=tk.LEFT,
            anchor="nw",
            wraplength=300,
            font=("Consolas", 8),
        ).pack(fill=tk.X)

        legend_body = self._scrollable_card(parent, "LEYENDA")
        if mode == "optimization":
            self._optimization_legend(legend_body)
        else:
            self._game_legend(legend_body)
        return {
            "algorithm": algorithm,
            "event": event,
            "progress": progress,
            "metrics": metrics,
            "detail": detail,
        }

    def _optimization_legend(self, parent: tk.Widget) -> None:
        self._legend_row(
            parent,
            "Módulo instalado",
            lambda c: (
                c.create_polygon(21, 3, 32, 8, 32, 17, 21, 22, 10, 17, 10, 8, fill=COLORS["selected"], outline=""),
                c.create_text(21, 13, text="M", fill="white", font=("Segoe UI", 8, "bold")),
            ),
        )
        self._legend_row(
            parent,
            "Sitio candidato vacío",
            lambda c: (
                c.create_oval(10, 3, 32, 23, outline=COLORS["candidate"], width=2, dash=(3, 2)),
                c.create_text(21, 13, text="N", fill=COLORS["muted"], font=("Segoe UI", 8, "bold")),
            ),
        )
        self._legend_row(
            parent,
            "Servicio crítico sin cubrir",
            lambda c: (
                c.create_polygon(21, 2, 32, 13, 21, 24, 10, 13, fill=COLORS["critical"], outline=""),
                c.create_text(21, 13, text="+", fill="white", font=("Segoe UI", 11, "bold")),
            ),
        )
        self._legend_row(
            parent,
            "Servicio crítico cubierto",
            lambda c: (
                c.create_polygon(21, 2, 32, 13, 21, 24, 10, 13, fill=COLORS["covered"], outline=""),
                c.create_text(21, 13, text="+", fill="white", font=("Segoe UI", 11, "bold")),
            ),
        )
        self._legend_row(
            parent,
            "Sitio con exposición",
            lambda c: (
                c.create_polygon(21, 2, 33, 22, 9, 22, fill=COLORS["risk"], outline=""),
                c.create_text(21, 15, text="!", fill="white", font=("Segoe UI", 8, "bold")),
            ),
        )
        self._legend_row(
            parent,
            "Relación redundante",
            lambda c: c.create_line(5, 13, 37, 13, fill=COLORS["redundancy"], width=3, dash=(5, 3)),
        )
        self._legend_row(
            parent,
            "Cambio de ubicación",
            lambda c: c.create_line(5, 13, 37, 13, fill="#3478c9", width=3, arrow=tk.LAST),
        )

    def _game_legend(self, parent: tk.Widget) -> None:
        self._legend_row(
            parent,
            "Defensor MAX",
            lambda c: (
                c.create_polygon(21, 2, 33, 7, 30, 19, 21, 24, 12, 19, 9, 7, fill=COLORS["defender"], outline=""),
                c.create_text(21, 13, text="MAX", fill="white", font=("Segoe UI", 6, "bold")),
            ),
        )
        self._legend_row(
            parent,
            "Intruso MIN",
            lambda c: (
                c.create_polygon(21, 2, 34, 13, 21, 24, 8, 13, fill=COLORS["intruder"], outline=""),
                c.create_text(21, 13, text="MIN", fill="white", font=("Segoe UI", 6, "bold")),
            ),
        )
        self._legend_row(
            parent,
            "Terminal pendiente",
            lambda c: (
                c.create_rectangle(9, 3, 33, 22, fill=COLORS["critical"], outline=""),
                c.create_text(21, 13, text="T", fill="white", font=("Segoe UI", 8, "bold")),
            ),
        )
        self._legend_row(
            parent,
            "Terminal activada por MAX",
            lambda c: (
                c.create_rectangle(9, 3, 33, 22, fill=COLORS["activated"], outline=""),
                c.create_text(21, 13, text="OK", fill="white", font=("Segoe UI", 7, "bold")),
            ),
        )
        self._legend_row(
            parent,
            "Último movimiento",
            lambda c: c.create_line(5, 13, 37, 13, fill=COLORS["defender"], width=3, arrow=tk.LAST),
        )

    @staticmethod
    def _cell_size(width: int, height: int) -> int:
        return max(25, min(52, 680 // max(width, height)))

    @staticmethod
    def _center(position: tuple[int, int], cell: int) -> tuple[float, float]:
        row, col = position
        return 35 + (col + 0.5) * cell, 45 + (row + 0.5) * cell

    @staticmethod
    def _draw_progress(canvas: tk.Canvas, current: int, total: int) -> None:
        x1, x2, y = 35, 720, 645
        canvas.create_rectangle(x1, y, x2, y + 8, fill="#cbd5df", outline="")
        ratio = 1.0 if total <= 0 else current / total
        canvas.create_rectangle(x1, y, x1 + (x2 - x1) * ratio, y + 8, fill="#3478c9", outline="")
        canvas.create_text(
            x1,
            y - 8,
            text=f"Progreso de la ejecución: {current}/{total}",
            anchor="w",
            fill=COLORS["muted"],
            font=("Segoe UI", 9),
        )

    @staticmethod
    def _dashboard_card(
        canvas: tk.Canvas,
        x: int,
        y: int,
        width: int,
        title: str,
        value: str,
        color: str,
        subtitle: str = "",
    ) -> None:
        canvas.create_rectangle(
            x,
            y,
            x + width,
            y + 72,
            fill="#ffffff",
            outline="#d6dee7",
            width=1,
        )
        canvas.create_rectangle(x, y, x + 5, y + 72, fill=color, outline="")
        canvas.create_text(
            x + 15,
            y + 16,
            text=title,
            anchor="w",
            fill=COLORS["muted"],
            font=("Segoe UI", 8, "bold"),
        )
        canvas.create_text(
            x + 15,
            y + 42,
            text=value,
            anchor="w",
            fill=color,
            font=("Segoe UI", 16, "bold"),
        )
        if subtitle:
            canvas.create_text(
                x + width - 10,
                y + 55,
                text=subtitle,
                anchor="e",
                fill=COLORS["muted"],
                font=("Segoe UI", 7),
            )

    def _draw_optimization_dashboard(
        self,
        canvas: tk.Canvas,
        score: float,
        coverage: float,
        redundancy: float,
        exposure: float,
        delta: float,
    ) -> None:
        canvas.create_text(
            35,
            528,
            text="PUNTAJE = COBERTURA − REDUNDANCIA − EXPOSICIÓN",
            anchor="w",
            fill=COLORS["text"],
            font=("Segoe UI", 10, "bold"),
        )
        cards = (
            (35,  "PUNTAJE", f"{score:.2f}", "#2463a7", f"Δ {delta:+.2f}"),
            (207, "COBERTURA", f"+{coverage:.2f}", COLORS["covered"], "beneficio"),
            (379, "REDUNDANCIA", f"−{redundancy:.2f}", COLORS["redundancy"], "penalización"),
            (551, "EXPOSICIÓN", f"−{exposure:.2f}", COLORS["risk"], "penalización"),
        )
        for x, title, value, color, subtitle in cards:
            self._dashboard_card(canvas, x, 545, 160, title, value, color, subtitle)

    def _draw_game_dashboard(
        self,
        canvas: tk.Canvas,
        actor: str,
        rounds: int,
        pending: int,
        score: float,
    ) -> None:
        canvas.create_text(
            35,
            528,
            text="ESTADO ACTUAL DE LA MISIÓN",
            anchor="w",
            fill=COLORS["text"],
            font=("Segoe UI", 10, "bold"),
        )
        actor_color = COLORS["defender"] if actor == "MAX" else COLORS["intruder"] if actor == "MIN" else "#64748b"
        cards = (
            (35, "ÚLTIMO TURNO", actor.upper(), actor_color, "agente"),
            (207, "RONDAS", str(rounds), "#2463a7", "completas"),
            (379, "PENDIENTES", str(pending), COLORS["critical"], "terminales"),
            (551, "PUNTAJE", f"{score:.1f}", COLORS["covered"], "defensor"),
        )
        for x, title, value, color, subtitle in cards:
            self._dashboard_card(canvas, x, 545, 160, title, value, color, subtitle)

    @staticmethod
    def _optimization_details(
        result: OptimizationResult,
        algorithm: str,
        states: list[Configuration],
        scores: list[float],
    ) -> list[dict[str, object]]:
        """Construye la información visual a partir del resultado del algoritmo."""
        details: list[dict[str, object]] = []
        initial_temperature = float(result.metadata.get("initial_temperature", 0.0))
        cooling_rate = float(result.metadata.get("cooling_rate", 1.0))
        for index, state in enumerate(states):
            delta = 0.0 if index == 0 else scores[index] - scores[index - 1]
            if index == 0:
                event = (
                    "Población inicial"
                    if algorithm == "geneticAlgorithm"
                    else "Configuración inicial"
                )
            elif algorithm == "hillClimbing":
                event = "Mejora aceptada"
            elif algorithm == "simulatedAnnealing":
                if state == states[index - 1]:
                    event = "Movimiento rechazado"
                elif delta > 0:
                    event = "Mejora aceptada"
                elif delta < 0:
                    event = "Deterioro aceptado"
                else:
                    event = "Movimiento lateral aceptado"
            elif delta > 0:
                event = "Nuevo mejor global"
            else:
                event = "Mejor global se mantiene"

            detail: dict[str, object] = {
                "event": event,
                "iteration": index,
                "generation": index,
                "delta": delta,
                "generation_best_score": scores[index],
            }
            if algorithm == "simulatedAnnealing":
                detail["temperature"] = initial_temperature * (
                    cooling_rate ** max(0, index - 1)
                )
            if index == len(states) - 1:
                detail["evaluations"] = result.evaluations
            details.append(detail)
        return details

    @staticmethod
    def _timeline_indices(
        result: OptimizationResult,
        details: list[dict[str, object]],
        max_frames: int = 120,
    ) -> list[int]:
        count = len(result.history)
        if count <= max_frames:
            return list(range(count))
        important = {0, count - 1}
        seen: set[str] = set()
        for index, detail in enumerate(details):
            event = str(detail.get("event", ""))
            if event and event not in seen:
                seen.add(event)
                important.add(index)
        stride = max(1, math.ceil((count - 1) / (max_frames - len(important))))
        chosen = important | set(range(0, count, stride))
        ordered = sorted(chosen)
        if len(ordered) <= max_frames:
            return ordered
        keep = sorted(important)
        remaining = [index for index in ordered if index not in important]
        slots = max_frames - len(keep)
        if slots > 0:
            step = len(remaining) / slots
            keep.extend(remaining[min(int(i * step), len(remaining) - 1)] for i in range(slots))
        return sorted(set(keep))

    @staticmethod
    def _movement_indices(
        origin: Configuration | None, target: Configuration | None
    ) -> tuple[int | None, int | None]:
        if origin is None or target is None:
            return None, None
        removed = next(
            (index for index, (before, after) in enumerate(zip(origin, target)) if before and not after),
            None,
        )
        added = next(
            (index for index, (before, after) in enumerate(zip(origin, target)) if not before and after),
            None,
        )
        return removed, added

    @staticmethod
    def _changed_indices(
        origin: Configuration, target: Configuration
    ) -> tuple[list[int], list[int]]:
        removed = [
            index for index, (before, after) in enumerate(zip(origin, target)) if before and not after
        ]
        added = [
            index for index, (before, after) in enumerate(zip(origin, target)) if not before and after
        ]
        return removed, added

    @staticmethod
    def _chromosome_text(configuration: object, cut: object = None) -> str:
        if not isinstance(configuration, tuple):
            return "—"
        bits = "".join(str(int(bit)) for bit in configuration)
        if isinstance(cut, int) and 0 < cut < len(bits):
            return f"{bits[:cut]}|{bits[cut:]}"
        return bits

    def _draw_optimization(
        self,
        canvas: tk.Canvas,
        problem: SmartGridOptimizationProblem,
        configuration: Configuration,
        previous: Configuration | None,
        detail: dict[str, object],
    ) -> None:
        canvas.delete("all")
        cell = self._cell_size(problem.width, problem.height)
        candidate_index = {position: index for index, position in enumerate(problem.candidates)}
        selected_positions = [
            problem.candidates[index] for index, selected in enumerate(configuration) if selected
        ]

        for row in range(problem.height):
            for col in range(problem.width):
                symbol = problem.grid[row][col]
                x1, y1 = 35 + col * cell, 45 + row * cell
                x2, y2 = x1 + cell, y1 + cell
                fill = COLORS["wall"] if symbol == "%" else COLORS["floor"]
                canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=COLORS["grid"])

        for offset, first in enumerate(selected_positions):
            for second in selected_positions[offset + 1 :]:
                if problem.distance(first, second) <= problem.redundancy_distance:
                    canvas.create_line(
                        *self._center(first, cell),
                        *self._center(second, cell),
                        fill=COLORS["redundancy"],
                        width=3,
                        dash=(5, 4),
                    )

        for critical in problem.critical_nodes:
            cx, cy = self._center(critical, cell)
            is_covered = any(
                problem.distance(candidate, critical) <= problem.coverage_radius
                for candidate in selected_positions
            )
            color = COLORS["covered"] if is_covered else COLORS["critical"]
            radius = cell * 0.29
            canvas.create_polygon(
                cx,
                cy - radius,
                cx + radius,
                cy,
                cx,
                cy + radius,
                cx - radius,
                cy,
                fill=color,
                outline="#ffffff",
                width=2,
            )
            canvas.create_line(cx - radius * 0.45, cy, cx + radius * 0.45, cy, fill="white", width=3)
            canvas.create_line(cx, cy - radius * 0.45, cx, cy + radius * 0.45, fill="white", width=3)

        for position, index in candidate_index.items():
            cx, cy = self._center(position, cell)
            selected = bool(configuration[index])
            radius = cell * 0.27
            risk = problem.candidate_risks[index]
            if selected:
                points = []
                for angle in range(0, 360, 60):
                    radians = math.radians(angle - 30)
                    points.extend((cx + radius * math.cos(radians), cy + radius * math.sin(radians)))
                canvas.create_polygon(*points, fill=COLORS["selected"], outline="white", width=2)
                canvas.create_text(cx, cy, text="M", fill="white", font=("Segoe UI", 11, "bold"))
                canvas.create_arc(
                    cx - radius * 1.35,
                    cy - radius * 1.35,
                    cx + radius * 1.35,
                    cy + radius * 1.35,
                    start=35,
                    extent=110,
                    style=tk.ARC,
                    outline="#1f6f47",
                    width=2,
                )
            else:
                canvas.create_oval(
                    cx - radius,
                    cy - radius,
                    cx + radius,
                    cy + radius,
                    fill="#eef2f6",
                    outline=COLORS["candidate"],
                    width=2,
                    dash=(3, 2),
                )
                canvas.create_text(cx, cy, text="N", fill="#596675", font=("Segoe UI", 9, "bold"))
            if risk > 0:
                tx, ty = cx + radius * 0.85, cy - radius * 0.9
                canvas.create_polygon(
                    tx,
                    ty - 7,
                    tx + 7,
                    ty + 6,
                    tx - 7,
                    ty + 6,
                    fill=COLORS["risk"],
                    outline="white",
                )
                canvas.create_text(tx, ty + 1, text="!", fill="white", font=("Segoe UI", 7, "bold"))

        ga_parent = detail.get("parent1")
        ga_child = detail.get("offspring_final")
        if isinstance(ga_parent, tuple) and isinstance(ga_child, tuple):
            removed_many, added_many = self._changed_indices(ga_parent, ga_child)
            for removed, added in zip(removed_many, added_many):
                start = self._center(problem.candidates[removed], cell)
                end = self._center(problem.candidates[added], cell)
                canvas.create_line(
                    *start,
                    *end,
                    arrow=tk.LAST,
                    fill="#7c4dcc",
                    width=3,
                    dash=(5, 3),
                )
            for indices, color, label in (
                (removed_many, COLORS["risk"], "SALE"),
                (added_many, "#3478c9", "ENTRA"),
            ):
                for changed in indices:
                    point = self._center(problem.candidates[changed], cell)
                    canvas.create_oval(
                        point[0] - cell * 0.38,
                        point[1] - cell * 0.38,
                        point[0] + cell * 0.38,
                        point[1] + cell * 0.38,
                        outline=color,
                        width=4,
                    )
                    canvas.create_text(
                        point[0],
                        point[1] + cell * 0.43,
                        text=label,
                        fill=color,
                        font=("Segoe UI", 8, "bold"),
                    )
        else:
            attempted = detail.get("candidate")
            origin = detail.get("previous")
            origin = origin if isinstance(origin, tuple) else previous
            target = attempted if isinstance(attempted, tuple) else configuration
            removed, added = self._movement_indices(origin, target)
        if not (isinstance(ga_parent, tuple) and isinstance(ga_child, tuple)) and removed is not None and added is not None:
            start = self._center(problem.candidates[removed], cell)
            end = self._center(problem.candidates[added], cell)
            accepted = detail.get("accepted", True)
            event = str(detail.get("event", ""))
            color = (
                COLORS["risk"]
                if accepted is False
                else COLORS["redundancy"]
                if "Deterioro" in event
                else "#3478c9"
            )
            canvas.create_line(
                *start,
                *end,
                arrow=tk.LAST,
                fill=color,
                width=4,
                dash=(6, 4) if accepted is False else (),
            )
            for point, label in ((start, "SALE"), (end, "ENTRA" if accepted else "INTENTO")):
                canvas.create_oval(
                    point[0] - cell * 0.37,
                    point[1] - cell * 0.37,
                    point[0] + cell * 0.37,
                    point[1] + cell * 0.37,
                    outline=color,
                    width=3,
                )
                canvas.create_text(
                    point[0],
                    point[1] + cell * 0.42,
                    text=label,
                    fill=color,
                    font=("Segoe UI", 8, "bold"),
                )
        coverage, redundancy, exposure = problem.score_components(configuration)
        self._draw_optimization_dashboard(
            canvas,
            configuration_score(problem, configuration),
            coverage,
            redundancy,
            exposure,
            float(detail.get("delta", 0.0)),
        )

    @staticmethod
    def _install_controls(
        root: tk.Tk,
        render,
        index: dict[str, int],
        paused: dict[str, bool],
        total: int,
    ):
        controls = tk.Frame(
            root,
            bg="#ffffff",
            highlightbackground="#d4dde7",
            highlightthickness=1,
        )
        controls.place(x=175, y=681)
        status = tk.StringVar(value="Reproduciendo")

        def sync() -> None:
            is_paused = bool(paused["value"])
            play_button.configure(text="▶" if is_paused else "⏸")
            status.set("Pausado" if is_paused else "Reproduciendo")

        def button(text: str, command) -> tk.Button:
            return tk.Button(
                controls,
                text=text,
                command=command,
                relief=tk.FLAT,
                bd=0,
                bg="#ffffff",
                activebackground="#dbeafe",
                activeforeground="#174c83",
                fg="#244a72",
                width=4,
                height=1,
                cursor="hand2",
                font=("Segoe UI Symbol", 14, "bold"),
            )

        def previous() -> None:
            paused["value"] = True
            index["value"] = max(0, index["value"] - 1)
            sync()
            render()

        def following() -> None:
            paused["value"] = True
            index["value"] = min(total, index["value"] + 1)
            sync()
            render()

        def toggle() -> None:
            if index["value"] >= total:
                index["value"] = 0
            paused["value"] = not paused["value"]
            sync()
            render()

        def restart() -> None:
            paused["value"] = True
            index["value"] = 0
            sync()
            render()

        button("↺", restart).pack(side=tk.LEFT, padx=(5, 1), pady=4)
        button("⏮", previous).pack(side=tk.LEFT, padx=1, pady=4)
        play_button = button("⏸", toggle)
        play_button.pack(side=tk.LEFT, padx=1, pady=4)
        button("⏭", following).pack(side=tk.LEFT, padx=1, pady=4)
        tk.Label(
            controls,
            textvariable=status,
            bg="#ffffff",
            fg=COLORS["muted"],
            width=13,
            font=("Segoe UI", 9),
        ).pack(side=tk.LEFT, padx=(4, 8))
        root.bind("<Left>", lambda _event: previous())
        root.bind("<Right>", lambda _event: following())
        root.bind("<space>", lambda _event: toggle())
        root.bind("r", lambda _event: restart())
        root.bind("R", lambda _event: restart())
        return sync

    def show_optimization(
        self, problem: SmartGridOptimizationProblem, result: OptimizationResult
    ) -> None:
        root, canvas, sidebar = self._window(f"Red Centinela - {problem.name}")
        ui = self._build_sidebar(sidebar, "optimization")
        algorithm = str(result.metadata.get("algorithm", ""))
        all_states = result.history or [result.best_configuration]
        all_scores = list(result.score_history)
        if len(all_scores) != len(all_states):
            all_scores = [configuration_score(problem, state) for state in all_states]
        all_details = self._optimization_details(result, algorithm, all_states, all_scores)
        if len(result._visualization_details) == len(all_details):
            for detail, visual_detail in zip(all_details, result._visualization_details):
                detail.update(visual_detail)
        timeline = self._timeline_indices(result, all_details) if result.history else [0]
        details = [all_details[position] for position in timeline]
        states = [
            detail.get("offspring_final")
            if algorithm == "geneticAlgorithm"
            and isinstance(detail.get("offspring_final"), tuple)
            else all_states[position]
            for position, detail in zip(timeline, details)
        ]
        global_scores = [all_scores[position] for position in timeline]
        displayed_scores = [configuration_score(problem, state) for state in states]
        index = {"value": 0}
        paused = {"value": False}

        def render() -> None:
            current = index["value"]
            detail = details[current]
            previous = states[current - 1] if current > 0 else None
            self._draw_optimization(canvas, problem, states[current], previous, detail)
            self._draw_progress(canvas, current, len(states) - 1)
            original_step = timeline[current]
            delta = float(detail.get("delta", 0.0))
            coverage, redundancy, exposure = problem.score_components(states[current])
            extra = ""
            if algorithm == "simulatedAnnealing":
                extra = (
                    f"Temperatura: {float(detail.get('temperature', 0.0)):.4f}\n"
                    f"Cambio del estado: {delta:+.2f}\n"
                )
            elif algorithm == "geneticAlgorithm":
                cut = detail.get("crossover_cut")
                if isinstance(detail.get("parent1"), tuple):
                    extra = (
                    f"Mejor de generación: "
                    f"{float(detail.get('generation_best_score', global_scores[current])):.2f}\n"
                    f"Mejor global: {global_scores[current]:.2f}\n\n"
                    f"CRUCE REPRESENTATIVO\n"
                    f"Padre 1: {self._chromosome_text(detail.get('parent1'), cut)}\n"
                    f"Padre 2: {self._chromosome_text(detail.get('parent2'), cut)}\n"
                    f"Corte: {cut if cut is not None else '—'}\n"
                    f"Hijo cruce: {self._chromosome_text(detail.get('offspring_raw'))}\n"
                    f"Reparado:   {self._chromosome_text(detail.get('offspring_repaired'))}\n"
                    f"Mutado:     {self._chromosome_text(detail.get('offspring_mutated'))}\n"
                    f"Reparación aplicada: "
                    f"{'sí' if detail.get('repair_applied') else 'no'}\n"
                    f"Mutación aplicada: "
                    f"{'sí' if detail.get('mutation_applied') else 'no'}\n"
                    f"Cambio frente al padre 1: {delta:+.2f}\n"
                    )
                else:
                    extra = (
                        f"Mejor de generación: "
                        f"{float(detail.get('generation_best_score', global_scores[current])):.2f}\n"
                        f"Mejor global: {global_scores[current]:.2f}\n\n"
                        "Se muestra el mejor resultado acumulado "
                        "hasta esta generación.\n"
                    )
            elif current > 0:
                extra = f"Mejora obtenida: {delta:+.2f}\n"
            termination = str(result.metadata.get("termination", ""))
            final_message = (
                f"\nFinalización: {termination}\n"
                if current == len(states) - 1 and termination
                else ""
            )
            sampling = (
                f"Fotograma representativo {current + 1}/{len(states)}"
                if len(all_states) > len(states)
                else f"Fotograma {current + 1}/{len(states)}"
            )
            step_label = (
                f"Generación {detail.get('generation', original_step)}"
                if algorithm == "geneticAlgorithm"
                else f"Iteración {detail.get('iteration', original_step)}"
            )
            event_text = str(detail.get("event", ""))
            event_color = (
                ("#fee2e2", "#991b1b")
                if "rechazado" in event_text.lower()
                else ("#ffedd5", "#9a3412")
                if "deterioro" in event_text.lower()
                else ("#dcfce7", "#166534")
                if "mejora" in event_text.lower() or "nuevo mejor" in event_text.lower()
                else ("#dbeafe", "#174c83")
            )
            ui["algorithm"].set(ALGORITHM_NAMES.get(algorithm, algorithm))
            ui["event"].configure(text=event_text, bg=event_color[0], fg=event_color[1])
            ui["progress"].set(f"{sampling}  ·  {step_label}")
            metric_vars = ui["metrics"]
            metric_vars["score"].set(f"{displayed_scores[current]:.2f}")
            metric_vars["coverage"].set(f"+{coverage:.2f}")
            metric_vars["redundancy"].set(f"−{redundancy:.2f}")
            metric_vars["exposure"].set(f"−{exposure:.2f}")
            metric_vars["best"].set(f"{global_scores[current]:.2f}")
            metric_vars["evaluations"].set(str(detail.get("evaluations", result.evaluations)))
            ui["detail"].set(f"{extra.strip()}{final_message}")

        def tick() -> None:
            if not paused["value"] and index["value"] < len(states) - 1:
                index["value"] += 1
                render()
            elif index["value"] >= len(states) - 1:
                paused["value"] = True
                control_sync()
            root.after(int(self.frame_time * 1000), tick)

        control_sync = self._install_controls(root, render, index, paused, len(states) - 1)
        render()
        root.after(int(self.frame_time * 1000), tick)
        root.mainloop()

    def _draw_game(
        self,
        canvas: tk.Canvas,
        state: GameState,
        previous: GameState | None,
        actor: str,
    ) -> None:
        canvas.delete("all")
        layout = state.layout
        cell = self._cell_size(layout.width, layout.height)
        for row in range(layout.height):
            for col in range(layout.width):
                symbol = layout.grid[row][col]
                x1, y1 = 35 + col * cell, 45 + row * cell
                x2, y2 = x1 + cell, y1 + cell
                fill = COLORS["wall"] if symbol == "%" else COLORS["floor"]
                canvas.create_rectangle(x1, y1, x2, y2, fill=fill, outline=COLORS["grid"])

        for terminal in layout.critical_nodes:
            cx, cy = self._center(terminal, cell)
            active = terminal in state.pending_terminals
            color = COLORS["critical"] if active else COLORS["activated"]
            radius = cell * 0.28
            canvas.create_rectangle(
                cx - radius,
                cy - radius,
                cx + radius,
                cy + radius,
                fill=color,
                outline="white",
                width=2,
            )
            for offset in (-0.45, 0, 0.45):
                canvas.create_oval(
                    cx - radius * 0.55,
                    cy + offset * radius - 2,
                    cx - radius * 0.55 + 4,
                    cy + offset * radius + 2,
                    fill="white",
                    outline="",
                )
            canvas.create_text(
                cx + radius * 0.25,
                cy,
                text="T" if active else "OK",
                fill="white",
                font=("Segoe UI", 8, "bold"),
            )

        if previous is not None and actor in {"MAX", "MIN"}:
            start_position = (
                previous.defender_position if actor == "MAX" else previous.intruder_position
            )
            end_position = state.defender_position if actor == "MAX" else state.intruder_position
            start = self._center(start_position, cell)
            end = self._center(end_position, cell)
            color = COLORS["defender"] if actor == "MAX" else COLORS["intruder"]
            if start == end:
                canvas.create_oval(
                    start[0] - cell * 0.42,
                    start[1] - cell * 0.42,
                    start[0] + cell * 0.42,
                    start[1] + cell * 0.42,
                    outline=color,
                    width=4,
                )
            else:
                canvas.create_line(*start, *end, fill=color, width=5, arrow=tk.LAST)

        dx, dy = self._center(state.defender_position, cell)
        radius = cell * 0.31
        canvas.create_polygon(
            dx,
            dy - radius,
            dx + radius,
            dy - radius * 0.45,
            dx + radius * 0.72,
            dy + radius * 0.55,
            dx,
            dy + radius,
            dx - radius * 0.72,
            dy + radius * 0.55,
            dx - radius,
            dy - radius * 0.45,
            fill=COLORS["defender"],
            outline="white",
            width=2,
        )
        canvas.create_text(dx, dy, text="MAX", fill="white", font=("Segoe UI", 8, "bold"))

        ix, iy = self._center(state.intruder_position, cell)
        canvas.create_polygon(
            ix,
            iy - radius,
            ix + radius,
            iy,
            ix,
            iy + radius,
            ix - radius,
            iy,
            fill=COLORS["intruder"],
            outline="white",
            width=2,
        )
        canvas.create_text(ix, iy, text="MIN", fill="white", font=("Segoe UI", 8, "bold"))
        if state.is_lose():
            canvas.create_line(ix - radius, iy - radius, ix + radius, iy + radius, fill="#111827", width=5)
            canvas.create_line(ix + radius, iy - radius, ix - radius, iy + radius, fill="#111827", width=5)
        self._draw_game_dashboard(
            canvas,
            actor,
            state.turns,
            len(state.pending_terminals),
            state.score,
        )

    def show_game(self, trace: list[GameState], labels: list[str], stats: dict[str, object]) -> None:
        root, canvas, sidebar = self._window(f"Red Centinela - {trace[0].layout.name}")
        ui = self._build_sidebar(sidebar, "game")
        index = {"value": 0}
        paused = {"value": False}
        metrics = stats.get("step_metrics", [])

        def render() -> None:
            current = index["value"]
            state = trace[current]
            previous = trace[current - 1] if current > 0 else None
            current_metrics = metrics[current] if isinstance(metrics, list) and current < len(metrics) else stats
            actor = str(current_metrics.get("actor", "inicio"))
            self._draw_game(canvas, state, previous, actor)
            self._draw_progress(canvas, current, len(trace) - 1)
            final_message = (
                f"\nRESULTADO FINAL\n"
                f"Resultado: {stats.get('result', '')}\n"
                f"Finalización: {stats.get('termination', '')}\n"
                if current == len(trace) - 1
                else ""
            )
            event_text = labels[current]
            event_color = (
                ("#dbeafe", "#174c83")
                if actor == "MAX"
                else ("#fee2e2", "#991b1b")
                if actor == "MIN"
                else ("#e2e8f0", "#475569")
            )
            if current == len(trace) - 1:
                event_color = (
                    ("#dcfce7", "#166534")
                    if stats.get("result") == "victoria"
                    else ("#fee2e2", "#991b1b")
                    if stats.get("result") == "derrota"
                    else ("#fef3c7", "#92400e")
                )
            ui["algorithm"].set(str(stats.get("agent", "Juego adversario")))
            ui["event"].configure(text=event_text, bg=event_color[0], fg=event_color[1])
            ui["progress"].set(
                f"Fotograma {current + 1}/{len(trace)}  ·  Acción inicial: "
                f"{stats.get('initial_action', '—')}"
            )
            metric_vars = ui["metrics"]
            metric_vars["depth"].set(f"{stats.get('depth', 0)} plies")
            metric_vars["rounds"].set(str(state.turns))
            metric_vars["pending"].set(str(len(state.pending_terminals)))
            metric_vars["score"].set(f"{state.score:.1f}")
            metric_vars["max_nodes"].set(str(current_metrics.get("nodes", 0)))
            metric_vars["min_nodes"].set(str(current_metrics.get("intruder_nodes", 0)))
            ui["detail"].set(
                final_message.strip()
                if final_message
                else "Las métricas muestran únicamente el trabajo acumulado hasta este turno."
            )

        def tick() -> None:
            if not paused["value"] and index["value"] < len(trace) - 1:
                index["value"] += 1
                render()
            elif index["value"] >= len(trace) - 1:
                paused["value"] = True
                control_sync()
            root.after(int(self.frame_time * 1000), tick)

        control_sync = self._install_controls(root, render, index, paused, len(trace) - 1)
        render()
        root.after(int(self.frame_time * 1000), tick)
        root.mainloop()
