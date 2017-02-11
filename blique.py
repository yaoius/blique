import genalg.alg as ga
from genalg.biology import *
import random
import time
import curses
import math

__author__ = 'Dillon Yao'
VERSION, BUILD = 0, 2

ANIMATION_SPEED = 0.05
STEP = 5

class Directions:
    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3
    LEFT = 4
    RIGHT = 5

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
    env = Environment(height, width, bliques)

    while True:
        if env.generation % STEP == 0:
            env.update()
            env.simulate(True)
        else:
            env.simulate(False)
        env.evolve_pop()

class Blique(Individual):
    """Creates a creature who dies upon touching a wall"""
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
        """Generates a name for the Blique based on either the parents name, or if it
        has no parents, creates a random one from the available phenomes"""
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
        """Determines the coordinates of the blique's eye"""
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
        """sets the blique's appearance when rendered"""
        self.image = ['+' + '-' * (self.width - 2) + '+']
        for i in range(self.height - 2):
            self.image.append('|' + ' ' * (self.width - 2) + '|')
        self.image.append('+' + '-' * (self.width - 2) + '+')

    def mate(self, other, mutation):
        """Returns a new Blique with a genome crossed with that of another Blique"""
        crossed_genome = Genome.crossover(self.genome, other.genome, mutation)
        child = Blique(genome=crossed_genome, parents=(self.name, other.name))
        return child

    def look_ahead(self):
        """Blique finds distance form eye to wall"""
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
        """Moves the Blique in the direction that it is facing by AMT tiles"""
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
        """Turns the Blique 90deg clockwise DIRECTION times. Using -1 turns the blique
        left and 1 turns the blique right."""
        self.facing = (self.facing + direction) % 4

    def get_next_move(self, *inp):
        """Takes the input of the blique and processes through the Bliques brain, using the
        inputs from INP"""
        turn, turn_dir, m1, m2 = self.brain.process(*inp)
        if turn:
            return lambda: self.turn(1 if turn_dir else -1)
        else:
            return lambda: self.move(m1 << 1 + m2)

    def get_tiles_under(self):
        """Returns the tiles under the blique as a list"""
        if not self.env:
            raise Exception('Blique is not in an Environment')
        return [self.env.get_tile(self.x + dx, self.y + dy) for dx in range(self.width) for dy in range(self.height)]

    def simulate(self):
        """Continues to call STEP until the blique is dead"""
        while self.alive:
            self.step()

    def step(self):
        """The blique will find how far it is to the nearest wall and take a move based
        on that output"""
        distance_to_obstacle = self.look_ahead()
        next_move = self.get_next_move(distance_to_obstacle)
        next_move()
        self.set_eye()
        if self.age > self.max_age or any(not tile.passable for tile in self.get_tiles_under()):
            self.alive = False
        if self.alive:
            self.age += ANIMATION_SPEED * 4

    def read_genome(self):
        """Creates a Brain instance (a neural network) with a single input and 5 outputs
        and a single convolution layer with 4 nodes. Weights are determined by genes
        of length 4 in the input subsequence"""
        self.brain = Brain(1, 4, 5)
        genes = [self.read_gene(self.genome.subsequence(i, i+3)) for i in range(0, self.genome_length, 3)]
        self.brain.set_layer1_weights([genes[:5]])
        self.brain.set_layer2_weights([genes[5:9], genes[9:13], genes[13:17], genes[17:21], genes[21:25]])

    def read_gene(self, gene):
        """Returns the binary value of the gene read using a sign bit"""
        weight = 1
        for i in gene[:-1]:
            weight = weight << 1
            weight += i
        if gene[-1]:
            weight = -weight
        return weight

    def fitness(self):
        """Returns the fitness of the current Blique"""
        return int(self.distance_traveled * 5 + self.age)

    def load_state(self, state):
        """Set the current blique's state to STATE"""
        self.alive, self.age, self.distance_traveled, _, coord = state
        self.x, self.y = coord
        self.set_eye()

    def reset(self):
        """Revert's the blique to its initial state"""
        self.load_state(self.initial_state)

    def bio(self):
        """Returns identification info on the blique"""
        return self.name, self.parents

    def state(self):
        """Returns a tuple representing the blique's state"""
        return self.alive, self.age, self.distance_traveled, self.fitness(), (self.x, self.y)

class Environment:
    """Handles the display, animation, and evolution of a population of bliques"""
    infobox_width = 35
    title = 'Blique Evolution Sim v {}.{}'.format(VERSION, BUILD)

    def __init__(self, height, width, bliques, grid=None):
        """TODO: add support for input file grids"""
        self.width = width
        self.height = height
        self.generation = 0
        self.view_height = height
        self.view_width = width - self.infobox_width
        self.grid = grid or self.make_grid()
        self.initialize_windows()
        self.bliques = bliques
        for blique in self.bliques:
            blique.env = self

    def initialize_windows(self):
        """initializes the viewbox and infobox for the Environment"""
        self.viewbox = curses.newwin(self.view_height, self.view_width, 0, 0)
        self.infobox = curses.newwin(self.view_height, self.infobox_width, 0, self.view_width)
        self.init_infobox()

    def init_infobox(self):
        """initializes the column headers for the infobox"""
        self.infobox.border()
        header = '{:<2} {:<5} {:<10} {:<3} {:<5}'.format('#', 'F', 'Name', 'Age', 'Distance')
        delimeter = '-  -     ----       --- --------'
        addstr(self.infobox, 1, 1, header)
        addstr(self.infobox, 1, 2, delimeter)
        self.infobox.refresh()

    def make_grid(self):
        """Generates an empty grid of all Tiles"""
        grid = [Tile() for _ in range(self.view_width * self.view_height)]
        return grid

    def get_tile(self, x, y):
        """Retrieves the Tile at coordinates (x, y) on the grid"""
        if x <= 0 or x >= self.view_width:
            return Wall()
        if y <= 0 or y >= self.view_height:
            return Wall()
        return self.grid[y * self.view_width + x]

    def add_blique(self, blique):
        """Add a new blique to the population"""
        self.bliques.add_individual(blique)
        blique.env = self

    def add_blique_to_viewbox(self, blique, color=None):
        """Draws a blique b at the coordinates (b.x, b.y)"""
        y = blique.y
        for line in blique.image:
            addstr(self.viewbox, blique.x, y, line)
            y += 1
        addstr(self.viewbox, blique.eye_x, blique.eye_y, 'O')
        addstr(self.viewbox, blique.x, blique.y + blique.height, blique.name)

    def undraw_blique(self, blique):
        """Removes the blique b from it's coordinates"""
        for dy in range(blique.height):
            for dx in range(blique.width):
                x, y = blique.x + dx, blique.y + dy
                if y * self.view_width + x < len(self.grid):
                    char = str(self.grid[y * self.view_width + x])
                    addstr(self.viewbox, x, y, char)
        addstr(self.viewbox, blique.x, blique.y + blique.height, ' ' * len(blique.name))
        self.viewbox.refresh()

    def update_info(self):
        """Updates the infobox with the bliques currently in the population, sorted by
        their fitness values"""
        offset = 3
        sorted_bliques = sorted(self.bliques, key=lambda b: b.fitness(), reverse=True)
        addstr(self.infobox, 1, 0, 'Generation: {}'.format(self.generation))
        for i, blique in enumerate(sorted_bliques):
            row = i + offset
            info = '{:<2} {:<5} {:<10} {:<3} {:<4}'.format(i+1, blique.fitness(), blique.name, int(blique.age), int(blique.distance_traveled))
            addstr(self.infobox, 1, row, info)
        self.infobox.refresh()

    def update(self, bliques=[]):
        """Update the viewbox and infobox"""
        self.viewbox.clear()
        for x in range(self.view_width):
            for y in range(self.view_height):
                char = str(self.grid[y * self.view_width + x])
                addstr(self.viewbox, x, y, char)
        self.viewbox.border()
        addstr(self.viewbox, 1, 0, self.title)
        self.update_info()
        for b in bliques:
            self.add_blique_to_viewbox(b)
        self.viewbox.refresh()

    def simulate(self, animate=False):
        """Simulate the bliques actions until all bliques are dead, drawing to the viewbox
        if ANIMATE"""
        for b in self.bliques:
            b.reset()
        to_draw = [b for b in self.bliques if b.alive]
        if not animate:
            self.update()
            addstr(self.viewbox, (self.view_width - len('SIMULATING')) // 2, self.view_height // 2, 'SIMULATING')
            self.viewbox.refresh()
        while to_draw:
            for b in to_draw:
                b.step()
                if not b.alive:
                    to_draw.remove(b)
            if animate:
                self.update(to_draw)
                time.sleep(ANIMATION_SPEED)
            self.update_info()

    def evolve_pop(self):
        """Evolves the population by a generation"""
        self.bliques = ga.step(self.bliques)
        for blique in self.bliques:
            blique.env = self
        self.generation += 1

    def str_rep(self):
        """A string representation of the current grid"""
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

    def __int__(self):
        return 1

class Wall(Tile):
    """An inpassable tile"""
    def __init__(self):
        super().__init__(False, '█')

    def __int__(self):
        return 2

class Food(Tile):
    """A tile which gives a Blique energy"""
    def __init__(self):
        super().__init__(s='+')

    def __int__(self):
        return 3

if __name__ == '__main__':
    curses.wrapper(main)
