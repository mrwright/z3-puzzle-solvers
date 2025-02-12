from z3 import Const, ForAll, Function, If, is_algebraic_value, is_false, is_int_value, is_rational_value, is_true

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

def as_tuple(model, val):
    tuple_size = val.sort().constructor(0).arity()
    return tuple(interpret(model.eval(val.sort().accessor(0, i)(val))) for i in range(tuple_size))

def interpret(val):
    """
    Try to turn a Z3 expression of a simple type into a Python value of an appropriate type, if possible
    :param val:
    :return:
    """
    if is_true(val):
        return True
    elif is_false(val):
        return False
    elif is_int_value(val):
        return val.as_long()
    elif is_rational_value(val):
        return val.numerator_as_long()/val.denominator_as_long()
    elif is_algebraic_value(val):
        approx = val.approx(20)
        return approx.numerator_as_long()/approx.denominator_as_long()
    else:
        # oh well, we tried
        return val

