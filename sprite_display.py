import cairo

from display import (CellContext, HorizEdgeContext, PointContext,
                     VertEdgeContext, get_surface, show_surface, transform_x,
                     transform_y)
from sprite import south, east, west, str_to_dir


class FramedMixin(object):
    @property
    def gx(self):
        return super(FramedMixin, self).gx + self.offset_gx

    @property
    def gy(self):
        return super(FramedMixin, self).gy + self.offset_gy


class FramedCellContext(FramedMixin, CellContext):
    def __init__(self, surface, cell, model, scale, offset_gx, offset_gy, t):
        CellContext.__init__(self, surface, cell, model, scale)
        self.offset_gx = offset_gx
        self.offset_gy = offset_gy
        self.t = t


class FramedHorizEdgeContext(FramedMixin, HorizEdgeContext):
    def __init__(self, surface, edge, model, scale, offset_gx, offset_gy, t):
        HorizEdgeContext.__init__(self, surface, edge, model, scale)
        self.offset_gx = offset_gx
        self.offset_gy = offset_gy
        self.t = t


class FramedVertEdgeContext(FramedMixin, VertEdgeContext):
    def __init__(self, surface, edge, model, scale, offset_gx, offset_gy, t):
        VertEdgeContext.__init__(self, surface, edge, model, scale)
        self.offset_gx = offset_gx
        self.offset_gy = offset_gy
        self.t = t


class FramedPointContext(FramedMixin, PointContext):
    def __init__(self, surface, point, model, scale, offset_gx, offset_gy, t):
        PointContext.__init__(self, surface, point, model, scale)
        self.offset_gx = offset_gx
        self.offset_gy = offset_gy
        self.t = t


class SpriteContext(object):
    def __init__(self, surface, sprite, model, scale, offset_gx, offset_gy, t):
        self.surface = surface
        self.ctx = cairo.Context(surface)
        self.sprite = sprite
        self.model = model
        self.scale = scale
        self.offset_gx = offset_gx
        self.offset_gy = offset_gy
        self.t = t

    def gx(self, t=None):
        if t is None:
            t = self.t
        return self.model.eval(self.sprite.x(t)).as_long()

    def gy(self, t=None):
        if t is None:
            t = self.t
        return self.model.eval(self.sprite.y(t)).as_long()

    def dir(self, t=None):
        if t is None:
            t = self.t
        return str_to_dir[str(self.model.eval(self.sprite.dir(t)))]

    def x(self, t):
        return transform_x(self.gx(t) + self.offset_gx + 0.5, self.scale)

    def y(self, t):
        return transform_y(self.gy(t) + self.offset_gy + 0.5, self.scale)

    def draw_rotated(self, path, t=None, width=1, color=(0, 0, 0, 1)):
        r, g, b, a = color
        self.ctx.set_source_rgba(b, g, r, a)
        self.ctx.set_line_width(width)
        self.ctx.set_line_join(cairo.LINE_JOIN_BEVEL)
        d = self.dir(t)
        dx = self.gx(t) + self.offset_gx
        dy = self.gy(t) + self.offset_gy
        first = True
        for x, y in path:
            if d == south:
                x, y = 1 - x, 1 - y
            elif d == east:
                x, y = 1 - y, x
            elif d == west:
                x, y = y, 1 - x
            x += dx
            y += dy
            if first:
                self.ctx.move_to(transform_x(x, self.scale),
                                 transform_y(y, self.scale))
                first = False
            else:
                self.ctx.line_to(transform_x(x, self.scale),
                                 transform_y(y, self.scale))
        self.ctx.stroke()

    def path(self, from_t, to_t, width=1, color=(0, 0, 0, 1)):
        r, g, b, a = color
        self.ctx.set_source_rgba(b, g, r, a)
        self.ctx.set_line_width(width)
        self.ctx.set_line_join(cairo.LINE_JOIN_BEVEL)
        self.ctx.move_to(self.x(from_t), self.y(from_t))
        for t in range(from_t + 1, to_t):
            self.ctx.line_to(self.x(t), self.y(t))
        self.ctx.stroke()


def draw_grid_frames_and_sprites(grid, model, scale, frame_rows, sprites,
                                 cell_fn=None, horiz_fn=None, vert_fn=None,
                                 point_fn=None, sprite_fn=None):
    frame_w = max(map(len, frame_rows))
    frame_h = len(frame_rows)

    canvas_w = ((grid.width + 1) * frame_w) * scale
    canvas_h = ((grid.height + 1) * frame_h) * scale

    surface = get_surface(canvas_w, canvas_h)

    i = 0
    for y0, row in enumerate(frame_rows):
        for x0, t in enumerate(row):
            x = x0 * (grid.width + 1)
            y = y0 * (grid.height + 1)
            if cell_fn:
                for cell in grid.cells:
                    cell_ctx = FramedCellContext(surface, cell, model, scale,
                                                 x, y, t)
                    cell_fn(cell_ctx, i)
            if horiz_fn:
                for horiz in grid.horizs:
                    horiz_ctx = FramedHorizEdgeContext(surface, horiz, model,
                                                       scale, x, y, t)
                    horiz_fn(horiz_ctx, i)
            if vert_fn:
                for vert in grid.verts:
                    vert_ctx = FramedVertEdgeContext(surface, vert, model,
                                                     scale, x, y, t)
                    vert_fn(vert_ctx, i)
            if point_fn:
                for point in grid.points:
                    point_ctx = FramedPointContext(surface, point, model,
                                                   scale, x, y, t)
                    point_fn(point_ctx, i)
            if sprite_fn:
                for sprite in sprites:
                    sprite_ctx = SpriteContext(surface, sprite, model, scale,
                                               x, y, t)
                    sprite_fn(sprite_ctx, i)
            i += 1

    show_surface(surface)
