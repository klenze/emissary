#!/usr/bin/python3 
import operator, traceback, sys, os
from functools import reduce
from pprint import pprint
from argparse2form import FormArgumentParser
import argparse
try:
    import difflib
except:
    print("Could not import difflib. You will not get suggestions for misspelled item names.")


__version__="0.1.1"
# local imports
import read_char as char
import default_costs
# stats for your character.
# note that you will manually have to run

import parsing
# parsing of actions/*.txt
# includes action class

import linear
import output

def initialize():
    print("initializing...")
    global items, actions, cards, item2category, parser
    item2category= parsing.read_all_categories()
    cards={} # dict: card name to list of action names
    actions={} # dict: name to action object
#    parsing.action("Grind Echos",
#                   {"Penny":100*char.attributes["EPA"]})\
#           .register(actions)
#    parsing.action("Grind for %0.2f SPA"%char.attributes["SPA"],
#                   {"Hinterland Scrip":char.attributes["SPA"]})\
#           .register(actions)
    parsing.read_all_actions(actions=actions,
                     item2category=item2category,
                     cards=cards)
    items=parsing.items_from_actions(actions, cards, item2category)


def mk_parser():
    parser=FormArgumentParser(sys.argv[0],\
                              formatter_class=argparse.ArgumentDefaultsHelpFormatter,\
                              add_help=False)
    parser.add_argument("-h", "--help",
                        action='store_true',
                        help="Show argument help text")
    parser.add_argument("-g", "--grind", metavar="'Hinterland Scrip'",
                        type=str, default=None,
                        help="Item to grind for. Acceptable options are 'Echo' or any other of --list-items.")
    parser.add_argument("-F", "--force-action", metavar="'actionname'",
                        type=str, default=None,
                        help="Advanced: Force the use of a specific action. Replaces -g."
                        " Only useful in conjunction with -b.")
    parser.add_argument("-L", "--list-items", 
                        action='store_true',
                        help="List all items the program knows about.")
    parser.add_argument("-A", "--grind-all-items", noweb=True,
                        action='store_true',
                        help="Try to grind all items (except for internal ones like Card, Meta, Choice or -b)")
    parser.add_argument("-W", "--write-costs", noweb=True,
                        action='store_true',
                        help="Write _gen_costs.py containing char-specific action costs required by generators")
    parser.add_argument("-n", "--num", metavar="num",
                        type=float, default=1,
                        help="Number of items we have to grind.")
    parser.add_argument("-m", "--max", metavar="limit",
                        type=int, default='15', webmax=5,
                        help="Write out at most limit grinds")
    parser.add_argument("-c", "--cards", noweb=True,
                        action='store_true',
                        help="Show the effect of cards on grind. (Note that searching for grinds with -C enabled is mostly a better alternative.)")
    parser.add_argument("-a", "--all", 
                        action='store_true', noweb=True,
                        help="For -c, even print cards which were not picked.")
    parser.add_argument("-d", "--debug", 
                        action='store_true',
                        help="Print debug output.")
    parser.add_argument("-v", "--verbose", 
                        action='store_true',
                        help="Be verbose, print details about each grind.")
    parser.add_argument("-f", "--favours", 
                        action='store_true',
                        help="Assume that we can indefinitely grind favours at one favour per action")
    parser.add_argument("-C", "--cards-available", 
                        action='store_true',
                        help="Assume that we can indefinitely draw any cards we need")
    parser.add_argument("-X", "--no-gift-cards", 
                        action='store_true',
                        help="Do *not* make the CtD and SiC cards freely available")
    parser.add_argument("-H", "--HTML", noweb=True,
                        action='store_true',
                        help="Write output in something akin to HTML (for debugging or web interface)")
    parser.add_argument("-b", "--background", metavar="item",
                        type=str, default=None,
                        help="Assume you will also spend lots of actions grinding for item, so any action which gains item as a side effect will save you some actions. (try Penny or 'Hinterland Scrip'")
    return parser

def parse_args(lst):
    return vars(mk_parser().parse_args(lst))


def single_item_dict(iname, num):
    if not iname in items:
            raise ValueError("I do not know of any item '%s'."
                             " Did you mean any of: %s"\
                             %(iname,
                               difflib.get_close_matches(iname, items)))
    return {iname:num}

def add_sources(d, args, quiet=False):
    def log(*args):
        if not quiet:
            print(*args)
    num_avail=100000 # no one item should need more than that many cards/favs to grind any item
    num_avail*=-1
    # negative because we modify the gains we want.
    # (negative gain requirement == algorithm may spend resource)
    if not args["no_gift_cards"]:
        d["Card: A Gift from the Capering Relicker"]=num_avail
        d["Card: Secrets and Spending"]=num_avail
    addcards=[]
    if args["cards_available"]:
        log("(We assume that any cards can be drawn indefinitely at will, including favour grinding cards like connected pets.)")
        addcards=cards.keys()
    elif args["favours"]:
        log("(We assume that favours are freely available for 1 action per favour.)")
        addcards= filter(lambda c:c.startswith("Meta: Favours:"), cards.keys())
    for c in addcards:
        cardname="Card: %s"%c
        d[cardname]=num_avail
    return d

def run(args):
    output.debug=args["debug"]
    output.verbose=args["verbose"]
    output.genHTML=args["HTML"]
    initialize()
    output.register(actions, items)
    if args["help"]:
        mk_parser().print_help()
        return
    if args["list_items"]:
        print("Known items:\n")
        # TODO: sort by category etc
        for i in sorted(items.keys()):
            print(i)
        return

    background={}
    if args["background"]!=None:
        num_bg=100.0
        print("Calculating action cost per background item %s"%args["background"])
        res=linear.optimize(actions, items, min_gains=add_sources(single_item_dict(args["background"], num_bg), args, quiet=True))
        assert res.status==0, "Background item grind search failed!"
        eps=0.0001 # adjust the background grind to be slightly preferrable to the best available grind
        background[args["background"]]=(1-eps)*res.gross_action_cost/num_bg
        print("Will assume that the best grind for background item %s takes %0.4f actions per %s (%0.4f %s per action)"
              %(args["background"], res.gross_action_cost/num_bg, args["background"], num_bg/res.gross_action_cost, args["background"]))
    if args["force_action"]:
        if args["force_action"] not in actions:
            raise ValueError("I do not know of any action '%s'."
                             " Did you mean any of: %s"\
                             %(args["force_action"],
                               difflib.get_close_matches(args["force_action"], actions)))
        assert not args["grind"], "Bad mix of options"
        args["grind"]="Meta: Force"
        actions[args["force_action"]].changes["Meta: Force"]=1
    
    if args["grind_all_items"] or args["write_costs"]:
        assert args["grind_all_items"] ^ args["write_costs"], "Bad mix of options"
        assert not args["cards"], "Bad mix of options"
        assert not args["grind"], "Bad mix of options"
        if args["grind_all_items"]:
            fname="_gen_allcosts.py"
            ilist=sorted(items.keys())
        else:
            fname="_gen_costs.py"
            ilist=default_costs.actioncosts.keys()
        min_gains=add_sources({}, args)
        actioncosts=dict(background)
        num=args["num"]
        for i in ilist:
            if i.startswith("Favours:") or i.startswith("Meta:") or i==args["background"] \
               or (i in ["Echo", "Penny"] and args["background"] in  ["Echo", "Penny"]) \
               or i.startswith("Choice:") or i.startswith("Card:"):
                continue
            print(i)
            assert not i in min_gains, "%s is already in min_gains"%i
            min_gains[i]=num
            acost,action=linear.best_grinds(actions, items, min_gains=min_gains, num_grinds=1, background=background)
            if acost!=None:
                acost/=num
            actioncosts[i]=acost/num
            del min_gains[i]
        f=open(fname, "w")
        f.write("# generated by %s, do not edit\n"%" ".join(sys.argv))
        f.write("# (see exact call for infos on background and card inclusion settings.)\n")
        f.write("char_hash = '%s'\n"%char.char_hash)
        f.write("actioncosts=%s\n"%actioncosts)
        f.close()
        print("results were written to %s"%fname)
        return
    if not args["grind"]:
        print("Nothing to do.")
        return
    min_gains=add_sources(single_item_dict(args["grind"], args["num"]), args)
    if args["cards"]:
        linear.best_card_grinds(actions, items, cards, min_gains, print_all=args["all"], favours=args["favours"], background=background)
    elif args["grind"]:
        linear.best_grinds(actions, items, min_gains=min_gains, num_grinds=args["max"], max_actions=None, background=background)

if __name__=="__main__":
    args=parse_args(sys.argv[1:])
    run(args)
