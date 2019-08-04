from z3 import *

# Note: doesn't yet work. We need something to find and ban "islands".

from grid import Grid
from display import draw_grid
from adjacency_manager import solve_grid
from invalidobj import EAnd, IOr, Invalid

s = Solver()

g = Grid(10, 10)

for c in g.cells:
    s.add(c.var >= 0)
    s.add(c.var <= 1)

def opts(pos, ln, tot):
    for i in range(ln):
        l = pos - i
        r = l + ln
        if l >= 0 and r <= tot:
            yield (l, r)

def horiz_opts(x, w):
    for r in opts(x, w, g.width):
        yield r

def vert_opts(y, h):
    for r in opts(y, h, g.height):
        yield r

def constrain_horiz(l, r, y):
    constraints = [
        g.cell(i, y).var == 1
        for i in range(l, r)
    ]
    if l - 1 >= 0:
        constraints.append(g.cell(l-1, y).var == 0)
    if r < g.width:
        constraints.append(g.cell(r, y).var == 0)
    return And(constraints)

def constrain_vert(t, b, x):
    constraints = [
        g.cell(x, i).var == 1
        for i in range(t, b)
    ]
    if t - 1 >= 0:
        constraints.append(g.cell(x, t-1).var == 0)
    if b < g.height:
        constraints.append(g.cell(x, b).var == 0)
    return And(constraints)

givens = [
    "6   6    4",
    "     6    ",
    "  3    5  ",
    "   7  9   ",
    " 5  3    5",
    "5    5  2 ",
    "   2  4   ",
    "  7    4  ",
    "    2     ",
    "5    6   6",
]

for j in range(g.height):
    for i in range(g.width):
        given = givens[j][i]
        if given == ' ':
            continue
        n = ord(given) - ord('0')

        s.add(Or([
            And([
                Or([constrain_horiz(l, r, j)
                    for l, r in horiz_opts(i, x_amt)
                ]),
                Or([constrain_vert(t, b, i)
                    for t, b in vert_opts(j, n - x_amt + 1)
                ]),
            ])

            for x_amt in range(1, n+1)
        ]))

#s.check()
#m = s.model()
m = solve_grid(s, g)

def cell_draw(ctx):
    if ctx.val == '0':
        ctx.fill(0.5, 0.5, 0.5, 1)
    else:
        ctx.fill(1, 1, 1, 1)
    ctx.text(givens[ctx.gy][ctx.gx], fontsize=24)

def edge_draw(ctx):
    ctx.draw(width=1)

draw_grid(g, m, 64, cell_draw, edge_draw, edge_draw)
