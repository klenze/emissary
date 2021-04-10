#!/usr/bin/python3
import sys
import generators
from sim import * # simulation 'framework'
from math import ceil

is_monster_hunter="Profession" in char.choices\
    and char.choices["Profession"] in ["*", "Monster-Hunter"]

quarry_ferocities={
    "warbler":6, 
    "albatross":8,
    "storm-bird":14, 
    "terror_bird":20,
    "auroch":18,
    "bear":16,
    "shark":18
}

destination_ferocities={
    "iron_warehouse":6,
    "townhouse":10,
    "weakness":10, # aka conversation
    "evidence":12,
    "hiding_place":14,
}

d={"storylet":["Lost in Strange Lands", "Seeking a Mirror from the Far Side", "Pursuing the Parabolan Quarry", "Face (Quarry) in its (Quarry Home)",
               "Embattled with Parabolan Quarry", None],
   "quarry":[None]+list(quarry_ferocities.keys()),
   "destination":[None]+list(destination_ferocities.keys()),
   "search_nest":False, 
   "scouting":0,
   "ferocity":0,
   "goal": 0.0,
   "partly_pursued":False
}
#
# Theoretically, scouting is not reset by succeeding Sneak forward
# In practice, it becomes irrelevant at that point, so we set zero to keep
# the number of states we have to consider small.
# 
actions=[
    #
    # Lost in Strange Lands
    #
    ca("Lost in Strange Lands", "Push onward",
       valid=lambda s: s.quarry and not s.partly_pursued,
       check=lambda s: broad(attr["Dangerous"], 180+20*(s.ferocity-s.scouting), s),
       succ=lambda s: s.set_storylet("Pursuing the Parabolan Quarry"),
       fail=lambda s: s.add_nightmares(1).add_scouting(2)),
    ca("Lost in Strange Lands", "Sneak forward",
       valid=lambda s: s.destination,
       check=lambda s: broad(attr["Shadowy"], 180+20*(s.ferocity-s.scouting), s),
       succ=lambda s: s.set_storylet("Seeking a Mirror from the Far Side").set_scouting(0),
       fail=lambda s: s.add_nightmares(2).add_scouting(2)),
    ca("Lost in Strange Lands", "Continue towards (Quarry Home)",
       valid=lambda s: s.partly_pursued, 
       check=lambda s: broad(attr["Dangerous"], 180+20*(s.ferocity-s.scouting), s),
       succ=lambda s: s.set_storylet("Face (Quarry) in its (Quarry Home)").set_scouting(0),
       fail=lambda s: s.add_nightmares(1).add_scouting(2)),
    ca("Lost in Strange Lands", "Apply your own knowledge",
       check=lambda s: narrow(attr["Glasswork"], 8 + s.scouting, s),
       succ=lambda s: s.add_scouting(10),
       fail=lambda s: s.add_scouting(1)),
    # "Claim the aid of Fingerkings" gives less scouting and costs more actions than
    #  the glass gazette, so it is not worth it unless you want to produce fingerking-possessed pets
    action("Lost in Strange Lands", "Make use of a Glass Gazette",
           changes=lambda s:[(1.0, s.copy().add_scouting(8))],
           actioncost=2), # gazettes are 1 action with church of the wild
    # Helpfully, the Airs specific options all cost more than 1 action in dreams CP (?)
    # while only giving marginally more scouting than the Gazette (10 instead of 8),
    # so we can safely ignore them (and the headache to implement the Air-dependency)
    
    #
    # Seeking a Mirror from the Far Side
    #
    ca("Seeking a Mirror from the Far Side", "Steal from Mr Iron's warehouse",
       valid=lambda s: s.destination== "iron_warehouse",
       check=lambda s: broad(attr["Shadowy"], 220, s),
       succ=win_goal,
       fail=lambda s: s.add_wounds(2).set_storylet(None)),
    ca("Seeking a Mirror from the Far Side", "Learn what you can",
       valid=lambda s: s.destination=="townhouse",
       check=lambda s: broad(attr["Shadowy"], 220, s),
       succ=win_goal,
       fail=lambda s: s.add_wounds(2).set_storylet(None)),
    action("Seeking a Mirror from the Far Side", "Case the place",
           valid=lambda s:s.destination=="weakness",
           changes=win_goal),
    action("Seeking a Mirror from the Far Side", "Make the evidence against yourself vanish",
           valid=lambda s:s.destination=="evidence",
           changes=win_goal),
    action("Seeking a Mirror from the Far Side", "Identify a location",
           valid=lambda s:s.destination=="hiding_place",
           changes=win_goal),
    #
    # Pursuing the Parabolan Quarry
    #
    action("Pursuing the Parabolan Quarry", "Await the Parabolan Quarry at its Lair",
           changes=lambda s:always(s.set_storylet("Lost in Strange Lands").set_partly_pursued(True))),
    action("Pursuing the Parabolan Quarry", "Trick the Parabolan Quarry into chasing you",
           changes=lambda s:always(s.set_storylet("Embattled with Parabolan Quarry"))),
    ca("Pursuing the Parabolan Quarry", "Wound Quarry",
       valid=lambda s:is_monster_hunter,
       check=lambda s:narrow(attr["Monstrous Anatomy"], ceil(s.ferocity/2.0)+1, s),
       succ=lambda s:s.add_ferocity(-attr["Monstrous Anatomy"]-1),
       fail=lambda s:s.add_wounds(2).add_nightmares(2)),
    action("Pursuing the Parabolan Quarry", "Bait the Focused Albatross",
           valid=lambda s:s.quarry=="albatross",
           changes=lambda s:always(s.set_storylet("Embattled with Parabolan Quarry")
                                   .add_ferocity(-3).add_actions(0.4*costs["Echo"]))),
    action("Pursuing the Parabolan Quarry", "Trap the bear", # Honey option is the same, + 1 action for 250 honey
           valid=lambda s:s.quarry=="bear",
           changes=lambda s:always(s.set_storylet("Embattled with Parabolan Quarry")
                                   .add_ferocity(-5))),
    #
    # Face (Quarry) in its (Quarry Home)
    #
    action("Face (Quarry) in its (Quarry Home)", "Strike (Quarry) down here in its (Quarry Home)",
           changes=lambda s:always(s.set_storylet("Embattled with Parabolan Quarry"))),

    # Technically, the nest search option is not valid for all quarries.
    # As we only use it to generate a Meta: ... items, we will just not use these for anything
    action("Face (Quarry) in its (Quarry Home)", "Search (Quarry Home)",
           valid=lambda s:s.search_nest,
           changes=win_goal),
    #
    # Embattled with Parabolan Quarry
    #
    action("Embattled with Parabolan Quarry", "Recapture the (Quarry)",
           valid=lambda s: not s.search_nest and (s.quarry == "terror_bird" or s.quarry=="auroch"),
           changes=win_goal),
    # Capture/Kill (Quarry) actually have different failure outcomes per quarry
    ca("Embattled with Parabolan Quarry", "Capture the Seven-Throated Warbler",
       valid=lambda  s:not s.search_nest and s.quarry=="warbler",
       check=lambda s:broad(attr["Dangerous"], 100+20*s.ferocity, s),
       succ=win_goal,
       fail=lambda s:s.add_wounds(5).add_nightmares(1).set_storylet("Lost in Strange Lands")),
    
    ca("Embattled with Parabolan Quarry", "Capture the Focused Albatross",
       valid=lambda  s:not s.search_nest and s.quarry == "albatross",
       check=lambda s:broad(attr["Dangerous"], 100+20*s.ferocity, s), 
       succ=win_goal,
       fail=lambda s:s.add_wounds(5).set_storylet("Pursuing the Parabolan Quarry")), 
    
    ca("Embattled with Parabolan Quarry", "Capture the Storm-bird",
       valid=lambda  s: not s.search_nest and s.quarry == "storm-bird",
       check=lambda s:broad(attr["Dangerous"], 100+20*s.ferocity, s),
       succ=win_goal,
       fail=lambda s:s.add_wounds(3).add_nightmares(3).set_storylet("Pursuing the Parabolan Quarry")), #TODO: check storlet change?
    
    ca("Embattled with Parabolan Quarry", "Capture the Honey-Mazed Bear",
       valid=lambda  s: not s.search_nest and s.quarry == "bear",
       check=lambda s:broad(attr["Dangerous"], 100+20*s.ferocity, s),
       succ=win_goal,
       fail=lambda s:s.add_wounds(5).set_storylet("Pursuing the Parabolan Quarry")),

    ca("Embattled with Parabolan Quarry", "Kill the Pinewood Shark",
       valid=lambda s: not s.search_nest and s.quarry=="shark",
       check=lambda s:broad(attr["Dangerous"], 100+20*s.ferocity, s),
       succ=win_goal,    
       fail=lambda s:s.add_wounds(5).set_storylet("Pursuing the Parabolan Quarry")),
    
    ca("Embattled with Parabolan Quarry", "Ambush the (Quarry) at close range",
       check=lambda s:narrow(attr["Monstrous Anatomy"], round(s.ferocity/3)+2, s),
       succ=lambda s:s.add_ferocity(-2-attr["Monstrous Anatomy Studies"]),
       fail=lambda s:s.add_wounds(2)),
]

state_t=build_state_type("states", d)
#start=state_t().set_destination("Mr Iron's Warehouse").set_ferocity(6)

#start=state_t().set_destination("evidence").set_ferocity(6)
#if start.quarry:
#    print("bad")
#best={}

#optimize(start, actions, best_options=best)
#print_tree(start, best)
f=open("actions/_gen_parabola_hunting.txt", "w")
generators.preamble(f)

def write_meta(target, actioncost, gain):
    f.write("Parabola: %s\n"%target)
    f.write("  Action Cost: %0.2f\n"%actioncost)
    f.write("  You've gained %0.2f x Meta: Parabola: %s\n"%(gain, target))
    if target in quarry_ferocities and is_monster_hunter:
        f.write("  You've lost 1 x Choice: Profession: Monster-Hunter")
    
for quarry, ferocity in  quarry_ferocities.items():
    for nest in range(2):
        best={}
        start=state_t().set_quarry(quarry).set_ferocity(ferocity)\
            .set_search_nest(nest)
        msg="%s %s"%(["Hunt", "Search Nest of"][nest], quarry)
        print("\n\n=== %s ===\n" %msg)
        res=optimize(start, actions, best_options=best, steps=12, logdepth=0)
        write_meta(msg, res[1], res[0])
        print(res[0], res[1], res[1]/res[0])
        print_tree(start, best, maxdepth=5)
        
for destination, ferocity in  destination_ferocities.items():
    start=state_t().set_destination(destination).set_ferocity(ferocity)
    msg="%s %s"%("Find", destination)
    print("\n\n=== %s ===\n"%(msg))
    res=optimize(start, actions, best_options=best, steps=10, logdepth=0)
    write_meta(msg, res[1], res[0])
    #        print(best)
    print(res[0], res[1], res[1]/res[0])
    print_tree(start, best, maxdepth=5)
f.close()
