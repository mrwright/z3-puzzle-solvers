import sys
import os

import cairo
from hexgrid import coord_add

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

# TODO: use cairo context transforms properly instead of passing scale everywhere
def transform_coords(coords, scale):
    n, se, sw = coords
    x = se - sw
    y = - n + se / 2 + sw / 2
    return x * scale, y * scale

class PointContext(object):
    def __init__(self, ctx, point, model, scale):
        self.point = point
        self.model = model
        self.scale = scale
        self.ctx = ctx

    @property
    def c0(self):
        return transform_coords(self.point.coords, self.scale)

    def draw_square(self, size=1, color=(0, 0, 0, 1)):
        r, g, b, a = color
        self.ctx.set_source_rgba(b, g, r, a)
        x, y = self.c0
        self.ctx.rectangle(x - size/2, y - size/2,
                           size, size)
        self.ctx.fill()

    def draw_circle(self, size=10, color=(0, 0, 0, 1), fill=False):
        r, g, b, a = color
        self.ctx.set_source_rgba(b, g, r, a)
        self.ctx.arc(*self.c0, size, 0, 6.3)
        if fill:
            self.ctx.fill()
        else:
            self.ctx.stroke()

class EdgeContext(object):
    def __init__(self, ctx, edge, model, scale):
        self.edge = edge
        self.model = model
        self.ctx = ctx
        self.scale = scale

    @property
    def val(self):
        return str(self.model[self.edge.var])

    @property
    def p0(self):
        return transform_coords(self.edge.coords, self.scale)

    def draw(self, width=1, color=(0, 0, 0, 1)):
        self.ctx.set_line_width(width)
        r, g, b, a = color
        self.ctx.set_source_rgba(b, g, r, a)
        self.ctx.move_to(*self.p0)
        self.ctx.line_to(*self.p1)
        self.ctx.stroke()

class VertContext(EdgeContext):
    def __init__(self, *a, **kw):
        super(VertContext, self).__init__(*a, **kw)

    @property
    def p1(self):
        return transform_coords(coord_add(self.edge.coords, (1, 0, 0)), self.scale)

class NE_SW_Context(EdgeContext):
    def __init__(self, *a, **kw):
        super(NE_SW_Context, self).__init__(*a, **kw)

    @property
    def p1(self):
        return transform_coords(coord_add(self.edge.coords, (0, 0, 1)), self.scale)

class NW_SE_Context(EdgeContext):
    def __init__(self, *a, **kw):
        super(NW_SE_Context, self).__init__(*a, **kw)

    @property
    def p1(self):
        return transform_coords(coord_add(self.edge.coords, (0, 1, 0)), self.scale)

class CellContext(object):
    def __init__(self, ctx, cell, model, scale):
        self.ctx = ctx
        self.cell = cell
        self.model = model
        self.scale = scale

    @property
    def val(self):
        return str(self.model[self.cell.var])

    @property
    def c0(self):
        return transform_coords(self.cell.coords, self.scale)

    def fill(self, r, g, b, a):
        self.ctx.set_source_rgba(b, g, r, a)
        # start at n corner
        self.ctx.move_to(*self.c0)
        self.ctx.rel_move_to(*transform_coords((1, 0, 0), self.scale))

        # walk around hex
        self.ctx.rel_line_to(*transform_coords((0, 1, 0), self.scale))
        self.ctx.rel_line_to(*transform_coords((-1, 0, 0), self.scale))
        self.ctx.rel_line_to(*transform_coords((0, 0, 1), self.scale))
        self.ctx.rel_line_to(*transform_coords((0, -1, 0), self.scale))
        self.ctx.rel_line_to(*transform_coords((1, 0, 0), self.scale))
        self.ctx.rel_line_to(*transform_coords((0, 0, -1), self.scale))

        # fill it
        self.ctx.fill()

    def text(self, text, fontsize=12, family='', bold=False, italic=False):
        self.ctx.set_font_size(fontsize)
        self.ctx.set_font_face(font(family, bold, italic))
        self.ctx.set_source_rgba(0, 0, 0, 1)
        draw_text(self.ctx, *self.c0, text)
        self.ctx.stroke()

    def circle(self, size=None, color=(0, 0, 0, 1), fill=False):
        # TODO: consistent name (circle vs. draw_circle)
        if not size:
            size = self.scale/1.5
        r, g, b, a = color
        self.ctx.set_source_rgba(b, g, r, a)
        self.ctx.arc(*self.c0, size, 0, 6.3)
        if fill:
            self.ctx.fill()
        else:
            self.ctx.stroke()

def draw_grid(grid, model, scale,
              cell_fn=None, edge_fn=None,
              point_fn=None):
    surface, ctx = get_surface(grid, scale)

    if cell_fn:
        for cell in grid.cells:
            cell_ctx = CellContext(ctx, cell, model, scale)
            cell_fn(cell_ctx)
    if edge_fn:
        for vert in grid.verts:
            vert_ctx = VertContext(ctx, vert, model, scale)
            edge_fn(vert_ctx)
        for ne_sw in grid.ne_sws:
            ne_sw_ctx = NE_SW_Context(ctx, ne_sw, model, scale)
            edge_fn(ne_sw_ctx)
        for nw_se in grid.nw_ses:
            nw_se_ctx = NW_SE_Context(ctx, nw_se, model, scale)
            edge_fn(nw_se_ctx)
    if point_fn:
        for point in grid.points:
            point_ctx = PointContext(ctx, point, model, scale)
            point_fn(point_ctx)
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
