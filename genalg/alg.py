from community import *
import time

class GeneticAlg:

    max_iter = 250

    def __init__(self, max_iter=max_iter):
        self.max_iter = max_iter

    def evolve(self, pop, iterations=max_iter, elitism=True, mutation=True):
        gen = self.stepper(pop, iterations, elitism, mutation)
        for current_pop in gen:
            pass
        return current_pop

    def stepper(self, pop, iterations=max_iter, elitism=True, mutation=True):
        for i in range(iterations):
            self.log(i, pop)
            new_pop = Population(member=pop.member, initialize=False)

            if elitism:
                new_pop.add_individual(pop.get_fittest())
            elitism_offset = 1 if elitism else 0

            for _ in range(elitism_offset, pop.size):
                parent1 = pop.tournament()
                parent2 = pop.tournament()
                offspring = parent1.mate(parent2, mutation)
                new_pop.add_individual(offspring)

            pop = new_pop
            yield pop

    def log(self, i, pop):
        print('\n',i,pop)
        print('FITTEST:', pop.get_fittest(), pop.get_fittest().fitness())
        print('avg_fitness:', pop.avg_fitness())
