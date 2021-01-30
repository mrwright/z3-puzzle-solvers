import z3

import display
from grid import Grid, RectDisplay

# I can't really think of a good way to specify the givens in one of these but this will have to do
givens = [
    "+-+-+-+-+-+-+-+",
    "| | | | | | | |",
    "+*+-+-+-*-+-*-+",
    "| | | | | | | |",
    "+-+-+*+-+-+-+-+",
    "| | | | * | | |",
    "+-*-+-+-+-+-*-+",
    "| | | | | | | |",
    "+-+-+-+-*-+-+-+",
    "| | | | | | * |",
    "+-+-+-+-+-+-+-+",
    "| | * | | | * |",
    "+-+-+-+-*-+-+-+",
    "|*| | | | | * |",
    "+-+-+-+-+-+-+-+",
]
# givens = [
#     "+-+-+-+-+",
#     "|*| | | |",
#     "+-+-*-+-+",
#     "| | | |*|",
#     "+-+-+-+-+",
# ]


height = (len(givens)-1) // 2
width = (len(givens[0])-1) // 2

# some helpers
def cell_given(cell):
    return givens[2*cell.y+1][2*cell.x+1] == "*"

def horiz_given(horiz):
    return givens[2*horiz.y][2*horiz.x+1] == "*"

def vert_given(vert):
    return givens[2*vert.y+1][2*vert.x] == "*"

def point_given(point):
    return givens[2*point.y][2*point.x] == "*"

def cell_near_given(cell):
    return any([
        cell_given(cell),
        horiz_given(cell.edge_above),
        horiz_given(cell.edge_below),
        vert_given(cell.edge_left),
        vert_given(cell.edge_right),
        point_given(cell.edge_left.point_above),
        point_given(cell.edge_left.point_below),
        point_given(cell.edge_right.point_above),
        point_given(cell.edge_right.point_below),
    ])

RelPosSort, RelPosVal, (DX, DY, DIST) = z3.TupleSort('RelPos', [z3.IntSort(), z3.IntSort(), z3.IntSort()])
def RelPos(name):
    return z3.Const(name, RelPosSort)

s = z3.Solver()
board = Grid(width, height, cellgen=RelPos, edgegen=z3.Bool)
# can't do cells with individual vars because i need to calculate coordinates based on z3 vars to enforce symmetry
cell_galaxy_fn = z3.Function("cell_galaxies", z3.IntSort(), z3.IntSort(), z3.IntSort())

def cell_galaxy(cell):
    return cell_galaxy_fn(*cell.coords)

# enforce borders split galaxies and non-borders don't
for e in board.edges:
    if e.is_outside:
        s.add(e.var)
    else:
        edge_cells = e.cells()
        s.add(e.var == (cell_galaxy(edge_cells[0]) != cell_galaxy(edge_cells[1])))

# enforce non-borders propagate relative positions
for e in board.verts:
    if e.is_outside: continue
    left, right = e.cell_left.var, e.cell_right.var
    relpos_rule = z3.And(DY(left) == DY(right), DX(left) + 2 == DX(right))
    s.add(z3.Or(e.var, relpos_rule))
for e in board.horizs:
    if e.is_outside: continue
    above, below = e.cell_above.var, e.cell_below.var
    relpos_rule = z3.And(DX(above) == DX(below), DY(above) + 2 == DY(below))
    s.add(z3.Or(e.var, relpos_rule))

# enforce galaxies are symmetric and connected
for c in board.cells:
    s.add(c.x - DX(c.var) >= 0)
    s.add(c.x - DX(c.var) < width)
    s.add(c.y - DY(c.var) >= 0)
    s.add(c.y - DY(c.var) < height)
    # this line is why we couldn't just use vars in each cell for cell_galaxy_fn
    s.add(cell_galaxy(c) == cell_galaxy_fn(c.x - DX(c.var), c.y - DY(c.var)))
    if not cell_near_given(c):
        # this cell has to have a positive distance to its star
        s.add(DIST(c.var) > 0)
        # and some neighboring cell has to be part of the same galaxy and have exactly 1 shorter distance
        s.add(z3.Or([z3.And(cell_galaxy(c2) == cell_galaxy(c), DIST(c2.var) == DIST(c.var) - 1) for c2 in c.neighbors()]))

# enforce star at center of each galaxy
starnum = 0
for c in board.cells:
    if cell_given(c):
        # cell-centered galaxy
        s.add(c.var == RelPosVal(0, 0, 0))
        s.add(cell_galaxy(c) == starnum)
        starnum += 1
    elif vert_given(c.edge_right):
        # vert-centered galaxy
        s.add(c.var == RelPosVal(-1, 0, 0))
        s.add(c.cell_right.var == RelPosVal(1, 0, 0))
        s.add(cell_galaxy(c) == starnum)
        s.add(cell_galaxy(c.cell_right) == starnum)
        s.add(z3.Not(c.edge_right.var))
        starnum += 1
    elif horiz_given(c.edge_below):
        # horiz-centered galaxy
        s.add(c.var == RelPosVal(0, -1, 0))
        s.add(c.cell_below.var == RelPosVal(0, 1, 0))
        s.add(cell_galaxy(c) == starnum)
        s.add(cell_galaxy(c.cell_below) == starnum)
        s.add(z3.Not(c.edge_below.var))
        starnum += 1
    elif point_given(c.edge_right.point_below):
        # point-centered galaxy
        s.add(c.var == RelPosVal(-1, -1, 0))
        s.add(c.cell_right.var == RelPosVal(1, -1, 0))
        s.add(c.cell_below.var == RelPosVal(-1, 1, 0))
        s.add(c.cell_right.cell_below.var == RelPosVal(1, 1, 0))
        s.add(cell_galaxy(c) == starnum)
        s.add(cell_galaxy(c.cell_below) == starnum)
        s.add(cell_galaxy(c.cell_right) == starnum)
        s.add(cell_galaxy(c.cell_right.cell_below) == starnum)
        s.add(z3.Not(c.edge_right.var))
        s.add(z3.Not(c.edge_below.var))
        s.add(z3.Not(c.cell_right.edge_below.var))
        s.add(z3.Not(c.cell_below.edge_right.var))
        starnum += 1

# enforce no stray galaxy numbers
for c in board.cells:
    s.add(cell_galaxy(c) >= 0)
    s.add(cell_galaxy(c) < starnum)

print(s.check())

def draw_edge(ctx, is_given):
    ctx.draw(width=5 if ctx.val == "True" else 1)
    if is_given:
        display.draw_circle(ctx.ctx, 0.5, 0, radius=0.15, fill=True, color=(0,1,0,1))

def draw_vert(ctx):
    draw_edge(ctx, vert_given(ctx.edge))

def draw_horiz(ctx):
    draw_edge(ctx, horiz_given(ctx.edge))

def draw_point(ctx):
    if point_given(ctx.point):
        ctx.draw_circle(radius=0.15, fill=True, color=(0, 1, 0, 1))

def draw_cell(ctx):
    if cell_given(ctx.cell):
        ctx.draw_circle(radius=0.3, fill=True, color=(0, 1, 0, 1))
    # galaxy = ctx.model.eval(cell_galaxy(ctx.cell))
    # dx = ctx.model.eval(DX(ctx.cell.var))
    # dy = ctx.model.eval(DY(ctx.cell.var))
    # dist = ctx.model.eval(DIST(ctx.cell.var))
    # ctx.text(f"{galaxy},{dx},{dy},{dist}", fontsize=18)

rect_display = RectDisplay(cell_fn=draw_cell, point_fn=draw_point, edge_fn=draw_vert)
rect_display.set_horiz_edge_fn(draw_horiz)
rect_display.display_grid(board, s.model(), 64)
