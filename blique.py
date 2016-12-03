from genalg.alg import GeneticAlg
from genalg.biology import *
import random
import time
import curses
import math

NORTH = 0
EAST = 1
SOUTH = 2
WEST = 3
LEFT = -1
RIGHT = 1

ANIMATION_SPEED = 0.1

def sigmoid(x):
  return 1 / (1 + math.exp(-x))

def addstr(stdscr, x, _y, s, color=None):
    try:
        if color:
            stdscr.addstr(y, x, s)
        else:
            stdscr.addstr(y, x, s)
    except:
        pass

def main(stdscr):
    curses.start_color()
    if not curses.has_colors():
        raise Exception('NO COLOR')
    height, width = curses.LINES, curses.COLS
    Blique.x = width // 2
    Blique.y = height // 2
    g = GeneticAlg()
    bliques = Population(size=10, member=Blique, initialize=True)
    for i, gen in enumerate(g.stepper(bliques, elitism=False)):
        environment = Environment(height, width, gen, stdscr)
        environment.update()
        environment.simulate(True)
        # key = stdscr.getkey()
        # if str(key) == 'q':
        #     break

class Blique(Individual):

    genome_length = 24
    max_move_distance = 3
    max_age = 50
    height, width = 3, 5
    x, y = 1, 1
    name_phenomes = [x + y for x in 'abcdefghijklmnoprstuvwxyz' for y in 'aeiouy']

    def __init__(self, parents=None, genome=None, coord=None):
        super().__init__(genome)
        self.parents = parents
        self.name = self.gen_name()
        if coord:
            self.x, self.y = coord
        self.alive = True
        self.age = 0
        self.distance_traveled = 0
        self.facing = random.randint(0, 3)
        self.set_eye()
        self.set_image()
        self.initial_state = self.state()

    def gen_name(self):
        name = ''
        if not self.parents:
            length = random.randint(2, 4)
            for i in range(length):
                name += random.choice(self.name_phenomes)
        else:
            p1, p2 = self.parents
            cut = random.randint(1, 2)
            name += p1[:cut*2]
            name += p2[cut*2:]
        return name.capitalize()

    def set_eye(self):
        if self.facing == NORTH:
            self.eye_x = self.x + self.width // 2
            self.eye_y = self.y
        elif self.facing == EAST:
            self.eye_x = self.x + self.width - 1
            self.eye_y = self.y + self.height // 2
        elif self.facing == SOUTH:
            self.eye_x = self.x + self.width // 2
            self.eye_y = self.y + self.height - 1
        elif self.facing == WEST:
            self.eye_x = self.x
            self.eye_y = self.y + self.height // 2

    def set_image(self):
        self.image = ['+' + '-' * (self.width - 2) + '+']
        for i in range(self.height - 2):
            self.image.append('|' + ' ' * (self.width - 2) + '|')
        self.image.append('+' + '-' * (self.width - 2) + '+')

    def mate(self, other, mutation):
        crossed_genome = Genome.crossover(self.genome, other.genome, mutation)
        child = Blique(genome=crossed_genome, parents=(self.name, other.name))
        return child

    def look_ahead(self):
        if not self.env:
            raise Exception('Blique not in an environemnt')
        if self.facing == NORTH:
            dx, dy = 0, -1
        elif self.facing == EAST:
            dx, dy = 1, 0
        elif self.facing == SOUTH:
            dx, dy = 0, 1
        elif self.facing == WEST:
            dx, dy = -1, 0
        x, y = self.eye_x + dx, self.eye_y + dy
        tile = self.env.get_tile(x, y)
        dist = 0
        while tile.passable:
            dist += 1
            x, y = x + dx, y + dy
            tile = self.env.get_tile(x, y)
        return dist

    def move(self, amt=1):
        if self.facing == NORTH:
            self.y -= amt
        elif self.facing == EAST:
            self.x += amt
        elif self.facing == SOUTH:
            self.y += amt
        elif self.facing == WEST:
            self.x -= amt
        self.distance_traveled += amt

    def turn(self, direction):
        self.facing = (self.facing + direction) % 4

    def get_next_move(self, inp):
        if random.choice([0, 1]):
            return lambda: self.move(random.randint(1, self.max_move_distance))
        else:
            return lambda: self.turn(random.choice([LEFT, RIGHT]))

    def get_tiles_under(self):
        if not self.env:
            raise Exception('Blique is not in an Environment')
        return [self.env.get_tile(self.x + dx, self.y + dy) for dx in range(self.width) for dy in range(self.height)]

    def simulate(self):
        while self.alive:
            self.step()

    def step(self):
        distance_to_obstacle = self.look_ahead()
        next_move = self.get_next_move(distance_to_obstacle)
        next_move()
        self.set_eye()
        if self.age > self.max_age or any(not tile.passable for tile in self.get_tiles_under()):
            self.alive = False
        else:
            self.age += ANIMATION_SPEED

    def read_genome(self):
        pass
        # self.brain = Brain(1, 2, 5)
        # genes = [self.read_gene(self.genome.subsequence(i, i+8)) for i in range(0, self.genome_length, 8)]
        # self.brain.set_layer1_weights([genes[:5]])
        # self.brain.set_layer2_weights([genes[5:7], genes[7:9], genes[9:11], genes[11:13], genes[13:]])

    def read_gene(self, gene):
        weight = 1
        for i in gene:
            weight << 1
            weight + i
        return sigmoid(weight)

    def fitness(self):
        return int(self.distance_traveled * self.age)

    def load_state(self, state):
        self.alive, self.age, self.distance_traveled, _, coord = state
        self.x, self.y = coord
        self.set_eye()

    def reset(self):
        self.load_state(self.initial_state)

    def bio(self):
        return self.name, self.parents

    def state(self):
        return self.alive, self.age, self.distance_traveled, self.fitness(), (self.x, self.y)

class Environment:

    def __init__(self, height, width, bliques, stdscr, grid=None):
        self.width = width
        self.height = height
        self.view_height = height - 2
        self.grid = grid or self.make_grid()
        self.bliques = bliques
        for ind in self.bliques:
            ind.env = self
        self.stdscr = stdscr

    def make_grid(self):
        grid = [None for _ in range(self.width * self.view_height)]
        for x in range(self.width):
            for y in range(self.view_height):
                if 0 < x < self.width - 1 and 0 < y < self.view_height - 1:
                    grid[y * self.width + x] = Tile()
                else:
                    grid[y * self.width + x] = Wall()
        return grid

    def get_tile(self, x, y):
        if x < 0 or x >= self.width:
            return Wall()
        if y < 0 or y >= self.view_height:
            return Wall()
        return self.grid[y * self.width + x]

    def add_blique(self, blique):
        self.bliques.add_individual(blique)
        blique.env = self

    def draw_blique(self, blique, color=None):
        y = blique.y
        for line in blique.image:
            addstr(self.stdscr, blique.x, y, line)
            y += 1
        addstr(self.stdscr, blique.eye_x, blique.eye_y, 'O')
        addstr(self.stdscr, blique.x, blique.y + blique.height, blique.name)
        self.stdscr.refresh()

    def undraw_blique(self, blique):
        for dy in range(blique.height):
            for dx in range(blique.width):
                x, y = blique.x + dx, blique.y + dy
                if y * self.width + x < len(self.grid):
                    char = str(self.grid[y * self.width + x])
                    addstr(self.stdscr, x, y, char)
        addstr(self.stdscr, blique.x, blique.y + blique.height, ' ' * len(blique.name))
        self.stdscr.refresh()

    def update_info(self):
        fittest = self.bliques.get_fittest()
        name, parents = fittest.bio()
        alive, age, distance, fitness, coord = fittest.state()
        info = 'fittest: {}, child of {}, lived for {} and traveled {}'.format(name, parents, int(age), distance)
        fitness = 'fitness: ' + str(fitness)
        addstr(self.stdscr, 0, self.height-2, ' ' * self.width)
        addstr(self.stdscr, 0, self.height-1, ' ' * self.width)
        addstr(self.stdscr, 0, self.height-2, info, color=curses.COLOR_GREEN)
        addstr(self.stdscr, 0, self.height-1, fitness)
        self.stdscr.refresh()

    def update(self):
        self.stdscr.clear()
        for x in range(self.width):
            for y in range(self.view_height):
                char = str(self.grid[y * self.width + x])
                addstr(self.stdscr, x, y, char)
        self.stdscr.refresh()
        self.update_info()
        for blique in self.bliques:
            self.draw_blique(blique)

    def simulate(self, animate=False):
        to_draw = [b for b in self.bliques if b.alive]
        while to_draw:
            for b in to_draw:
                if animate:
                    self.undraw_blique(b)
                b.step()
                if animate and b.alive:
                    self.update_info()
                    if b is self.bliques.get_fittest():
                        self.draw_blique(b, color=curses.color_pair(2))
                    else:
                        self.draw_blique(b)
                else:
                    to_draw.remove(b)
            time.sleep(ANIMATION_SPEED)
        for b in self.bliques:
            b.reset()

    def str_rep(self):
        grid = ''
        for y in range(self.view_height):
            for x in range(self.width):
                grid += str(self.grid[y * self.width + x])
            grid += '\n'
        return grid

class Brain:
    """Basic neural network"""
    def __init__(self, num_in, num_out, conv_size, init=False):
        self.num_in = num_in
        self.num_out = num_out
        self.conv_size = conv_size
        if init:
            self.set_layer1_weights([[random.uniform(-1, 1) for _ in range(conv_size)] for _ in range(num_in)])
            self.set_layer2_weights([[random.uniform(-1, 1) for _ in range(num_out)] for _ in range(conv_size)])

    def process(self, *inputs):
        assert(len(inputs) == self.num_in)
        self.inputs = inputs
        self.conv_layer = self.convolve(self.inputs, self.layer1)
        self.output = self.convolve(self.conv_layer, self.layer2)
        self.output = [round(x) for x in self.output]
        return self.output

    def convolve(self, inputs, weight_set):
        output_layer = [0 for _ in range(len(weight_set[0]))]
        for i, weights in zip(inputs, weight_set):
            for dst, w in enumerate(weights):
                output_layer[dst] += w * i
        return [sigmoid(x) for x in output_layer]

    def set_layer1_weights(self, weights):
        """sets the edge weights for layer 1 of the network, where WEIGHTS is an iterable
        of size SELF.NUM_IN of lists of size SELF.CONVOL_SIZE of weights for a
        single input."""
        # assert(len(weights) == self.num_in)
        # assert(all(len(w) == self.conv_size for w in weights))
        self.layer1 = weights

    def set_layer2_weights(self, weights):
        """sets the edge weights for layer 2 of the network, where WEIGHTS is an iterable
        of size SELF.CONVOL_SIZE of lists of size SELF.NUM_OUT of weights
        for a single colnvolution layer node."""
        # assert(len(weights) == self.conv_size)
        # assert(all(len(w) == self.num_out for w in weights))
        self.layer2 = weights

class Tile:
    """A square in the environment that can be passable or not and looks like S in string form"""
    def __init__(self, passable=True, s=' '):
        self.representation = s
        self.passable = passable

    def __str__(self):
        return self.representation

class Wall(Tile):
    """An inpassable tile"""
    def __init__(self):
        super().__init__(False, '█')

if __name__ == '__main__':
    curses.wrapper(main)
