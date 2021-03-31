import functools
import itertools


# list versions of map and reduce. (lmap, lreduce)
def listify(f):
    globals()["l"+f.__name__]=lambda *args,**kwargs:list(f(*args, **kwargs))

listify(map)
listify(functools.reduce)
listify(itertools.product)


# s is the state here for calls from simulation actions, or
# None otherwise.
# Because we absolutely need the state for simulations, it
# is no longer default assigned to None.

def broad(attr, difficulty, s):
    if difficulty<=0:
        return 1.0
    if s and hasattr(s, "_second") and s._second:
        return 1-pow(1-broad(attr, difficulty, None), 2)
    return min(1.0, 0.6*attr/difficulty)
cbroad=lambda attr, diff:functools.partial(broad, attr, diff)

def narrow(attr, difficulty, s):
    if difficulty<=0:
        return 1.0
    return max(0.1, min(1.0, (attr+6-difficulty)/10.0))
cnarrow=lambda attr, diff:functools.partial(narrow, attr, diff)
def float_eq(a, b):
    eps=0.001
    abs(a-b)<eps
    
def print_eval(s):
    fail=False
    try:
        print("%s evaluates to %s"%(s, eval(s)))
    except Exception as e:
        print("%s raised '%s' when evaluated!"%(s,e))
        fail=True
    if fail:
        # raise again (hopefully) without the "while handling exception" stuff
        eval(s) 
