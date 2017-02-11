import random

class Genome:
    """Represents genetic information as a bitarray"""

    mutation_rate = 0.015
    substitution_rate = 0.8
    deletion_rate = 0.1
    insertion_rate = 0.1

    MUTATION_SUB = 0
    MUTATION_INS = 0
    MUTATION_DEL = 0

    def __init__(self, genome_length, sequence=None):
        if sequence:
            self.sequence = sequence
        else:
            self.sequence = list()
            self.sequence.extend([random.choice([1, 0]) for _ in range(genome_length)])
        self.length = genome_length
        self.mutation_rates =   {
                                self.substitution: self.substitution_rate,
                                self.deletion: self.deletion_rate,
                                self.insertion: self.insertion_rate,
                                }

    def crossover(self, other, mutation):
        """
        Returns a new Gene that is the result of randomly selecting from either parent
        Gene. When Genes are unequally sized, 0's are appended to the shorter until they
        are equal in length.
        """
        crossed = list()
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
        """
        Mutates a gene according to the rates defined for the class
        """
        mutation_chance = random.randint(0, 100)
        if mutation_chance > Genome.mutation_rate * 100:
            return 0

        mutation = self.choose_mutation()
        mutation_locus = random.randint(0, self.length - 1)
        mutation_type = mutation(mutation_locus)
        return mutation_type

    def choose_mutation(self):
        """
        Returns the mutation function to use based on the mutation rates defined for
        the class
        """
        total = sum([w for m, w in self.mutation_rates.items()])
        r = random.uniform(0, total)
        upto = 0
        for m, w in self.mutation_rates.items():
            if upto + w >= r:
                return m
            upto += w
        return False

    def substitution(self, location):
        """
        Flips a the bit at index LOCATION
        """
        self.sequence[location] = self.sequence[location] ^ 1
        return Genome.MUTATION_SUB

    def deletion(self, location):
        """
        Deletes the bit at index LOCATION
        """
        self.sequence.pop(location)
        return Genome.MUTATION_DEL

    def insertion(self, location):
        """
        Adds a random bit at LOCATION
        """
        self.sequence.insert(location, random.choice([0, 1]))
        return Genome.MUTATION_DEL

    def subsequence(self, i, j):
        """
        Returns a slice of the bitarray
        TODO: Replace with slice override
        """
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
        """
        Crosses over the genes of SELF and OTHER. Attemps to mutate if MUTATION is true.
        """
        crossed_genome = Genome.crossover(self.genome, other.genome, mutation)
        return self.__class__(crossed_genome)

    def read_genome(self):
        """
        By default, returns the bit value of the gene's bitarray.
        """
        out = 0
        for bit in self.genome:
            out = (out << 1) | bit
        self.val = out

    def fitness(self):
        """
        Return the binary value of the gene's bitarray
        """
        return self.val

    def __repr__(self):
        return 'ind' + str(self.genome)[3:]


class Population:

    default_size = 20

    def __init__(self, size=default_size, member=Individual, initialize=True):
        """
        Initializes a random population of MEMBER objects of size SIZE if INITIALIZE is true.
        Sets self's member class to MEMBER and size to SIZE
        """
        self.member = member
        self.size = size
        self.individuals = [member() for _ in range(size)] if initialize else list()

    def set_population(self, ind_list):
        """
        Replaces the current list of individuals with IND_LIST
        """
        self.individuals = ind_list

    def add_individual(self, ind):
        """
        Adds IND to the populations individuals
        """
        self.individuals.append(ind)

    def get_fittest(self):
        """
        Returns the fittest individual in the population
        """
        return max(self.individuals, key=lambda i: i.fitness())

    def avg_fitness(self):
        """
        Returns the average fitness of individuals in the population
        """
        return sum([i.fitness() for i in self.individuals]) / len(self.individuals)

    def tournament(self, size=10):
        """
        Runs a tournamnet select of size SIZE, choosing SIZE random members from the
        population and choosing the fittest from the sample
        """
        t = Population(member=self.member, initialize=False)
        t.set_population(random.sample(self.individuals, size))
        return t.get_fittest()

    def __iter__(self):
        return iter(self.individuals)

    def __repr__(self):
        return 'pop' + str(self.individuals)
