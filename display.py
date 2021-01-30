import math
import sys
import os
from collections import defaultdict

import cairo
from PIL import Image

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

class BaseDisplay:
    def __init__(self, cell_fn=None, edge_fn=None, point_fn=None, padding=0.5):
        self.cell_fns = defaultdict(lambda: cell_fn)
        self.edge_fns = defaultdict(lambda: edge_fn)
        self.point_fns = defaultdict(lambda: point_fn)
        self.padding = padding

    def set_cell_fn(self, cell_fn, only_for=None):
        if only_for:
            self.cell_fns[only_for] = cell_fn
        else:
            self.cell_fns = defaultdict(lambda: cell_fn)

    def get_cell_fn(self, kind=None):
        return self.cell_fns[kind]

    def set_edge_fn(self, edge_fn, only_for=None):
        if only_for:
            self.edge_fns[only_for] = edge_fn
        else:
            self.edge_fns = defaultdict(lambda: edge_fn)

    def get_edge_fn(self, kind=None):
        return self.edge_fns[kind]

    def set_point_fn(self, point_fn, only_for=None):
        if only_for:
            self.point_fns[only_for] = point_fn
        else:
            self.point_fns = defaultdict(lambda: point_fn)

    def get_point_fn(self, kind=None):
        return self.point_fns[kind]

    def display_grid(self, grid, model, scale):
        self.display_all_grids([(grid, 0, 0)], model, scale)

    # grids is a list of tuples: (grid, x, y)
    def display_all_grids(self, grids, model, scale):
        surface, ctx = self._get_surface(grids, scale)

        for grid, x, y in grids:
            self._draw_grid_elements(ctx, grid, x, y, model)

        self._show_pygame_window(surface)

        def handle(events):
            for event in events:
                if event.type == pygame.QUIT:
                    return True
                elif event.type == pygame.KEYDOWN:
                    if event.key == 27:
                        return True
            return False

        quitting = False
        while not quitting:
            quitting = handle(pygame.event.get())


    def _show_pygame_window(self, surface):
        width = surface.get_width()
        height = surface.get_height()
        pygame.init()
        pygame.display.set_mode((width, height))
        screen = pygame.display.get_surface()
        buf = surface.get_data()
        # cairo.surface.get_data() returns pixels in aRGB machine-native byte order.
        # pygame.image.frombuffer() expects pixels in a predictable big-endian ARGB order
        # so we use PIL's "native" output format to convert predictably
        # really this should read with "I;32N" and write with "I;32B", but no such output packer exists in PIL
        pil_image = Image.frombuffer("I", (width, height), bytes(buf), "raw", "I;32B", 0, 1)
        fixed_buf = pil_image.tobytes("raw", "I;32S")
        image = pygame.image.frombuffer(fixed_buf, (width, height), "ARGB")
        # Transfer to Screen
        # also, cairo outputs premultiplied alpha but pygame normally expects straight alpha.
        # we could use PIL again to fix this but modern versions of pygame have this flag instead.
        screen.blit(image, (0, 0), special_flags=pygame.BLEND_PREMULTIPLIED)
        pygame.display.flip()

    def _draw_grid_elements(self, ctx, grid, x, y, model):
        ctx.save()
        ctx.translate(x, y)
        for cell in grid.cells:
            fn, matrix = self._setup_cell(cell)
            if fn:
                ctx.save()
                ctx.transform(matrix)
                cell_ctx = CellContext(ctx, cell, model, self._cell_corners())
                fn(cell_ctx)
                ctx.restore()
        for edge in grid.edges:
            fn, matrix = self._setup_edge(edge)
            if fn:
                ctx.save()
                ctx.transform(matrix)
                edge_ctx = EdgeContext(ctx, edge, model)
                fn(edge_ctx)
                ctx.restore()
        for point in grid.points:
            fn, matrix = self._setup_point(point)
            if fn:
                ctx.save()
                ctx.transform(matrix)
                point_ctx = PointContext(ctx, point, model)
                fn(point_ctx)
                ctx.restore()
        ctx.restore()

    def _get_surface(self, grids, scale):
        lefts = []
        rights = []
        tops = []
        bottoms = []
        def adjust(extents, x, y):
            l, t, r, b = extents
            return l+x, t+y, r+x, b+y

        lefts, tops, rights, bottoms = tuple(zip(*[adjust(self._get_extents(grid), x, y) for grid, x, y in grids]))
        left = min(lefts)
        top = min(tops)
        right = max(rights)
        bottom = max(bottoms)

        # add half a grid on every side
        width = (right - left + self.padding * 2) * scale
        height = (bottom - top + self.padding * 2) * scale
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, int(width), int(height))
        ctx = cairo.Context(surface)
        ctx.set_source_rgba(1, 1, 1, 1)
        ctx.rectangle(0, 0, width, height)
        ctx.fill()

        # translate context so user origin and grid origin coincide
        ctx.scale(scale, scale)
        ctx.translate(-left + self.padding, -top + self.padding)
        return surface, ctx

    def _get_extents(self, grid):
        raise NotImplementedError

    def _setup_cell(self, cell):
        raise NotImplementedError

    def _setup_edge(self, edge):
        raise NotImplementedError

    def _setup_point(self, point):
        raise NotImplementedError

    def _cell_corners(self):
        raise NotImplementedError



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
        self.ctx.set_source_rgba(*color)
        self.ctx.rectangle(- size/2, - size/2,
                           size, size)
        self.ctx.fill()

    def draw_circle(self, radius=(1/3), **kw):
        draw_circle(self.ctx, 0, 0, radius, **kw)

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
        self.ctx.set_source_rgba(*color)
        self.ctx.move_to(0,0)
        self.ctx.line_to(1,0)
        self.ctx.stroke()


class CellContext(object):
    def __init__(self, ctx, cell, model, corners):
        self.ctx = ctx
        self.cell = cell
        self.model = model
        self.corners = corners

    @property
    def val(self):
        return str(self.model[self.cell.var])

    def fill(self, r, g, b, a):
        self.ctx.set_source_rgba(r, g, b, a)
        self.ctx.move_to(*self.corners[-1])
        for corner in self.corners:
            self.ctx.line_to(*corner)
        # fill it
        self.ctx.fill()

    def draw_text(self, text, **kw):
        draw_text(self.ctx, 0, 0, text, **kw)

    def draw_circle(self, radius=1/1.5, **kw):
        draw_circle(self.ctx, 0, 0, radius, **kw)

    def draw_line(self, x0, y0, x1, y1, size=1, color=(0, 0, 0, 1)):
        self.ctx.set_source_rgba(*color)
        self.ctx.set_line_width(size)
        self.ctx.move_to(x0, y0)
        self.ctx.line_to(x1, y1)
        self.ctx.stroke()

    def draw_line_corners(self, c0, c1, *a, **kw):
        self.draw_line(*self.corners[c0], *self.corners[c1], *a, **kw)

def draw_text(ctx, x, y, t, fontsize=12, family='', bold=False, italic=False, color=(0,0,0,1)):
    ctx.set_font_size(convert_stroke_width(ctx, fontsize))
    ctx.set_font_face(font(family, bold, italic))
    ctx.set_source_rgba(*color)
    _, _, w, h, dx, dy = ctx.text_extents(str(t))
    ctx.move_to(x - w/2, y + h/2)
    ctx.show_text(str(t))
    ctx.stroke()

def draw_circle(ctx, x, y, radius, color=(0, 0, 0, 1), fill=False, stroke_width=2):
    ctx.set_source_rgba(*color)
    ctx.arc(x, y, radius, 0, 6.3)
    if fill:
        ctx.fill()
    else:
        real_width = convert_stroke_width(ctx, stroke_width)
        ctx.set_line_width(real_width)
        ctx.stroke()


