"""Алгоритмы поиска пути: BFS (волновой), Дейкстра, A*.

Все алгоритмы работают через единый интерфейс PathFinder и выполняются
ПОШАГОВО: один вызов step() = раскрытие одной клетки. Это позволяет
интерфейсу анимировать поиск, а тестам и бенчмарку — прогонять его до конца.
Модуль ничего не знает о графике.
"""
import heapq
import itertools
from collections import deque
from time import perf_counter

from grid import SQRT2

OPEN, CLOSE, PATH = "open", "close", "path"   # виды событий


class PathFinder:
    """Базовый класс. Наследники реализуют генератор _search()."""

    name = "?"

    def __init__(self, grid, diagonal=False):
        self.grid = grid
        self.diagonal = diagonal
        self.start, self.goal = grid.start, grid.goal
        self.open_cells = set()     # клетки в очереди (граница поиска)
        self.closed_cells = set()   # уже обработанные клетки
        self.parent = {}            # откуда пришли (для восстановления пути)
        self.path = []
        self.found = False
        self.finished = False
        self.expanded = 0           # сколько клеток раскрыто
        self.max_frontier = 0       # максимальный размер очереди
        self.elapsed = 0.0          # чистое время работы алгоритма, с
        self._gen = self._search()

    # ---------- общий интерфейс ----------
    def step(self):
        """Один шаг поиска.

        Возвращает список событий [(вид, клетка), ...] или None, если поиск окончен.
        """
        if self.finished:
            return None
        t0 = perf_counter()
        try:
            events = next(self._gen)
        except StopIteration:
            self.finished = True
            events = None
        self.elapsed += perf_counter() - t0
        return events

    def run_to_end(self):
        """Выполняет поиск целиком и возвращает статистику."""
        while self.step() is not None:
            pass
        return self.stats()

    def stats(self):
        return {
            "algorithm": self.name,
            "found": self.found,
            "expanded": self.expanded,
            "max_frontier": self.max_frontier,
            "path_len": len(self.path),
            "path_cost": self.path_cost(),
            "time_ms": self.elapsed * 1000,
        }

    def path_cost(self):
        """Реальная стоимость найденного пути (с учётом болот и диагоналей)."""
        return sum(self.grid.move_cost(a, b) for a, b in zip(self.path, self.path[1:]))

    # ---------- служебное для наследников ----------
    def _search(self):
        raise NotImplementedError

    def _push(self, pos, events):
        self.open_cells.add(pos)
        self.max_frontier = max(self.max_frontier, len(self.open_cells))
        events.append((OPEN, pos))

    def _pop(self, pos, events):
        self.open_cells.discard(pos)
        self.closed_cells.add(pos)
        self.expanded += 1
        events.append((CLOSE, pos))

    def _finish_path(self):
        """Восстанавливает путь от финиша к старту и возвращает события."""
        node, path = self.goal, []
        while node is not None:
            path.append(node)
            node = self.parent[node]
        self.path = path[::-1]
        self.found = True
        return [(PATH, p) for p in self.path]


class BFS(PathFinder):
    """Поиск в ширину (волновой алгоритм). Минимизирует число шагов,
    стоимость клеток не учитывает."""

    name = "BFS (волновой)"

    def _search(self):
        events = []
        queue = deque([self.start])
        self.parent[self.start] = None
        self._push(self.start, events)
        yield events
        while queue:
            events = []
            cur = queue.popleft()
            self._pop(cur, events)
            if cur == self.goal:
                yield events + self._finish_path()
                return
            for nb, _ in self.grid.neighbors(cur, self.diagonal):
                if nb not in self.parent:
                    self.parent[nb] = cur
                    queue.append(nb)
                    self._push(nb, events)
            yield events


class Dijkstra(PathFinder):
    """Алгоритм Дейкстры: кратчайший путь по СТОИМОСТИ (учитывает болота)."""

    name = "Дейкстра"

    def _search(self):
        events = []
        counter = itertools.count()          # для устойчивого порядка в куче
        dist = {self.start: 0}
        heap = [(0, next(counter), self.start)]
        self.parent[self.start] = None
        self._push(self.start, events)
        yield events
        while heap:
            events = []
            d, _, cur = heapq.heappop(heap)
            if cur in self.closed_cells:      # устаревшая запись в куче
                continue
            self._pop(cur, events)
            if cur == self.goal:
                yield events + self._finish_path()
                return
            for nb, cost in self.grid.neighbors(cur, self.diagonal):
                nd = d + cost
                if nb not in self.closed_cells and nd < dist.get(nb, float("inf")):
                    dist[nb] = nd
                    self.parent[nb] = cur
                    heapq.heappush(heap, (nd, next(counter), nb))
                    self._push(nb, events)
            yield events


class AStar(PathFinder):
    """A*: Дейкстра + эвристика расстояния до цели, f = g + h."""

    name = "A*"

    def heuristic(self, a, b):
        dx, dy = abs(a[0] - b[0]), abs(a[1] - b[1])
        if self.diagonal:                       # октильное расстояние
            return (dx + dy) + (SQRT2 - 2) * min(dx, dy)
        return dx + dy                          # манхэттенское расстояние

    def _search(self):
        events = []
        counter = itertools.count()
        g = {self.start: 0}
        h0 = self.heuristic(self.start, self.goal)
        heap = [(h0, h0, next(counter), self.start)]
        self.parent[self.start] = None
        self._push(self.start, events)
        yield events
        while heap:
            events = []
            _, _, _, cur = heapq.heappop(heap)
            if cur in self.closed_cells:
                continue
            self._pop(cur, events)
            if cur == self.goal:
                yield events + self._finish_path()
                return
            for nb, cost in self.grid.neighbors(cur, self.diagonal):
                ng = g[cur] + cost
                if nb not in self.closed_cells and ng < g.get(nb, float("inf")):
                    g[nb] = ng
                    self.parent[nb] = cur
                    h = self.heuristic(nb, self.goal)
                    heapq.heappush(heap, (ng + h, h, next(counter), nb))
                    self._push(nb, events)
            yield events


ALGORITHMS = {
    BFS.name: BFS,
    Dijkstra.name: Dijkstra,
    AStar.name: AStar,
}
