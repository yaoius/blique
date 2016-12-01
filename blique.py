from genalg.alg import GeneticAlg
from genalg.biology import *
import random
import time
import curses

NORTH = 0
EAST = 1
SOUTH = 2
WEST = 3

LEFT = -1
RIGHT = 1

def addstr(stdscr, x, y, s, color=None):
    try:
        if color:
            stdscr.addstr(y, x, s, color)
        else:
            stdscr.addstr(y, x, s)
    except:
        pass

def main(stdscr):
    curses.start_color()
    if not curses.has_colors():
        raise Exception('NO COLOR')
    height, width = curses.LINES, curses.COLS
    g = GeneticAlg()
    bliques = Population(size=1, member=Blique, initialize=True)
    for i, gen in enumerate(g.stepper(bliques)):
        environment = Environment(height, width, gen, stdscr)
        environment.update()
        environment.simulate(True)
        key = stdscr.getkey()
        if str(key) == 'q':
            break
    stdscr.getkey()

class Blique(Individual):

    genome_length = 24
    max_move_distance = 3
    max_age = 500
    height, width = 3, 5
    name_pheomes = [x + y for x in 'abcdefghijklmnoprstuvwxyz' for y in 'aeiouy']

    def __init__(self, parents=None, genome=None, coord=None):
        super().__init__(genome)
        self.parents = parents
        self.name = self.gen_name()
        if coord:
            self.x, self.y = coord
        else:
            self.x, self.y = 1, 1
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
                name += random.choice(self.name_pheomes)
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
            dx, dy = 0, 1
        elif self.facing == EAST:
            dx, dy = 1, 0
        elif self.facing == SOUTH:
            dx, dy = 0, -1
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

    def get_next_move(self, input):
        return self.move

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
            self.age += 1

    def read_genome(self):
        for i in range(0, self.genome_length, 8):
            gene = self.genome.subsequence(i, i+8)

    def fitness(self):
        return self.distance_traveled * self.age

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
        self.stdscr.refresh()

    def undraw_blique(self, blique):
        for dy in range(blique.height):
            for dx in range(blique.width):
                x, y = blique.x + dx, blique.y + dy
                if y * self.width + x < len(self.grid):
                    char = str(self.grid[y * self.width + x])
                    addstr(self.stdscr, x, y, char)
        self.stdscr.refresh()

    def update_info(self):
        fittest = self.bliques.get_fittest()
        name, parents = fittest.bio()
        alive, age, distance, fitness, coord = fittest.state()
        info = 'fittest: {}, child of {}, lived for {} and traveled {}'.format(name, parents, age, distance)
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
        while any(b.alive for b in self.bliques):
            for b in self.bliques:
                if b.alive:
                    if animate:
                        self.undraw_blique(b)
                    b.step()
                    if animate:
                        self.update_info()
                        if b is self.bliques.get_fittest():
                            self.draw_blique(b, color=curses.color_pair(2))
                        else:
                            self.draw_blique(b)
            time.sleep(0.1)
        for b in self.bliques:
            b.reset()

    def str_rep(self):
        grid = ''
        for y in range(self.view_height):
            for x in range(self.width):
                grid += str(self.grid[y * self.width + x])
            grid += '\n'
        return grid

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
