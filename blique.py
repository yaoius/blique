import genalg.alg as ga
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

ANIMATION_SPEED = 0.05

def sigmoid(x):
    return 1 / (1 + math.exp(-x))

def addstr(stdscr, x, y, s, color=None):
    try:
        if color:
            stdscr.addstr(y, x, s)
        else:
            stdscr.addstr(y, x, s)
    except:
        pass

def main(stdscr):
    Genome.deletion_rate = 0
    curses.start_color()
    if not curses.has_colors():
        raise Exception('NO COLOR')
    height, width = curses.LINES, curses.COLS
    Blique.x = (3 * height - Blique.width) // 2
    Blique.y = (height - Blique.height) // 2
    bliques = Population(size=15, member=Blique, initialize=True)
    for i, gen in enumerate(ga.stepper(bliques, elitism=False)):
        environment = Environment(height, width, gen)
        if i % 10 == 0:
            environment.update()
            environment.simulate(True)
        else:
            environment.simulate(False)
        # key = stdscr.getkey()
        # if str(key) == 'q':
        #     break

class Blique(Individual):

    genome_length = 75
    max_move_distance = 3
    max_age = 30
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
        dist = 1
        while tile.passable:
            x, y = x + dx, y + dy
            tile = self.env.get_tile(x, y)
            dist += 1
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
        turn, turn_dir, m1, m2 = self.brain.process(inp)
        if turn:
            return lambda: self.turn(1 if turn_dir else -1)
        else:
            return lambda: self.move(m1 << 1 + m2)

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
        if self.alive:
            self.age += ANIMATION_SPEED * 4

    def read_genome(self):
        self.brain = Brain(1, 4, 5)
        genes = [self.read_gene(self.genome.subsequence(i, i+3)) for i in range(0, self.genome_length, 3)]
        self.brain.set_layer1_weights([genes[:5]])
        self.brain.set_layer2_weights([genes[5:9], genes[9:13], genes[13:17], genes[17:21], genes[21:25]])

    def read_gene(self, gene):
        weight = 1
        for i in gene[:-1]:
            weight = weight << 1
            weight += i
        if gene[-1]:
            weight = -weight
        return weight

    def fitness(self):
        return int(self.distance_traveled*5 + self.age)

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

    def __init__(self, height, width, bliques, grid=None):
        self.width = width
        self.height = height
        self.view_height = height
        self.view_width = 3 * height
        self.view = curses.newwin(self.view_height, self.view_width, 0, 0)
        self.info_box = curses.newwin(self.view_height, width - self.view_width, 0, self.view_width)
        self.info_box.border()
        header = '{:<2} {:<5} {:<10} {:<3} {:<5}'.format('#', 'F', 'Name', 'Age', 'Distance')
        delimeter = '-  -     ----       --- --------'
        addstr(self.info_box, 1, 1, header)
        addstr(self.info_box, 1, 2, delimeter)
        self.grid = grid or self.make_grid()
        self.bliques = bliques
        for ind in self.bliques:
            ind.env = self

    def make_grid(self):
        grid = [None for _ in range(self.view_width * self.view_height)]
        for x in range(self.view_width):
            for y in range(self.view_height):
                if 0 <= x < self.view_width and 0 <= y < self.view_height:
                    grid[y * self.view_width + x] = Tile()
                else:
                    grid[y * self.view_width + x] = Wall()
        return grid

    def get_tile(self, x, y):
        if x < 0 or x >= self.view_width:
            return Wall()
        if y < 0 or y >= self.view_height:
            return Wall()
        return self.grid[y * self.view_width + x]

    def add_blique(self, blique):
        self.bliques.add_individual(blique)
        blique.env = self

    def draw_blique(self, blique, color=None):
        y = blique.y
        for line in blique.image:
            addstr(self.view, blique.x, y, line)
            y += 1
        addstr(self.view, blique.eye_x, blique.eye_y, 'O')
        addstr(self.view, blique.x, blique.y + blique.height, blique.name)
        self.view.refresh()

    def undraw_blique(self, blique):
        for dy in range(blique.height):
            for dx in range(blique.width):
                x, y = blique.x + dx, blique.y + dy
                if y * self.view_width + x < len(self.grid):
                    char = str(self.grid[y * self.view_width + x])
                    addstr(self.view, x, y, char)
        addstr(self.view, blique.x, blique.y + blique.height, ' ' * len(blique.name))
        self.view.refresh()

    def update_info(self):
        offset = 3
        sorted_bliques = sorted(self.bliques, key=lambda b: b.fitness(), reverse=True)
        for i, blique in enumerate(sorted_bliques):
            row = i + offset
            info = '{:<2} {:<5} {:<10} {:<3} {:<4}'.format(i+1, blique.fitness(), blique.name, int(blique.age), int(blique.distance_traveled))
            addstr(self.info_box, 1, row, info)
        self.info_box.refresh()

    def update(self, bliques=None):
        bliques = bliques or self.bliques
        self.view.clear()
        for x in range(self.view_width):
            for y in range(self.view_height):
                char = str(self.grid[y * self.view_width + x])
                addstr(self.view, x, y, char)
        self.view.border()
        self.view.refresh()
        self.update_info()
        for b in bliques:
            self.draw_blique(b)

    def simulate(self, animate=False):
        for b in self.bliques:
            b.reset()
        to_draw = [b for b in self.bliques if b.alive]
        if not animate:
            addstr(self.view, (self.view_width - len('SIMULATING')) // 2, self.view_height // 2, 'SIMULATING')
            self.view.border()
            self.view.refresh()
        while to_draw:
            for b in to_draw:
                b.step()
                if not b.alive:
                    to_draw.remove(b)
            if animate:
                self.update(to_draw)
                time.sleep(ANIMATION_SPEED)
            self.update_info()

        

    def str_rep(self):
        grid = ''
        for y in range(self.view_height):
            for x in range(self.view_width):
                grid += str(self.grid[y * self.view_width + x])
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
        """Uses inputs from INPUTS, convolving to the convolution layer and again from
        the convolution later to the final output. Must have the number of inputs defined
        for this Brain"""
        assert(len(inputs) == self.num_in)
        self.inputs = inputs
        self.conv_layer = self.convolve(self.inputs, self.layer1)
        self.output = self.convolve(self.conv_layer, self.layer2)
        self.output = [round(x) for x in self.output]
        return self.output

    def convolve(self, inputs, weight_set):
        """Given a list of INPUTS and WEIGHT_SET, a list of list of edge weights. Element
        j from list i from WEIGHT_SET is the edge weight from input i to node j in the
        next layer. Returns the list representing the values of the convolution layer."""
        output_layer = [0 for _ in range(len(weight_set[0]))]
        for i, weights in zip(inputs, weight_set):
            for dst, w in enumerate(weights):
                output_layer[dst] += w * i
        return [sigmoid(x / 100) for x in output_layer]

    def set_layer1_weights(self, weights):
        """sets the edge weights for layer 1 of the network, where WEIGHTS is an iterable
        of size SELF.NUM_IN of lists of size SELF.CONVOL_SIZE of weights for a
        single input."""
        assert(len(weights) == self.num_in)
        assert(all(len(w) == self.conv_size for w in weights))
        self.layer1 = weights

    def set_layer2_weights(self, weights):
        """sets the edge weights for layer 2 of the network, where WEIGHTS is an iterable
        of size SELF.CONVOL_SIZE of lists of size SELF.NUM_OUT of weights
        for a single colnvolution layer node."""
        assert(len(weights) == self.conv_size)
        assert(all(len(w) == self.num_out for w in weights))
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
