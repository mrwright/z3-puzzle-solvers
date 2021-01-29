import math
import sys
import os

import cairo

def font(family='', bold=False, italic=False):
    return cairo.ToyFontFace(
        family,
        cairo.FontSlant.ITALIC if italic else cairo.FontSlant.NORMAL,
        cairo.FontWeight.BOLD if bold else cairo.FontWeight.NORMAL,
    )

with open(os.devnull, 'w') as f:
    # disable stdout
    oldstdout = sys.stdout
    sys.stdout = f

    import pygame

    # enable stdout
    sys.stdout = oldstdout

HALF_SQRT3 = math.sqrt(3)/2
def transform_coords(coords):
    n, se, sw = coords
    x = (se - sw) * HALF_SQRT3
    y = - n + se / 2 + sw / 2
    return x, y

SQRT2 = math.sqrt(2)
# users would much rather specify stroke widths and text sizes in device coordinates, instead of user coordinates.
def convert_stroke_width(ctx, width):
    # try to get an average "scaling factor", in case of non-square scaling
    dx, dy = ctx.device_to_user_distance(width/SQRT2, width/SQRT2)
    return math.sqrt(dx*dx+dy*dy)

class PointContext(object):
    def __init__(self, ctx, point, model):
        self.point = point
        self.model = model
        self.ctx = ctx

    def draw_square(self, size=(1/3), color=(0, 0, 0, 1)):
        r, g, b, a = color
        self.ctx.set_source_rgba(b, g, r, a)
        self.ctx.rectangle(- size/2, - size/2,
                           size, size)
        self.ctx.fill()

    def draw_circle(self, radius=(1/3), color=(0, 0, 0, 1), fill=False, stroke_width=2):
        r, g, b, a = color
        self.ctx.set_source_rgba(b, g, r, a)
        self.ctx.arc(0, 0, radius, 0, 6.3)
        if fill:
            self.ctx.fill()
        else:
            real_width = convert_stroke_width(self.ctx, stroke_width)
            self.ctx.set_line_width(real_width)
            self.ctx.stroke()

class EdgeContext(object):
    def __init__(self, ctx, edge, model):
        self.edge = edge
        self.model = model
        self.ctx = ctx

    @property
    def val(self):
        return str(self.model[self.edge.var])

    def draw(self, width=1, color=(0, 0, 0, 1)):
        self.ctx.set_line_cap(cairo.LINE_CAP_SQUARE)
        # transform width into user space
        real_width = convert_stroke_width(self.ctx, width)
        self.ctx.set_line_width(real_width)
        r, g, b, a = color
        self.ctx.set_source_rgba(b, g, r, a)
        self.ctx.move_to(0,0)
        self.ctx.line_to(1,0)
        self.ctx.stroke()


class CellContext(object):
    def __init__(self, ctx, cell, model):
        self.ctx = ctx
        self.cell = cell
        self.model = model

    @property
    def val(self):
        return str(self.model[self.cell.var])

    def fill(self, r, g, b, a):
        self.ctx.set_source_rgba(b, g, r, a)
        # start at n corner
        self.ctx.move_to(0, 0)
        self.ctx.rel_move_to(*transform_coords((1, 0, 0)))

        # walk around hex
        self.ctx.rel_line_to(*transform_coords((0, 1, 0)))
        self.ctx.rel_line_to(*transform_coords((-1, 0, 0)))
        self.ctx.rel_line_to(*transform_coords((0, 0, 1)))
        self.ctx.rel_line_to(*transform_coords((0, -1, 0)))
        self.ctx.rel_line_to(*transform_coords((1, 0, 0)))
        self.ctx.rel_line_to(*transform_coords((0, 0, -1)))

        # fill it
        self.ctx.fill()

    def draw_text(self, text, fontsize=12, family='', bold=False, italic=False):
        self.ctx.set_font_size(convert_stroke_width(self.ctx, fontsize))
        self.ctx.set_font_face(font(family, bold, italic))
        self.ctx.set_source_rgba(0, 0, 0, 1)
        draw_text(self.ctx, 0, 0, text)
        self.ctx.stroke()

    def draw_circle(self, size=1/1.5, color=(0, 0, 0, 1), fill=False, stroke_width=1):
        r, g, b, a = color
        self.ctx.set_source_rgba(b, g, r, a)
        self.ctx.arc(0, 0, size, 0, 6.3)
        if fill:
            self.ctx.fill()
        else:
            self.ctx.set_line_width(convert_stroke_width(self.ctx, stroke_width))
            self.ctx.stroke()

def draw_grid(grid, model, scale,
              cell_fn=None, edge_fn=None, point_fn=None,
              vert_fn=None, ne_sw_fn=None, nw_se_fn=None,
              north_point_fn=None, south_point_fn=None):
    surface, ctx = get_surface(grid, scale)

    if cell_fn:
        for cell in grid.cells:
            ctx.save()
            # move context so 0,0 is the center of the cell
            ctx.translate(*transform_coords(cell.coords))
            cell_ctx = CellContext(ctx, cell, model)
            cell_fn(cell_ctx)
            ctx.restore()
    if edge_fn or vert_fn or ne_sw_fn or nw_se_fn:
        edge_fns = {
            (1,0,0): vert_fn or edge_fn,
            (0,1,0): nw_se_fn or edge_fn,
            (0,0,1): ne_sw_fn or edge_fn,
        }
        for edge in grid.edges:
            fn = edge_fns[edge.vector]
            if fn:
                ctx.save()
                # set up context so that the edge goes from 0,0 to 1,0
                ctx.translate(*transform_coords(edge.coords))
                d_x, d_y = transform_coords(edge.vector)
                ctx.transform(cairo.Matrix(d_x, d_y, -d_y, d_x, 0, 0))
                edge_ctx = EdgeContext(ctx, edge, model)
                fn(edge_ctx)
                ctx.restore()
    if point_fn or north_point_fn or south_point_fn:
        point_fns = {
            1: north_point_fn or point_fn,
            -1: south_point_fn or point_fn,
        }
        for point in grid.points:
            fn = point_fns[point.direction]
            if fn:
                ctx.save()
                # move context so 0,0 is the point
                # and turn it upside down for southward points
                ctx.translate(*transform_coords(point.coords))
                ctx.scale(point.direction, point.direction)
                point_ctx = PointContext(ctx, point, model)
                fn(point_ctx)
                ctx.restore()
    show_surface(surface)

def draw_text(ctx, x, y, t):
    _, _, w, h, dx, dy = ctx.text_extents(t)
    ctx.move_to(x - w/2, y + h/2)
    ctx.show_text(t)

def input(events):
    for event in events:
        if event.type == pygame.QUIT:
            sys.exit(0)
        elif event.type == pygame.KEYDOWN:
            if event.key == 27:
                sys.exit(0)

def get_surface(grid, scale):
    # in half-hexes
    w = grid.width * 2 + abs(grid.west_row - grid.east_row)
    h = grid.height * 3 / 2 + 1 / 2

    width = (w+1) * scale
    height = (h+1) * scale
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, int(height))
    ctx = cairo.Context(surface)
    ctx.set_source_rgba(1, 1, 1, 1)
    ctx.rectangle(0, 0, width, height)
    ctx.fill()

    # translate context so user origin and hex origin coincide
    ctx.translate((grid.west_row + 1.5) * scale, 1.5 * scale)
    ctx.scale(scale, scale)
    return surface, ctx

def show_surface(surface):
    width = surface.get_width()
    height = surface.get_height()

    pygame.init()
    pygame.display.set_mode((width, height))

    screen = pygame.display.get_surface()
    buf = surface.get_data()

    # TODO: color management is a little funny, probably due to pixel
    # formats here. In a bunch of places we need to call rgb functions
    # but pass things in in g, b, r order.
    image = pygame.image.frombuffer(buf, (width, height), "RGBA")
    # Tranfer to Screen
    screen.blit(image, (0, 0))
    pygame.display.flip()

    while True:
        input(pygame.event.get())
