from z3 import *
from invalidobj import Invalid

class Cell(object):
    def __init__(self, var, x, y):
        self.var = var
        self.edge_above = Invalid()
        self.edge_below = Invalid()
        self.edge_left = Invalid()
        self.edge_right = Invalid()
        self.cell_above = Invalid()
        self.cell_below = Invalid()
        self.cell_left = Invalid()
        self.cell_right = Invalid()
        self.x = x
        self.y = y

    def edges(self):
        return [x for x in [self.edge_above, self.edge_below,
                            self.edge_left, self.edge_right]
                if not isinstance(x, Invalid)]

    def neighbors(self):
        return [x for x in [self.cell_above, self.cell_below,
                            self.cell_left, self.cell_right]
                if not isinstance(x, Invalid)]

    def __str__(self):
        return "Cell({} @ {},{})".format(self.var, self.x, self.y)

class HorizEdge(object):
    def __init__(self, var, x, y):
        self.var = var
        self.x = x
        self.y = y
        self.edge_left = Invalid()
        self.edge_right = Invalid()
        self.cell_below = Invalid()
        self.cell_above = Invalid()
        self.point_left = Invalid()
        self.point_right = Invalid()

    def cells(self):
        return [x for x in [self.cell_below, self.cell_above]
                if not isinstance(x, Invalid)]

    @property
    def is_outside(self):
        return len(self.cells()) < 2

    def __str__(self):
        return "Horiz({})".format(self.var)

class VertEdge(object):
    def __init__(self, var, x, y):
        self.var = var
        self.x = x
        self.y = y
        self.edge_above = Invalid()
        self.edge_below = Invalid()
        self.cell_left = Invalid()
        self.cell_right = Invalid()
        self.point_above = Invalid()
        self.point_below = Invalid()

    def cells(self):
        return [x for x in [self.cell_left, self.cell_right]
                if not isinstance(x, Invalid)]

    @property
    def is_outside(self):
        return len(self.cells()) < 2

    def __str__(self):
        return "Vert({})".format(self.var)

class Point(object):
    def __init__(self, var, x, y):
        self.var = var
        self.x = x
        self.y = y
        self.edge_above = Invalid()
        self.edge_below = Invalid()
        self.edge_left = Invalid()
        self.edge_right = Invalid()
        self.point_left = Invalid()
        self.point_right = Invalid()
        self.point_above = Invalid()
        self.point_below = Invalid()

    def edges(self):
        return [x for x in [self.edge_above,
                            self.edge_below,
                            self.edge_left,
                            self.edge_right]
                if not isinstance(x, Invalid)]

    @property
    def is_outside(self):
        return len(self.edges()) < 4

    def horiz_edge(self, offs):
        assert offs != 0
        if offs == 1:
            return self.edge_right
        elif offs == -1:
            return self.edge_left
        elif offs > 0:
            return self.point_right.horiz_edge(offs-1)
        elif offs < 0:
            return self.point_left.horiz_edge(offs+1)

    def vert_edge(self, offs):
        assert offs != 0
        if offs == 1:
            return self.edge_below
        elif offs == -1:
            return self.edge_above
        elif offs > 0:
            return self.point_below.vert_edge(offs-1)
        elif offs < 0:
            return self.point_above.vert_edge(offs+1)

class Grid(object):
    def __init__(self, width, height, basename='', cellgen=Int, pointgen=Int, edgegen=Int):
        self.width = width
        self.height = height

        cell_array = {}
        vert_array = {}
        horiz_array = {}
        point_array = {}

        cells = []
        verts = []
        horizs = []
        points = []

        for x in range(width):
            for y in range(height):
                v = cellgen('{}cell_{},{}'.format(basename, x, y))
                c = Cell(v, x, y)
                cells.append(c)
                cell_array[x,y] = c

        self.cell_array = cell_array
        self.cells = cells

        for x in range(width+1):
            for y in range(height):
                v = edgegen('{}vert_{},{}'.format(basename, x, y))
                c = VertEdge(v, x, y)
                verts.append(c)
                vert_array[x,y] = c

        self.vert_array = vert_array
        self.verts = verts

        for x in range(width):
            for y in range(height+1):
                v = edgegen('{}horiz_{},{}'.format(basename, x, y))
                c = HorizEdge(v, x, y)
                horizs.append(c)
                horiz_array[x,y] = c

        self.horiz_array = horiz_array
        self.horizs = horizs

        for x in range(width+1):
            for y in range(height+1):
                v = pointgen('{}point_{},{}'.format(basename, x, y))
                c = Point(v, x, y)
                points.append(c)
                point_array[x, y] = c

        self.point_array = point_array
        self.points = points

        for x in range(width):
            for y in range(height):
                c = cell_array[x,y]
                c.cell_above = self.cell(x,y-1)
                c.cell_below = self.cell(x,y+1)
                c.cell_left = self.cell(x-1,y)
                c.cell_right = self.cell(x+1,y)

                c.edge_above = self.horiz(x, y)
                c.edge_above.cell_below = c
                c.edge_below = self.horiz(x, y+1)
                c.edge_below.cell_above = c
                c.edge_left = self.vert(x, y)
                c.edge_left.cell_right = c
                c.edge_right = self.vert(x+1, y)
                c.edge_right.cell_left = c

        for x in range(width+1):
            for y in range(height):
                e = self.vert(x, y)
                e.edge_above = self.vert(x, y-1)
                e.edge_below = self.vert(x, y+1)

        for x in range(width):
            for y in range(height+1):
                e = self.horiz(x, y)
                e.edge_left = self.horiz(x-1, y)
                e.edge_right = self.horiz(x+1, y)

        for x in range(width+1):
            for y in range(height+1):
                p = self.point(x, y)
                p.edge_left = self.horiz(x-1, y)
                p.edge_left.point_right = p
                p.edge_right = self.horiz(x, y)
                p.edge_right.point_left = p
                p.edge_above = self.vert(x, y-1)
                p.edge_above.point_below = p
                p.edge_below = self.vert(x, y)
                p.edge_below.point_above = p
                p.point_right = self.point(x+1, y)
                p.point_left = self.point(x-1, y)
                p.point_above = self.point(x, y-1)
                p.point_below = self.point(x, y+1)

    def cell(self, x, y):
        return self.cell_array.get((x, y), Invalid())

    def horiz(self, x, y):
        return self.horiz_array.get((x, y), Invalid())

    def vert(self, x, y):
        return self.vert_array.get((x, y), Invalid())

    def point(self, x, y):
        return self.point_array.get((x, y), Invalid())

    @property
    def edges(self):
        return self.horizs + self.verts

# g = EdgedGrid(10, 10)

# s = Solver()

# for c in g.cells:
#     s.add(c.var >= 0)
#     s.add(c.var < 10)

# #for x in range(10):
# #    s.add(Distinct([g.cell(x, y).var for y in range(10)]))
# #    s.add(Distinct([g.cell(y, x).var for y in range(10)]))

# s.check()
# m = s.model()
# for x in list(m):
#     print m[x]
# for y in range(10):
#     r = ""
#     for x in range(10):
#         r += str(m[g.cell(x, y).var].as_long())
#     print r
