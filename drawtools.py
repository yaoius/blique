import curses

class Canvas:

	_initialized = False

	def __init__(self):
		if _initialized:
			raise Exception('Only one instance of Canvas may be instantiated')
		_initialized = True
		self.init()
		self.height, self.width = curses.LINES, curses.COLS

	def init(self):
		self.stdscr = curses.initscr()
		curses.noecho()
		curses.cbreak()
		curses.start_color()
		self.stdscr.keypad(True)

	def close(self):
		curses.nocbreak()
		self.stdscr.keypad(False)
		curses.echo()
		curses.endwin()

	def update(self):
		self.stdscr.refresh()

	def clear(self):
		self.stdscr.clear()

	def draw_ch(x, y, char):
		self.stdscr.addch(x, y, char)

	def draw_str(x, y, s):
		self.stdscr.addstr(x, y, s)

	@wrap
	def

	def wrap(fn):
		def safe_draw(*args):
			try:
				fn(*args)
			except Exception as e:
				self.close()
				raise e
