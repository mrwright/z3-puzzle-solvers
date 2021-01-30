from z3 import *

from grid import Grid, RectDisplay
from adjacency_manager import solve

s = Solver()
#g = Grid(6, 6)
g = Grid(11, 11)

for e in g.edges:
    s.add(e.var >= 0)
    s.add(e.var <= 1)

for p in g.points:
    count = Sum([e.var for e in p.edges()])
    s.add(Or([count == 0, count == 2]))

# givens = [
#     "1  0 3",
#     " 03222",
#     "0    1",
#     "3    3",
#     "32202 ",
#     "3 3  3",
# ]

givens = [
    "33 3 3 3 33",
    "32   2   13",
    "  33   32  ",
    "2 03   13 1",
    "    123    ",
    "31  123  23",
    "    123    ",
    "1 20   03 3",
    "  32   23  ",
    "31   3   13",
    "33 2 3 0 33",
]

given_constraints = []
for y in range(g.height):
    row = []
    for x in range(g.width):
        if givens[y][x] != ' ':
            row.append(Sum([
                e.var for e in g.cell(x, y).edges()
            ]) == ord(givens[y][x]) - ord('0'))
        else:
            row.append(None)
    given_constraints.append(row)

for x in range(g.width):
    items = [given_constraints[y][x] for y in range(g.height)]
    items = [i for i in items if i is not None]
    s.add(
        Or([
            And(items[:i] + [Not(items[i])] + items[i+1:])
            for i in range(len(items))
        ])
    )

for y in range(g.height):
    items = [given_constraints[y][x] for x in range(g.width)]
    items = [i for i in items if i is not None]
    s.add(
        Or([
            And(items[:i] + [Not(items[i])] + items[i+1:])
            for i in range(len(items))
        ])
    )

def adjacency_fn(grid, model):
    for point in grid.points:
        yield [edge.var for edge in point.edges()
               if model[edge.var].as_long() == 1]

m = solve(s, g, adjacency_fn)

def cell_draw(ctx):
    given = givens[ctx.cell.y][ctx.cell.x]
    count = sum([m[edge.var].as_long() for edge in ctx.cell.edges()])
    if given == ' ' or ord(given) - ord('0') == count:
        ctx.fill(1., 1., 1., 1.)
    else:
        ctx.fill(1, 0.5, 0.5, 1)
    ctx.draw_text(str(given), fontsize=24)

def edge_draw(ctx):
    if ctx.val == '1':
        ctx.draw(width=4)

def point_draw(ctx):
    ctx.draw_square(size=1/8)

display = RectDisplay(cell_fn=cell_draw, edge_fn=edge_draw, point_fn=point_draw)
display.display_grid(g, m, 64)
