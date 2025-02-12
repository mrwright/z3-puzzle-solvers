from collections import defaultdict

from grid import Grid, RectDisplay
import z3

givens = [
    "aaabbbbccd",
    "aaabccbccd",
    "aaabcccccd",
    "aaaacceedd",
    "ffeeeeeedd",
    "ffffeggggd",
    "ffhffggggd",
    "iihhgggggd",
    "ijjhhhhggd",
    "ijjjjhgggg",
]

board = Grid(len(givens[0]), len(givens), "grid", cellgen=z3.Int)
s = z3.Solver()

for cell in board.cells:
    s.add(cell.var >= 0)
    s.add(cell.var <= 1)

# build regions
regions = defaultdict(list)
for y, row in enumerate(givens):
    for x, cell in enumerate(row):
        regions[cell].append(board.cell(x, y).var)

for region in regions.values():
    s.add(z3.Sum(region) == 2)

for y in range(board.height):
    s.add(z3.Sum([board.cell(x, y).var for x in range(board.width)]) == 2)

for x in range(board.width):
    s.add(z3.Sum([board.cell(x, y).var for y in range(board.height)]) == 2)

for e in board.edges:
    s.add(z3.Sum([cell.var for cell in e.cells()]) < 2)

for p in board.points:
    if p.is_outside: continue
    s.add(z3.Sum(p.edge_left.cell_above.var, p.edge_right.cell_below.var) < 2)
    s.add(z3.Sum(p.edge_left.cell_below.var, p.edge_right.cell_above.var) < 2)

print(s.check())
m = s.model()

def draw_edge(ctx):
    ctx.draw(width=5 if (ctx.edge.is_outside or len({givens[cell.y][cell.x] for cell in ctx.edge.cells()}) == 2) else 1)

def draw_cell(ctx):
    if ctx.val == "1":
        ctx.draw_circle(fill=True)

display = RectDisplay(cell_fn=draw_cell, edge_fn=draw_edge)
display.display_grid(board, m, 64)
