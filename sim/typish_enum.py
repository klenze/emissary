#!/usr/bin/python3 -i
from functools import partialmethod, partial
import inspect
from copy import deepcopy
import types

enum_classes={}
# setting setattr(self, "__eq__", ...) in __init__ tends not to get called by ==.
# so instead, we use type() again to construct the whole class on the fly

def enum_class(membername, allowed_values):
    """Returns an object of a custom class which can only be compared against a limited amount of values"""
    if membername in enum_classes:
        return enum_classes[membername]
    
    def _test(self, v):
        if hasattr(v, "value"):
            v=v.value
        if v not in self.allowed_values:
            raise ValueError("Value %s is not allowed for member %s. Allowed values are: %s"
                             %(v, self.membername, self.allowed_values))
        return v
    def init(self, val):
#        print("init called with %s %s %s %s"%(self, val, allowed_values, membername))
        self.value=self._test(val)
    def opcall(self, name,*args):
#        if name!="__str__":
#            print("opcall called with name=%s self=%s args=%s\n\n"%(name, (self), args))
        if name=="__bool__":  # str has no __bool__
            return bool(self.value)
        return  getattr(self.value, name)(*map(self._test, args))
    d={"allowed_values":allowed_values,
       "membername":membername,
       "_test":partialmethod(_test),
       "__init__":partialmethod(init)
    }
    for op in [ "__ne__", "__eq__", "__cmp__", "__repr__", "__str__", "__bool__", "__hash__"]:
        d[op]=partialmethod(opcall, op)
    res=type("enum for %s"%membername, (), d)
    enum_classes[membername]=res
    return res

if __name__=="__main__":
    foo_t=enum_class("foo", ["Foo", "Bar"])
    x=foo_t("Foo")
    print(x)
    print(x==("Baz"))
