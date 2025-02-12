from z3 import *

from grid import Grid, RectDisplay

s = Solver()
#g = Grid(6, 6)
g = Grid(20, 20)

# givens = [
#     "    1 ",
#     "1 0 1 ",
#     "1     ",
#     "   1  ",
#     "  0   ",
#     " 1  00",
# ]

givens = [
    "      00     0 1 00 ",
    " 11                1",
    "    1  1     0 0    ",
    "  0   1    0 0 0 00 ",
    "11       0 00       ",
    "          1     0  1",
    "     0       1      ",
    "  00  1 11     1 11 ",
    "      1        1    ",
    " 00      11 1 0    1",
    "      1 1   1  1 1 1",
    "1       1           ",
    "         0     1  0 ",
    "   1 0 1           1",
    "1 01            0   ",
    "  0     00 1 0  0 0 ",
    "1  1       1 0      ",
    "0    0 1      1   1 ",
    " 1  0 0  0          ",
    "   1       1 1   1  ",
]

for c in g.cells:
    s.add(c.var >= 0)
    s.add(c.var <= 1)

for x in range(g.width-2):
    for y in range(g.height):
        c = g.cell(x, y)
        sm = Sum([c.var, c.cell_right.var, c.cell_right.cell_right.var])
        s.add(sm != 0)
        s.add(sm != 3)

for x in range(g.width):
    for y in range(g.height-2):
        c = g.cell(x, y)
        sm = Sum([c.var, c.cell_below.var, c.cell_below.cell_below.var])
        s.add(sm != 0)
        s.add(sm != 3)

for x0 in range(g.width):
    for x1 in range(x0+1, g.width):
        s.add(Or([
            g.cell(x0, y).var != g.cell(x1, y).var
            for y in range(g.height)
        ]))

for y0 in range(g.height):
    for y1 in range(y0+1, g.height):
        s.add(Or([
            g.cell(x, y0).var != g.cell(x, y1).var
            for x in range(g.width)
        ]))

for x in range(g.width):
    for y in range(g.height):
        a = givens[y][x]
        if a == '0':
            s.add(g.cell(x, y).var == 0)
        elif a == '1':
            s.add(g.cell(x, y).var == 1)

for x in range(g.width):
    s.add(Sum([g.cell(x, y).var for y in range(g.height)]) == (g.height/2))

for y in range(g.height):
    s.add(Sum([g.cell(x, y).var for x in range(g.width)]) == (g.width/2))

s.check()
m = s.model()


def cell_draw(ctx):
    if givens[ctx.cell.y][ctx.cell.x] != ' ':
        ctx.fill(1, 0.7, 0.7, 1)
    else:
        ctx.fill(1, 1, 1, 1)

    ctx.draw_circle(fill=(ctx.val == '0'))

display = RectDisplay(cell_fn=cell_draw)
display.display_grid(g, m, 30)
