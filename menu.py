"""Interfaz de terminal interactiva para el Taller 2: Red Centinela."""

import json
import subprocess
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parent
MAIN_FILE = PROJECT_DIR / "main.py"


WORKSHOP_POINTS = [
    {
        "title": "Punto 1 - Ascenso de colina",
        "subtitle": "Óptimo local",
        "description": "Mejorar una configuración usando el mejor vecino disponible.",
        "mode": "optimization",
        "folder": "optimization",
        "algorithm": "hillClimbing",
        "label": "Hill Climbing",
    },
    {
        "title": "Punto 2 - Recocido simulado",
        "subtitle": "Escape probabilístico",
        "description": "Aceptar movimientos controlados por temperatura para escapar de máximos locales.",
        "mode": "optimization",
        "folder": "optimization",
        "algorithm": "simulatedAnnealing",
        "label": "Simulated Annealing",
    },
    {
        "title": "Punto 3 - Algoritmo genético",
        "subtitle": "Búsqueda poblacional",
        "description": "Evolucionar configuraciones mediante selección, cruce, mutación y elitismo.",
        "mode": "optimization",
        "folder": "optimization",
        "algorithm": "geneticAlgorithm",
        "label": "Genetic Algorithm",
    },
    {
        "title": "Punto 4 - Minimax",
        "subtitle": "Juego adversario",
        "description": "Elegir la defensa suponiendo que el intruso responde de forma óptima.",
        "mode": "adversarial",
        "folder": "adversarial",
        "algorithm": "MinimaxAgent",
        "label": "Minimax",
    },
    {
        "title": "Punto 5 - Alfa-beta",
        "subtitle": "Poda y evaluación",
        "description": "Conservar la decisión de Minimax explorando menos nodos del árbol.",
        "mode": "adversarial",
        "folder": "adversarial",
        "algorithm": "AlphaBetaAgent",
        "label": "Alpha-Beta",
    },
]


DISPLAY_MODES = [
    ("graphics", "Ventana gráfica"),
    ("text", "Modo texto"),
    ("quiet", "Sin animación"),
]

SPEEDS = [
    (0.18, "Rápida"),
    (0.55, "Normal"),
    (1.20, "Lenta"),
]

RUN_COUNTS = [(1, "1 ejecución"), (3, "3 ejecuciones"), (5, "5 ejecuciones")]

PROFILES = {
    "hillClimbing": [
        ("quick", "Rápido", "150 iteraciones", ["--iterations", "150"]),
        ("balanced", "Equilibrado", "500 iteraciones", ["--iterations", "500"]),
        ("deep", "Profundo", "1500 iteraciones", ["--iterations", "1500"]),
    ],
    "simulatedAnnealing": [
        (
            "quick",
            "Rápido",
            "250 iter. · T=15 · α=0.95",
            ["--iterations", "250", "--temperature", "15", "--cooling", "0.95"],
        ),
        (
            "balanced",
            "Equilibrado",
            "750 iter. · T=20 · α=0.97",
            ["--iterations", "750", "--temperature", "20", "--cooling", "0.97"],
        ),
        (
            "deep",
            "Profundo",
            "2000 iter. · T=30 · α=0.99",
            ["--iterations", "2000", "--temperature", "30", "--cooling", "0.99"],
        ),
    ],
    "geneticAlgorithm": [
        (
            "quick",
            "Rápido",
            "20 individuos · 40 generaciones",
            ["--population", "20", "--generations", "40", "--mutation", "0.08", "--elite", "2"],
        ),
        (
            "balanced",
            "Equilibrado",
            "40 individuos · 100 generaciones",
            ["--population", "40", "--generations", "100", "--mutation", "0.05", "--elite", "2"],
        ),
        (
            "deep",
            "Profundo",
            "80 individuos · 250 generaciones",
            ["--population", "80", "--generations", "250", "--mutation", "0.03", "--elite", "4"],
        ),
    ],
    "MinimaxAgent": [
        ("quick", "Profundidad 1", "1 ply: acción de MAX · máximo 40 rondas", ["-d", "1", "--max-rounds", "40"]),
        ("balanced", "Profundidad 2", "2 plies: MAX + MIN (una ronda) · máximo 40 rondas", ["-d", "2", "--max-rounds", "40"]),
        ("deep", "Profundidad 4", "4 plies: MAX + MIN + MAX + MIN (dos rondas) · máximo 40 rondas", ["-d", "4", "--max-rounds", "40"]),
    ],
    "AlphaBetaAgent": [
        ("quick", "Profundidad 1", "1 ply: acción de MAX · máximo 40 rondas", ["-d", "1", "--max-rounds", "40"]),
        ("balanced", "Profundidad 2", "2 plies: MAX + MIN (una ronda) · máximo 40 rondas", ["-d", "2", "--max-rounds", "40"]),
        ("deep", "Profundidad 4", "4 plies: MAX + MIN + MAX + MIN (dos rondas) · máximo 40 rondas", ["-d", "4", "--max-rounds", "40"]),
    ],
}


LAYOUT_PURPOSES = {
    "tiny_coverage": "Control pequeño para validar configuraciones, puntaje y vecindad.",
    "local_peak": "Cuencas con máximos locales para observar dependencia de la configuración inicial.",
    "plateau_grid": "Meseta subóptima: varios vecinos empatan y la mejora estricta se detiene.",
    "redundant_modules": "Aísla el costo de instalar módulos con cobertura espacial redundante.",
    "risk_corridor": "Contrapone cobertura y exposición; contiene varias cuencas de calidad distinta.",
    "balanced_city": "Instancia amplia para comparar exploración, parámetros, semillas y costo computacional.",
    "barrier_districts": "Barreras y servicios dispersos generan tres cuencas de calidad distinta.",
    "exposure_tradeoff": "Contrasta sitios cercanos de alto riesgo con alternativas seguras más distantes.",
    "wide_plateau": "Simetrías y empates forman una meseta subóptima amplia.",
    "metropolitan_network": "Caso de estrés con 54264 configuraciones válidas y varios máximos locales.",
    "single_terminal": "Control adversario sencillo para verificar turnos, terminales y estados finales.",
    "tiny_defense": "Escenario corto sensible a la profundidad para depurar MAX y MIN.",
    "bottleneck": "Cuello de botella que obliga a anticipar la intercepción del intruso.",
    "deceptive_distance": "Rutas de apariencia favorable que permiten estudiar el efecto horizonte.",
    "dual_terminal": "Dos terminales cuyo orden de activación cambia la respuesta adversaria.",
    "medium_defense": "Mapa de estrés con ciclos, rutas alternativas y mayor árbol de juego.",
    "forked_routes": "Tres objetivos en rutas alternativas; la profundidad cambia la primera decisión.",
    "loop_network": "Red con ciclos y cuatro terminales para analizar horizonte y decisiones repetidas.",
    "horizon_ambush": "La profundidad permite distinguir una ruta segura de una decisión miope.",
    "fortified_city": "Escenario amplio de cinco terminales y alta ramificación para estudiar la poda.",
}


try:
    from rich.markup import escape
    from textual import on
    from textual.app import App, ComposeResult
    from textual.binding import Binding
    from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
    from textual.message import Message
    from textual.widgets import Button, Footer, Header, Input, Static

    TEXTUAL_AVAILABLE = True
except ModuleNotFoundError:
    TEXTUAL_AVAILABLE = False


def main() -> int:
    if not TEXTUAL_AVAILABLE:
        print_missing_textual_message()
        return 1
    RedCentinelaMenuApp().run()
    return 0


def available_layouts(folder: str) -> list[str]:
    suffix = "*.json" if folder == "optimization" else "*.lay"
    infos = [layout_info(folder, path.stem) for path in (PROJECT_DIR / "layouts" / folder).glob(suffix)]
    infos.sort(key=lambda item: (item["width"] * item["height"], item["name"].lower()))
    return [str(item["name"]) for item in infos]


def layout_path(folder: str, name: str) -> Path:
    suffix = ".json" if folder == "optimization" else ".lay"
    return PROJECT_DIR / "layouts" / folder / f"{name}{suffix}"


def layout_info(folder: str, name: str) -> dict[str, object]:
    path = layout_path(folder, name)
    if folder == "optimization":
        data = json.loads(path.read_text(encoding="utf-8"))
        rows = [str(row) for row in data["grid"]]
        text = "".join(rows)
        return {
            "name": name,
            "rows": rows,
            "width": len(rows[0]) if rows else 0,
            "height": len(rows),
            "candidates": text.count("N"),
            "critical": text.count("C"),
            "modules": int(data["modules"]),
            "radius": int(data.get("coverage_radius", 0)),
        }
    rows = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    text = "".join(rows)
    return {
        "name": name,
        "rows": rows,
        "width": len(rows[0]) if rows else 0,
        "height": len(rows),
        "critical": text.count("C"),
        "defenders": text.count("D"),
        "intruders": text.count("I"),
    }


def layout_meta_label(point: dict[str, object], info: dict[str, object]) -> str:
    size = f"{info['width']}×{info['height']}"
    if point["mode"] == "optimization":
        return f"{size} · {info['candidates']} sitios · {info['modules']} módulos"
    return f"{size} · {info['critical']} terminales"


def compact_label(value: str, max_length: int = 24) -> str:
    return value if len(value) <= max_length else value[: max_length - 3] + "..."


def command_to_text(command: list[str]) -> str:
    return " ".join(f'"{part}"' if " " in str(part) else str(part) for part in command)


def command_to_multiline_text(command: list[str]) -> str:
    if len(command) <= 2:
        return command_to_text(command)
    lines = [command_to_text(command[:2])]
    index = 2
    while index < len(command):
        current = str(command[index])
        if current.startswith("-") and index + 1 < len(command) and not str(command[index + 1]).startswith("-"):
            lines.append(f"  {current} {command_to_text([str(command[index + 1])])}")
            index += 2
        else:
            lines.append(f"  {command_to_text([current])}")
            index += 1
    return "\n".join(lines)


def print_missing_textual_message() -> None:
    print("\nLa interfaz interactiva de Red Centinela usa Textual.")
    print("Instálelo con:\n  python -m pip install -r requirements.txt")
    print("\nTambién puede ejecutar un caso directamente:")
    print("  python main.py -m optimization -a hillClimbing -l local_peak -t")
    print("  python main.py -m adversarial -a AlphaBetaAgent -l tiny_defense -d 2 -t\n")


if TEXTUAL_AVAILABLE:

    class SeedInput(Input):
        """Campo numérico que reserva las teclas globales R y Q."""

        def check_consume_key(self, key: str, character: str | None) -> bool:
            if key in {"r", "q"}:
                return False
            return super().check_consume_key(key, character)


    class PointCard(Static):
        can_focus = True
        BINDINGS = [Binding("enter", "select", "Seleccionar", show=False)]

        class Selected(Message):
            def __init__(self, index: int) -> None:
                self.index = index
                super().__init__()

        def __init__(self, index: int, point: dict[str, object]) -> None:
            self.index = index
            content = (
                f"[bold #f0c040]{escape(str(point['title']))}[/]\n"
                f"[#58a6ff]{escape(str(point['subtitle']))}[/] [dim]· {escape(str(point['label']))}[/]"
            )
            super().__init__(content, classes="point-card")

        def action_select(self) -> None:
            self.post_message(self.Selected(self.index))

        def on_click(self, event=None) -> None:
            self.action_select()


    class LayoutCard(Static):
        can_focus = True
        BINDINGS = [Binding("enter", "select", "Seleccionar", show=False)]

        class Selected(Message):
            def __init__(self, layout_name: str) -> None:
                self.layout_name = layout_name
                super().__init__()

        def __init__(self, point: dict[str, object], info: dict[str, object]) -> None:
            self.layout_name = str(info["name"])
            content = (
                f"[bold]{escape(compact_label(self.layout_name))}[/]\n"
                f"[dim]{escape(layout_meta_label(point, info))}[/]"
            )
            super().__init__(content, classes="layout-card")

        def action_select(self) -> None:
            self.post_message(self.Selected(self.layout_name))

        def on_click(self, event=None) -> None:
            self.action_select()


    class OptionCard(Static):
        can_focus = True
        BINDINGS = [Binding("enter", "select", "Seleccionar", show=False)]

        class Selected(Message):
            def __init__(self, option_group: str, option_value: object) -> None:
                self.option_group = option_group
                self.option_value = option_value
                super().__init__()

        def __init__(self, group: str, value: object, label: str) -> None:
            self.option_group = group
            self.option_value = value
            super().__init__(f"[bold]{escape(label)}[/]", classes="option-card")

        def action_select(self) -> None:
            self.post_message(self.Selected(self.option_group, self.option_value))

        def on_click(self, event=None) -> None:
            self.action_select()


    CSS = """
    Screen { background: #0d1117; color: #e6edf3; }
    #shell { height: 1fr; layout: horizontal; }
    .title-bar { height: 3; padding: 0 2; background: #161b22; border-bottom: solid #30363d; content-align: left middle; }
    .panel { background: #0d1117; border: solid #30363d; padding: 1; height: 100%; }
    #point-panel { width: 30; min-width: 26; }
    #layout-panel { width: 1fr; }
    #settings-panel { width: 36; min-width: 32; }
    .section-title { height: 2; color: #f0c040; text-style: bold; }
    .setting-label { height: 1; margin-top: 1; color: #58a6ff; text-style: bold; }
    #point-list, #settings-scroll { height: 1fr; }
    #layout-grid { height: 1fr; layout: grid; grid-size: 2; grid-columns: 1fr 1fr; grid-rows: 4; grid-gutter: 1; overflow-y: auto; }
    .point-card { height: 4; padding: 0 1; margin-bottom: 1; border: solid #21262d; background: #161b22; }
    .layout-card { height: 4; min-height: 4; padding: 0 1; border: solid #21262d; background: #161b22; }
    .option-card { height: 3; padding: 0 1; border: solid #21262d; background: #161b22; content-align: center middle; }
    .point-card:hover, .layout-card:hover, .option-card:hover,
    .point-card:focus, .layout-card:focus, .option-card:focus { border: solid #58a6ff; background: #1c2128; }
    .--selected { border: solid #f0c040; background: #1c2836; }
    #selected-info { height: auto; min-height: 10; padding: 0 1; border: solid #21262d; background: #0a0f16; }
    #display-options, #speed-options, #profile-options, #runs-options { height: auto; layout: grid; grid-size: 2; grid-gutter: 1; }
    #display-options, #profile-options { grid-size: 1; }
    #runs-options { grid-size: 3; }
    #seed-input { height: 3; border: solid #21262d; background: #0a0f16; }
    #profile-help { height: auto; min-height: 2; color: #8b949e; }
    #command-preview { height: auto; min-height: 9; padding: 0 1; margin-top: 1; border: dashed #30363d; background: #0a0f16; color: #8b949e; }
    #action-buttons { height: auto; align: center middle; }
    .action-button { width: 25; }
    #status-line { height: auto; min-height: 3; padding: 0 1; margin-top: 1; color: #3fb950; }
    Button { height: 3; margin-top: 1; border: solid #30363d; }
    """


    class RedCentinelaMenuApp(App):
        TITLE = "Taller 2: Búsqueda local y juegos adversarios"
        SUB_TITLE = "Red Centinela"
        CSS = CSS
        CTRL_C_QUIT = True
        BINDINGS = [
            Binding("q", "quit", "Salir", priority=True),
            Binding("r", "run", "Ejecutar", priority=True),
            Binding("ctrl+c", "quit", "Salir", show=False),
        ]

        def __init__(self) -> None:
            super().__init__()
            self.point_index = 0
            self.layout_name = available_layouts(str(self.current_point["folder"]))[0]
            self.display_mode = "graphics"
            self.frame_time = 0.55
            self.profile_name = "balanced"
            self.runs = 1
            self.seed_text = "7"

        @property
        def current_point(self) -> dict[str, object]:
            return WORKSHOP_POINTS[self.point_index]

        @property
        def current_layouts(self) -> list[str]:
            return available_layouts(str(self.current_point["folder"]))

        @property
        def current_profiles(self) -> list[tuple[str, str, str, list[str]]]:
            return PROFILES[str(self.current_point["algorithm"])]

        def compose(self) -> ComposeResult:
            yield Header(show_clock=True)
            yield Static(
                "  [bold #f0c040]TALLER 2[/]  [#58a6ff]Búsqueda local y juegos adversarios[/]  "
                "[dim]Selecciona punto, escenario y configuración; R ejecuta.[/]",
                classes="title-bar",
            )
            with Horizontal(id="shell"):
                with Vertical(id="point-panel", classes="panel"):
                    yield Static("PUNTOS DEL TALLER", classes="section-title")
                    yield ScrollableContainer(id="point-list")
                with Vertical(id="layout-panel", classes="panel"):
                    yield Static("", id="layout-title", classes="section-title")
                    yield ScrollableContainer(id="layout-grid")
                with Vertical(id="settings-panel", classes="panel"):
                    yield Static("CONFIGURACIÓN", classes="section-title")
                    with ScrollableContainer(id="settings-scroll"):
                        yield Static("", id="selected-info")
                        yield Static("Visualización", classes="setting-label")
                        yield Container(id="display-options")
                        yield Static("Velocidad de animación", classes="setting-label")
                        yield Container(id="speed-options")
                        yield Static("Perfil de búsqueda", classes="setting-label")
                        yield Container(id="profile-options")
                        yield Static("", id="profile-help")
                        yield Static("Repeticiones", id="runs-label", classes="setting-label")
                        yield Container(id="runs-options")
                        yield Static("Semilla aleatoria", id="seed-label", classes="setting-label")
                        yield SeedInput(value="7", placeholder="Número entero", id="seed-input")
                        yield Static("", id="command-preview")
                        with Container(id="action-buttons"):
                            yield Button("Ejecutar selección", id="run-button", classes="action-button", variant="primary")
                            yield Button("Salir", id="quit-button", classes="action-button")
                        yield Static("", id="status-line")
            yield Footer()

        def on_mount(self) -> None:
            self.rebuild_all()

        def clear_container(self, selector: str):
            container = self.query_one(selector)
            for child in list(container.children):
                child.remove()
            return container

        def rebuild_all(self) -> None:
            self.rebuild_points()
            self.rebuild_layouts()
            self.rebuild_options()
            self.refresh_details()

        def rebuild_points(self) -> None:
            container = self.clear_container("#point-list")
            for index, point in enumerate(WORKSHOP_POINTS):
                card = PointCard(index, point)
                if index == self.point_index:
                    card.add_class("--selected")
                container.mount(card)

        def rebuild_layouts(self) -> None:
            title = f"Selecciona un escenario  ·  {self.current_point['subtitle']}"
            self.query_one("#layout-title", Static).update(escape(title))
            container = self.clear_container("#layout-grid")
            for layout in self.current_layouts:
                info = layout_info(str(self.current_point["folder"]), layout)
                card = LayoutCard(self.current_point, info)
                if layout == self.layout_name:
                    card.add_class("--selected")
                container.mount(card)

        def rebuild_option_group(self, selector: str, group: str, options: list[tuple[object, str]], selected: object) -> None:
            container = self.clear_container(selector)
            for value, label in options:
                card = OptionCard(group, value, label)
                if value == selected:
                    card.add_class("--selected")
                container.mount(card)

        def update_layout_selection(self) -> None:
            """Actualiza el mapa seleccionado sin reemplazar la tarjeta enfocada."""
            for card in self.query(LayoutCard):
                if card.layout_name == self.layout_name:
                    card.add_class("--selected")
                else:
                    card.remove_class("--selected")

        def update_option_selection(self, group: str, selected: object) -> None:
            """Actualiza una opción sin dejar el foco en un widget eliminado."""
            for card in self.query(OptionCard):
                if card.option_group != group:
                    continue
                if card.option_value == selected:
                    card.add_class("--selected")
                else:
                    card.remove_class("--selected")

        def focus_point(self, index: int) -> None:
            """Devuelve el foco a la tarjeta reconstruida del punto activo."""
            for card in self.query(PointCard):
                if card.index == index:
                    card.focus()
                    return

        def rebuild_options(self) -> None:
            self.rebuild_option_group("#display-options", "display", DISPLAY_MODES, self.display_mode)
            self.rebuild_option_group("#speed-options", "speed", SPEEDS, self.frame_time)
            self.rebuild_option_group(
                "#profile-options",
                "profile",
                [(name, label) for name, label, _description, _args in self.current_profiles],
                self.profile_name,
            )
            self.rebuild_option_group("#runs-options", "runs", RUN_COUNTS, self.runs)
            self.query_one("#profile-help", Static).update(f"[dim]{escape(self.active_profile()[2])}[/]")
            uses_randomness = self.current_point["mode"] == "optimization"
            self.query_one("#runs-label", Static).styles.display = (
                "block" if uses_randomness else "none"
            )
            self.query_one("#runs-options", Container).styles.display = (
                "block" if uses_randomness else "none"
            )
            self.query_one("#seed-label", Static).styles.display = (
                "block" if uses_randomness else "none"
            )
            self.query_one("#seed-input", Input).styles.display = (
                "block" if uses_randomness else "none"
            )

        def active_profile(self) -> tuple[str, str, str, list[str]]:
            for profile in self.current_profiles:
                if profile[0] == self.profile_name:
                    return profile
            return self.current_profiles[0]

        def refresh_details(self) -> None:
            point = self.current_point
            info = layout_info(str(point["folder"]), self.layout_name)
            mode_label = "Optimización" if point["mode"] == "optimization" else "Juego adversario"
            lines = [
                f"[bold #f0c040]{escape(str(point['title']))}[/]",
                f"[dim]{escape(str(point['description']))}[/]",
                "",
                f"Escenario: [#58a6ff]{escape(self.layout_name)}[/]",
                f"Mapa: [bold]{escape(layout_meta_label(point, info))}[/]",
                f"Propósito: [dim]{escape(LAYOUT_PURPOSES.get(self.layout_name, 'Escenario experimental.'))}[/]",
                f"Modo: [#58a6ff]{mode_label}[/]",
                f"Algoritmo: [#58a6ff]{escape(str(point['algorithm']))}[/]",
            ]
            if point["mode"] == "optimization":
                lines.append(f"Nodos críticos: [bold]{info['critical']}[/] · Radio: [bold]{info['radius']}[/]")
            else:
                lines.append(f"Terminales críticas: [bold]{info['critical']}[/]")
            self.query_one("#selected-info", Static).update("\n".join(lines))
            self.query_one("#command-preview", Static).update(
                "[bold]Comando generado[/]\n[dim]"
                + escape(command_to_multiline_text(self.build_command(preview=True)))
                + "[/]"
            )

        def build_command(self, preview: bool = False) -> list[str]:
            command = [
                "python" if preview else sys.executable,
                "main.py" if preview else str(MAIN_FILE),
                "-m",
                str(self.current_point["mode"]),
                "-a",
                str(self.current_point["algorithm"]),
                "-l",
                self.layout_name,
            ]
            if self.current_point["mode"] == "optimization":
                command.extend(
                    [
                        "--seed",
                        self.seed_text.strip() or "7",
                        "-n",
                        str(self.runs),
                    ]
                )
            command.extend(
                [
                    "-x",
                    str(self.frame_time),
                    *self.active_profile()[3],
                ]
            )
            if self.display_mode == "text":
                command.append("-t")
            elif self.display_mode == "quiet":
                command.append("-q")
            return command

        @on(PointCard.Selected)
        def on_point_selected(self, event: PointCard.Selected) -> None:
            self.point_index = event.index
            self.layout_name = self.current_layouts[0]
            self.profile_name = "balanced"
            self.rebuild_all()
            self.call_after_refresh(self.focus_point, event.index)

        @on(LayoutCard.Selected)
        def on_layout_selected(self, event: LayoutCard.Selected) -> None:
            self.layout_name = event.layout_name
            self.update_layout_selection()
            self.refresh_details()

        @on(OptionCard.Selected)
        def on_option_selected(self, event: OptionCard.Selected) -> None:
            if event.option_group == "display":
                self.display_mode = str(event.option_value)
            elif event.option_group == "speed":
                self.frame_time = float(event.option_value)
            elif event.option_group == "profile":
                self.profile_name = str(event.option_value)
            elif event.option_group == "runs":
                self.runs = int(event.option_value)
            self.update_option_selection(event.option_group, event.option_value)
            if event.option_group == "profile":
                self.query_one("#profile-help", Static).update(
                    f"[dim]{escape(self.active_profile()[2])}[/]"
                )
            self.refresh_details()

        @on(Input.Changed, "#seed-input")
        def on_seed_changed(self, event: Input.Changed) -> None:
            self.seed_text = event.value
            self.refresh_details()

        @on(Button.Pressed)
        def on_button_pressed(self, event: Button.Pressed) -> None:
            if event.button.id == "run-button":
                self.action_run()
            elif event.button.id == "quit-button":
                self.action_quit()

        def action_run(self) -> None:
            if self.current_point["mode"] == "optimization":
                try:
                    int(self.seed_text.strip())
                except ValueError:
                    self.query_one("#status-line", Static).update(
                        "[red]La semilla debe ser un número entero.[/]"
                    )
                    return
            command = self.build_command()
            self.query_one("#status-line", Static).update(
                "Ejecutando la selección. Al cerrar la visualización, volverás al menú."
            )
            with self.suspend():
                print("\nEjecutando:\n  " + command_to_text(command) + "\n")
                result = subprocess.run(command, cwd=str(PROJECT_DIR), check=False)
                if result.returncode == 0:
                    print("\nEjecución finalizada correctamente.")
                else:
                    print(f"\nLa ejecución terminó con código {result.returncode}.")
                input("Presiona Enter para volver al menú...")

        def action_quit(self) -> None:
            self.exit()
