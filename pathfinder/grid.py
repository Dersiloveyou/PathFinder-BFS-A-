import random

class Grid:
    def __init__(self, rows=25, cols=40):
        self.resize(rows, cols)

    def resize(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.walls = set()                        
        self.start = (rows // 2, cols // 4)
        self.goal = (rows // 2, 3 * cols // 4)

    def in_bounds(self, pos):
        return 0 <= pos[0] < self.rows and 0 <= pos[1] < self.cols

    def is_free(self, pos):
        return self.in_bounds(pos) and pos not in self.walls

    def add_wall(self, pos):
        if self.in_bounds(pos) and pos != self.start and pos != self.goal:
            self.walls.add(pos)

    def remove_wall(self, pos):
        self.walls.discard(pos)

    def set_start(self, pos):
        if self.in_bounds(pos) and pos != self.goal:
            self.walls.discard(pos)
            self.start = pos

    def set_goal(self, pos):
        if self.in_bounds(pos) and pos != self.start:
            self.walls.discard(pos)
            self.goal = pos

    def clear_walls(self):
        self.walls.clear()

    def random_walls(self, density):
        self.walls.clear()
        for r in range(self.rows):
            for c in range(self.cols):
                pos = (r, c)
                if pos != self.start and pos != self.goal and random.random() < density:
                    self.walls.add(pos)

    def neighbors(self, pos):
        r, c = pos
        result = []
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nb = (r + dr, c + dc)
            if self.is_free(nb):
                result.append(nb)
        return result
