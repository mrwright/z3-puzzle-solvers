from z3 import *
from invalidobj import Invalid

# This module represents a hex grid that has columns of hexes. If your puzzle has rows of hexes, turn it sideways.

# How coordinates work:
# Everything is identified by three coordinates: E, NW, and SW. A value of 1 in a coordinate is enough to move from
# the center of a cell to a corner, or along an edge.
#
# By convention, cells have coordinates that sum to 0. So the cell with coordinates 3, -2, -1 is actually
# three columns to the east and half a hex south of the cell at 0, 0, 0, because you move 3 half-hexes east,
# two southeast, and one northeast. The nice thing about this convention is that you can subtract coordinates to make
# vectors (also with 0 coordinate sum if they represent movement by a whole number of hexes), and the length of a vector
# is always the largest absolute value of the components. If you ever have a set of coordinates that you think should
# represent a cell, but they don't sum to 0, subtract 1/3 of the sum from each coordinate so that they do. (If the sum
# isn't divisible by 3, it doesn't represent a cell, but a point of one kind or the other.)
#
# Westward points (those with edges to the west, ne, and se) have coordinates that sum to 1.
# Eastward points (those with edges to the east, nw, and sw) have coordinates that sum to -1.
# The code upholds all of these conventions internally, but the part-accessors in HexGrid fix coordinates if clients
# lost track.
#
# All edges are identified by their eastward point (this is just a convention I decided on): so horizontal edges are
# identified by their western point, ne-sw (like /) edges by their ne point, and nw-se (like \) edges by their se point.

class Cell:
    def __init__(self, var, e, nw, sw):
        self.var = var
        self.edge_n = Invalid()
        self.edge_s = Invalid()
        self.edge_nw = Invalid()
        self.edge_ne = Invalid()
        self.edge_sw = Invalid()
        self.edge_se = Invalid()
        self.cell_n = Invalid()
        self.cell_s = Invalid()
        self.cell_nw = Invalid()
        self.cell_ne = Invalid()
        self.cell_sw = Invalid()
        self.cell_se = Invalid()
        self.e = e
        self.nw = nw
        self.sw = sw

def edges(self):
    return [x for x in [self.edge_n, self.edge_ne,
                        self.edge_se, self.edge_s,
                        self.edge_sw, self.edge_nw]
            if not isinstance(x, Invalid)]

def neighbors(self):
    return [x for x in [self.cell_n, self.cell_ne,
                        self.cell_se, self.cell_s,
                        self.cell_sw, self.cell_nw]
            if not isinstance(x, Invalid)]

def __str__(self):
    return "Cell({} @ {},{},{})".format(self.var, self.e, self.nw, self.sw)

class HorizEdge(object):
    def __init__(self, var, e, nw, sw):
        self.var = var
        self.e = e
        self.nw = nw
        self.sw = sw
        self.edge_nw = Invalid()
        self.edge_sw = Invalid()
        self.edge_ne = Invalid()
        self.edge_se = Invalid()
        self.cell_s = Invalid()
        self.cell_n = Invalid()
        self.point_w = Invalid()
        self.point_e = Invalid()

    def cells(self):
        return [x for x in [self.cell_s, self.cell_n]
                if not isinstance(x, Invalid)]

    def __str__(self):
        return "Horiz({})".format(self.var)

class NW_SE_Edge(object):
    def __init__(self, var, e, nw, sw):
        self.var = var
        self.e = e
        self.nw = nw
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

class NE_SW_Edge(object):
    def __init__(self, var, e, nw, sw):
        self.var = var
        self.e = e
        self.nw = nw
        self.sw = sw
        self.edge_nw = Invalid()
        self.edge_e = Invalid()
        self.edge_w = Invalid()
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

class EastwardPoint(object):
    def __init__(self, var, e, nw, sw):
        self.var = var
        self.e = e
        self.nw = nw
        self.sw = sw
        self.edge_e = Invalid()
        self.edge_nw = Invalid()
        self.edge_sw = Invalid()
        self.point_e = Invalid()
        self.point_nw = Invalid()
        self.point_sw = Invalid()
        self.cell_w = Invalid()
        self.cell_ne = Invalid()
        self.cell_se = Invalid()

    def edges(self):
        return [x for x in [self.edge_e,
                            self.edge_nw,
                            self.edge_sw]
                if not isinstance(x, Invalid)]

class WestwardPoint(object):
    def __init__(self, var, e, nw, sw):
        self.var = var
        self.e = e
        self.nw = nw
        self.sw = sw
        self.edge_w = Invalid()
        self.edge_ne = Invalid()
        self.edge_se = Invalid()
        self.point_w = Invalid()
        self.point_ne = Invalid()
        self.point_se = Invalid()
        self.cell_e = Invalid()
        self.cell_nw = Invalid()
        self.cell_sw = Invalid()

    def edges(self):
        return [x for x in [self.edge_w,
                            self.edge_ne,
                            self.edge_se]
                if not isinstance(x, Invalid)]

# This function figures out how tall column x should be, and the coordinates of the northernmost hex in that column
def calc_bounds(height, north_column, south_column, x):
    e = x
    if x < north_column:
        nw = 0
        sw = -x
    else:
        nw = north_column - x
        sw = -north_column

    column_height = height + x - min(north_column, south_column)
    if x > north_column:
        column_height = column_height - (x - north_column)
    if x > south_column:
        column_height = column_height - (x - south_column)

    return column_height, e, nw, sw

# This function returns the given coords regularized to be close to the e + nw + sw = 0 plane
def regularize_coords(e, nw, sw):
    sum = e + nw + sw
    adj = (sum + 1) // 3
    return e-adj, nw-adj, sw-adj

# This class describes an oblong (possibly degenerate) hexagon. width is the total number of columns in the grid.
# height is the height of the column containing the north corner, which is the same as the maximum height of a column.
# north_column is the (0-based) index of that column. south_column is the (0-based) index of the column containing
# the south corner. These values are not independent: so that the westernmost and easternmost columns have a positive
# length, we require that north_column < height and south_column + height >= width (for left-leaning boards), or vice
# versa (for right-leaning boards).
# The northwest corner is hex 0,0,0 in the coordinate system, because that's where we start generating cells.
class HexGrid(object):
    def __init__(self, width, height, north_column, south_column, basename='', cellgen=Int, pointgen=Int, edgegen=Int):
        self.width = width
        self.height = height
        self.north_column = north_column
        self.south_column = south_column

        cell_array = {}
        horiz_array = {}
        ne_sw_array = {}
        nw_se_array = {}
        eastward_point_array = {}
        westward_point_array = {}

        cells = []
        horizs = []
        ne_sws = []
        nw_ses = []
        eastward_points = []
        westward_points = []

        # make cells
        for x in range(width):
            column_height, e, nw, sw = calc_bounds(height, north_column, south_column, x)

            for y in range(column_height):
                # make cell
                cv = cellgen('{}cell_{},{},{}'.format(basename, e, nw, sw))
                c = Cell(cv, e, nw, sw)
                cells.append(c)
                cell_array[e, nw, sw] = c

                nw = nw - 1
                sw = sw + 1

        self.cell_array = cell_array
        self.cells = cells

        # make eastward points
        # one more for eastern edge of board
        for x in range(width+1):
            column_height, e, nw, sw = calc_bounds(height, north_column, south_column, x)
            # one more for the sw corner of the column
            column_height = column_height + 1
            # start to nw of first hex
            nw = nw + 1
            for y in range(column_height):
                # make point to nw
                nw_pv = pointgen('{}point_{},{},{}'.format(basename, e, nw, sw))
                nw_p = EastwardPoint(nw_pv, e, nw, sw)
                eastward_points.append(nw_p)
                eastward_point_array[e, nw, sw] = nw_p

                nw = nw - 1
                sw = sw + 1

        self.eastward_points = eastward_points
        self.eastward_point_array = eastward_point_array

        # make westward points
        # one more for eastern edge of board
        for x in range(width+1):
            column_height, e, nw, sw = calc_bounds(height, north_column, south_column, x)
            if x > north_column:
                # one more at the north end for the ne corner of the column
                column_height = column_height + 1
                nw = nw + 1
                sw = sw - 1
            if x > south_column:
                # one more at the south end for the se corner of the column
                column_height = column_height + 1
            # start to w of first hex
            e = e - 1
            for y in range(column_height):
                # make point to w
                w_pv = pointgen('{}point_{},{},{}'.format(basename, e, nw, sw))
                w_p = WestwardPoint(w_pv, e, nw, sw)
                westward_points.append(w_p)
                westward_point_array[e, nw, sw] = w_p
                nw = nw - 1
                sw = sw + 1

        self.westward_points = westward_points
        self.westward_point_array = westward_point_array

        # make horiz edges
        for x in range(width):
            column_height, e, nw, sw = calc_bounds(height, north_column, south_column, x)
            # one more for south edge of board
            column_height = column_height + 1
            # start to n of first hex
            nw = nw + 1
            for y in range(column_height):
                # make edge to n
                n_ev = edgegen('{}horiz_{},{},{}'.format(basename, e, nw, sw))
                n_e = HorizEdge(n_ev, e, nw, sw)
                horizs.append(n_e)
                horiz_array[e, nw, sw] = n_e
                nw = nw - 1
                sw = sw + 1

        self.horiz_array = horiz_array
        self.horizs = horizs

        # make ne_sw edges
        # one more for east edge of board
        for x in range(width + 1):
            column_height, e, nw, sw = calc_bounds(height, north_column, south_column, x)
            if x > south_column:
                # one more for se edge of board
                column_height = column_height + 1
            # start to nw of first hex
            nw = nw + 1
            for y in range(column_height):
                # make edge to nw
                nw_ev = edgegen('{}ne_sw_{},{},{}'.format(basename, e, nw, sw))
                nw_e = NE_SW_Edge(nw_ev, e, nw, sw)
                ne_sws.append(nw_e)
                ne_sw_array[e, nw, sw] = nw_e
                nw = nw - 1
                sw = sw + 1

        self.ne_sw_array = ne_sw_array
        self.ne_sws = ne_sws

        # make nw_se edges
        # one more for east edge of board
        for x in range(width + 1):
            column_height, e, nw, sw = calc_bounds(height, north_column, south_column, x)
            if x > north_column:
                # one more at north end for ne edge of board
                column_height = column_height + 1
                nw = nw + 1
                sw = sw - 1
            # start to sw of first hex
            sw = sw + 1
            for y in range(column_height + 1):
                #make edge to sw
                sw_ev = edgegen('{}nw_se_{},{},{}'.format(basename, e, nw, sw))
                sw_e = NW_SE_Edge(sw_ev, e, nw, sw)
                nw_ses.append(sw_e)
                nw_se_array[e, nw, sw] = sw_e
                nw = nw - 1
                sw = sw + 1

        self.nw_se_array = nw_se_array
        self.nw_ses = nw_ses

        # link things up
        for c in self.cells:
            e, nw, sw = c.e, c.nw, c.sw
            c.cell_n = self.cell(e, nw+1, sw-1)
            c.cell_s = self.cell(e, nw-1, sw+1)
            c.cell_nw = self.cell(e-1, nw+1, sw)
            c.cell_ne = self.cell(e+1, nw, sw-1)
            c.cell_sw = self.cell(e-1, nw, sw+1)
            c.cell_se = self.cell(e+1, nw-1, sw)

            c.edge_n = self.horiz(e, nw+1, sw)
            c.edge_n.cell_s = c
            c.edge_s = self.horiz(e, nw, sw+1)
            c.edge_s.cell_n = c
            c.edge_nw = self.ne_sw(e, nw+1, sw)
            c.edge_nw.cell_se = c
            c.edge_se = self.ne_sw(e+1, nw, sw)
            c.edge_se.cell_nw = c
            c.edge_ne = self.nw_se(e, nw+1, sw)
            c.edge_ne.cell_sw = c
            c.edge_sw = self.nw_se(e, nw, sw+1)
            c.edge_sw.cell_ne = c

            self.eastward_point(e+1, nw, sw).cell_w = c
            self.westward_point(e-1, nw, sw).cell_e = c
            self.eastward_point(e, nw+1, sw).cell_se = c
            self.westward_point(e, nw-1, sw).sell_nw = c
            self.eastward_point(e, nw, sw+1).cell_ne = c
            self.westward_point(e, nw, sw-1).cell_sw = c

        for p in eastward_points:
            e, nw, sw = p.e, p.nw, p.sw
            p.edge_e = self.horiz(e, nw, sw)
            p.edge_nw = self.nw_se(e, nw, sw)
            p.edge_sw = self.ne_sw(e, nw, sw)
            if not isinstance(p.edge_e, Invalid):
                p.edge_e.point_w = p
                p.edge_e.edge_nw = p.edge_nw
                p.edge_e.edge_sw = p.edge_sw
            if not isinstance(p.edge_nw, Invalid):
                p.edge_nw.point_se = p
                p.edge_nw.edge_e = p.edge_e
                p.edge_nw.edge_sw = p.edge_sw
            if not isinstance(p.edge_sw, Invalid):
                p.edge_sw.point_ne = p
                p.edge_sw.edge_e = p.edge_e
                p.edge_sw.edge_nw = p.edge_nw

        for p in westward_points:
            e, nw, sw = p.e, p.nw, p.sw
            p.edge_w = self.horiz(e, nw+1, sw+1)
            p.edge_ne = self.ne_sw(e+1, nw+1, sw)
            p.edge_se = self.nw_se(e+1, nw, sw+1)
            if not isinstance(p.edge_w, Invalid):
                p.edge_w.point_e = p
                p.edge_w.edge_ne = p.edge_ne
                p.edge_w.edge_se = p.edge_se
            if not isinstance(p.edge_ne, Invalid):
                p.edge_ne.point_sw = p
                p.edge_ne.edge_w = p.edge_w
                p.edge_ne.edge_se = p.edge_se
            if not isinstance(p.edge_se, Invalid):
                p.edge_se.point_nw = p
                p.edge_se.edge_w = p.edge_w
                p.edge_se.edge_ne = p.edge_ne

    def cell(self, e, nw, sw):
        return self.cell_array.get(regularize_coords(e, nw, sw), Invalid())

    def horiz(self, e, nw, sw):
        return self.horiz_array.get(regularize_coords(e, nw, sw), Invalid())

    def nw_se(self, e, nw, sw):
        return self.nw_se_array.get(regularize_coords(e, nw, sw), Invalid())

    def ne_sw(self, e, nw, sw):
        return self.ne_sw_array.get(regularize_coords(e, nw, sw), Invalid())

    def westward_point(self, e, nw, sw):
        return self.westward_point_array.get(regularize_coords(e, nw, sw), Invalid())

    def eastward_point(self, e, nw, sw):
        return self.eastward_point_array.get(regularize_coords(e, nw, sw), Invalid())

    @property
    def edges(self):
        return self.horizs + self.ne_sws + self.nw_ses

    @property
    def points(self):
        return self.eastward_points + self.westward_points

