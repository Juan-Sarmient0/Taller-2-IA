import random
import time

import algorithms.optimization as optimization_algorithms
from algorithms.optimization import genetic_algorithm, hill_climbing, simulated_annealing
from optimization.problem import SmartGridOptimizationProblem
from optimization.result import Configuration, OptimizationResult


class _RecordingRandom(random.Random):
    """Fuente aleatoria que conserva las selecciones necesarias para animar."""

    def __init__(self, seed: int) -> None:
        super().__init__(seed)
        self.selected: list[object] = []

    def choice(self, sequence):
        selected = super().choice(sequence)
        self.selected.append(selected)
        return selected


def _crossover_cut(
    parent1: Configuration,
    parent2: Configuration,
    child1: Configuration,
    child2: Configuration,
) -> int | None:
    for cut in range(1, len(parent1)):
        if (
            child1 == parent1[:cut] + parent2[cut:]
            and child2 == parent2[:cut] + parent1[cut:]
        ):
            return cut
    return None


def _run_genetic_algorithm(
    problem: SmartGridOptimizationProblem,
    args,
    rng: random.Random,
) -> tuple[OptimizationResult, list[dict[str, object]]]:
    """Ejecuta GA y registra sus operadores sin intervenir su implementación."""
    operations: list[dict[str, object]] = []
    pending: list[dict[str, object]] = []
    original_crossover = optimization_algorithms.one_point_crossover
    original_mutation = optimization_algorithms.swap_mutation

    def traced_crossover(parent1, parent2, source):
        child1, child2 = original_crossover(parent1, parent2, source)
        pending.clear()
        cut = _crossover_cut(parent1, parent2, child1, child2)
        for child in (child1, child2):
            pending.append(
                {
                    "parent1": parent1,
                    "parent2": parent2,
                    "crossover_cut": cut,
                    "offspring_raw": child,
                }
            )
        return child1, child2

    def traced_mutation(individual, probability, source):
        mutated = original_mutation(individual, probability, source)
        detail = pending.pop(0) if pending else {}
        detail.update(
            {
                "offspring_repaired": individual,
                "offspring_mutated": mutated,
                "offspring_final": mutated,
                "repair_applied": detail.get("offspring_raw") != individual,
                "mutation_applied": individual != mutated,
            }
        )
        operations.append(detail)
        return mutated

    optimization_algorithms.one_point_crossover = traced_crossover
    optimization_algorithms.swap_mutation = traced_mutation
    try:
        result = genetic_algorithm(
            problem,
            population_size=args.population,
            generations=args.generations,
            mutation_probability=args.mutation,
            elite_size=args.elite,
            rng=rng,
        )
    finally:
        optimization_algorithms.one_point_crossover = original_crossover
        optimization_algorithms.swap_mutation = original_mutation
    return result, operations


def _attach_sa_details(
    result: OptimizationResult,
    problem: SmartGridOptimizationProblem,
    candidates: list[object],
    initial_temperature: float,
    cooling_rate: float,
) -> None:
    details: list[dict[str, object]] = [{}]
    for index, current in enumerate(result.history[1:], start=1):
        if index - 1 >= len(candidates):
            details.append({})
            continue
        candidate = candidates[index - 1]
        previous = result.history[index - 1]
        candidate_score = optimization_algorithms.configuration_score(problem, candidate)
        previous_score = optimization_algorithms.configuration_score(problem, previous)
        delta = candidate_score - previous_score
        accepted = current == candidate
        event = "Movimiento rechazado"
        if accepted:
            event = (
                "Mejora aceptada"
                if delta > 0
                else "Deterioro aceptado"
                if delta < 0
                else "Movimiento lateral aceptado"
            )
        details.append(
            {
                "event": event,
                "iteration": index,
                "temperature": initial_temperature * (cooling_rate ** (index - 1)),
                "delta": delta,
                "candidate": candidate,
                "previous": previous,
                "accepted": accepted,
            }
        )
    result._visualization_details = details


def _attach_ga_details(
    result: OptimizationResult,
    problem: SmartGridOptimizationProblem,
    operations: list[dict[str, object]],
    population_size: int,
    elite_size: int,
) -> None:
    details: list[dict[str, object]] = [{} for _ in result.history]
    operations_per_generation = max(1, population_size - elite_size)
    for generation in range(1, len(details)):
        operation_index = (generation - 1) * operations_per_generation
        if operation_index >= len(operations):
            break
        operation = operations[operation_index]
        parent = operation.get("parent1")
        offspring = operation.get("offspring_final")
        if isinstance(parent, tuple) and isinstance(offspring, tuple):
            operation["delta"] = optimization_algorithms.configuration_score(
                problem, offspring
            ) - optimization_algorithms.configuration_score(problem, parent)
        details[generation] = operation
    result._visualization_details = details


def run_optimization(problem: SmartGridOptimizationProblem, algorithm: str, args) -> tuple[OptimizationResult, float]:
    record_visualization = not getattr(args, "quiet", False) and not getattr(
        args, "text", False
    )
    rng = _RecordingRandom(args.seed) if record_visualization else random.Random(args.seed)
    start = time.perf_counter()
    if algorithm == "hillClimbing":
        initial = problem.random_configuration(rng)
        result = hill_climbing(problem, initial, args.iterations)
    elif algorithm == "simulatedAnnealing":
        initial = problem.random_configuration(rng)
        if isinstance(rng, _RecordingRandom):
            rng.selected.clear()
        result = simulated_annealing(
            problem,
            initial,
            initial_temperature=args.temperature,
            cooling_rate=args.cooling,
            max_iterations=args.iterations,
            rng=rng,
        )
        if isinstance(rng, _RecordingRandom):
            _attach_sa_details(
                result,
                problem,
                rng.selected,
                args.temperature,
                args.cooling,
            )
    elif algorithm == "geneticAlgorithm":
        if record_visualization:
            result, operations = _run_genetic_algorithm(problem, args, rng)
            _attach_ga_details(
                result,
                problem,
                operations,
                args.population,
                args.elite,
            )
        else:
            result = genetic_algorithm(
                problem,
                population_size=args.population,
                generations=args.generations,
                mutation_probability=args.mutation,
                elite_size=args.elite,
                rng=rng,
            )
    else:
        raise ValueError(f"Algoritmo de optimización desconocido: {algorithm}")
    result.metadata.setdefault("algorithm", algorithm)
    if algorithm == "hillClimbing":
        termination = (
            "Límite de iteraciones"
            if result.iterations >= args.iterations
            else "Sin mejora estricta"
        )
        result.metadata.setdefault("termination", termination)
    elif algorithm == "simulatedAnnealing":
        result.metadata.setdefault("initial_temperature", args.temperature)
        result.metadata.setdefault("cooling_rate", args.cooling)
        termination = (
            "Límite de iteraciones"
            if result.iterations >= args.iterations
            else "Temperatura mínima o ausencia de vecinos"
        )
        result.metadata.setdefault("termination", termination)
    elif algorithm == "geneticAlgorithm":
        result.metadata.setdefault("population_size", args.population)
        result.metadata.setdefault("generations", args.generations)
        result.metadata.setdefault("termination", "Generaciones completadas")
    return result, time.perf_counter() - start
