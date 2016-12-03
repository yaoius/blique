from genalg.biology import *
import time

class GeneticAlg:

    max_iter = 5000

    def __init__(self, max_iter=max_iter):
        self.max_iter = max_iter

    def evolve(self, pop, iterations=max_iter, elitism=True, mutation=True):
        gen = self.stepper(pop, iterations, elitism, mutation)
        for current_pop in gen:
            pass
        return current_pop

    def stepper(self, pop, iterations=max_iter, tournament_size=10, elitism=True, mutation=True):
        for i in range(iterations):
            yield pop
            new_pop = Population(size=pop.size, member=pop.member, initialize=False)

            if elitism:
                new_pop.add_individual(pop.get_fittest())
            elitism_offset = 1 if elitism else 0

            for _ in range(elitism_offset, pop.size):
                t_size = min(tournament_size, pop.size)
                parent1 = pop.tournament(t_size)
                parent2 = pop.tournament(t_size)
                offspring = parent1.mate(parent2, mutation)
                new_pop.add_individual(offspring)

            pop = new_pop
