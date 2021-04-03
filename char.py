# note: for fake identities, it is assumed that your A Player of Chess
# skill can be archived at the same time as Shadowy or B,D,R.
# (then again, it is not like there are 10 items to boost APoC.)

attributes={
    "Shadowy":277,
    "Dangerous":261,
    "Persuasive":283,
    "Watchful":271,
    "A Player of Chess":9,
    "Bizarre":15,
    "Dreaded":10,
    "Respectable":18,
    "Artisan of the Red Science":7,
    "Glasswork": 8, #TODO"
    "Kataleptic Toxicology":7,
    "Mithridacy":7,
    "Monstrous Anatomy":7, #TODO
    "Monstrous Anatomy Studies":2,
    "Shapeling Arts":7,
   # costs for menance losses (in actions per CP)
    "CP Loss: Suspicion":0.25455,
    "CP Loss: Wounds":0.33333,
    "CP Loss: Scandal":0.40000,
    "CP Loss: Nightmares": 0.4,
    # action cost to acquire a second chance
    "Second Chance Action Cost":1,
    # echos per action, roughly (for use by hunting_generator.py)
    "EPA": 4
}

# see choice_specific_generator.py for description
# and possible values
choices={
    "Antisocial":"*",
    "Profession":"*",
    "Ealing Garden Statue": "*",
    "Jericho Locks Statue":"*",
    "Magistracy Statue":"*",
    "Burrow-Infra-Mump Statue": "*",
    "A Church in the Wild": "*",
}


