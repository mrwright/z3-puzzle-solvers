from z3 import *

vars = [[Int('x %d %d' % (x, y)) for x in xrange(9)] for y in xrange(9)]

s = Solver()

# Numbers must be from 1 to 9
for x in vars:
    for y in x:
        s.add(y >= 1)
        s.add(y <= 9)

# Rows and columns must be distinct
for i in xrange(9):
    s.add(Distinct([vars[i][j] for j in xrange(9)]))
    s.add(Distinct([vars[j][i] for j in xrange(9)]))

# 3x3 squares must be distinct
for xo in xrange(0, 9, 3):
    for yo in xrange(0, 9, 3):
        s.add(Distinct([vars[xo + i][yo + j]
                        for i in xrange(3) for j in xrange(3)]))

l = [[5,3,0, 0,0,0, 0,0,0],
     [0,0,0, 0,0,5, 0,0,0],
     [0,9,8, 0,0,0, 0,6,0],

     [8,0,0, 0,6,0, 0,0,3],
     [4,0,0, 8,0,0, 0,0,1],
     [0,0,0, 0,2,0, 0,0,6],

     [0,6,0, 0,0,0, 2,8,0],
     [0,0,0, 4,1,9, 0,0,0],
     [0,0,0, 0,0,0, 0,7,0],
    ]

# Add constraints for the values we're given
for i in xrange(9):
    for j in xrange(9):
        if l[i][j] != 0:
            s.add(vars[i][j] == l[i][j])

s.check()
m = s.model()

# Pretty-print the result
vals = [[str(m[v]) for v in x] for x in vars]

for i in xrange(9):
    print (" ".join(vals[i][0:3]) + "|" +
           " ".join(vals[i][3:6]) + "|" +
           " ".join(vals[i][6:9]))
    if i % 3 == 2 and i < 8:
        print "+".join(["-" * 5] * 3)

# Just for fun, check that the solution is actually unique.
for i in xrange(9):
    for j in xrange(9):
        s.push()
        s.add(vars[i][j] != m[vars[i][j]])
        assert s.check() == unsat
        s.pop()
