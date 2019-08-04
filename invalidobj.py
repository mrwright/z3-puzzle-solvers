from z3 import ArithRef, Solver, AstRef, And, Or

# TODO: this file should probably be redone so it doesn't patch z3.
# Instead we can provide our own wrapper functions for z3's, and things
# can import them from here.

_ops = ["__add__", "__mul__", "__sub__", "__pow__", "__div__", "__mod__",
        "__le__", "__lt__", "__gt__", "__ge__", "__eq__", "__ne__"]

# TODO: can we just make Invalid a falsy object as far as z3 is concerned?
# That would avoid having to wrap And/Or (and others which we don't yet...)
class Invalid(object):
    '''
    Represents an invalid constraint, which will be discarded.
    This allows us to work without bothering with bounds checking.
    '''
    def __getattr__(self, attr):
        return Invalid()

    def __call__(self, *a, **kw):
        return Invalid()

def inner(self, other):
    return Invalid()
for op in _ops:
    setattr(Invalid, op, inner)

for op in _ops:
    orig_op = getattr(ArithRef, op)
    def make_new_op(op=op, orig_op=orig_op):
        def new_op(self, other):
            if isinstance(other, Invalid):
                return Invalid()
            return orig_op(self, other)
        return new_op
    setattr(ArithRef, op, make_new_op())

orig_add = Solver.add
def new_add(self, constraint):
    if isinstance(constraint, Invalid):
        return
    return orig_add(self, constraint)
Solver.add = new_add

def Wrap(f):
    def inner(l):
        return f([False if isinstance(x, Invalid) else x
                  for x in l])
    return inner

IAnd = Wrap(And)
IOr = Wrap(Or)

# TODO: move this particular patch elsewhere.
AstRef.__hash__ = AstRef.hash
