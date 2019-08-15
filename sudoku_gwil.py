import z3
import grid
import display
import adjacency_manager

s = z3.Solver()

givens = [
  [7, 0, 3,  0, 0, 0,  0, 0, 6],
  [0, 1, 0,  0, 0, 9,  0, 0, 0],
  [0, 9, 6,  1, 0, 0,  0, 3, 0],

  [5, 0, 0,  0, 0, 7,  9, 0, 4],
  [0, 0, 0,  8, 1, 0,  2, 0, 0],
  [0, 0, 0,  5, 0, 0,  0, 0, 0],

  [0, 0, 2,  4, 0, 0,  0, 0, 8],
  [0, 0, 0,  0, 0, 0,  0, 0, 0],
  [3, 0, 4,  0, 0, 0,  0, 6, 0]]

g = grid.Grid(9, 9)

# TK: init_edges, init_points
# creates cell.given, cell.var
g.init_cells(givens, lambda cell: z3.Int(cell.name))

for cell in g.cells:
    # would be nice if we could say: cell.var.constrain_range(1, 9) (inclusive?)
    # or even specify the range for all cells at once, usually it's the same, instead of z3.Int maybe ourthing.numrange_inclusive(1, 9)
    s.add(cell.var >= 1)
    s.add(cell.var <= 9)
    if cell.given != 0:
        # could automate this if givens are cell vars? but how to indicate?
        s.add(cell.var == cell.given)

for row in g.cell_rows():
    s.add(z3.Distinct([cell.var for cell in row]))

for col in g.cell_cols():
    s.add(z3.Distinct([cell.var for cell in col]))

for box in g.cell_boxes(3, 3):
    s.add(z3.Distinct([cell.var for cell in box]))

s.check()
m = s.model()

print m

# check for uniqueness
# do graphicsy stuff