from z3 import *

from grid import Grid, RectDisplay
from adjacency_manager import solve
from invalidobj import IAnd, IOr

s = Solver()
g = Grid(9, 9)

for e in g.edges:
    s.add(e.var >= 0)
    s.add(e.var <= 1)

for p in g.points:
    count = Sum([e.var for e in p.edges()])
    s.add(Or([count == 0, count == 2]))

givens = [
    "  o o     ",
    "    o   . ",
    "  . . o   ",
    "   o  o   ",
    ".    o   o",
    "  o    o  ",
    "  .   o   ",
    "o   .    o",
    "      oo  ",
    "  .      .",
]

for x in range(g.width+1):
    for y in range(g.height+1):
        pt = g.point(x, y)
        if givens[y][x] == 'o':
            hor = [pt.edge_left.var == 1, pt.edge_right.var == 1]
            ver = [pt.edge_above.var == 1, pt.edge_below.var == 1]
            s.add(IOr([
                IAnd(hor + [extra_edge.var == 1])
                for near_point in [pt.point_left, pt.point_right]
                for extra_edge in [near_point.edge_above, near_point.edge_below]
            ] + [
                IAnd(ver + [extra_edge.var == 1])
                for near_point in [pt.point_above, pt.point_below]
                for extra_edge in [near_point.edge_left, near_point.edge_right]
            ]))

        elif givens[y][x] == '.':
            s.add(IOr([
                IAnd([pt.horiz_edge(dx).var == 1, pt.horiz_edge(dx*2).var == 1,
                     pt.vert_edge(dy).var == 1, pt.vert_edge(dy*2).var == 1])
                for dx, dy in [
                        ( 1, 1),
                        ( 1,-1),
                        (-1, 1),
                        (-1,-1),
                ]
            ]))


def adjacency_fn(grid, model):
    for point in grid.points:
        yield [edge.var for edge in point.edges()
               if model[edge.var].as_long() == 1]

m = solve(s, g, adjacency_fn)

def cell_draw(ctx):
    ctx.fill(1, 0.5, 0.5, 1)

def edge_draw(ctx):
    if ctx.val == '1':
        ctx.draw(width=4)

def point_draw(ctx):
    #ctx.draw_square(size=7)
    if givens[ctx.point.y][ctx.point.x] == 'o':
        ctx.draw_circle(fill=False)
    elif givens[ctx.point.y][ctx.point.x] == '.':
        ctx.draw_circle(fill=True)

display = RectDisplay(cell_fn=cell_draw, edge_fn=edge_draw, point_fn=point_draw)
display.display_grid(g, m, 64)

