"""Тесты алгоритмов. Запуск: python test_algorithms.py"""
import unittest

from algorithms import BFS, AStar, Dijkstra, ALGORITHMS
from grid import Cell, Grid


def make(rows, cols, start, goal):
    g = Grid(rows, cols)
    g.start, g.goal = start, goal
    return g


class TestPathfinding(unittest.TestCase):
    def test_empty_grid_shortest(self):
        for cls in ALGORITHMS.values():
            g = make(10, 10, (0, 0), (9, 9))
            s = cls(g).run_to_end()
            self.assertTrue(s["found"])
            self.assertEqual(s["path_len"], 19)          # 18 шагов + старт

    def test_start_equals_goal(self):
        for cls in ALGORITHMS.values():
            g = make(5, 5, (2, 2), (2, 2))
            s = cls(g).run_to_end()
            self.assertTrue(s["found"])
            self.assertEqual(s["path_len"], 1)

    def test_no_path(self):
        for cls in ALGORITHMS.values():
            g = make(7, 7, (0, 0), (6, 6))
            for r in range(7):
                g.cells[r][3] = Cell.WALL                 # сплошная стена
            s = cls(g).run_to_end()
            self.assertFalse(s["found"])
            self.assertEqual(s["path_len"], 0)

    def test_path_is_valid(self):
        g = Grid(30, 30)
        g.random_obstacles(0.25, seed=1)
        for cls in ALGORITHMS.values():
            for diag in (False, True):
                f = cls(g, diag)
                f.run_to_end()
                if not f.found:
                    continue
                self.assertEqual(f.path[0], g.start)
                self.assertEqual(f.path[-1], g.goal)
                for a, b in zip(f.path, f.path[1:]):
                    self.assertIn(b, [n for n, _ in g.neighbors(a, diag)])

    def test_dijkstra_equals_astar_cost(self):
        """Оба алгоритма оптимальны по стоимости, A* раскрывает не больше клеток."""
        for diag in (False, True):
            for seed in range(30):
                g = Grid(25, 25)
                g.random_obstacles(0.25, seed=seed)
                for r in range(25):                       # добавим болота
                    for c in range(25):
                        if g.cells[r][c] == Cell.EMPTY and (r * 7 + c * 3 + seed) % 11 == 0:
                            g.set_cell((r, c), Cell.MUD)
                d = Dijkstra(g, diag); d.run_to_end()
                a = AStar(g, diag); a.run_to_end()
                self.assertEqual(d.found, a.found)
                if d.found:
                    self.assertAlmostEqual(d.path_cost(), a.path_cost(), places=6)
                    self.assertLessEqual(a.expanded, d.expanded)

    def test_bfs_not_optimal_on_weighted(self):
        """BFS минимизирует число шагов, поэтому на болоте он дороже Дейкстры."""
        g = make(5, 7, (2, 0), (2, 6))
        for c in range(2, 5):
            g.cells[2][c] = Cell.MUD                      # болото на прямом пути
        b = BFS(g); b.run_to_end()
        d = Dijkstra(g); d.run_to_end()
        self.assertGreater(b.path_cost(), d.path_cost())
        self.assertEqual(len(b.path), 7)

    def test_no_corner_cutting(self):
        g = make(2, 2, (0, 0), (1, 1))
        g.cells[0][1] = Cell.WALL
        g.cells[1][0] = Cell.WALL
        self.assertFalse(AStar(g, True).run_to_end()["found"])

    def test_maze_solvable(self):
        g = Grid(31, 31)
        g.generate_maze(seed=3)
        for cls in ALGORITHMS.values():
            self.assertTrue(cls(g).run_to_end()["found"])

    def test_step_interface(self):
        f = AStar(make(5, 5, (0, 0), (4, 4)))
        self.assertIsNotNone(f.step())
        while f.step() is not None:
            pass
        self.assertTrue(f.finished and f.found)


if __name__ == "__main__":
    unittest.main(verbosity=2)
