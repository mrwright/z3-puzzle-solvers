from z3 import *
from hexgrid import HexGrid, HexDisplay, coord_add
from invalidobj import Invalid, IAnd, IOr
from functools import reduce

givens = [
    '    ',
    '     ',
    ' Y  N ',
    '     0 ',
    '      ',
    '  NO ',
    '    '
]
height, width, west_row, east_row = 7, 7, 3, 3
composite_allowed = False

# givens = [
#     '0 ',
#     ' B ',
#     ' B'
# ]
# height, width, west_row, east_row = 3, 3, 1, 1
# composite_allowed = False

ColorSort, ColorVal, (R, Y, B) = TupleSort('Color', [BoolSort(), BoolSort(), BoolSort()])

def Color(name):
    return Const(name, ColorSort)

given_values = {
    '0': (False, False, False),
    'B': (False, False, True),
    'Y': (False, True, False),
    'G': (False, True, True),
    'R': (True, False, False),
    'V': (True, False, True),
    'O': (True, True, False),
    'N': (True, True, True)
}

def combine_colors(left, right):
    return ColorVal(Or(R(left), R(right)), Or(Y(left), Y(right)), Or(B(left), B(right)))

def combine_all_colors(list):
    return reduce(combine_colors, list, ColorVal(False, False, False))

g = HexGrid(height, width, west_row, east_row, cellgen=Color)

s = Solver()

dirs = [
    (1,-1,0),
    (1,0,-1),
    (-1,1,0),
    (-1,0,1),
    (0,1,-1),
    (0,-1,1)
]
def seen_from(cell):
    yield cell
    for dir in dirs:
        here = g.cell(*coord_add(cell.coords, dir))
        while not isinstance(here, Invalid) and here.given == ' ':
            yield here
            here = g.cell(*coord_add(here.coords, dir))

for (givenrow, cellrow) in zip(givens, g.rows):
    for (given, cell) in zip(givenrow, cellrow):
        cell.given = given

for cell in g.cells:
    if cell.given != ' ':
        # no lights in givens
        s.add(cell.var == ColorVal(False, False, False))
        # given must see correct color
        s.add(combine_all_colors([other.var for other in seen_from(cell)]) == ColorVal(*given_values[cell.given]))
    else:
        # only allow proper colors
        if composite_allowed:
            s.add(AtMost(R(cell.var), Y(cell.var), B(cell.var), 2))
        else:
            s.add(AtMost(R(cell.var), Y(cell.var), B(cell.var), 1))

    # all cells must see a light of some kind
    if cell.given != '0':
        s.add(IOr([other.var != ColorVal(False, False, False) for other in seen_from(cell)]))
    # no two lights can see each other
    s.add(IOr([cell.var == ColorVal(False, False, False), IAnd([other.var == ColorVal(False, False, False) for other in seen_from(cell) if other != cell])]))

s.check()

print(s.model())

def draw_edge(ctx):
    ctx.draw()

colors = {
    (False, False, False): (0.8, 0.8, 0.8, 0.8),
    (False, False, True): (0, 0, 1, 1),
    (False, True, False): (1, 1, 0, 1),
    (False, True, True): (0, 1, 0, 1),
    (True, False, False): (1, 0, 0, 1),
    (True, False, True): (1, 0, 1, 1),
    (True, True, False): (1, 0.5, 0, 1),
    (True, True, True): (0.5, 0.2, 0, 1)
}

def draw_cell(ctx):
    if ctx.cell.given != ' ':
        color = colors[given_values[ctx.cell.given]]
        ctx.fill(*color)
    else:
        color = ctx.model[ctx.cell.var]
        realcolor = colors[(bool(ctx.model.eval(R(color))), bool(ctx.model.eval(Y(color))), bool(ctx.model.eval(B(color))))]
        ctx.draw_circle(color=realcolor, fill=True)
        # ctx.draw_text("hi", fontsize=14)

def draw_point(ctx):
    ctx.draw_square(color=(1,0,0,1))
    # ctx.draw_circle(color=(0,1,0,1))
    # ctx.ctx.set_line_width(1/10)
    # ctx.ctx.set_source_rgba(0,0,1,1)
    # ctx.ctx.move_to(0,0)
    # ctx.ctx.line_to(0, -0.2)
    # ctx.ctx.stroke()
    pass

def draw_south_point(ctx):
    ctx.draw_circle(color=(0,1,0,1))

display = HexDisplay(cell_fn=draw_cell, edge_fn=draw_edge, point_fn=draw_point)
display.set_southward_point_fn(draw_south_point)

display.display_grid(g, s.model(), 40)

