import re

pyprint=print

verbose=False
debug=False
genHTML=False

items=None
actions=None
def register(actions_, items_):
    global items, actions
    items=items_
    actions=actions_

def _wiki_link(name, linktext=None):
    if not linktext:
        linktext=name
    # for items, reject special stuff
    if name in actions and not actions[name].on_wiki:
        return linktext
    if name.startswith("Choice:") or name.startswith("Meta:"):
        return linktext
    name=name.replace("CP: ", "").replace("CP Loss: ", "")
    return '<a href="https://fallenlondon.wiki/wiki/%s">%s</a>'%(name, linktext)

def _githublink(action, linkname=None):
    if type(action)==str:
        action=actions[action]
    if not linkname:
        linkname=action.name
    url="https://github.com/klenze/emissary/blob/main/"
    return '<a href="%s/%s#L%d">%s</a>' %(url,action.file,
                                          action.line, linkname)

buysellre=re.compile("((?:Buy|Sell) at .*): (.*)")
def link_action(aname):
    if not genHTML:
        return aname
    res=""
    res+=_githublink(aname)
    m=buysellre.match(aname)
    if actions[aname].on_wiki:
        res+="  "+_wiki_link(aname, "(wiki)")
    elif m:
        res+="  "+_wiki_link(m.group(2), "(wiki)")
    return res

def print_details(res, key_action="", skip=0, force=False):
    if not verbose and not force:
        return
    for a,c in res.actions.items():
        if a.startswith("Parabola (Wrapper)") or a.startswith("Convert:")\
           or a.startswith("Get Choice:"):
            continue
        print("%s  %c  %2.7f %s"%(skip*" ",[" ", "*"][int(a==key_action)],c, link_action(a)))

def warn_constraints(res, dontwarn=None, skip=5):
    for l in res.losses.keys():
        if l==dontwarn:
            continue
        if l.startswith("Card:") or l.startswith("Choice"):
            l=l.replace("Card: Meta: ", "")
            print("%sNote: This grind uses %s."%(skip*" ",l))
