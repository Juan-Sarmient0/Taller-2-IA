import argparse
from pathlib import Path
import statistics
import sys

from optimization.problem import SmartGridOptimizationProblem
from optimization.runner import run_optimization
from view.display import NullDisplay
from view.text_display import TextDisplay
from world.layout import GridLayout
from world.runner import run_game


ROOT = Path(__file__).resolve().parent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Taller 2 - Red Centinela")
    parser.add_argument("-m", "--mode", choices=("optimization", "adversarial"), required=True)
    parser.add_argument("-a", "--algorithm", required=True)
    parser.add_argument("-l", "--layout", required=True)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("-n", "--runs", type=int, default=1)
    parser.add_argument("-q", "--quiet", action="store_true")
    parser.add_argument("-t", "--text", action="store_true")
    parser.add_argument("-x", "--frame-time", type=float, default=0.55)

    parser.add_argument("--iterations", type=int, default=500)
    parser.add_argument("--temperature", type=float, default=20.0)
    parser.add_argument("--cooling", type=float, default=0.97)
    parser.add_argument("--population", type=int, default=40)
    parser.add_argument("--generations", type=int, default=100)
    parser.add_argument("--mutation", type=float, default=0.05)
    parser.add_argument("--elite", type=int, default=2)

    parser.add_argument("-d", "--depth", type=int, default=2)
    parser.add_argument("--max-rounds", type=int, default=60)
    return parser


def get_display(args):
    if args.quiet:
        return NullDisplay()
    if args.text:
        return TextDisplay()
    try:
        from view.graphics_display import GraphicsDisplay

        return GraphicsDisplay(args.frame_time)
    except (ImportError, RuntimeError):
        print("No fue posible iniciar Tkinter; se usará visualización textual.")
        return TextDisplay()


def optimization_layout(name: str) -> Path:
    path = Path(name)
    if path.exists():
        return path
    if path.suffix != ".json":
        path = ROOT / "layouts" / "optimization" / f"{name}.json"
    return path


def adversarial_layout(name: str) -> Path:
    path = Path(name)
    if path.exists():
        return path
    if path.suffix != ".lay":
        path = ROOT / "layouts" / "adversarial" / f"{name}.lay"
    return path


def main() -> None:
    if len(sys.argv) == 1:
        from menu import main as menu_main

        raise SystemExit(menu_main())

    args = build_parser().parse_args()
    if args.runs < 1:
        raise SystemExit("--runs debe ser al menos 1")
    if args.mode == "adversarial" and args.runs != 1:
        raise SystemExit("--runs solo se utiliza en el modo optimization")
    if args.depth < 1:
        raise SystemExit("--depth debe ser al menos 1 ply")
    if args.max_rounds < 1:
        raise SystemExit("--max-rounds debe ser al menos 1")
    display = get_display(args)
    original_seed = args.seed

    if args.mode == "optimization":
        problem = SmartGridOptimizationProblem(optimization_layout(args.layout))
        results = []
        elapsed = []
        for run in range(args.runs):
            args.seed = original_seed + run
            result, seconds = run_optimization(problem, args.algorithm, args)
            results.append(result)
            elapsed.append(seconds)
        best = max(results, key=lambda item: item.best_score)
        scores = [item.best_score for item in results]
        print(
            f"{args.algorithm} | mejor={best.best_score:.2f} | "
            f"promedio={statistics.mean(scores):.2f} | "
            f"desviación={statistics.pstdev(scores):.2f} | "
            f"evaluaciones_promedio="
            f"{statistics.mean(item.evaluations for item in results):.1f} | "
            f"tiempo_promedio={statistics.mean(elapsed):.6f}s"
        )
        display.show_optimization(problem, best)
        return

    layout = GridLayout.load(adversarial_layout(args.layout))
    trace, labels, stats = run_game(
        layout,
        args.algorithm,
        args.depth,
        args.max_rounds,
    )
    print(
        f"{args.algorithm} | profundidad={args.depth} plies | "
        f"acción_inicial={stats['initial_action']} | "
        f"resultado={stats['result']} | "
        f"finalización={stats['termination']} | "
        f"nodos={stats['nodes']} | "
        f"nodos_intruso={stats['intruder_nodes']} | "
        f"tiempo={float(stats['time']):.6f}s"
    )
    display.show_game(trace, labels, stats)


if __name__ == "__main__":
    main()
