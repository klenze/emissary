#!/usr/bin/python3 -i

from functools import partialmethod, partial
import inspect
from copy import deepcopy
import types
from functions import *
from typish_enum import *

from char import attributes as attr
#
# state based simulation for actions with complex dependencies, e.g. hunting in Parabola
# 
# For brevity, we want to use lambda expressions to describe state transitions.
# Lamemtably, lambda expressions are limited to expressions, not statements,
# so we can't just do multiple member assignments to update the state.
# So, we will use the fluent interface pattern


def build_state_type(name, members):
    def set_member_val(obj, membername, allowed_values, newval):
        if allowed_values:
            setattr(obj, membername, enum_class(membername, allowed_values)(newval))
        else:
            setattr(obj, membername, newval)
        return obj
    def add_member_val(obj, membername, delta, negative="negative ok"):
        setattr(obj, membername, getattr(obj, membername)+delta)
        assert negative in ["negative ok", "non-negative"], "Illegal value for parameter neg."
        if negative!="negative ok" and getattr(obj, membername)<0:
            setattr(obj, membername, 0)
        return obj
    def add_menace_cost(obj, menace, delta):
        if delta<0:
            raise ValueError("This method is not meant for menace reduction!")
        obj.add_actions(delta*attr["CP Loss: "+menace])
        return obj
    members=dict(members)
    # actions should generally specified as actioncost and not added explicitly
    # in the lambda expression
    # is is ok to use add_actions() to specify an additional item/CP cost
    # on success or failure. (see add_$menace below)
    members["actions"]=0
    # Note that the actions field is only stored set in the state during the apply
    # step, otherwise, it is piecewise tracked in the callgraph. 

    # This one is hacky: tells a broad check to use a second chance
    # works only if the state is passed as the third argument to broad call
    # this framework is responsible to test for action dependence and add costs
    # done this way to keep the lambda expressions in action definitions simple
    # Should never be set by an actions lambda expression
    members["_second"]=[False, True]
    d=dict()
    
    for k in members:
        # Somehow, a straightforward lambda does not capture k.
        # This is why C++ has capture by value or reference. 
        # whatever, partial works.
        if type(members[k])==list:  # an enum like construct with limited allowed values
            allowed=members[k]
        else: # No value restriction. 
            allowed=None # no check for allowed
            d["add_"+k]=(partialmethod(add_member_val,k))
        d["set_"+k]=(partialmethod(set_member_val,k,allowed))
    d["add_by_name"]=partialmethod(add_member_val)
    d["set_by_name"]=partialmethod(set_member_val)
    for menace in ["Wounds", "Scandal", "Nightmares", "Suspicion"]:
        d["add_"+menace.lower()]=partialmethod(add_menace_cost, menace)
    d["memberlist"]=list(filter(lambda k: k!="_steps" and "k!=second", members))
    def hash(self):
#        print("hashing %s"%self.__class__.memberlist)
        return sum(map(lambda k: k.__hash__() ^ getattr(self, k).__hash__(), self.__class__.memberlist ))
    d["__hash__"]=hash
    def equal(self, other):
#        print(members)
        for k in self.__class__.memberlist:
#            a=getattr(self, k)
#            b=getattr(other, k)
            if getattr(self, k) != getattr(other, k):
#                print(a, b, a!=b, a==b)
                return False
        return True
    d["__eq__"]=equal
    def init(self):
#        print("init: self=%s"%type(self))
        for k,v in members.items():
            if type(members[k])==list:
                setattr(self, k, enum_class(k, v)(v[0])) # initialize with first as default
            else:
                setattr(self, k, v)
            #print("init %s to %s"%(k,v))
    d["__init__"]=init
    d["copy"]=lambda self:deepcopy(self)
    def strrep(self):
        s=""
        for k in members:
            if getattr(self, k):
                s+="%s: %s, "%(k, getattr(self, k))
        return "%s{%s}"%(name,s)
    d["__str__"]=strrep
    d["__repr__"]=strrep
    def clean_actions(self):
        self.set__second(False)
        res=self.actions
        self.actions=0
        return res
    d["_clean_actions"]=clean_actions
    res=type(name, (), d)
    return res

class action():
    """A class suitable to represent any action. changes is a method taking a state and returning
       a list of tuples(float, state). The argument state must be copied if used in multiple list entries!"""
    def __init__(self, storylet, name, changes, valid=lambda state:True, actioncost=1):
        self.storylet=storylet
        self.name=name
        self._valid=valid
        self._changes=lambda s:changes(s.copy().add_actions(self.actioncost))
        self.actioncost=actioncost
    def allowed(self, state):
        # for now, we assume that we are in a fixed storylet which we can not exit
        return self.storylet==state.storylet and self._valid(state)
    def apply(self, state):
        return self._changes(state)
    def __repr__(self):
        return "[%s]"%self.name

def prune(outcomes):
    """Returns flattened outcome list with states with zero (or low) probability removed"""
    res=[]
    for p, oc in outcomes:
        if type(oc)==list:
            for p2, oc2 in prune(oc):
                res.append((p*p2, oc2))
        else:
            res.append((p, oc))
    return filter(lambda a:a[0]>1e-4, res)
class ca(action): # aka check action
    """A class for an action which depends on the result of a skill check, with one success and one failure case"""
    @staticmethod
    def check_action(check, succ, fail, state):
        prob=check(state)
        return prune([(prob, succ(state.copy())), (1.0-prob, fail(state.copy()))])
    def __init__(self, storylet, name, check, succ, fail, valid=lambda state:True, actioncost=1):
        self.check=check
        changes=partial(ca.check_action, check, succ, fail)
        action.__init__(self, storylet, name, changes, valid, actioncost)

always=lambda s:[(1.0, s)]
win_goal=lambda s:always(s.add_goal(1.0).set_storylet(None))
fail_goal=lambda s:always(s.set_storylet(None))

if __name__=='__main__':
    d={"scouting":0, "quarry":[None,"warbler"]}
    print("testing simulation system")
    state=build_state_type("state", d)
    x=state()
    x.set_quarry("warbler")
    y=x.copy()
    print("copied state is identical  (True):", x==y)
    print("initial quarry is warbler (True): ",  x.quarry=="warbler")
    try:
        x.set_quarry("cat") # You can't hunt cats in Parabola, obviously
        raise Exception("Successfully assigned illegal value. This is bad.")
    except ValueError:
        pass
    try:
        x.quarry=="cat" # You can't even test for equality
        raise Exception("Successfully tested against illegal value. This is bad.")
    except ValueError:
        pass

    x.set_scouting(2)
    x.add_scouting(2)
    x.add_nightmares(50)
    print(x)
    print(x.__hash__())
    testaction=ca("Lost in Strange Lands", "Apply your own knowledge (fake option with rare success)",
                  # check is a function mapping a state to a floating point variable:
                  check=lambda s: narrow(attr["Glasswork"], 8 + s.scouting),
                  # succ is a special case here: a list of tuples (prob, state):
                  # (notice the copy() calls!).
                  # See fail for simpler default
                  succ=lambda s: [(0.9, s.copy().add_scouting(10)), (0.1, s.copy().add_scouting(20))],
                  # fail is the default case: just one outcome on failure
                  fail=lambda s: s.add_scouting(1))
    print(list(testaction._changes(y)))
    print(y)


def default_goal(s):
    """Evaluates the results of final states, or returns 0 otherwise"""
    if s.storylet!=None:
        return None
    else:
        res=(float(s.goal),s.actions)
        #         print("res=%s,%s"%res)
        return res

def optimize(state, actions, processing=None, best_options=None, goal=default_goal, steps=8, logdepth=0, startsteps=None):
    """brute force search: returns a tuple, expected goal"""
    # stupid but reasonably effective. Not efficient, though.
    # the number of actions spent to reach a state is irrelevant for checks used in a state.
    # as we want to keep a dict of as few as possible states, we require state.actions to be zero
    # the caller should track additional costs to reach that state and add them.
    # That way, we can reuse outcomes already for a different number of actions spent
    if startsteps==None:
        startsteps=steps
    calldepth=startsteps-steps
    def log(msg):
        if logdepth>0:
            print("%s%s"%(calldepth*"    ",msg))
    log("considering state %s"%(state))
    fail=(0.0, state.actions)
    g=goal(state)
    if g != None:
        log("end state: %s"%(g,))
        return g
    if state.actions!=0:
        raise ValueError("Will only calculate costs from states in which zero actions were spend.")
    if state._second:
        raise ValueError("You may not set state._second!")
    if steps<1:
        return fail # to many steps
    if not processing:
        processing=[]
    if best_options==None:
        best_options={} # map state -> (expected_goal, expected_actioncost, actiontext, steps)
    if state in best_options:
        res=best_options[state]
        if res[3]>=steps:
            # was already calculated with as many steps as we are allowed to use.
            return res[0:2]
        else:
            log("recalculation with more steps")
#    if state in processing:
#        return fail
    best=(0.0, 1.0, None, 0) # goal, actions_used, action
    outcomes=[]
    startstates=[state, state.copy().set__second(True)]
    for a in filter(lambda a:a.allowed(state), actions):
        for second_chance in range(2):
            goalsum=0   # expected value of goal after taking the action
            actionsum=0 # expected action cost for taking the action (plus downstream action costs to reach goal)
            chance_suffix= ["", " SECOND CHANCE"][second_chance]
            log(" action: %s%s"%(a.name, chance_suffix))
            if second_chance:
                if hasattr(a, "check") and a.check(startstates[1])> a.check(startstates[0]):
                    actionsum+=attr["Second Chance Action Cost"]
                else:
                    log("  ignored because not %s."%["applicable", "helpful"][hasattr(a, "check")])
                    if hasattr(a, "check"):
                        log("%f %f"%(a.check(startstates[1]), a.check(startstates[0])))
                        log(list(map(lambda a: a._second, startstates)))
                    continue # Not a failable broad check, no point to waste chance
            
            for prob, daughter in a.apply(startstates[second_chance]):
                actioncost=daughter._clean_actions() # also cleans _second
                goalc, downstreamactioncost=optimize(daughter, actions, processing, best_options, goal, steps-1, logdepth-1, startsteps)
                goalsum+=prob*goalc
                actionsum+=prob*(actioncost+downstreamactioncost)
                log("  %0.2f (%0.2f/%0.2f) %s"%(prob, goalc, actioncost+downstreamactioncost,chance_suffix))
            outcome=(goalsum, actionsum, a.name+chance_suffix)
            outcomes.append(outcome)
            if best[0]*outcome[1] < outcome[0]*best[1]: # test for goals per action improvement without divisions by zero
                best=(outcome[0], outcome[1], a, steps, second_chance)
                log(" updated best to %s"%(best,))
    for goalsum, actionsum, name in outcomes:
        log(" (%0.4f/%0.2f=%0.2f) %s"%(goalsum, actionsum, goalsum/actionsum, name))
        
    log("  final best is %s"%(best,))
    if state in best_options:
        pass # loop detected. 
    best_options[state]=best
    return best[0:2]

def print_tree(state, best, depth=0, maxdepth=6, goal=default_goal, printed=None, totalcost=0, totalprob=1.0):
    def log(msg):
            print("%s%s"%(depth*"    ",msg))
    if depth>maxdepth:
        log("...")
        return
    if printed==None:
        printed=set()
    g=goal(state)
    if g != None:
        log("Goal: %0.2f for %0.2f actions"%(g[0], g[1]+totalcost))
        return
    bestval=best[state]
#    log((totalcost, totalprob,bestval[1] ).__str__())
    log("goal=%0.4f actioncost=%0.2f %s"%(bestval[0], bestval[1]+totalcost,state))
    if state in printed:
        log(" (see above)")
        return
    printed.add(state)
    a=best[state][2]
    second=best[state][4]
    log("Take [%s]:"%(a.name+["", " SECOND CHANCE"][second]))
    state.set__second(second)
    for prob, daughter in a.apply(state):
        actioncost=daughter._clean_actions()
        log("  p=%0.2f [absolute: %0.4f] cost=%3.2f"%(prob, prob*totalprob, actioncost))
        print_tree(daughter, best, depth+1, maxdepth, goal, printed, totalcost=totalcost+actioncost, totalprob=prob*totalprob)
