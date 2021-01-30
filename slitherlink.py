from z3 import *

from grid import Grid, RectDisplay
from adjacency_manager import solve

s = Solver()
g = Grid(10, 10)
#g = Grid(6, 6)

for e in g.edges:
    s.add(e.var >= 0)
    s.add(e.var <= 1)

for p in g.points:
    count = Sum([e.var for e in p.edges()])
    s.add(Or([count == 0, count == 2]))

givens = [
    "   12 33  ",
    " 311302  2",
    " 3 1   22 ",
    " 2 22 2   ",
    "   2232  2",
    " 2  1 1 2 ",
    "    1     ",
    "2  21  31 ",
    " 3220313  ",
    " 22     1 ",
]

# givens = [
#     "    0 ",
#     "33  1 ",
#     "  12  ",
#     "  20  ",
#     " 1  11",
#     " 2    ",
# ]

for x in range(g.width):
    for y in range(g.height):
        if givens[y][x] != ' ':
            s.add(Sum([
                e.var for e in g.cell(x, y).edges()
            ]) == ord(givens[y][x]) - ord('0'))

def adjacency_fn(grid, model):
    for point in grid.points:
        yield [edge.var for edge in point.edges()
               if model[edge.var].as_long() == 1]

m = solve(s, g, adjacency_fn)

def cell_draw(ctx):
    ctx.fill(0.9, 0.9, 1, 1)
    given = givens[ctx.cell.y][ctx.cell.x]
    ctx.draw_text(str(given), fontsize=24)

def edge_draw(ctx):
    if ctx.val == '1':
        ctx.draw(width=2)

def point_draw(ctx):
    ctx.draw_square(size=1/8)

display = RectDisplay(cell_fn=cell_draw, edge_fn=edge_draw, point_fn=point_draw)
display.display_grid(g, m, 64)
