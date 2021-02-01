import time

from more_itertools import chunked
from six import print_
from z3 import *

from display import draw_polygon, rotation_matrix_for_vector, transform_drawing_context
from grid import Grid, RectDisplay
from sprite import Dir, Sprite, dir_to_vector, draw_sprite, make_frames, north, east, south, west
from z3utils import Switch, lift_to_solver


def initial_laser_dir(firing):
    return [north, east, south, west][firing % 4]


class QuebecatCell(object):
    def __init__(self, name):
        self.has_mirror = Bool('{}_has_mirror'.format(name))
        self.mirror_state = Function('{}_mirror_state'.format(name), IntSort(),
                                     BoolSort())


def solve_board(board, display=False):
    """
    Solve a single page of Rage of the Quebecats.

    Returns:
        A triple (laser, x, y), where laser is the distance traveled by the
        laser, and x and y are the coordinates of an off-grid "cell" struck by
        the laser.

    Example:
        >>> solve_board(boards[4])
        solving board... solution found
        (22, 2, -1)
    """
    start_time = time.perf_counter()
    grid = Grid(5, 5, cellgen=QuebecatCell)
    laser = Sprite('laser', grid)
    human = grid.cell_array[2, 2]

    s = Solver()

    s.add(Not(human.var.has_mirror))

    # The conceptual timeline of the board is broken into ticks, and each
    # tick adds a set of constraints in effect at that point in time. First,
    # we define functions that abstract out the different kinds of ticks and
    # the constraints they add.

    @lift_to_solver(s, Dir, Dir)
    def reflect_swne(d):
        r"""Reflect a laser with a "/" mirror (mirror_state=True)"""
        return Switch(d,
                      (north, east), (east, north),
                      (south, west), (west, south))

    @lift_to_solver(s, Dir, Dir)
    def reflect_nwse(d):
        r"""Reflect a laser with a "\" mirror (mirror_state=False)"""
        return Switch(d,
                      (north, west), (west, north),
                      (south, east), (east, south))

    @lift_to_solver(s, IntSort(), BoolSort())
    def interact_with_grid(t):
        """
        State evolution logic that should take place every tick (except for new
        firings).
        """
        constraints = []
        laser_dir_prev = laser.dir(t - 1)
        reflected_nwse = reflect_nwse(laser_dir_prev)
        reflected_swne = reflect_swne(laser_dir_prev)
        for cell in grid.cells:
            laser_is_here = laser.in_cell(cell, t)
            state_prev = cell.var.mirror_state(t - 1)
            state = cell.var.mirror_state(t)
            # If the laser hits a mirror here, flip the mirror; otherwise,
            # maintain the mirror's rotation.
            constraints.append(
                state == If(laser_is_here, Not(state_prev), state_prev))

            # If the laser is here, determine the laser's new direction from
            # the presence/absence of a mirror here and, if present, its
            # rotation.
            reflected_dir = If(state_prev, reflected_swne, reflected_nwse)
            constraints.append(
                Implies(laser_is_here, laser.dir(t) == If(cell.var.has_mirror, reflected_dir, laser_dir_prev)))
        return And(constraints)

    @lift_to_solver(s, IntSort(), Dir, BoolSort())
    def tick_new_firing(t, laser_dir):
        """
        Constraint applied at the beginning of each firing of the laser.
        """
        return And(
            laser.in_cell(human, t),
            laser.dir(t) == laser_dir,
            *(cell.var.mirror_state(t) == cell.var.mirror_state(t - 1) for cell in grid.cells))

    @lift_to_solver(s, IntSort(), BoolSort())
    def tick_continue(t):
        """
        Constraint applied while a firing continues.
        """
        return And(
            laser.in_bounds(t),
            laser.forward(t),
            interact_with_grid(t))

    @lift_to_solver(s, IntSort(), Dir, IntSort(), IntSort(), BoolSort())
    def tick_hit_wall(t, laser_dir, x_final, y_final):
        """
        Constraint applied when the laser is known to hit a wall at the end of
        the tick.
        """
        return And(
            laser.has_position(x_final, y_final, t),
            laser.dir(t) == laser_dir,
            laser.forward(t),
            interact_with_grid(t))

    @lift_to_solver(s, IntSort(), BoolSort())
    def tick_epilogue(t):
        """
        Constraint applied while the final firing continues--this is basically
        the same as tick_continue, except that we don't know when the laser
        leaves the grid.
        """
        return And(
            laser.forward(t),
            interact_with_grid(t))

    # Now we use the board data to determine what kinds of ticks happen when,
    # and actually add the tick constraints to the solver.

    # This is an ascending list of the ticks at which the laser fires. The
    # last element of the list corresponds to the final, unknown firing.
    firing_ticks = []

    tick = 0
    for firing, (dt, wall, coord) in enumerate(board):
        firing_ticks.append(tick)

        # Compute the coordinates of the laser just before it hits the wall.
        x_final = (0 if wall == west
                   else grid.width - 1 if wall == east
                   else coord)
        y_final = (0 if wall == north
                   else grid.height - 1 if wall == south
                   else coord)

        # Each firing with a time/range of dt will start will one
        # tick_new_firing tick, followed by dt - 1 tick_continue ticks, and
        # then a final tick_hit_wall tick, for a total of dt + 1 ticks per
        # firing.
        s.add(tick_new_firing(tick, initial_laser_dir(firing)))
        end_tick = tick + dt
        for t in range(tick + 1, end_tick):
            s.add(tick_continue(t))
        s.add(tick_hit_wall(end_tick, wall, x_final, y_final))
        tick = end_tick + 1

    # Finally there is an "epilogue" firing, where we don't know the ultimate
    # fate of the laser. (I am using the knowledge that the laser must hit a
    # wall within 26 ticks, because the final range corresponds to a letter,
    # but this isn't critical information; the solver would work with a looser
    # bound on the epilogue's duration.)
    firing_ticks.append(tick)
    s.add(tick_new_firing(tick, initial_laser_dir((firing + 1) % 4)))
    for t in range(tick + 1, tick + 27):
        s.add(tick_epilogue(t))

    print_("solving board... ", end='', flush=True)

    if s.check() == unsat:
        print("solution not found")
    else:
        end_time = time.perf_counter()
        print(f"solution found in {end_time - start_time}")
        model = s.model()

        # Determine the range of the final firing by finding the first tick
        # when the laser goes off the grid.
        t = firing_ticks[-1] + 1
        final_range = 0
        while model.eval(laser.in_bounds(t)):
            final_range += 1
            t += 1

        firing_ticks.append(t)
        if display:
            def cell_draw(ctx):
                frame, t_start, t_end = ctx.extra
                draw_sprite(ctx, laser, t_start, t_end, laser_draw)

                if ctx.model.eval(ctx.cell.var.has_mirror):
                    color = (0, 0, 1, 1)
                    if ctx.model.eval(ctx.cell.var.mirror_state(t_start)):
                        ctx.draw_line(-0.3, 0.3, 0.3, -0.3, color=color)
                    else:
                        ctx.draw_line(-0.3, -0.3, 0.3, 0.3, color=color)

                if ctx.cell.coords == human.coords:
                    # orient the human correctly
                    with transform_drawing_context(ctx, rotation_matrix_for_vector(*dir_to_vector[initial_laser_dir(frame)])):
                        draw_polygon(ctx, [(0, 0), (-0.3, -0.3), (0.3, 0), (-0.3, 0.3)], color=(1,0,0,1))

                if ctx.model.eval(laser.in_cell(ctx.cell, t_end - 1)):
                    # draw the number outside
                    ctx.draw_text(t_end - t_start - 1, *dir_to_vector[ctx.model.eval(laser.dir(t_end-1))], fontsize=24)

            def edge_draw(ctx):
                ctx.draw(width=3)

            def laser_draw(ctx, t):
                color = (1, 0, 0, 1)
                ctx.draw_line(0, 0, 1, 0, color=color)

            rect_display = RectDisplay(edge_fn=edge_draw, cell_fn=cell_draw, padding=1.5)
            grids = make_frames(grid, firing_ticks, 4)
            rect_display.display_all_grids(grids, model, 32)

        return (final_range,
                model.eval(laser.x(t)).as_long(),
                model.eval(laser.y(t)).as_long())


# Each board is a page of the puzzle; each triple in the board corresponds to
# one of the grids on the page. The triples consist of:
#   * the distance measured by the laser
#   * the wall struck by the laser
#   * the coordinate where the wall is struck, where 0 is the leftmost or
#     topmost position on the wall and 4 is the rightmost or bottommost
boards = [
    [
        ( 3, east , 1), ( 4, east , 0), ( 6, north, 4), ( 4, west , 0),
        ( 4, west , 2), ( 8, south, 4), ( 6, north, 4), ( 6, west , 4),
        ( 3, east , 1), (15, south, 1)
    ], [
        ( 4, north, 4), ( 4, east , 0), ( 3, south, 3), (12, north, 0),
        (13, north, 1), ( 4, south, 4), ( 4, south, 0), ( 3, south, 1),
        ( 4, north, 4), ( 6, west , 0), ( 3, south, 3)
    ], [
        ( 4, west , 2), ( 7, north, 3), ( 5, north, 3), (15, east , 1),
        ( 6, north, 4), ( 7, north, 1), ( 4, east , 4), ( 8, south, 4),
        ( 3, east , 1), ( 7, north, 3), ( 4, west , 4)
    ], [
        ( 4, north, 4), ( 9, west , 3), ( 3, south, 3), ( 4, west , 4),
        ( 8, south, 0), ( 4, east , 4), ( 6, west , 2), ( 4, west , 4),
        (12, west , 0), ( 5, west , 3), ( 7, west , 3)
    ], [
        ( 6, south, 2), (15, west , 3), ( 3, east , 3), ( 6, east , 0),
        ( 6, south, 0), ( 3, east , 1), ( 8, east , 4), ( 4, north, 0),
        (13, east , 3)
    ], [
        ( 7, north, 3), ( 3, north, 3), ( 8, east , 4), ( 4, west , 0),
        ( 4, west , 2), ( 3, north, 3), ( 7, north, 3), ( 4, west , 4),
        (13, north, 3), ( 8, west, 2)
    ], [
        ( 8, north, 0), (10, south, 0), (12, north, 4), ( 5, south, 1),
        ( 5, west , 3), ( 4, east , 4), ( 3, east , 3), ( 3, west , 1),
        ( 5, south, 3)
    ], [
        (11, west , 1), ( 4, north, 2), ( 4, south, 0), ( 3, west , 3),
        ( 3, east , 1), (12, north, 2), ( 5, west , 3), (12, west , 4),
        ( 3, east , 1), (10, north, 2), ( 4, south, 4)
    ], [
        (12, east , 2), ( 4, east , 0), ( 3, south, 1), ( 4, west , 4),
        ( 5, east , 1), ( 3, south, 3), ( 5, east , 3), (13, west , 3),
        ( 4, north, 4), ( 6, north, 0), ( 4, south, 4)
    ], [
        (15, west , 1), ( 4, south, 4), ( 4, east , 2), ( 7, west , 3),
        ( 8, east , 2), ( 4, north, 2), ( 4, east , 4), ( 3, south, 1),
        ( 9, south, 1), ( 4, south, 2)
    ]
]


def solve_all():
    letters = {}
    for i, board in enumerate(boards):
        print("starting board {}".format(i))
        r, x, y = solve_board(board)
        letters[x, y] = chr(ord('@') + r)

    print("final answer: {}".format(
        ''.join(letters[x, y] for y in (-1, 5) for x in range(5))))


if __name__ == '__main__':
    # solve_all()
    solve_board(boards[4], display=True)
