import heapq
from collections import deque


class PathFinder:

    name = ""

    def __init__(self, grid):
        self.grid = grid
        self.start = grid.start
        self.goal = grid.goal
        self.parent = {self.start: None} 
        self.open_cells = {self.start}     
        self.closed_cells = set()        
        self.path = []                    
        self.found = False                 
        self.finished = False              
        self.expanded = 0            

    def _visit(self, cell):
        self.open_cells.discard(cell)
        self.closed_cells.add(cell)
        self.expanded += 1

    def _no_path(self):
        self.finished = True
        return []

    def _finish_path(self):
        cell = self.goal
        while cell is not None:
            self.path.append(cell)
            cell = self.parent[cell]
        self.path.reverse()
        self.found = True
        self.finished = True
        return self.path


class BFS(PathFinder):

    name = "BFS (волновой)"

    def __init__(self, grid):
        super().__init__(grid)
        self.queue = deque([self.start])   

    def step(self):
        if not self.queue:
            return self._no_path()
        cell = self.queue.popleft()        
        self._visit(cell)
        if cell == self.goal:
            return [cell] + self._finish_path()
        changed = [cell]
        for nb in self.grid.neighbors(cell):
            if nb not in self.parent:
                self.parent[nb] = cell
                self.queue.append(nb)
                self.open_cells.add(nb)
                changed.append(nb)
        return changed


class Dijkstra(PathFinder):

    name = "Дейкстра"

    def __init__(self, grid):
        super().__init__(grid)
        self.dist = {self.start: 0}           
        self.heap = [(0, self.start)]          

    def step(self):
        if not self.heap:
            return self._no_path()
        dist, cell = heapq.heappop(self.heap)  
        self._visit(cell)
        if cell == self.goal:
            return [cell] + self._finish_path()
        changed = [cell]
        for nb in self.grid.neighbors(cell):
            new_dist = dist + 1                
            if nb not in self.dist or new_dist < self.dist[nb]:
                self.dist[nb] = new_dist
                self.parent[nb] = cell
                heapq.heappush(self.heap, (new_dist, nb))
                self.open_cells.add(nb)
                changed.append(nb)
        return changed


class AStar(PathFinder):
   
    name = "A*"

    def __init__(self, grid):
        super().__init__(grid)
        self.g = {self.start: 0}               
        h = self.heuristic(self.start)
        self.heap = [(h, h, self.start)]       

    def heuristic(self, cell):
        return abs(cell[0] - self.goal[0]) + abs(cell[1] - self.goal[1])

    def step(self):
        cell = None
        while self.heap:                      
            _, _, candidate = heapq.heappop(self.heap)
            if candidate not in self.closed_cells:
                cell = candidate
                break
        if cell is None:
            return self._no_path()
        self._visit(cell)
        if cell == self.goal:
            return [cell] + self._finish_path()
        changed = [cell]
        for nb in self.grid.neighbors(cell):
            new_g = self.g[cell] + 1
            if nb not in self.g or new_g < self.g[nb]:
                self.g[nb] = new_g
                self.parent[nb] = cell
                h = self.heuristic(nb)
                heapq.heappush(self.heap, (new_g + h, h, nb))
                self.open_cells.add(nb)
                changed.append(nb)
        return changed

ALGORITHMS = {cls.name: cls for cls in (BFS, Dijkstra, AStar)}
