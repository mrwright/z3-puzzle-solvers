import z3
from grid import Grid, RectDisplay


def get_cells(puzzle, r, c, dr, dc):
    r += dr
    c += dc
    cells = []
    while r < len(puzzle) and c < len(puzzle[r]) and puzzle[r][c] is None:
        cells.append((r, c))
        r += dr
        c += dc
    return cells

def build_clue(clue, cells, s, grid):
    s.add(z3.Distinct(*[grid.cell(c, r).var for r, c in cells]))
    if clue != '?':
        clue = int(clue)
        s.add(z3.Sum(*[grid.cell(c, r).var for r, c in cells]) == clue)

def build_clues(puzzle, r, c, s, grid):
    vert, horiz = puzzle[r][c]
    if vert:
        cells = get_cells(puzzle, r, c, 1, 0)
        build_clue(vert, cells, s, grid)
    if horiz:
        cells = get_cells(puzzle, r, c, 0, 1)
        build_clue(horiz, cells, s, grid)

def solve_kakuro(puzzle, base=10):
    grid = Grid(len(puzzle[0]), len(puzzle), cellgen=z3.Int)

    s = z3.Solver()

    for r, row in enumerate(puzzle):
        for c, cell in enumerate(row):
            if cell is None:
                s.add(1 <= grid.cell(c, r).var)
                s.add(grid.cell(c, r).var < base)
            else:
                build_clues(puzzle, r, c, s, grid)

    print(s)
    print(s.check())
    m = s.model()

    def cell_draw(ctx):
        ctx.fill(0.9, 0.9, 1, 1)
        ctx.draw_text(ctx.val, fontsize=24)

    def horiz_edge_draw(ctx):
        ctx.draw(width=1)

    def vert_edge_draw(ctx):
        ctx.draw(width=1)

    display = RectDisplay(cell_fn=cell_draw, edge_fn=vert_edge_draw)
    display.set_horiz_edge_fn(horiz_edge_draw)
    display.display_grid(grid, m, 64)


if __name__ == '__main__':

    puzzle = [
        [(0,0),  (0,0),   (45,0), (16,0), (28,0), (0,0),    (8,0),  ('?',0), (45,0), (0,0)],
        [(0,0),  (11,18), None,   None,   None,   (24,7),   None,   None,    None,   (21,0)],
        [(0,45), None,    None,   None,   None,   None,     None,   None,    None,   None],
        [(0,17), None,    None,   (9,9),  None,   None,     (26,9), None,    None,   None],
        [(0,22), None,    None,   None,   None,   None,     None,   (7,9),   None,   None],
        [(0,0),  (9,22),  None,   None,   None,   (10,'?'), None,   None,    None,   (22,0)],
        [(0,7),  None,    None,   (9,25), None,   None,     None,   None,    None,   None],
        [(0,14), None,    None,   None,   (8,12), None,     None,   (6,10),    None,   None],
        [(0,45), None,    None,   None,   None,   None,     None,   None,    None,   None],
        [(0,0),  (0,20),  None,   None,   None,   (0,9),    None,   None,    None,   (0,0)],
    ]

    # solve_kakuro(puzzle, 10)

    def base_12(num):
        if num == '?': return '?'
        return int(str(num), 12)

    def base_12_cell(cell):
        if cell is None: return None
        vert, horiz = cell
        return base_12(vert), base_12(horiz)

    base_12_puzzle = [
        [
            base_12_cell(cell) for cell in row
        ] for row in puzzle
    ]

    solve_kakuro(base_12_puzzle, 12)
