from z3 import *
import cairo

from display import BaseDisplay
from invalidobj import Invalid

# This module represents a hex grid that has rows of hexes. If your puzzle has columns of hexes, turn it sideways.

# How coordinates work:
# Everything is identified by three coordinates: N, SE, and SW. A value of 1 in a coordinate is enough to move from
# the center of a cell to a corner, or along an edge.
#
# By convention, cells have coordinates that sum to 0. So the cell with coordinates 3N, -2SE, -1SW is actually
# three rows to the north and half a hex west of the cell at 0, 0, 0, because you move 3 half-hexes north,
# two northwest, and one northeast. The nice thing about this convention is that you can subtract coordinates to make
# vectors (also with 0 coordinate sum if they represent movement by a whole number of hexes), and the length of a vector
# is always the largest absolute value of the components. If you ever have a set of coordinates that you think should
# represent a cell, but they don't sum to 0, subtract 1/3 of the sum from each coordinate so that they do. (If the sum
# isn't divisible by 3, it doesn't represent a cell, but a point of one kind or the other.)
#
# Northward points (those with edges to the north, se, and sw) have coordinates that sum to 1.
# Southward points (those with edges to the south, nw, and ne) have coordinates that sum to -1.
# The code upholds all of these conventions internally, but the part-accessors in HexGrid fix coordinates if clients
# lost track.
#
# All edges are identified by their northward point (this is just a convention I decided on): so vertical edges are
# identified by their southern point, ne-sw (like /) edges by their ne point, and nw-se (like \) edges by their nw
# point. The edge accessors in HexGrid also correct you if you accidentally ask for an edge by its southward point
# instead.

class Cell:
    def __init__(self, var, n, se, sw):
        self.var = var
        self.n = n
        self.se = se
        self.sw = sw
        self.edge_w = Invalid()
        self.edge_e = Invalid()
        self.edge_nw = Invalid()
        self.edge_ne = Invalid()
        self.edge_sw = Invalid()
        self.edge_se = Invalid()
        self.cell_w = Invalid()
        self.cell_e = Invalid()
        self.cell_nw = Invalid()
        self.cell_ne = Invalid()
        self.cell_sw = Invalid()
        self.cell_se = Invalid()

    def edges(self):
        return [x for x in [self.edge_ne, self.edge_e,
                            self.edge_se, self.edge_sw,
                            self.edge_w, self.edge_nw]
                if not isinstance(x, Invalid)]

    def neighbors(self):
        return [x for x in [self.cell_ne, self.cell_e,
                            self.cell_se, self.cell_sw,
                            self.cell_w, self.cell_nw]
                if not isinstance(x, Invalid)]

    def __str__(self):
        return "Cell({} @ {},{},{})".format(self.var, self.n, self.se, self.sw)

    @property
    def coords(self):
        return self.n, self.se, self.sw

class VertEdge(object):
    def __init__(self, var, n, se, sw):
        self.var = var
        self.n = n
        self.se = se
        self.sw = sw
        self.edge_nw = Invalid()
        self.edge_sw = Invalid()
        self.edge_ne = Invalid()
        self.edge_se = Invalid()
        self.cell_w = Invalid()
        self.cell_e = Invalid()
        self.point_n = Invalid()
        self.point_s = Invalid()

    def cells(self):
        return [x for x in [self.cell_w, self.cell_e]
                if not isinstance(x, Invalid)]

    def __str__(self):
        return "Vert({})".format(self.var)

    @property
    def coords(self):
        return self.n, self.se, self.sw

    @property
    def vector(self):
        return 1, 0, 0

class NW_SE_Edge(object):
    def __init__(self, var, n, se, sw):
        self.var = var
        self.n = n
        self.se = se
        self.sw = sw
        self.edge_ne = Invalid()
        self.edge_w = Invalid()
        self.edge_e = Invalid()
        self.edge_sw = Invalid()
        self.cell_ne = Invalid()
        self.cell_sw = Invalid()
        self.point_nw = Invalid()
        self.point_se = Invalid()

    def cells(self):
        return [x for x in [self.cell_ne, self.cell_sw]
                if not isinstance(x, Invalid)]
    def __str__(self):
        return "NW_SE({})".format(self.var)

    @property
    def coords(self):
        return self.n, self.se, self.sw

    @property
    def vector(self):
        return 0, 1, 0

class NE_SW_Edge(object):
    def __init__(self, var, n, se, sw):
        self.var = var
        self.n = n
        self.se = se
        self.sw = sw
        self.edge_nw = Invalid()
        self.edge_n = Invalid()
        self.edge_s = Invalid()
        self.edge_se = Invalid()
        self.cell_nw = Invalid()
        self.cell_se = Invalid()
        self.point_ne = Invalid()
        self.point_sw = Invalid()

    def cells(self):
        return [x for x in [self.cell_nw, self.cell_se]
                if not isinstance(x, Invalid)]
    def __str__(self):
        return "NE_SW({})".format(self.var)

    @property
    def coords(self):
        return self.n, self.se, self.sw

    @property
    def vector(self):
        return 0, 0, 1

class NorthwardPoint(object):
    def __init__(self, var, n, se, sw):
        self.var = var
        self.n = n
        self.se = se
        self.sw = sw
        self.edge_n = Invalid()
        self.edge_se = Invalid()
        self.edge_sw = Invalid()
        self.point_n = Invalid()
        self.point_se = Invalid()
        self.point_sw = Invalid()
        self.cell_s = Invalid()
        self.cell_ne = Invalid()
        self.cell_nw = Invalid()

    def edges(self):
        return [x for x in [self.edge_n,
                            self.edge_se,
                            self.edge_sw]
                if not isinstance(x, Invalid)]
    def __str__(self):
        return "NWP({})".format(self.var)

    @property
    def coords(self):
        return self.n, self.se, self.sw

class SouthwardPoint(object):
    def __init__(self, var, n, se, sw):
        self.var = var
        self.n = n
        self.se = se
        self.sw = sw
        self.edge_s = Invalid()
        self.edge_ne = Invalid()
        self.edge_nw = Invalid()
        self.point_s = Invalid()
        self.point_ne = Invalid()
        self.point_nw = Invalid()
        self.cell_n = Invalid()
        self.cell_se = Invalid()
        self.cell_sw = Invalid()

    def edges(self):
        return [x for x in [self.edge_s,
                            self.edge_ne,
                            self.edge_nw]
                if not isinstance(x, Invalid)]
    def __str__(self):
        return "SWP({})".format(self.var)

    @property
    def coords(self):
        return self.n, self.se, self.sw

# This function figures out how wide row y should be, and the coordinates of the westernmost hex in that column.
# I figured it out by drawing a lot of pictures. The northwest corner (the first hex of row 0) is hex 0,0,0 in the
# coordinate system, because that's where we start generating cells.
def calc_bounds(width, west_row, east_row, y):
    n = -y
    if y < west_row:
        se = 0
        sw = y
    else:
        se = y - west_row
        sw = west_row

    row_width = width + y - min(west_row, east_row)
    if y > west_row:
        row_width = row_width - (y - west_row)
    if y > east_row:
        row_width = row_width - (y - east_row)

    return row_width, n, se, sw

# This function returns the given coords regularized so that -1 <= n + se + sw <= 1
def regularize_coords(n, se, sw):
    sum = n + se + sw
    adj = (sum + 1) // 3
    return n - adj, se - adj, sw - adj

def coord_add(left, right):
    ln, lse, lsw = left
    rn, rse, rsw = right
    return ln+rn, lse+rse, lsw+rsw

def coord_neg(input):
    n, se, sw = input
    return -n, -se, -sw

# This class describes an oblong (possibly degenerate) hexagon. height is the total number of rows in the grid.
# width is the width of the row containing the west corner, which is the same as the maximum width of a row.
# west_row is the (0-based) index of that row. east_row is the (0-based) index of the row containing
# the east corner. These values are not independent: so that the northernmost and southernmost rows have a positive
# length, we require that west_row < width and east_row + width >= height (for left-leaning boards), or vice
# versa (for right-leaning boards).
# The northwest corner is hex 0,0,0 in the coordinate system, because that's where we start generating cells.
class HexGrid(object):
    def __init__(self, height, width, west_row, east_row, basename='', cellgen=Int, pointgen=Int, edgegen=Int):
        self.height = height
        self.width = width
        self.west_row = west_row
        self.east_row = east_row

        cell_array = {}
        vert_array = {}
        ne_sw_array = {}
        nw_se_array = {}
        northward_point_array = {}
        southward_point_array = {}

        cells = []
        verts = []
        ne_sws = []
        nw_ses = []
        northward_points = []
        southward_points = []

        # make cells
        for y in range(height):
            row_width, n, se, sw = calc_bounds(width, west_row, east_row, y)

            for _ in range(row_width):
                # make cell
                cv = cellgen('{}cell_{},{},{}'.format(basename, n, se, sw))
                c = Cell(cv, n, se, sw)
                cells.append(c)
                cell_array[n, se, sw] = c
                se = se + 1
                sw = sw - 1

        self.cell_array = cell_array
        self.cells = cells

        # make southward points to nw of each hex
        # one more row for south edge of board
        for y in range(height + 1):
            row_width, n, se, sw = calc_bounds(width, west_row, east_row, y)
            # one more for the ne corner of the row
            row_width = row_width + 1
            # start to nw of first hex
            se = se - 1
            for _ in range(row_width):
                # make point to nw
                nw_pv = pointgen('{}point_{},{},{}'.format(basename, n, se, sw))
                nw_p = SouthwardPoint(nw_pv, n, se, sw)
                southward_points.append(nw_p)
                southward_point_array[n, se, sw] = nw_p
                se = se + 1
                sw = sw - 1

        self.southward_points = southward_points
        self.southward_point_array = southward_point_array

        # make northward points to n of each hex
        # one more row for south edge of board
        for y in range(height + 1):
            row_width, n, se, sw = calc_bounds(width, west_row, east_row, y)
            if y > west_row:
                # one more at the west end for the sw corner of the row
                row_width = row_width + 1
                se = se - 1
                sw = sw + 1
            if y > east_row:
                # one more at the east end for the se corner of the row
                row_width = row_width + 1
            # start to n of first hex
            n = n + 1
            for _ in range(row_width):
                # make point to w
                n_pv = pointgen('{}point_{},{},{}'.format(basename, n, se, sw))
                n_p = NorthwardPoint(n_pv, n, se, sw)
                northward_points.append(n_p)
                northward_point_array[n, se, sw] = n_p
                se = se + 1
                sw = sw - 1

        self.northward_points = northward_points
        self.northward_point_array = northward_point_array

        # make vert edges w of each hex
        for y in range(height):
            row_width, n, se, sw = calc_bounds(width, west_row, east_row, y)
            # one more for east edge of board
            row_width = row_width + 1
            # start to w of first hex
            sw = sw + 1
            for _ in range(row_width):
                # make edge to w
                w_ev = edgegen('{}vert_{},{},{}'.format(basename, n, se, sw))
                w_e = VertEdge(w_ev, n, se, sw)
                verts.append(w_e)
                vert_array[n, se, sw] = w_e
                se = se + 1
                sw = sw - 1

        self.vert_array = vert_array
        self.verts = verts

        # make ne_sw edges nw of each hex
        # one more row for south edge of board
        for y in range(height + 1):
            row_width, n, se, sw = calc_bounds(width, west_row, east_row, y)
            if y > east_row:
                # one more for se edge of board
                row_width = row_width + 1
            # start to nw of first hex
            n = n + 1
            for _ in range(row_width):
                # make edge to nw
                nw_ev = edgegen('{}ne_sw_{},{},{}'.format(basename, n, se, sw))
                nw_e = NE_SW_Edge(nw_ev, n, se, sw)
                ne_sws.append(nw_e)
                ne_sw_array[n, se, sw] = nw_e
                se = se + 1
                sw = sw - 1

        self.ne_sw_array = ne_sw_array
        self.ne_sws = ne_sws

        # make nw_se edges ne of each hex
        # one more row for south edge of board
        for y in range(height + 1):
            row_width, n, se, sw = calc_bounds(width, west_row, east_row, y)
            if y > west_row:
                # one more at west end for sw edge of board
                row_width = row_width + 1
                se = se - 1
                sw = sw + 1
            # start to ne of first hex
            n = n + 1
            for _ in range(row_width):
                # make edge to ne
                ne_ev = edgegen('{}nw_se_{},{},{}'.format(basename, n, se, sw))
                ne_e = NW_SE_Edge(ne_ev, n, se, sw)
                nw_ses.append(ne_e)
                nw_se_array[n, se, sw] = ne_e
                se = se + 1
                sw = sw - 1

        self.nw_se_array = nw_se_array
        self.nw_ses = nw_ses

        # link things up
        for c in self.cells:
            n, se, sw = c.n, c.se, c.sw
            c.cell_e = self.cell(n, se + 1, sw - 1)
            c.cell_w = self.cell(n, se - 1, sw + 1)
            c.cell_se = self.cell(n-1, se+1, sw)
            c.cell_ne = self.cell(n+1, se, sw-1)
            c.cell_sw = self.cell(n-1, se, sw+1)
            c.cell_nw = self.cell(n+1, se-1, sw)

            c.edge_w = self.vert(n, se, sw+1)
            c.edge_w.cell_e = c
            c.edge_e = self.vert(n, se+1, sw)
            c.edge_e.cell_w = c
            c.edge_nw = self.ne_sw(n+1, se, sw)
            c.edge_nw.cell_se = c
            c.edge_se = self.ne_sw(n, se+1, sw)
            c.edge_se.cell_nw = c
            c.edge_ne = self.nw_se(n+1, se, sw)
            c.edge_ne.cell_sw = c
            c.edge_sw = self.nw_se(n, se, sw+1)
            c.edge_sw.cell_ne = c

            self.northward_point(n + 1, se, sw).cell_s = c
            self.southward_point(n - 1, se, sw).cell_n = c
            self.northward_point(n, se + 1, sw).cell_nw = c
            self.southward_point(n, se - 1, sw).sell_nw = c
            self.northward_point(n, se, sw + 1).cell_ne = c
            self.southward_point(n, se, sw - 1).cell_sw = c

        for p in northward_points:
            n, se, sw = p.n, p.se, p.sw
            p.edge_n = self.vert(n, se, sw)
            p.edge_se = self.nw_se(n, se, sw)
            p.edge_sw = self.ne_sw(n, se, sw)
            if not isinstance(p.edge_n, Invalid):
                p.edge_n.point_s = p
                p.edge_n.edge_se = p.edge_se
                p.edge_n.edge_sw = p.edge_sw
            if not isinstance(p.edge_se, Invalid):
                p.edge_se.point_nw = p
                p.edge_se.edge_n = p.edge_n
                p.edge_se.edge_sw = p.edge_sw
            if not isinstance(p.edge_sw, Invalid):
                p.edge_sw.point_ne = p
                p.edge_sw.edge_n = p.edge_n
                p.edge_sw.edge_se = p.edge_se

        for p in southward_points:
            n, se, sw = p.n, p.se, p.sw
            p.edge_s = self.vert(n, se+1, sw+1)
            p.edge_ne = self.ne_sw(n+1, se+1, sw)
            p.edge_nw = self.nw_se(n+1, se, sw+1)
            if not isinstance(p.edge_s, Invalid):
                p.edge_s.point_n = p
                p.edge_s.edge_ne = p.edge_ne
                p.edge_s.edge_nw = p.edge_nw
            if not isinstance(p.edge_ne, Invalid):
                p.edge_ne.point_sw = p
                p.edge_ne.edge_s = p.edge_s
                p.edge_ne.edge_nw = p.edge_nw
            if not isinstance(p.edge_nw, Invalid):
                p.edge_nw.point_se = p
                p.edge_nw.edge_s = p.edge_s
                p.edge_nw.edge_ne = p.edge_ne

    def cell(self, n, se, sw):
        return self.cell_array.get(regularize_coords(n, se, sw), Invalid())

    def vert(self, n, se, sw):
        n, se, sw = regularize_coords(n, se, sw)
        if n + se + sw == -1:
            se = se + 1
            sw = sw + 1
        return self.vert_array.get((n, se, sw), Invalid())

    def nw_se(self, n, se, sw):
        n, se, sw = regularize_coords(n, se, sw)
        if n + se + sw == -1:
            n = n + 1
            sw = sw + 1
        return self.nw_se_array.get((n, se, sw), Invalid())

    def ne_sw(self, n, se, sw):
        n, se, sw = regularize_coords(n, se, sw)
        if n + se + sw == -1:
            n = n + 1
            se = se + 1
        return self.ne_sw_array.get((n, se, sw), Invalid())

    def southward_point(self, n, se, sw):
        return self.southward_point_array.get(regularize_coords(n, se, sw), Invalid())

    def northward_point(self, n, se, sw):
        return self.northward_point_array.get(regularize_coords(n, se, sw), Invalid())

    @property
    def edges(self):
        return self.verts + self.ne_sws + self.nw_ses

    @property
    def points(self):
        return self.southward_points + self.northward_points

    @property
    def rows(self):
        for y in range(self.height):
            row_width, n, se, sw = calc_bounds(self.width, self.west_row, self.east_row, y)
            yield [self.cell(n, se+x, sw-x) for x in range(row_width)]


HALF_SQRT3 = math.sqrt(3)/2
def _transform_coords(coords):
    n, se, sw = coords
    x = (se - sw) * HALF_SQRT3
    y = - n + se / 2 + sw / 2
    return x, y

class HexDisplay(BaseDisplay):
    def set_vert_edge_fn(self, fn):
        self.set_edge_fn(fn, only_for=(1,0,0))

    def set_nw_se_edge_fn(self, fn):
        self.set_edge_fn(fn, only_for=(0,1,0))

    def set_ne_sw_edge_fn(self, fn):
        self.set_edge_fn(fn, only_for=(0,0,1))

    def set_northward_point_fn(self, fn):
        self.set_point_fn(fn, only_for=1)

    def set_southward_point_fn(self, fn):
        self.set_point_fn(fn, only_for=-1)

    def _get_extents(self, grid):
        # in half-hexes
        left, _ = _transform_coords((-grid.west_row, 0, grid.west_row+1))
        _, top = _transform_coords((1, 0, 0))
        width, _, se, sw = calc_bounds(grid.width, grid.west_row, grid.east_row, grid.east_row)
        right, _ = _transform_coords((0, se+width-1, sw-width))
        _, bottom = _transform_coords((-grid.height, grid.height-1, 0))

        return left, top, right, bottom

    def _setup_cell(self, cell):
        matrix = cairo.Matrix()
        matrix.translate(*_transform_coords(cell.coords))
        fn = self.get_cell_fn()
        return fn, matrix

    def _setup_edge(self, edge):
        # matrix = cairo.Matrix()
        # matrix.translate(*HexDisplay.transform_coords(edge.coords))
        d_x, d_y = _transform_coords(edge.vector)
        matrix = cairo.Matrix(d_x, d_y, -d_y, d_x, *_transform_coords(edge.coords))
        fn = self.get_edge_fn(edge.vector)
        return fn, matrix

    def _setup_point(self, point):
        matrix = cairo.Matrix()
        matrix.translate(*_transform_coords(point.coords))
        if sum(point.coords) == -1:
            matrix.scale(-1, -1)
        fn = self.get_point_fn(sum(point.coords))
        return fn, matrix

    CELL_CORNERS = [
        _transform_coords((1,0,0)),
        _transform_coords((0,0,-1)),
        _transform_coords((0,1,0)),
        _transform_coords((-1,0,0)),
        _transform_coords((0,0,1)),
        _transform_coords((0,-1,0)),
    ]
    def _cell_corners(self):
        return HexDisplay.CELL_CORNERS





# g = HexGrid(1, 1, 0, 0)
#
# print([str(c) for c in g.cells])
# print([str(e) for e in g.edges])
# print([str(p) for p in g.points])
