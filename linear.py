from parsing import action
from output import *

import numpy as np
np.seterr(invalid="ignore", # 0./0.
          divide="ignore")  #  x/0.
float64=np.float64
np.set_printoptions(precision=3) # for my numpy, this does not work on float64s outside arrays.

from scipy.optimize import linprog
from copy import deepcopy
import operator
from functools import reduce

np.set_printoptions(precision=3)

def filter_actions_items(actions, items, min_gains={}, allow_cards=True,
                         blocked_actions=set(), blocked_items=set()):
    selected_actions={}
    selected_items={}
    if type(blocked_items)!=set:
        blocked_items=set(blocked_items)
    blocked_items.add("Meta: Impossible")
    def add_action(a):
        if a.name in selected_actions \
           or a.name in blocked_actions\
           or bool(a.card)>allow_cards:\
            return
        losses=list(map(lambda c: c[0], filter(lambda c:c[1]<0, a.changes.items())))
        # check if we need any blocked items, if we do, this action will not be added.
        for iname in losses:
            if iname in blocked_items:
                return
        selected_actions[a.name]=deepcopy(a)
        for iname in losses:
            add_item(items[iname])
    def add_item(i):
        if i.name in selected_items:
            return
        selected_items[i.name]=i
        for aname in i.sources:
            add_action(actions[aname])
    ######################################################
    
    for iname in items.keys():
        add_item(items[iname])

    return selected_actions, selected_items

def list_mappings(l):
    """returns two dicts, element2int, int2element and length"""
    en=list(enumerate(l))
    return dict(list(map(lambda a:(a[1],a[0]), en))), dict(en), len(l)

def vector2dict(array, mapping, eps):
    res={}
    with np.nditer(array, flags=["multi_index"]) as it:
        for val in it:
            if abs(val)>eps:
                idx=it.multi_index
                if len(idx)==1:
                    idx=idx[0]
                res[mapping[idx]]=np.float64(val)
    res=dict(sorted(res.items(), key=lambda a:-a[1]))
    return res

# TODO: optimize should really be an optimizer class, so that we can reuse
# list_mappings etc between calls.
# This would also give us the opportunity to hand the user res.x and just
# have them call us if they need any of the myres dictionaries, instead of
# wasting time precalculating all of them.
def optimize(selected_actions, selected_items, min_gains, eps=1e-5, background={}):
    # our matrix is going to be sparse.
    # However, that is an optimization issue which we ignore for now.
    # actionname to number etc:
    a2n,n2a,alen=list_mappings(selected_actions.keys())
    # itemname to number etc:    
    i2n,n2i,ilen=list_mappings(selected_items.keys())
    #
    # reading the docs on scipy.optimize.linprog, it seems that the scipy
    # people decided to only provide one function which can handle both
    # covering and packing problems (and more besides).
    #
    # x will be the unknown vector 0..(alen-1) stating how often we run
    # each action.
    # as we minimize c  @ x, c will be the vector 0..(alen-1)
    # containing the action costs
    c0=np.full((alen,), np.nan)
    for a in selected_actions.values():
        c0[a2n[a.name]]=a.actioncost
    c=np.array(c0)
    # the (non-strict) constraints are given as
    #   A_ub @ x <= b_ub
    # of course, we have a covering problem, where we would like to solve a
    # constraint of the type B @ x >= d (with x, and d elementwise >=0)
    # Luckily, scipy allows b_ub to be negative, so we can select
    # A_ub=-B, b_ub = -d and call it a day.
    A_ub=np.zeros((ilen, alen,))
    for a in selected_actions.values():
        for iname, amount in a.changes.items():
            A_ub[i2n[iname]][a2n[a.name]] = - amount
    A0=np.array(A_ub) # memory is cheap
    b_ub=np.zeros((ilen,))
    for iname, amount in min_gains.items():
        b_ub[i2n[iname]]= - amount
    if len(background):
        bg=np.zeros((ilen,))
        for iname, actioncost in background.items():
            assert not iname in min_gains, "You can not grind for your background resource (%s)."%iname
            bg[i2n[iname]]=actioncost
        # the amount of items we /gain/ is -A_ub @ x
        # the amount of actions we *save* bg @ -A_ub @ x
        # the cost of that
        c+=  bg @ A_ub
        for iname in background:
            for aidx in range(0, alen):
                A_ub[i2n[iname]][aidx]=0

    # let's call scipy.optimize.linprog
    # note that method="highs" only appeared in SciPy 1.6.0.
    # The improvement over simplex makes it definitely worth
    # manually installing SciPy 1.6.1 (or later)
    
    res=linprog(c=c, A_ub=A_ub, b_ub=b_ub, method="highs")

    # now, present the results in a nice form
    
    myres=type("result", (), {})()
    myres.status=res.status
    myres.result=res

    if type(res.x)==type(None):
        if False and res.message.find("Please submit a bug report.")!=-1:
            # submitted as https://github.com/scipy/scipy/issues/13767
            f=open("bug_reproducer.py", "w")
            f.write("import numpy, scipy.optimize\n")
            for var in ["c", "A_ub", "b_ub"]:
                f.write("%s=numpy.array(%s)\n"%(var, locals()[var].tolist()))
            f.write("res=scipy.optimize.linprog(c=c, A_ub=A_ub, b_ub=b_ub, method='highs')\n")
            f.write("print('status=', res.status)\n")
            f.write("print('message=', res.message)\n")
            f.close()
            print("wrote bug reproducer file.")
        return myres
    #    if not res.success:
    #        raise Exception("linprog did not converge")
    #for idx in range(alen):
    #    if res.x[idx]<eps:
    #        res.x[idx]=0.0
    myres.actions= vector2dict(res.x, n2a, eps)

    netchanges=A0 @ (-res.x) 
    myres.changes = vector2dict(netchanges, n2i, eps)
    myres.residual= vector2dict(netchanges + b_ub, n2i, eps)

    # gross changes
    gains = - np.vectorize(lambda x:x*int(x<0))(A0) @ res.x 
    myres.gains  = vector2dict(gains, n2i, eps)
    myres.losses = vector2dict(gains - netchanges, n2i, eps)

    myres.net_action_cost  = res.fun    # with rebate from background
    myres.gross_action_cost= c0 @ res.x # without rebate from background
    return myres

def run(actions, items, min_gains, **kwargs):
    print("========================================")
    print("Running with min_gains=%s"%min_gains)
    sel_actions, sel_items=filter_actions_items(actions, items, min_gains=min_gains,**kwargs)
    print("optimizing for %d actions, %d items"%(len(sel_actions), len(sel_items)))
    res=optimize(sel_actions, sel_items,min_gains, eps=1e-2)
    print(res.actions)
    print("----------------------------------------")
    print(res.changes)
    print("----------------------------------------")
    print("res.status:", res.status)
    print("actioncost=%s"%res.net_action_cost)
    print(res.result.message)


def pos_gains(min_gains):
    """
    Returns a three-tuple. 
    First element: a dict with the negative gains (e.g. expendable items, cards, etc) from a min_gains
                   (expendable items, cards available etc) removed.
    2nd, 3rd element: Of there remains only one element in the dict, return its key and value.
                      Otherwise  None,None. 
    """
    min_gains_pos=dict(filter(lambda a: a[1]>0, min_gains.items()))
    iname=None
    amount=None
    if len(min_gains_pos)==1:
        for iname,amount in min_gains_pos.items():
            pass
    return min_gains_pos,iname,amount


def best_grinds(actions, items, min_gains, num_grinds, max_actions=None, background={}):
    """
    Find the best grinds for item given as wanted argument
    After we figure out the best grind, we remove the key action of that grind, and see what is now best. 
    """
    min_gains_pos, iname, amount=pos_gains(min_gains)
    print("Listing methods of grinding for %s."%min_gains_pos)
    if len(background):
        print("(While grinding in the background for %s)"%list(background.keys()))
    min_action_cost=None
    best_key_action=None
    blocked_actions=set()
    # The following are considered preparatory actions not central to the grind (for Scrip/Echo grinds)
    keep_prefixes=["Sell at ", "Buy at ", "Parabola: Find","Parabola (Wrapper)",
                   "Wander the", "Paint with Moonlight", "Mount the beast and lead a raid",
                   "Provide news from London", "Watch a parade",
                   "Examine ", "Sell her a human ribcage", 
                   "Drink the medicine they bring", "Sneak away from your wounds",
                   "Convert Opening a Bundle",
                   "Burly guards and porters", "Hire Strong-backed Labour", "Recruit Clay Man labour",
                   "Rumours of treasure",
                   "Seek out the music of dreams",
                   "Serve up the",
                   "Work with your expert student",
                   "Flatter the Ghillie", "Compel",
                   "Convert","Gain Favours:", "Get Choice:",
                   "Do a heist", "Prepare Newspaper"]
    for i in range(num_grinds):
        sel_actions, sel_items=filter_actions_items(actions, items, blocked_actions=blocked_actions)
        res=optimize(sel_actions, sel_items, min_gains=min_gains, eps=1e-7, background=background)
        if res.status==4:
            print("warning: linprog returned: %s"%res.result.message)
        elif res.status!=0:
            print("linprog failed. (%d: %s) Looks like there are no (further) grinds."%(res.status, res.result.message))
            break
        if iname!=None and not iname in ["Echo", "Penny", "Hinterland Scrip"]:
            # key action is the action which yields the most <item>
            key_action=sorted(res.actions.items(),
                              key=lambda a:-a[1]*actions[a[0]].changes.get(iname, 0.0))
        else:
            key_action=sorted(filter(lambda a:not reduce(operator.or_,
                                                         map(lambda p:a[0].startswith(p), keep_prefixes)),
                                     res.actions.items()),
                              key=lambda a:-a[1])
        if len(key_action)==0:
            print("Could not identify key action! Dumping all actions used")
            key_action="__invalid__"
        else:
            key_action=key_action[0][0]
        if min_action_cost==None:
            min_action_cost=res.net_action_cost
            best_key_action=key_action

        if max_actions!=None and res.net_action_cost>max_actions and i>3:
            print("All other grinds take more than %s actions."%(max_actions))
            break
        ipa=""
        if iname!=None:
            ipa="(%0.2f %s per action) "%(amount/np.float64(res.net_action_cost),iname)
        print("%3.2f actions %swith '%s':"%(res.net_action_cost, ipa, link_action(key_action)))
        warn_constraints(res)
        print_details(res, key_action,force=key_action=="__invalid__")
        blocked_actions.add(key_action)
        if key_action=="__invalid__":
            print("I do not know which action to remove. Giving up.")
            break
        print()
    return min_action_cost, best_key_action
        
def best_card_grinds(actions, items, cards, min_gains, print_all=False, background={}):
    min_gains_pos, iname, amount=pos_gains(min_gains)
    print("If we are grinding for %s drawing the following cards would decrease the number of actions we have to spend:"%min_gains_pos)
    gains=deepcopy(min_gains)
    num_avail=1000 # how many cards should we make available?  
    
    num_avail*=-1
    # negative because we modify the gains we want.
    # (negative gain requirement == algorithm may spend resource)
    
    print()
    baseres=optimize(actions, items, min_gains=gains)
    cardvalues={}
    cardvalues["* WITHOUT CARDS *"]=(0.0, 0, baseres)
    for c in cards:
        if debug:
            print("running for card %s"%c)
        cardname="Card: %s"%c
        gains.setdefault(cardname, 0)
        gains[cardname]+=num_avail # make (more) cards available
        cardres=optimize(actions, items, min_gains=gains, background=background)
        if cardres.status!=0:
                raise Exception(" Failed with msg= %s"%cardres.result.message)
        if not cardname in cardres.residual:
            raise Exception("The algorithm used up all of the cards %s we provided. try increasing num_avail?"%cardname)
        cards_used=-(cardres.residual[cardname]+gains[cardname])
        actions_saved=(baseres.net_action_cost-cardres.net_action_cost)
        
        gains[cardname]+=-num_avail # undo the above
        if gains[cardname]==0:
            del gains[cardname]

        if not print_all and ( cards_used<0.001 or actions_saved/baseres.net_action_cost <0.0001):
            continue
        cardvalues[c]=(actions_saved/cards_used, cards_used, cardres)
    fmt="%15s  %15s %15s   %s"
    print(fmt%("actions", "draws", "actions saved","cardname"))
    print(fmt%("needed",  "needed", "per draw",""))
    if (iname):
        print(fmt%("(items/action)",  "", "",""))

    print(80*"=")
    for c,(v,u,res) in sorted(cardvalues.items(), key=lambda a:a[1][2].net_action_cost):
        v=max(v, 0.0) # numerical issues?
        u=max(u, 0.0) 
        print(fmt%("%5.2f"%res.net_action_cost, "%4.1f"%u, "%1.6f"%v, c))
        if iname:
            print(fmt%("(%0.2f)"%(amount/res.net_action_cost), "", "", ""))
        warn_constraints(res, "Card: %s"%c, skip=len(fmt%("", "", "", " ")))
        if verbose:
            print_details(res, skip=len(fmt%("", "", "", " ")))
            print()
