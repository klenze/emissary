#!/usr/bin/python3
# Some things like Statues, Church of the Wild outcomes, Professions
# are difficult to change.
#
# Actions which depend on them will require a specific ingredient
# Meta: <Choice name>: <Choice value>
# Here, we write actions to generate these.
# If you have that choice, you can generate them for free.
# (action cost=0).
# Otherwise, you can generate them from Meta: Impossible, e.g.
# not at all. (action cost=\infty). This is mainly to keep the main
# program from complaining about missing sources for these "items"
#
# If any choice value is set to "*", all options will be made available
#
import generators
import sys
from  read_char import *
choices_options={
    # see actions/antisocial.txt
    "Antisocial":["Alt Oppressor",           # willing to dupe alts, etc
                  "Correspondant Oppressor", # a correspondant alt provides a steady stream of flame-proof missives
                  "Multi Alt Oppressor",     # have multiple alts sending you names in Gant
                  "Mass Alt Oppressor"],     # have armies of alts constantly send you Surprise Packages
    
    "Profession":["Licentiate",
                  "Correspondent",
                  "Monster-Hunter",
                  "Crooked-Cross",
                  "Midnighter",
                  "Notary"],
    "Club":["The Parthenaeum",
            "The Young Stags' Club",
            "The Clay Tailor Club",
            "Sophia's"],
    "Completed Ambition":["Light Fingers!",
                          "Heart's Desire!",
                          "Nemesis!",
                          "Bag a Legend!"],
    "Ambition Items":["A False-Star of your Own",
                      "A Kitten-Sized Diamond, Liberated from the Mountain"],
    "Ealing Garden Statue":["Sinning Jenny", "Feducci",
                            "Jovial Contrarian", "Virginia",
                            "Tentacled Entrepreneur", "Yourself"],
    "Ealing Station Space":["Lounge", "Shop", "Chapel", "Clinic", "Notary"], 
    "Jericho Locks Statue":["Dean of Xenotheology", "Bishop of Southwark",
                            "Bishop of St Fiacre's", "Yourself"],
    "Magistracy Statue":["Gracious Widow", "Clay Highwayman", "Yourself"],
    "Station VIII Statue":["anything"], # no specific branches

    "Burrow-Infra-Mump Statue":["St Augustine", "Custom-Made Saint",
                                "St Hildegard", "Yourself"],
    # ^^ No 'yourself, bishop' option (FATE)
    "A Church in the Wild":["Anglican", "Wild", "Counter-Church", "Hell"],
    "Moulin Statue":["Clio, Muse of History",
                     "Yourself, Preeminent Archaeologist",
                     "Yourself, Ambassador to the Khanate",
                     "Yourself, Legendary Zee-Captain"],
    }

f=open("actions/_gen_choices.txt", "w")
generators.preamble(f)
for k, v in choices.items():
    if k not in choices_options:
        print("Ignored unknown choices key %s. Valid keys are %s."%(k, choices_options.keys()))
        continue
    if type(v)==list:
        for v1 in v:
            if v1 not in choices_options[k]:
                print('Invalid choices value for key "%s": List item "%s". Valid list items are %s. Item will be ignored.'%(k, v1, choices_options[k]))
    elif v!="*" and v!=None and v not in choices_options[k]:
        print('Invalid choices value for key "%s": "%s". Valid keys are None, "*" or any of %s.'%(k, v, choices_option[k]))
        print("Setting to None for now")
        choices[k]=None
for k,v in choices_options.items():
    if k not in choices:
        choices[k]=None
    f.write("# === Choice: %s (with option \"%s\") ===\n"%(k, choices[k]))
    for c in v+["any"]:
        name="Choice: %s: %s"%(k, c)
        f.write("Get %s\n"%name)
        f.write("  Action Cost: 0\n")
        cs=choices[k]
        f.write("  You've gained 1 x %s\n"%name)
        if cs==c or cs=="*":
            continue
        if type(cs)==list and c in cs:
            continue
        if c=="any" and cs!=None:
            continue
        f.write("  You've lost   1 x Meta: Impossible\n")
