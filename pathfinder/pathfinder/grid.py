"""Модель двумерной сетки (слой данных, никакой графики).

Координаты клеток задаются кортежем (строка, столбец).
"""
import random
from enum import IntEnum

SQRT2 = 2 ** 0.5


class Cell(IntEnum):
    """Тип клетки сетки."""
    EMPTY = 0   # свободная клетка, стоимость прохода 1
    WALL = 1    # препятствие (непроходимо)
    MUD = 2     # «болото»: проходимо, но стоимость прохода 5


COSTS = {Cell.EMPTY: 1, Cell.MUD: 5}

ORTHOGONAL = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIAGONAL = ((-1, -1), (-1, 1), (1, -1), (1, 1))


class Grid:
    """Сетка с препятствиями, стартом и финишем."""

    def __init__(self, rows=25, cols=40):
        self.resize(rows, cols)

    # ---------- создание и изменение ----------
    def resize(self, rows, cols):
        """Создаёт пустую сетку нового размера."""
        self.rows, self.cols = rows, cols
        self.cells = [[Cell.EMPTY] * cols for _ in range(rows)]
        self.start = (rows // 2, cols // 4)
        self.goal = (rows // 2, (3 * cols) // 4)

    def clear(self):
        """Убирает все препятствия и болота (старт и финиш остаются)."""
        self.cells = [[Cell.EMPTY] * self.cols for _ in range(self.rows)]

    def set_cell(self, pos, kind):
        """Ставит клетку заданного типа. Старт и финиш менять нельзя."""
        if pos in (self.start, self.goal) or not self.in_bounds(pos):
            return False
        self.cells[pos[0]][pos[1]] = kind
        return True

    def move_start(self, pos):
        if not self.in_bounds(pos) or pos == self.goal:
            return False
        self.cells[pos[0]][pos[1]] = Cell.EMPTY
        self.start = pos
        return True

    def move_goal(self, pos):
        if not self.in_bounds(pos) or pos == self.start:
            return False
        self.cells[pos[0]][pos[1]] = Cell.EMPTY
        self.goal = pos
        return True

    # ---------- генераторы карт ----------
    def random_obstacles(self, density, seed=None):
        """Случайные стены: каждая клетка становится стеной с вероятностью density."""
        rng = random.Random(seed)
        self.clear()
        for r in range(self.rows):
            for c in range(self.cols):
                if (r, c) not in (self.start, self.goal) and rng.random() < density:
                    self.cells[r][c] = Cell.WALL

    def generate_maze(self, seed=None, loops=0.06):
        """Лабиринт (поиск в глубину) + немного дополнительных проходов (петель).

        Без петель путь в лабиринте единственный, и все алгоритмы
        ведут себя одинаково; петли делают сравнение интереснее.
        """
        rng = random.Random(seed)
        R, C = self.rows, self.cols
        self.cells = [[Cell.WALL] * C for _ in range(R)]
        self.cells[1][1] = Cell.EMPTY
        stack = [(1, 1)]
        while stack:
            r, c = stack[-1]
            options = [(r + dr, c + dc, dr, dc)
                       for dr, dc in ((-2, 0), (2, 0), (0, -2), (0, 2))
                       if 1 <= r + dr <= R - 2 and 1 <= c + dc <= C - 2
                       and self.cells[r + dr][c + dc] == Cell.WALL]
            if not options:
                stack.pop()
                continue
            nr, nc, dr, dc = rng.choice(options)
            self.cells[r + dr // 2][c + dc // 2] = Cell.EMPTY
            self.cells[nr][nc] = Cell.EMPTY
            stack.append((nr, nc))
        # петли: пробиваем часть стен между соседними коридорами
        for r in range(1, R - 1):
            for c in range(1, C - 1):
                if (r + c) % 2 == 1 and self.cells[r][c] == Cell.WALL and rng.random() < loops:
                    self.cells[r][c] = Cell.EMPTY
        self.start = (1, 1)
        self.goal = (R - 2 if (R - 2) % 2 == 1 else R - 3,
                     C - 2 if (C - 2) % 2 == 1 else C - 3)

    # ---------- запросы ----------
    def in_bounds(self, pos):
        return 0 <= pos[0] < self.rows and 0 <= pos[1] < self.cols

    def passable(self, r, c):
        return 0 <= r < self.rows and 0 <= c < self.cols and self.cells[r][c] != Cell.WALL

    def cell_cost(self, pos):
        return COSTS[self.cells[pos[0]][pos[1]]]

    def move_cost(self, a, b):
        """Стоимость шага из a в соседнюю b (диагональ длиннее в √2 раз)."""
        length = SQRT2 if (a[0] != b[0] and a[1] != b[1]) else 1
        return length * self.cell_cost(b)

    def neighbors(self, pos, diagonal=False):
        """Соседи клетки: пары (клетка, стоимость шага).

        По диагонали нельзя «срезать угол» стены.
        """
        r, c = pos
        for dr, dc in ORTHOGONAL:
            nr, nc = r + dr, c + dc
            if self.passable(nr, nc):
                yield (nr, nc), self.move_cost(pos, (nr, nc))
        if diagonal:
            for dr, dc in DIAGONAL:
                nr, nc = r + dr, c + dc
                if (self.passable(nr, nc) and self.passable(r + dr, c)
                        and self.passable(r, c + dc)):
                    yield (nr, nc), self.move_cost(pos, (nr, nc))
