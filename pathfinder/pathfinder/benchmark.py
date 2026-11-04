"""Сравнительный анализ алгоритмов на разных типах карт.

Запуск: python benchmark.py   (результат: таблица в консоли + results.csv)
Размер карт 51x51, 4 направления движения. Для случайных карт —
среднее по 20 картам, для остальных — одна карта (время усреднено по 5 запускам).
"""
import csv
import statistics

from algorithms import ALGORITHMS
from grid import Cell, Grid

N = 51


def empty(seed):
    g = Grid(N, N); g.start, g.goal = (1, 1), (N - 2, N - 2)
    return g


def random_map(density):
    def build(seed):
        g = empty(seed)
        g.random_obstacles(density, seed=seed)
        return g
    return build


def maze(seed):
    g = Grid(N, N)
    g.generate_maze(seed=7)
    return g


def u_trap(seed):
    """Финиш внутри «кармана» в форме U, открытого в сторону от старта."""
    g = empty(seed)
    g.start, g.goal = (N // 2, 3), (N // 2, N - 12)
    for r in range(N // 2 - 8, N // 2 + 9):
        g.cells[r][N - 17] = Cell.WALL          # левая вертикальная стена
    for c in range(N - 17, N - 5):
        g.cells[N // 2 - 8][c] = Cell.WALL      # верхняя
        g.cells[N // 2 + 8][c] = Cell.WALL      # нижняя
    g.cells[N // 2][N - 17] = Cell.WALL
    return g


def swamp(seed):
    """Широкая полоса болота с узким проходом: выгоднее обойти, чем пройти насквозь."""
    g = empty(seed)
    g.start, g.goal = (N // 2, 2), (N // 2, N - 3)
    for r in range(N):
        for c in range(N // 2 - 6, N // 2 + 7):
            g.cells[r][c] = Cell.MUD
    for r in range(0, 4):                       # «сухой» проход у верхней границы
        for c in range(N // 2 - 6, N // 2 + 7):
            g.cells[r][c] = Cell.EMPTY
    return g


SCENARIOS = [
    ("Пустая карта", empty, [0]),
    ("Препятствия 20%", random_map(0.20), list(range(20))),
    ("Препятствия 35%", random_map(0.35), list(range(20))),
    ("Лабиринт", maze, [0]),
    ("Ловушка «U»", u_trap, [0]),
    ("Карта с болотом", swamp, [0]),
]


def main():
    rows = []
    for title, build, seeds in SCENARIOS:
        for name, cls in ALGORITHMS.items():
            exp, cost, times = [], [], []
            for seed in seeds:
                grid = build(seed)
                runs = [cls(grid).run_to_end() for _ in range(5)]
                s = runs[0]
                if not s["found"]:
                    continue
                exp.append(s["expanded"]); cost.append(s["path_cost"])
                times.append(statistics.median(r["time_ms"] for r in runs))
            rows.append({"scenario": title, "algorithm": name,
                         "expanded": round(statistics.mean(exp)),
                         "path_cost": round(statistics.mean(cost), 1),
                         "time_ms": round(statistics.mean(times), 2),
                         "maps": len(exp)})
    with open("results.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys(), delimiter=";")
        w.writeheader(); w.writerows(rows)
    print(f"{'Карта':<18}{'Алгоритм':<16}{'Раскрыто':>9}{'Стоимость':>11}{'мс':>8}")
    for r in rows:
        print(f"{r['scenario']:<18}{r['algorithm']:<16}{r['expanded']:>9}{r['path_cost']:>11}{r['time_ms']:>8}")


if __name__ == "__main__":
    main()
