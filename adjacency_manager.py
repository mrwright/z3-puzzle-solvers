from z3 import *
from unionfind import UnionFind

# TODO: this whole thing should be redone.
# Separate out "finding connected components" from "ban components and
# regenerate solutions".

class AdjacencyManager(object):
    def __init__(self):
        self.uf = UnionFind()

    def add(self, adjacencies):
        if not adjacencies:
            return
        for item in adjacencies[1:]:
            self.uf.union(adjacencies[0], item)

    def add_all(self, adjacency_list):
        for adj in adjacency_list:
            self.add(adj)

    def classes(self):
        return self.uf.classes()

    def constraints(self, model):
        res = []
        for c in self.classes():
            res.append(Or([v != model[v].as_long() for v in c]))

        return res

def solve(s, grid, adjacency_fn):
    while True:
        s.check()
        m = s.model()

        adjacencies = list(adjacency_fn(grid, m))
        am = AdjacencyManager()
        am.add_all(adjacencies)
        if len(am.classes()) == 1:
            return m

        print "Found disconnected solution; attempting again..."

        for constraint in am.constraints(m):
            s.add(constraint)

def solve_grid(s, grid):
    def grid_adj_fn(model):
        for edge in grid.edges:
            yield [cell.var for cell in edge.cells()
                   if model[cell.var].as_long() == 1]
    cell_map = {
        c.var: c for c in grid.cells
    }

    def boundary(model, cc):
        boundary = set()
        for cell_var in cc:
            cell = cell_map[cell_var]
            boundary.update([
                c.var for c in cell.neighbors()
                if model[c.var].as_long() == 0
            ])
        return boundary

    # TODO: combine some of this code with solve.
    while True:
        s.check()
        m = s.model()

        adjacencies = list(grid_adj_fn(m))
        am = AdjacencyManager()
        am.add_all(adjacencies)
        am.add_all([c.var, c.var] for c in grid.cells if m[c.var].as_long() == 1)
        print am.classes()
        if len(am.classes()) == 1:
            return m

        print "Found disconnected solution; attempting again..."

        for cls in am.classes():
            s.add(Or([v != m[v].as_long() for v in cls] +
                     [v != m[v].as_long() for v in boundary(m, cls)]))
