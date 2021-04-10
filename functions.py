import functools
import itertools
import hashlib

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


def dict_hash(d, hashobj=None):
    """
    Calculate a uniqueish hash value for a dictionary.
    Disregards item order. 
    Assumes that str method is injective
    (so {"x":True} and {"x":"True"} might end up having the same hash value)

    Since Python 3, python defaults to seeding hash with a per-process random value. 
    This can be turned of by setting some env var before starting the process, but not within
    a running process (which would also destroy all hash-based collections). 
    Still a hash(obj, seed=None) which allows overriding the seed would have been nice. 
    
    Instead, we use hashlib, which is overkill but whatever.
    """
    if hashobj==None:
        hashobj=hashlib.sha3_512()
    for k,v in sorted(d.items(),
                      key=lambda a:a[0]):
        hashobj.update(bytes("%s:%s\n"%(str(k),str(v)), "ascii"))
    return hashobj

def git_hash():
    try:
        fname="HEAD"
        for i in range(3): # per Yudkowsky's Law of Ultrafinite Recursion
            rev=open(".git/%s"%fname).read().strip()
            if rev.startswith("ref: "):
                fname=rev[5:]
            else:
                return rev
    except None:
        return None
