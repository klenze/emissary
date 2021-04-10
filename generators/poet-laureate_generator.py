#!/usr/bin/python3
import sys
import generators
from functions import *
from read_char import *

f=open("actions/_gen_poet-laureate.txt", "w")
generators.preamble(f)

# this is a rather expensive check to fail, so we will always use
# second chances. Also, we will not factor in the costs to grind them,
# they are minimal compared to the A Fine Piece costs anyhow
# scandal on failure is also ignored.
class empty:
    pass
s=empty()
s._second=True

for i in range(0,21):
    prob=broad(attributes["Persuasive"],150+10*i, s)
    f.write("Submit your work for consideration (with A Poet-Laureate %d)\n"%i)
    if (i>0):
        f.write("  You've lost   %0.2f x Meta: A Poet-Laureate %d\n"%(prob, i))
    f.write("  You've gained %0.2f x Meta: A Poet-Laureate %d\n"%(prob, i+1))
    f.write("  You've lost     %2d x A Fine Piece\n"%(i+5))

