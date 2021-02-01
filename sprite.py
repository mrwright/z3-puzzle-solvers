from more_itertools import chunked
from z3 import And, EnumSort, Function, IntSort

import display
from z3utils import Switch

Dir, dir_values = EnumSort('Dir', ('north', 'east', 'south', 'west'))
north, east, south, west = dir_values

str_to_dir = {str(d): d for d in dir_values}
dir_to_vector = {
    north: (0, -1),
    east: (1, 0),
    south: (0, 1),
    west: (-1, 0),
}

class Sprite(object):
    """
    A Sprite is an entity that can move around a Grid over time.

    A Sprite has a position (given by .x(t), .y(t) functions) and a direction
    (.dir(t)). Sprites don't impose any additional constraints on these
    functions, but the .forward(t) method can be used to constrain a Sprite to
    move around its Grid one step at a time, and the .in_bounds(t) method can
    be used to constrain a Sprite to stay within its Grid. More puzzle-specific
    constraints can be added on .x, .y, and .dir directly, or via higher-level
    functions defined here.
    """
    def __init__(self, name, grid):
        self.grid = grid
        self.x = Function('{}_x'.format(name), IntSort(), IntSort())
        self.y = Function('{}_y'.format(name), IntSort(), IntSort())
        self.dir = Function('{}_dir'.format(name), IntSort(), Dir)

    def in_bounds(self, t):
        """
        Constrain this Sprite to be in a valid Grid cell at time t.
        """
        return And(self.x(t) >= 0, self.x(t) < self.grid.width,
                   self.y(t) >= 0, self.y(t) < self.grid.height)

    def forward(self, t):
        """
        Constrain this Sprite to take a step forward at time t.

        This function relates the Sprite's direction and position from time
        t - 1 to its position at time t. If .dir(t) is constrained, it will not
        affect the motion of the Sprite corresponding to .forward(t)--it will
        affect the motion of the Sprite corresponding to .forward(t + 1).
        """
        d = self.dir(t - 1)
        x = self.x(t - 1) + Switch(d, (east, 1), (west, -1), (None, 0))
        y = self.y(t - 1) + Switch(d, (south, 1), (north, -1), (None, 0))
        return self.has_position(x, y, t)

    def in_cell(self, cell, t):
        """
        Constrain this Sprite to be in the given cell at time t.
        """
        return self.has_position(cell.x, cell.y, t)

    def has_position(self, x, y, t):
        """
        Constrain this Sprite to have the given coordinates at time t.

        x and y do not have to be valid Grid coordinates.
        """
        return And(self.x(t) == x, self.y(t) == y)

def draw_sprite(ctx:display.CellContext, sprite, t_start, t_end, sprite_fn):
    """
    If sprite is in the given cell at any time between t_start (inclusive) and t_end (exclusive), rotates the drawing
    context so that the sprite is pointing in the positive X direction, and calls sprite_fn(ctx, t)
    """
    for t in range(t_start, t_end):
        if ctx.model.eval(sprite.in_cell(ctx.cell, t)):
            dir = ctx.model.eval(sprite.dir(t))
            vx, vy = dir_to_vector[dir]
            with display.transform_drawing_context(ctx, display.rotation_matrix_for_vector(vx, vy)):
                sprite_fn(ctx, t)

def make_frames(grid, frame_breaks, frames_per_row, spacing=3):
    """
    Turns a grid (presumably using sprites) and a list of times, and produces a list of "augmented grids" suitable
    to plug into display.draw_all_grids(). The extra data for each grid will be the frame number, the start time of
    that frame, and the start time of the next frame.
    """
    raw_grids = [(grid, frame, frame_breaks[frame], frame_breaks[frame+1]) for frame in range(len(frame_breaks) - 1)]
    raw_grid_rows = chunked(raw_grids, frames_per_row)
    frame_width = grid.width + spacing
    frame_height = grid.height + spacing
    frames = [(grid, x * frame_width, y * frame_height, frame, t_start, t_end)
              for y, row in enumerate(raw_grid_rows) for x, (grid, frame, t_start, t_end) in enumerate(row)]
    return frames