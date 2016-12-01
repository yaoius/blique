import random
from bitarray import bitarray

class Genome:

    mutation_rate = 0.015
    substitution_rate = 0.8
    deletion_rate = 0.1
    insertion_rate = 0.1

    def __init__(self, genome_length, sequence=None):
        if sequence:
            self.sequence = sequence
        else:
            self.sequence = bitarray(endian='big')
            self.sequence.extend([random.choice([1, 0]) for _ in range(genome_length)])
        self.length = genome_length
        self.mutation_rates =   {
                                self.substitution: self.substitution_rate,
                                self.deletion: self.deletion_rate,
                                self.insertion: self.insertion_rate,
                                }

    def crossover(self, other, mutation):
        crossed = bitarray(endian='big')
        seq1 = self.sequence[:]
        seq2 = other.sequence[:]

        diff = self.length - other.length
        if diff > 0:
            seq2.extend([0] * diff)
        elif diff < 0:
            seq1.extend([0] * abs(diff))

        for pair in zip(seq1, seq2):
            crossed.append(random.choice(pair))

        crossed_genome = Genome(len(crossed), crossed)
        if mutation:
            crossed_genome.mutate()

        return crossed_genome

    def mutate(self):
        mutation_chance = random.randint(0, 100)
        if mutation_chance > Genome.mutation_rate * 100:
            return 0

        mutation = self.choose_mutation()
        mutation_locus = random.randint(0, self.length - 1)
        mutation_type = mutation(mutation_locus)
        return mutation_type

    def choose_mutation(self):
        total = sum([w for m, w in self.mutation_rates.items()])
        r = random.uniform(0, total)
        upto = 0
        for m, w in self.mutation_rates.items():
            if upto + w >= r:
                return m
            upto += w
        return False

    def substitution(self, location):
        self.sequence[location] = self.sequence[location] ^ 1
        return 1

    def deletion(self, location):
        self.sequence.pop(location)
        return 2

    def insertion(self, location):
        self.sequence.insert(location, random.choice([0, 1]))
        return 3

    def subsequence(self, i, j):
        return self.sequence[i:j]

    def __iter__(self):
        return iter([int(b) for b in self.sequence])

    def __repr__(self):
        return 'gen' + str(self.sequence)[8:]


class Individual:

    genome_length = 20

    def __init__(self, genome=None):
        if genome:
            self.genome = genome
            self.genome_length = genome.length
        else:
            self.genome = Genome(self.genome_length)
        self.read_genome()

    def mate(self, other, mutation):
        crossed_genome = Genome.crossover(self.genome, other.genome, mutation)
        return self.__class__(crossed_genome)

    def read_genome(self):
        out = 0
        for bit in self.genome:
            out = (out << 1) | bit
        self.val = out

    def fitness(self):
        return self.val

    def __repr__(self):
        return 'ind' + str(self.genome)[3:]


class Population:

    default_size = 20

    def __init__(self, size=default_size, member=Individual, initialize=True):
        self.member = member
        self.size = size
        self.individuals = [member() for _ in range(size)] if initialize else list()

    def set_population(self, ind_list):
        self.individuals = ind_list

    def add_individual(self, ind):
        self.individuals.append(ind)

    def get_fittest(self):
        return max(self.individuals, key=lambda i: i.fitness())

    def avg_fitness(self):
        return sum([i.fitness() for i in self.individuals]) / len(self.individuals)

    def tournament(self, size=10):
        t = Population(member=self.member, initialize=False)
        t.set_population(random.sample(self.individuals, size))
        return t.get_fittest()

    def __iter__(self):
        return iter(self.individuals)

    def __repr__(self):
        return 'pop' + str(self.individuals)
