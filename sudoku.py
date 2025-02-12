from z3 import *

from grid import Grid, RectDisplay

g = Grid(9, 9)

s = Solver()

for i in range(9):
    s.add(Distinct([g.cell(i, j).var for j in range(9)]))
    s.add(Distinct([g.cell(j, i).var for j in range(9)]))

for i in range(3):
    for j in range(3):
        s.add(Distinct([g.cell(3*i+di, 3*j+dj).var
                        for di in range(3) for dj in range(3)]))

for cell in g.cells:
    s.add(cell.var >= 1)
    s.add(cell.var <= 9)

l = [[5,3,0, 0,0,0, 0,0,0],
     [0,0,0, 0,0,5, 0,0,0],
     [0,9,8, 0,0,0, 0,6,0],

     [8,0,0, 0,6,0, 0,0,3],
     [4,0,0, 8,0,0, 0,0,1],
     [0,0,0, 0,2,0, 0,0,6],

     [0,6,0, 0,0,0, 2,8,0],
     [0,0,0, 4,1,9, 0,0,0],
     [0,0,0, 0,0,0, 0,7,0],
    ]

for y in range(9):
    for x in range(9):
        if l[y][x] != 0:
            s.add(g.cell(x, y).var == l[y][x])

s.check()
m = s.model()

def cell_draw(ctx):
    ctx.fill(0.9, 0.9, 1, 1)
    bold = l[ctx.cell.y][ctx.cell.x] != 0
    ctx.draw_text(ctx.val, fontsize=24, bold=bold)

def horiz_edge_draw(ctx):
    ctx.draw(width=5 if (ctx.edge.y % 3 == 0) else 1)

def vert_edge_draw(ctx):
    ctx.draw(width=5 if (ctx.edge.x % 3 == 0) else 1)

display = RectDisplay(cell_fn=cell_draw, edge_fn=vert_edge_draw)
display.set_horiz_edge_fn(horiz_edge_draw)
display.display_grid(g, m, 64)
