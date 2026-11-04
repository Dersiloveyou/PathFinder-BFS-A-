"""Графический интерфейс (Tkinter): отрисовка сетки, редактор, анимация поиска."""
import tkinter as tk
from tkinter import ttk

from algorithms import ALGORITHMS, OPEN, CLOSE, PATH
from grid import Grid, Cell

# ---- фирменные цвета ТУСУР и цвета состояний клеток ----
BRAND = "#3C388D"
PANEL_BG = "#F4F3FA"
FONT = ("Verdana", 9)
FONT_B = ("Verdana", 9, "bold")

C_EMPTY, C_GRIDLINE = "#FFFFFF", "#DAD9EA"
C_WALL = "#3C388D"
C_MUD = "#C8A97E"
C_OPEN = "#36CCE8"        # в очереди
C_CLOSED = "#B3B2CB"      # посещена
C_CLOSED_MUD = "#9A8FB0"
C_PATH = "#F5A623"
C_START = "#9FC53A"
C_GOAL = "#652580"

MAX_W, MAX_H = 860, 620   # максимальный размер холста в пикселях
TICK_MS = 20              # период таймера анимации


class App:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Визуализатор алгоритмов поиска пути — ТУСУР")
        self.root.configure(bg=PANEL_BG)

        self.grid = Grid(25, 40)
        self.finder = None          # текущий поиск (None — поиск не запущен)
        self.path_set = set()
        self.running = False
        self.after_id = None
        self.acc = 0.0              # накопитель шагов для плавной скорости
        self.drag = None            # что тащим мышью: "start" / "goal" / None
        self.rects = []
        self.cell = 20

        self._build_ui()
        self._rebuild_canvas()

    # ================= построение интерфейса =================
    def _build_ui(self):
        left = tk.Frame(self.root, bg=PANEL_BG)
        left.pack(side="left", padx=10, pady=10)
        self.canvas = tk.Canvas(left, bg=C_EMPTY, highlightthickness=1,
                                highlightbackground=BRAND)
        self.canvas.pack()
        self.canvas.bind("<Button-1>", lambda e: self._press(e, False))
        self.canvas.bind("<B1-Motion>", lambda e: self._motion(e, False))
        self.canvas.bind("<ButtonRelease-1>", lambda e: setattr(self, "drag", None))
        for btn in ("<Button-3>", "<Button-2>"):          # правая кнопка (на macOS — Button-2)
            self.canvas.bind(btn, lambda e: self._press(e, True))
        for btn in ("<B3-Motion>", "<B2-Motion>"):
            self.canvas.bind(btn, lambda e: self._motion(e, True))

        panel = tk.Frame(self.root, bg=PANEL_BG)
        panel.pack(side="left", fill="y", padx=(0, 10), pady=10)

        tk.Label(panel, text="ПОИСК ПУТИ", bg=PANEL_BG, fg=BRAND,
                 font=("Verdana", 13, "bold")).pack(anchor="w")

        # --- алгоритм ---
        box = self._section(panel, "Алгоритм")
        self.algo = tk.StringVar(value=list(ALGORITHMS)[0])
        cb = ttk.Combobox(box, textvariable=self.algo, values=list(ALGORITHMS),
                          state="readonly", font=FONT, width=24)
        cb.pack(fill="x")
        cb.bind("<<ComboboxSelected>>", lambda e: self._reset_search())
        self.diagonal = tk.BooleanVar(value=False)
        tk.Checkbutton(box, text="Движение по диагонали (8 направлений)",
                       variable=self.diagonal, command=self._reset_search,
                       bg=PANEL_BG, font=FONT, activebackground=PANEL_BG).pack(anchor="w")

        # --- управление ---
        box = self._section(panel, "Управление")
        row = tk.Frame(box, bg=PANEL_BG)
        row.pack(fill="x")
        self.btn_run = self._button(row, "Старт", self._toggle_run)
        self.btn_run.pack(side="left", expand=True, fill="x", padx=(0, 3))
        self._button(row, "Шаг", self._step_once).pack(side="left", expand=True, fill="x", padx=3)
        self._button(row, "Сброс", self._reset_search).pack(side="left", expand=True, fill="x", padx=(3, 0))
        tk.Label(box, text="Скорость (шагов в секунду)", bg=PANEL_BG, font=FONT).pack(anchor="w", pady=(6, 0))
        self.speed = tk.Scale(box, from_=1, to=500, orient="horizontal", bg=PANEL_BG,
                              font=FONT, highlightthickness=0, troughcolor="#DAD9EA")
        self.speed.set(40)
        self.speed.pack(fill="x")

        # --- рисование ---
        box = self._section(panel, "Рисование (ЛКМ — рисовать, ПКМ — стереть)")
        self.tool = tk.StringVar(value="wall")
        for value, text in (("wall", "Стена"), ("mud", "Болото (стоимость 5)"),
                            ("erase", "Ластик"), ("start", "Поставить старт"),
                            ("goal", "Поставить финиш")):
            tk.Radiobutton(box, text=text, value=value, variable=self.tool, bg=PANEL_BG,
                           font=FONT, activebackground=PANEL_BG).pack(anchor="w")
        tk.Label(box, text="Старт и финиш можно перетаскивать мышью",
                 bg=PANEL_BG, fg="#6F6CA8", font=("Verdana", 8)).pack(anchor="w")

        # --- карта ---
        box = self._section(panel, "Карта")
        row = tk.Frame(box, bg=PANEL_BG)
        row.pack(fill="x")
        tk.Label(row, text="Строк", bg=PANEL_BG, font=FONT).pack(side="left")
        self.sp_rows = tk.Spinbox(row, from_=10, to=60, width=4, font=FONT)
        self.sp_rows.delete(0, "end"); self.sp_rows.insert(0, self.grid.rows)
        self.sp_rows.pack(side="left", padx=(3, 8))
        tk.Label(row, text="Столбцов", bg=PANEL_BG, font=FONT).pack(side="left")
        self.sp_cols = tk.Spinbox(row, from_=10, to=100, width=4, font=FONT)
        self.sp_cols.delete(0, "end"); self.sp_cols.insert(0, self.grid.cols)
        self.sp_cols.pack(side="left", padx=3)
        self._button(box, "Применить размер", self._apply_size, small=True).pack(fill="x", pady=(4, 0))
        tk.Label(box, text="Плотность случайных препятствий, %", bg=PANEL_BG, font=FONT).pack(anchor="w", pady=(6, 0))
        self.density = tk.Scale(box, from_=0, to=50, orient="horizontal", bg=PANEL_BG,
                                font=FONT, highlightthickness=0, troughcolor="#DAD9EA")
        self.density.set(25)
        self.density.pack(fill="x")
        row = tk.Frame(box, bg=PANEL_BG)
        row.pack(fill="x")
        self._button(row, "Случайные", self._random, small=True).pack(side="left", expand=True, fill="x", padx=(0, 3))
        self._button(row, "Лабиринт", self._maze, small=True).pack(side="left", expand=True, fill="x", padx=3)
        self._button(row, "Очистить", self._clear, small=True).pack(side="left", expand=True, fill="x", padx=(3, 0))

        # --- сравнение и статистика ---
        self._button(panel, "Сравнить все алгоритмы", self._compare).pack(fill="x", pady=(8, 0))
        box = self._section(panel, "Статистика")
        self.info = tk.StringVar(value="Расставьте препятствия и нажмите «Старт»")
        tk.Label(box, textvariable=self.info, bg=PANEL_BG, font=FONT, justify="left",
                 anchor="w", wraplength=270).pack(fill="x")

        # --- легенда ---
        box = self._section(panel, "Легенда")
        legend = ((C_START, "старт"), (C_GOAL, "финиш"), (C_WALL, "стена"), (C_MUD, "болото"),
                  (C_OPEN, "в очереди"), (C_CLOSED, "посещена"), (C_PATH, "найденный путь"))
        grid_f = tk.Frame(box, bg=PANEL_BG)
        grid_f.pack(fill="x")
        for i, (color, text) in enumerate(legend):
            tk.Label(grid_f, bg=color, width=2, relief="solid", bd=1).grid(row=i // 2, column=(i % 2) * 2, padx=(0, 4), pady=1)
            tk.Label(grid_f, text=text, bg=PANEL_BG, font=("Verdana", 8)).grid(
                row=i // 2, column=(i % 2) * 2 + 1, sticky="w", padx=(0, 10))

    def _section(self, parent, title):
        frame = tk.LabelFrame(parent, text=title, bg=PANEL_BG, fg=BRAND, font=FONT_B,
                              padx=6, pady=4)
        frame.pack(fill="x", pady=(6, 0))
        return frame

    def _button(self, parent, text, command, small=False):
        return tk.Button(parent, text=text, command=command, bg=BRAND, fg="white",
                         activebackground="#6F6CA8", activeforeground="white", relief="flat",
                         font=("Verdana", 8 if small else 9, "bold"), pady=3 if small else 5,
                         cursor="hand2")

    # ================= отрисовка =================
    def _rebuild_canvas(self):
        g = self.grid
        self.cell = max(6, min(MAX_W // g.cols, MAX_H // g.rows))
        self.canvas.config(width=g.cols * self.cell, height=g.rows * self.cell)
        self.canvas.delete("all")
        self.rects = []
        for r in range(g.rows):
            row = []
            for c in range(g.cols):
                x, y = c * self.cell, r * self.cell
                row.append(self.canvas.create_rectangle(
                    x, y, x + self.cell, y + self.cell,
                    fill=self._color((r, c)), outline=C_GRIDLINE))
            self.rects.append(row)

    def _color(self, pos):
        """Цвет клетки по приоритету: старт/финиш > стена > путь > посещена > очередь > болото."""
        g, f = self.grid, self.finder
        if pos == g.start:
            return C_START
        if pos == g.goal:
            return C_GOAL
        kind = g.cells[pos[0]][pos[1]]
        if kind == Cell.WALL:
            return C_WALL
        if pos in self.path_set:
            return C_PATH
        if f is not None:
            if pos in f.closed_cells:
                return C_CLOSED_MUD if kind == Cell.MUD else C_CLOSED
            if pos in f.open_cells:
                return C_OPEN
        return C_MUD if kind == Cell.MUD else C_EMPTY

    def _paint(self, pos):
        self.canvas.itemconfigure(self.rects[pos[0]][pos[1]], fill=self._color(pos))

    def _refresh_all(self):
        for r in range(self.grid.rows):
            for c in range(self.grid.cols):
                self._paint((r, c))

    # ================= мышь и редактирование =================
    def _pos(self, e):
        pos = (e.y // self.cell, e.x // self.cell)
        return pos if self.grid.in_bounds(pos) else None

    def _press(self, e, erase):
        pos = self._pos(e)
        if pos is None:
            return
        self._reset_search()                    # любое изменение карты сбрасывает поиск
        if not erase and pos == self.grid.start:
            self.drag = "start"
        elif not erase and pos == self.grid.goal:
            self.drag = "goal"
        else:
            self.drag = None
            self._apply_tool(pos, erase)

    def _motion(self, e, erase):
        pos = self._pos(e)
        if pos is None:
            return
        if self.drag == "start":
            old = self.grid.start
            if pos != old and self.grid.move_start(pos):
                self._paint(old); self._paint(pos)
        elif self.drag == "goal":
            old = self.grid.goal
            if pos != old and self.grid.move_goal(pos):
                self._paint(old); self._paint(pos)
        else:
            self._apply_tool(pos, erase)

    def _apply_tool(self, pos, erase):
        g, tool = self.grid, self.tool.get()
        if erase or tool == "erase":
            g.set_cell(pos, Cell.EMPTY)
        elif tool == "wall":
            g.set_cell(pos, Cell.WALL)
        elif tool == "mud":
            g.set_cell(pos, Cell.MUD)
        elif tool == "start":
            old = g.start
            if g.move_start(pos):
                self._paint(old)
        elif tool == "goal":
            old = g.goal
            if g.move_goal(pos):
                self._paint(old)
        self._paint(pos)

    # ================= запуск и анимация поиска =================
    def _new_search(self):
        self._stop()
        self.path_set.clear()
        self.finder = ALGORITHMS[self.algo.get()](self.grid, self.diagonal.get())
        self._refresh_all()

    def _toggle_run(self):
        if self.running:
            self._stop()
            return
        if self.finder is None or self.finder.finished:
            self._new_search()
        self.running = True
        self.btn_run.config(text="Пауза")
        self.acc = 0.0
        self._tick()

    def _step_once(self):
        self._stop()
        if self.finder is None:
            self._new_search()
        if not self.finder.finished:
            self._do_step()

    def _tick(self):
        """Таймер анимации: за каждый тик делает столько шагов, сколько нужно скорости."""
        if not self.running:
            return
        self.acc += self.speed.get() * TICK_MS / 1000
        n, self.acc = int(self.acc), self.acc - int(self.acc)
        for _ in range(n):
            if not self._do_step():
                return
        self.after_id = self.root.after(TICK_MS, self._tick)

    def _do_step(self):
        """Один шаг алгоритма + перерисовка изменившихся клеток. False — поиск окончен."""
        events = self.finder.step()
        if events is None:
            self._stop()
            self._show_stats(final=True)
            return False
        for kind, pos in events:
            if kind == PATH:
                self.path_set.add(pos)
            self._paint(pos)
        self._show_stats()
        return True

    def _stop(self):
        self.running = False
        self.btn_run.config(text="Старт")
        if self.after_id is not None:
            self.root.after_cancel(self.after_id)
            self.after_id = None

    def _reset_search(self):
        self._stop()
        if self.finder is not None or self.path_set:
            self.finder = None
            self.path_set.clear()
            self._refresh_all()
        self.info.set("Расставьте препятствия и нажмите «Старт»")

    def _show_stats(self, final=False):
        f = self.finder
        text = f"Раскрыто клеток: {f.expanded}\nВ очереди: {len(f.open_cells)}"
        if final or f.found:
            if f.found:
                text += (f"\nПуть найден: {len(f.path)} клеток\nСтоимость пути: {f.path_cost():.1f}"
                         f"\nВремя алгоритма: {f.elapsed * 1000:.2f} мс")
            else:
                text += "\nПуть НЕ найден"
        self.info.set(text)

    # ================= кнопки карты =================
    def _apply_size(self):
        try:
            rows = min(60, max(10, int(self.sp_rows.get())))
            cols = min(100, max(10, int(self.sp_cols.get())))
        except ValueError:
            return
        self._reset_search()
        self.grid.resize(rows, cols)
        self._rebuild_canvas()

    def _random(self):
        self._reset_search()
        self.grid.random_obstacles(self.density.get() / 100)
        self._refresh_all()

    def _maze(self):
        self._reset_search()
        if self.grid.rows < 5 or self.grid.cols < 5:
            return
        self.grid.generate_maze()
        self._refresh_all()

    def _clear(self):
        self._reset_search()
        self.grid.clear()
        self._refresh_all()

    # ================= сравнение алгоритмов =================
    def _compare(self):
        """Прогоняет все алгоритмы на текущей карте и показывает таблицу."""
        self._reset_search()
        results = [cls(self.grid, self.diagonal.get()).run_to_end() for cls in ALGORITHMS.values()]
        win = tk.Toplevel(self.root)
        win.title("Сравнение алгоритмов на текущей карте")
        win.configure(bg=PANEL_BG)
        cols = ("Алгоритм", "Раскрыто клеток", "Макс. очередь", "Длина пути", "Стоимость пути", "Время, мс")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=len(results))
        for c in cols:
            tree.heading(c, text=c)
            tree.column(c, width=130 if c != "Алгоритм" else 150, anchor="center")
        for s in results:
            if s["found"]:
                tree.insert("", "end", values=(s["algorithm"], s["expanded"], s["max_frontier"],
                                               s["path_len"], f"{s['path_cost']:.1f}", f"{s['time_ms']:.2f}"))
            else:
                tree.insert("", "end", values=(s["algorithm"], s["expanded"], s["max_frontier"],
                                               "нет пути", "—", f"{s['time_ms']:.2f}"))
        tree.pack(padx=10, pady=10)

    def run(self):
        self.root.mainloop()
