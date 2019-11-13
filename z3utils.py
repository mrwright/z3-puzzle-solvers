from z3 import Const, ForAll, Function, If

_unique_id = 0


def lift_to_solver(solver, *sorts):
    """
    Lift a Python function that accepts and returns Z3 expressions into the
    Z3 solver. This is useful if the function is called many times and
    repeating its body would add bloat to the problem.

    Args:
        solver: a z3.Solver instance
        *sorts: the sorts of the arguments and returned value

    Example:
        >>> @lift_to_solver(solver, IntSort(), IntSort(), BoolSort())
        ... def are_equal_mod_3(x, y):
        ...    return x % 3 == y % 3
    """
    def decorator(fn):
        global _unique_id
        solver_fn = Function(fn.__name__, sorts)
        args = [Const('${}_{}'.format(i, _unique_id), s)
                for i, s in enumerate(sorts[:-1])]
        solver.add(ForAll(args, solver_fn(*args) == fn(*args)))
        _unique_id += 1
        return solver_fn
    return decorator


def Switch(var, *branches):
    """
    Emulate a switch statement in Z3. Equivalent to a sequence of chained If
    expressions.

    Example:
        >>> (Switch(a + b,
        ...        (1, when_one),
        ...        (2, when_two),
        ...        (None, when_otherwise)) ==
        ...    If(a + b == 1, when_one,
        ...       If(a + b == 2, when_two, when_otherwise)))

    Note that the condition in the final branch is *not* checked. By
    convention, this can be None, or if a member of a finite domain is being
    exhaustively matched, this can be the final value in the domain--either
    way, the Z3 expression produced is the same.
    """
    result = branches[-1][1]
    for i in range(len(branches) - 2, -1, -1):
        l, r = branches[i]
        result = If(var == l, r, result)
    return result
