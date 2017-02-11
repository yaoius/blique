from genalg.biology import *
import time

max_iter = 5000

def evolve(pop, iterations=None, elitism=True, mutation=True):
    """Evolves a population ITERATION times"""
    gen = self.stepper(pop, iterations, elitism, mutation)
    for current_pop in gen:
        pass
    return current_pop

def stepper(pop, iterations=None, tournament_size=10, elitism=True, mutation=True):
    """Returns a generator. Calling next on this object will call step once and return
    the resulting population."""
    iterations = iterations or max_iter
    for i in range(iterations):
        yield pop
        pop = step(pop, iterations, tournament_size, elitism, mutation)

def step(pop, tournament_size=10, elitism=True, mutation=True):
    """
    Performs selection, crossover, then mutation on the current population.
    tournament_size: size of tournment for tournament selection
    elitism: keep fittest individual if true for next population
    mutation: include mutation when creating offspring in crossover
    """
    new_pop = Population(size=pop.size, member=pop.member, initialize=False)
    if elitism:
        new_pop.add_individual(pop.get_fittest())
    elitism_offset = 1 if elitism else 0
    t_size = min(tournament_size, pop.size)

    for _ in range(elitism_offset, pop.size):
        parent1 = pop.tournament(t_size)
        parent2 = pop.tournament(t_size)
        offspring = parent1.mate(parent2, mutation)
        new_pop.add_individual(offspring)
    return new_pop
