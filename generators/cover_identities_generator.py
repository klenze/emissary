#!/usr/bin/python3
import generators
import sys
from functions import *
from read_char import *
problist=[] # for fencing identities, see below.

f=open("actions/_gen_cover_identities.txt", "w")
generators.preamble(f)
f.write("Develop your cover identity more deeply (to 2)\n")
f.write("  You've gained 1 x Meta: Cover Identity: Elaboration 2\n")
for i in range(3,11):
    prob=broad(attributes["Shadowy"],150+10*(i-1), None) # not simplified for readability
    problist.append(prob)
    f.write("Develop your cover identity more deeply (to %d)\n"%i)
    f.write("  You've lost   %0.2f x Meta: Cover Identity: Elaboration %d\n"%(prob, i-1))
    f.write("  You've gained %0.2f x Meta: Cover Identity: Elaboration %d\n"%(prob, i))
    if (1-prob)>0:
        f.write("  Suspicion is increasing… (+%0.2f CP)\n"%((1-prob)*3))
for aspect, skill, descr in [("Nuance",    "Bizarre", "Endow your cover identity with eccentricities"),
                             ("Witnesses", "Dreaded", "Make sure your cover identity has been observed "
                              "in the right quarters"),
                             ("Credentials", "Respectable", "Credential your cover identity")]:
    f.write("#\n# %s (%s (%d))\n#\n" %(aspect, skill, attributes[skill]))
    for i in range(1, 7):
        prob0=narrow(attributes["A Player of Chess"], 4+(i-1), None)
        prob1=narrow(attributes[skill], 6+(i-1), None)
        prob=prob0*prob1
        problist.append(prob)
        f.write(descr+" (to %d)\n"%i)
        f.write("# prob=%0.2f (chess) * %0.2f (%s) = %0.2f\n"%(prob0, prob1, skill, prob))
        if (i>1):
            f.write("  You've lost   %0.2f x Meta: Cover Identity: %s %d\n"%(prob, aspect, i-1))
        f.write("  You've gained %0.2f x Meta: Cover Identity: %s %d\n"%(prob, aspect, i))
        if (1-prob)>0:
            f.write("  Suspicion is increasing… (+%0.2f CP)\n"%((1-prob)*3))
# Okay, now for fencing identities
# Each point of elaboration, nuance, witnesses, credentials increases the reward
# Fencing takes one action, so in principle, we want big identities to keep this cost down
# OTOH, as the probabilities to succeed get lower, boosting these identity aspects takes
# more actions. Furthermore, it also takes more actions to compensate Suspicion accrued in
# failed rolls.
# The following is only strictly correct for fencing tieless identities, as we do not consider
# the cost for getting the favour, which is typically at least one action and might be
# argued to be considerable higher.
#
# We assume we always succeed for the first level of Elaboration, so:
fence_items  =1     # 1 item gained
fence_actions=2.0   # 1 action for elaboration 1, one to fence id

for prob in sorted(problist, reverse=True):
    # we need 1/prob tries, on average
    # we will accrue 3*(1/prob - 1 ) CP suspicion which we will have to compensate
    acost=1/prob + 3*(1/prob - 1 ) * costs["CP Loss: Suspicion"]
    print("comparing %d / %0.2f to %0.2f (prob=%0.2f)"%(fence_items, fence_actions,1.0/acost, prob))
    if fence_items / fence_actions < 1.0/acost:
        # ok, items/action rate is improved
        fence_items+=1
        fence_actions+=acost
    else:
        break
for item, ties, fav in [ ("Bottle of Broken Giant 1844", "tieless", None),
                         ("Thirsty Bombazine Scrap", "Surface-tied", "The Great Game"),
                         ("Touching Love Story", "Bazaar-tied", "Society"),
                         ("Sworn Statement", "Dispossessed-tied", "Urchins")]:
    f.write("Build and fence %s identity\n" % ties)
    f.write("# Build elaboration, nuance, witnesses, credentials while total success\n"
            "# probability is larger than %0.2f\n"%prob)
    f.write("# action cost includes suspicion reduction here.\n")
    f.write("  Action Cost: %0.2f\n" % fence_actions)
    f.write("  You've gained %d x %s\n"%(fence_items,item))
    if fav:
        f.write("  You've lost 1 x Favours: %s\n"%fav)
