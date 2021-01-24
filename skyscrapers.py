from z3 import *

from grid import Grid
from display import draw_grid

# left_givens = [4, 4, 0, 0, 0]
# top_givens = [0, 0, 2, 1, 0]
# bottom_givens = [2, 0, 1, 0, 0]
# right_givens = [0, 0, 5, 0, 0]

left_givens = [2, 2, 1, 4, 3]
right_givens = [3, 3, 2, 1, 2]
top_givens = [2, 2, 1, 3, 4]
bottom_givens = [3, 2, 3, 1, 2]


w = len(left_givens)
s = Solver()
g = Grid(w, w)
left = Grid(w, w, 'left')
right = Grid(w, w, 'right')
top = Grid(w, w, 'top')
bottom = Grid(w, w, 'bottom')

for i in range(w):
    s.add(Distinct([g.cell(i, j).var for j in range(w)]))
    s.add(Distinct([g.cell(j, i).var for j in range(w)]))

for c in g.cells:
    s.add(c.var >= 1)
    s.add(c.var <= w)

for grid in [left, right, top, bottom]:
    for c in grid.cells:
        s.add(c.var >= 0)
        s.add(c.var <= 1)

def constrain(building_vars, aux_vars):
    for i, (bv, av) in enumerate(zip(building_vars, aux_vars)):
        s.add((av == 1) == And([
            building_vars[j] < bv
            for j in range(i)
        ]))

for i in range(w):
    constrain([g.cell(j, i).var for j in range(w)],
              [left.cell(j, i).var for j in range(w)])
    constrain([g.cell(i, j).var for j in range(w)],
              [top.cell(i, j).var for j in range(w)])
    constrain([g.cell(w - 1 - j, i).var for j in range(w)],
              [right.cell(w - 1 - j, i).var for j in range(w)])
    constrain([g.cell(i, w - 1 - j).var for j in range(w)],
              [bottom.cell(i, w - 1 - j).var for j in range(w)])

for i in range(w):
    if left_givens[i] != 0:
        s.add(Sum([left.cell(j, i).var for j in range(w)]) == left_givens[i])
    if right_givens[i] != 0:
        s.add(Sum([right.cell(j, i).var for j in range(w)]) == right_givens[i])
    if top_givens[i] != 0:
        s.add(Sum([top.cell(i, j).var for j in range(w)]) == top_givens[i])
    if bottom_givens[i] != 0:
        s.add(Sum([bottom.cell(i, j).var for j in range(w)]) == bottom_givens[i])

s.check()
m = s.model()

def cell_draw(ctx):
    ctx.text(ctx.val, fontsize=24)

def edge_draw(ctx):
    ctx.draw(width=1)

draw_grid(g, m, 64, cell_draw, edge_draw, edge_draw)
