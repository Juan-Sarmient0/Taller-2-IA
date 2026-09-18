import math
import random

from optimization.problem import SmartGridOptimizationProblem
from optimization.result import Configuration, OptimizationResult


def configuration_score(
    problem: SmartGridOptimizationProblem, configuration: Configuration
) -> float:
    """
    Combina cobertura, redundancia y exposición en un puntaje a maximizar.

    Tips:
    - Use problem.score_components(configuration); ya retorna cobertura,
      redundancia y exposición en ese orden.
    """
    coverage, redundancy, exposure = problem.score_components(configuration)
    return coverage - redundancy - exposure


def hill_climbing(
    problem: SmartGridOptimizationProblem,
    initial_configuration: Configuration,
    max_iterations: int = 500,
) -> OptimizationResult:
    """
    Ejecuta ascenso de colina con mejora estricta.

    Debe examinar todos los vecinos, seleccionar el de mayor puntaje y
    conservar el orden entregado por el problema para desempatar. La búsqueda
    termina cuando no existe una mejora estricta o se alcanza el límite.

    Tips:
    - problem.neighbors(current) retorna vecinos válidos en el orden que debe
      usarse para desempatar.
    - Cada llamada a configuration_score(...) cuenta como una evaluación.
    - Inicialice los historiales con la configuración inicial y agregue solo las
      mejoras aceptadas antes de retornar el OptimizationResult.
    """
    current = tuple(initial_configuration)
    current_score = configuration_score(problem, current)

    
    evaluations = 1 #configuración inicial ya cuenta como una evaluacion
    iterations = 0 #conteo de movimientos aceptados
    history = [current]
    score_history = [current_score]
    searching = True

    while iterations < max_iterations and searching:
        neighbors = problem.neighbors(current) #todos los vecinos de la configuracion actual

        if len(neighbors) == 0: # si no existen vecinos la busqueda termina
            searching = False

        else:
            best_neighbor = None #al inicio no hay un mejor vecino
            best_neighbor_score = float("-inf")

            for neighbor in neighbors:
                neighbor_score = configuration_score(
                    problem,
                    neighbor
                )
                evaluations += 1

                # > y no >= para conservar el primer vecino en caso de empate
                if neighbor_score > best_neighbor_score:
                    best_neighbor = neighbor
                    best_neighbor_score = neighbor_score

            if best_neighbor_score > current_score: #solo si es mejor
                current = best_neighbor
                current_score = best_neighbor_score
                iterations += 1
                history.append(current)
                score_history.append(current_score)

            else:
                # si ningún vecino mejora al estado actual, se llega a un máximo local y termina
                searching = False

    return OptimizationResult(
        best_configuration=current,
        best_score=current_score,
        evaluations=evaluations,
        iterations=iterations,
        history=history,
        score_history=score_history,
    )


def cooling_schedule(initial_temperature: float, cooling_rate: float, iteration: int) -> float:
    """
    Retorna el programa geométrico T(t) = T0 * alpha**t.

    Esta función se invoca desde simulated_annealing en cada iteración.
    """
    return initial_temperature* (cooling_rate**iteration)

def simulated_annealing(
    problem: SmartGridOptimizationProblem,
    initial_configuration: Configuration,
    initial_temperature: float = 20.0,
    cooling_rate: float = 0.97,
    max_iterations: int = 500,
    rng: random.Random | None = None,
) -> OptimizationResult:
    """
    Ejecuta recocido simulado para un problema de maximización.

    Debe proponer un vecino aleatorio por iteración, aceptar siempre las
    mejoras y aplicar exp(delta / temperature) en los demás casos. El estado
    actual y el mejor estado encontrado deben conservarse por separado.

    Tips:
    - Seleccione el candidato con rng.choice(problem.neighbors(current)) y use
      exclusivamente rng para conservar la reproducibilidad.
    - Obtenga la temperatura con cooling_schedule(...) y calcule la aceptación
      con delta = puntaje_candidato - puntaje_actual y math.exp(...).
    - Mantenga separados el estado actual y el mejor encontrado; registre el
      estado actual después de cada intento, incluso si se rechaza.
    - Detenga la ejecución cuando la temperatura alcance minimum_temperature.
    """
    rng = rng or random.Random()
    minimum_temperature = 1e-9

    current = tuple(initial_configuration) # Estado actual
    current_score = configuration_score(problem, current)
    best_configuration = current
    best_score = current_score

    evaluations = 1  
    iterations = 0   
    history = [current]
    score_history = [current_score]

    for iteration in range(max_iterations):
        temperature = cooling_schedule(initial_temperature, cooling_rate, iteration)
        if temperature <= minimum_temperature:
            break

        neighbors = problem.neighbors(current)
        if not neighbors:
            break

        candidate = rng.choice(neighbors)
        candidate_score = configuration_score(problem, candidate)
        evaluations += 1

        delta = candidate_score - current_score
        if delta > 0 or rng.random() < math.exp(delta / temperature):
            current = candidate
            current_score = candidate_score

        iterations += 1
        history.append(current)    
        score_history.append(current_score)

        if current_score > best_score:  
            best_configuration = current
            best_score = current_score

    return OptimizationResult(
        best_configuration=best_configuration,
        best_score=best_score,
        evaluations=evaluations,
        iterations=iterations,
        history=history,
        score_history=score_history,
    )


def one_point_crossover(
    parent1: Configuration, parent2: Configuration, rng: random.Random
) -> tuple[Configuration, Configuration]:
    """
    Realiza un cruce de un punto y retorna dos descendientes.

    La reparación de la cantidad de módulos se realiza posteriormente.

    Tips:
    - Seleccione con rng un corte interior, entre las posiciones 1 y len-1.
    - Cada descendiente combina el prefijo de un padre con el sufijo del otro.
    - Retorne tuplas y no repare aquí los descendientes.
    """
    if len(parent1) != len(parent2):
        raise ValueError("Los padres deben tener la misma longitud")
    if len(parent1) < 2:
        return parent1, parent2

    corte =rng.randint(1, len(parent1)-1)
    descendiente1 = tuple(parent1[:corte] + tuple(parent2[corte:]) )
    descendiente2 = tuple(parent2[:corte] + tuple(parent1[corte:]) )
    return descendiente1, descendiente2
    

def swap_mutation(
    individual: Configuration, mutation_probability: float, rng: random.Random
) -> Configuration:
    """
    Aplica mutación por intercambio con la probabilidad indicada.

    Cuando ocurre una mutación, intercambia un bit activo y uno inactivo para
    conservar la cantidad de módulos instalados.

    Tips:
    - Use rng.random() para decidir si se aplica la mutación.
    - Identifique por separado los índices activos e inactivos y seleccione uno
      de cada grupo con rng.choice(...).
    - Si alguno de los dos grupos está vacío, no hay un intercambio posible.
    - Retorne una tupla nueva; no modifique el individuo recibido.
    """

    if rng.random() >= mutation_probability:
        return tuple(individual)

    active = [index for index, bit in enumerate(individual) if bit == 1]
    inactive = [index for index, bit in enumerate(individual) if bit == 0]

    if not active or not inactive:
        return tuple(individual)

    active_index = rng.choice(active)
    inactive_index = rng.choice(inactive)

    mutated = list(individual)
    mutated[active_index], mutated[inactive_index] = (
        mutated[inactive_index],
        mutated[active_index],
    )
    return tuple(mutated)
  
def genetic_algorithm(
    problem: SmartGridOptimizationProblem,
    population_size: int = 40,
    generations: int = 100,
    mutation_probability: float = 0.05,
    elite_size: int = 2,
    rng: random.Random | None = None,
) -> OptimizationResult:
    """
    Ejecuta un algoritmo genético generacional.

    Debe integrar la población inicial, la selección por torneo, el cruce, la
    reparación, la mutación y el elitismo entregados por el proyecto. Retorna
    el mejor individuo encontrado durante toda la ejecución.

    Tips:
    - Use problem.initial_population(...), problem.tournament_select(...) y
      problem.repair_configuration(...) para las operaciones ya entregadas.
    - Aplique one_point_crossover(...) antes de reparar y swap_mutation(...)
      después de la reparación.
    - Conserve los mejores individuos por elitismo y registre en los historiales
      el mejor global de cada generación.
    """
    rng = rng or random.Random()
    if population_size < 2:
        raise ValueError("La población debe tener al menos dos individuos")
    if generations < 0:
        raise ValueError("El número de generaciones no puede ser negativo")
    if not 0.0 <= mutation_probability <= 1.0:
        raise ValueError("La probabilidad de mutación debe estar entre 0 y 1")
    if not 0 <= elite_size <= population_size:
        raise ValueError("elite_size debe estar entre 0 y population_size")


    rng = rng or random.Random()
    if population_size < 2:
        raise ValueError("La población debe tener al menos dos individuos")
    if generations < 0:
        raise ValueError("El número de generaciones no puede ser negativo")
    if not 0.0 <= mutation_probability <= 1.0:
        raise ValueError("La probabilidad de mutación debe estar entre 0 y 1")
    if not 0 <= elite_size <= population_size:
        raise ValueError("elite_size debe estar entre 0 y population_size")

    # Población inicial y su evaluación
    population = problem.initial_population(population_size, rng)
    scores = [configuration_score(problem, individual) for individual in population]
    evaluations = len(population)

    # Mejor global de toda la ejecución; no solo de la última generación
    best_index = max(range(len(population)), key=lambda i: scores[i])
    best_configuration = population[best_index]
    best_score = scores[best_index]

    history = [best_configuration]
    score_history = [best_score]

    for _ in range(generations):
        ranked = sorted(range(len(population)), key=lambda i: scores[i], reverse=True)
        new_population = [population[i] for i in ranked[:elite_size]]

        while len(new_population) < population_size:
            parent1 = problem.tournament_select(population, scores, rng)
            parent2 = problem.tournament_select(population, scores, rng)

            child1, child2 = one_point_crossover(parent1, parent2, rng)
            child1 = problem.repair_configuration(child1, rng)
            child2 = problem.repair_configuration(child2, rng)
            child1 = swap_mutation(child1, mutation_probability, rng)
            child2 = swap_mutation(child2, mutation_probability, rng)

            new_population.append(child1)
            if len(new_population) < population_size:
                new_population.append(child2)

        population = new_population
        scores = [configuration_score(problem, individual) for individual in population]
        evaluations += len(population)

        generation_best = max(range(len(population)), key=lambda i: scores[i])
        if scores[generation_best] > best_score:
            best_configuration = population[generation_best]
            best_score = scores[generation_best]

        history.append(best_configuration)
        score_history.append(best_score)

    return OptimizationResult(
        best_configuration=best_configuration,
        best_score=best_score,
        evaluations=evaluations,
        iterations=generations,
        history=history,
        score_history=score_history,
    )    
