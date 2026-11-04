import tkinter as tk
from tkinter import ttk

from algorithms import ALGORITHMS
from grid import Grid


COLOR_EMPTY = "#FFFFFF"
COLOR_WALL = "#3C388D"
COLOR_START = "#9FC53A"
COLOR_GOAL = "#E53935"
COLOR_OPEN = "#36CCE8"
COLOR_CLOSED = "#B3B2CB"
COLOR_PATH = "#F5A623"
COLOR_LINE = "#DAD9EA"

CELL_SIZE = 20


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Визуализатор алгоритмов поиска пути")

        self.grid = Grid(25, 40)
        self.finder = None
        self.running = False
        self.after_id = None
        self.rects = []
        self.info = tk.StringVar()

        self.build_ui()
        self.draw_grid()

    def build_ui(self):
        left = tk.Frame(self.root)
        left.pack(side="left", padx=10, pady=10)

        self.canvas = tk.Canvas(left)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.on_mouse)
        self.canvas.bind("<B1-Motion>", self.on_mouse)

        panel = tk.Frame(self.root)
        panel.pack(side="left", fill="y", padx=10, pady=10)

        tk.Label(panel, text="Алгоритм:").pack(anchor="w")
        self.algo = ttk.Combobox(panel, values=list(ALGORITHMS), state="readonly")
        self.algo.current(0)
        self.algo.pack(fill="x")
        self.algo.bind("<<ComboboxSelected>>", lambda event: self.reset())

        tk.Button(panel, text="Старт / Пауза", command=self.toggle_run).pack(fill="x", pady=10)
        tk.Button(panel, text="Шаг", command=self.step_once).pack(fill="x")
        tk.Button(panel, text="Сброс поиска", command=self.reset).pack(fill="x")

        tk.Label(panel, text="Задержка, мс:").pack(anchor="w", pady=(10, 0))
        self.speed = tk.Scale(panel, from_=1, to=500, orient="horizontal")
        self.speed.set(50)
        self.speed.pack(fill="x")

        tk.Label(panel, text="Инструмент:").pack(anchor="w", pady=(10, 0))
        self.tool = tk.StringVar(value="wall")

        for value, text in (
            ("wall", "Стена"),
            ("start", "Старт"),
            ("goal", "Финиш"),
        ):
            tk.Radiobutton(
                panel,
                text=text,
                value=value,
                variable=self.tool
            ).pack(anchor="w")

        tk.Button(panel, text="Случайные стены", command=self.random_walls).pack(fill="x", pady=10)
        tk.Button(panel, text="Очистить стены", command=self.clear_walls).pack(fill="x")
        tk.Label(panel, textvariable=self.info, justify="left", anchor="w").pack(fill="x", pady=(10, 0))

    def draw_grid(self):
        self.canvas.config(
            width=self.grid.cols * CELL_SIZE,
            height=self.grid.rows * CELL_SIZE
        )
        self.canvas.delete("all")
        self.rects = []

        for r in range(self.grid.rows):
            row = []
            for c in range(self.grid.cols):
                x = c * CELL_SIZE
                y = r * CELL_SIZE

                rect = self.canvas.create_rectangle(
                    x, y,
                    x + CELL_SIZE, y + CELL_SIZE,
                    fill=self.color((r, c)),
                    outline=COLOR_LINE
                )
                row.append(rect)

            self.rects.append(row)

    def color(self, pos):
        if pos == self.grid.start:
            return COLOR_START
        if pos == self.grid.goal:
            return COLOR_GOAL
        if pos in self.grid.walls:
            return COLOR_WALL

        if self.finder is not None:
            if pos in self.finder.path:
                return COLOR_PATH
            if pos in self.finder.closed_cells:
                return COLOR_CLOSED
            if pos in self.finder.open_cells:
                return COLOR_OPEN

        return COLOR_EMPTY

    def paint(self, pos):
        r, c = pos
        self.canvas.itemconfig(self.rects[r][c], fill=self.color(pos))

    def repaint_all(self):
        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                self.paint((r, c))

    def on_mouse(self, event):
        pos = (event.y // CELL_SIZE, event.x // CELL_SIZE)

        if not self.grid.in_bounds(pos):
            return

        self.reset()

        tool = self.tool.get()

        if tool == "wall":
            self.grid.add_wall(pos)
        elif tool == "start":
            self.grid.set_start(pos)
        elif tool == "goal":
            self.grid.set_goal(pos)

        if tool in ("start", "goal"):
            self.repaint_all()
        else:
            self.paint(pos)

    def new_search(self):
        self.reset()
        algorithm_class = ALGORITHMS[self.algo.get()]
        self.finder = algorithm_class(self.grid)

    def toggle_run(self):
        if self.running:
            self.stop()
            return

        if self.finder is None or self.finder.finished:
            self.new_search()

        self.running = True
        self.tick()

    def tick(self):
        if not self.running:
            return

        self.do_step()

        if self.running:
            delay = self.speed.get()
            self.after_id = self.root.after(delay, self.tick)

    def step_once(self):
        self.stop()

        if self.finder is None:
            self.new_search()

        if not self.finder.finished:
            self.do_step()

    def do_step(self):
        changed_cells = self.finder.step()

        for pos in changed_cells:
            self.paint(pos)

        self.update_info()

        if self.finder.finished:
            self.stop()


    def update_info(self):
        f = self.finder

        text = (
            "Раскрыто клеток: " + str(f.expanded) + "\n"
            "В очереди: " + str(len(f.open_cells))
        )

        if f.finished:
            if f.found:
                text += "\nДлина пути: " + str(len(f.path) - 1) + " шагов"
            else:
                text += "\nПуть не найден"

        self.info.set(text)

    def stop(self):
        self.running = False

        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def reset(self):
        self.stop()

        if self.finder is not None:
            self.finder = None
            self.repaint_all()
        self.info.set("")
    
    def random_walls(self):
        self.reset()
        self.grid.random_walls(0.25)
        self.repaint_all()

    def clear_walls(self):
        self.reset()
        self.grid.clear_walls()
        self.repaint_all()

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    App().run()