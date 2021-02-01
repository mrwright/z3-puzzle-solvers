from z3 import *

from grid import Grid, RectDisplay
from invalidobj import Invalid


def get_surrounding_cells(cell):
    """
    Returns a fixed-length list of surrounding cells. Some cells may be
    invalid, but they still occupy a space in the list anyway.
    """
    return [
        cell.cell_right,
        cell.cell_right.cell_above,
        cell.cell_above,
        cell.cell_above.cell_left,
        cell.cell_left,
        cell.cell_left.cell_below,
        cell.cell_below,
        cell.cell_below.cell_right,
    ]


def do_groups_match_clues(groups, clues):
    """
    Given collections of bit group sizes and clue characters respectively,
    determines whether the groups match the clues.
    """
    if len(groups) != len(clues):
        return False

    clues = list(clues)
    for group in groups:
        group = str(group)
        if group in clues:
            clues.remove(group)
        elif '?' in clues:
            clues.remove('?')
        else:
            return False

    return True


def iterate_bitmasks_for_clues(clues, num_bits):
    """
    Returns an iterator yielding the subset of integers in [0, 2^num_bits)
    which, when interpreted as a bitmask, would be valid as the fill state of
    cells surrounding a cell with the given clues.
    """
    bound = 1 << num_bits
    high_bit = bound >> 1
    mask = bound - 1
    for bits in range(bound):
        orig_bits = bits
        groups = []
        if bits == mask:
            groups.append(num_bits)
        elif bits != 0:
            # Rotate the bits until the high bit is clear so we don't have to
            # worry about bit groups wrapping around (we are guaranteed that at
            # least one bit is clear because we just handled the bits == mask
            # case)
            while bits & high_bit != 0:
                bits = (bits << 1) & mask | 1

            count = 0
            while bits > 0:
                if bits & 1 == 1:
                    count += 1
                else:
                    if count > 0:
                        groups.append(count)
                    count = 0
                bits >>= 1
            if count > 0:
                groups.append(count)
        if do_groups_match_clues(groups, clues):
            yield orig_bits


def solve_tapa(puzzle):
    lines = [
        [
            [
                char for char in cell if char != ' '
            ] for cell in line.split('|')
        ] for line in puzzle.strip().split('\n') if line != ''
    ]

    # Each cell in this grid will have an integer variable which is >= 0 if the
    # cell is filled and < 0 otherwise. (The specific values within those
    # ranges are only relevant for the one-contiguous-region constraints.)
    g = Grid(len(lines[0]), len(lines))

    def neighbor_is_filled(c):
        return not isinstance(c, Invalid) and c.var >= 0

    s = Solver()

    for cell in g.cells:
        clues = lines[cell.y][cell.x]
        if clues:
            # Clued cells may not be filled
            s.add(cell.var < 0)

            if clues != ['*']:
                # Constrain the surroundings of a cell by its clues
                surrounding_cells = get_surrounding_cells(cell)
                num_bits = len(surrounding_cells)
                s.add(Or([
                    And([
                        neighbor_is_filled(cell2) == (bits & (1 << i) != 0)
                        for i, cell2 in enumerate(surrounding_cells)
                    ]) for bits in iterate_bitmasks_for_clues(clues, num_bits)
                ]))
        else:
            # Filled cells must form one contiguous region (part 1)
            s.add(Or(cell.var <= 0, *(
                And(n.var >= 0, cell.var > n.var) for n in cell.neighbors()
            )))

    # Filled cells must form one contiguous region (part 2)
    s.add(Distinct([c.var for c in g.cells]))

    # No 2×2 regions
    for y in range(g.height - 1):
        for x in range(g.width - 1):
            s.add(Not(And(
                g.cell(x,     y)    .var >= 0,
                g.cell(x + 1, y)    .var >= 0,
                g.cell(x,     y + 1).var >= 0,
                g.cell(x + 1, y + 1).var >= 0)))

    s.check()
    m = s.model()

    def cell_draw(ctx):
        if int(ctx.val) >= 0:
            ctx.fill(0.3, 0.5, 0.7, 1)
        else:
            ctx.draw_text(' '.join(lines[ctx.cell.y][ctx.cell.x]))

    def edge_draw(ctx):
        ctx.draw(1)

    grid_display = RectDisplay(cell_fn=cell_draw, edge_fn=edge_draw)
    grid_display.display_grid(g, m, 48)


if __name__ == '__main__':
    solve_tapa('''
          |2 |  |  |  |  |2?|  |1 |
        2 |  |  |  |2?|  |  |  |  |2
          |  |  |  |  |  |  |  |  |
          |  |  |  |1?|  |  |  |  |2?
          |3?|  |2?|  |  |  |  |  |
          |  |  |  |  |  |1?|  |2?|
        2?|  |  |  |  |2?|  |  |  |
          |  |  |  |  |  |  |  |  |
        1 |  |  |  |  |1?|  |  |  |2
          |2 |  |3?|  |  |  |  |2 |
    ''')
