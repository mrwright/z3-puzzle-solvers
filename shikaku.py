from z3 import *

from grid import Grid, RectDisplay
from invalidobj import Invalid

s = Solver()
#g = Grid(5, 5)
g = Grid(20, 20)

def factors(n):
    for i in range(1, n+1):
        if i * (n//i) == n:
            yield (i, n//i)

def possibilities(px, py, n):
    gw = g.width
    gh = g.height

    for w, h in factors(n):
        for dx in range(w):
            for dy in range(h):
                left = px - dx
                right = px - dx + w
                top = py - dy
                bottom = py - dy + h
                if left < 0 or top < 0 or right > gw or bottom > gh:
                    continue
                yield (left, top, right, bottom)

# givens = [
#     "   3 ",
#     "2 3 5",
#     " 2   ",
#     " 24  ",
#     " 2 2 ",
# ]

givens = [
    "2      2 2 2 5   2  ",
    "                  4 ",
    " T         `        ",
    "                   6",
    "                    ",
    "     :       =      ",
    "      2  F         2",
    "      2             ",
    "          @      8  ",
    "  4                 ",
    " 2             2 2  ",
    "           9     4  ",
    "  3            3 2 B",
    "    X      222      ",
    "=               6   ",
    "27                  ",
    "                 3  ",
    "  6h              3 ",
    "                 3  ",
    "3    9    3    4  3 ",
]

count = 0
for y in range(g.height):
    for x in range(g.width):
        c = givens[y][x]
        if c == ' ':
            continue
        n = ord(c) - ord('0')

        # Note: we don't need negative constraints, since the regions
        # will always cover the entire grid. (If that weren't the case,
        # we'd need to add constraints saying that cells that aren't
        # part of this region have a value other than "count".)
        s.add(Or([
            And([
                g.cell(cx, cy).var == count
                for cx in range(l, r)
                for cy in range(t, b)
            ])
            for l, t, r, b in possibilities(x, y, n)
        ]))

        count += 1

s.check()
m = s.model()


def cell_draw(ctx):
    ctx.fill(1, 0.5, 0.5, 1)
    given = givens[ctx.cell.y][ctx.cell.x]
    if given != ' ':
        ctx.draw_text(str(ord(given) - ord('0')), fontsize=24)

def edge_draw(ctx):
    regions = set(ctx.model[cell.var].as_long() for cell in ctx.edge.cells())
    ctx.draw(width=5 if ctx.edge.is_outside or len(regions) > 1 else 1)

display = RectDisplay(cell_fn=cell_draw, edge_fn=edge_draw)
display.display_grid(g, m, 64)
