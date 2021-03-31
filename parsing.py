
import os,re, traceback, operator
from functools import reduce

def read_category_file(fname, item2category):
    cat_name=re.match(".*/(.*).txt",fname).group(1).replace("_"," ")
    ftxt=open(fname)
    for l in ftxt:
        l=l.strip()
        if len(l)>3:
            item2category[l]=cat_name

def read_all_categories():
    res={}
    for f in filter(lambda f:f.endswith(".txt"), os.listdir("categories")):
        read_category_file("categories/"+f, res)
    return res


class action:
    def __init__(self, name, changes={}, actioncost=1, card=None, fav=False, file=None, line=None, is_buy=False):
        self.card=card
        self.fav=fav
        self.msg=None
#            name=name[6:]
        self.name=name
        self.file=file
        self.line=line
        self.is_buy=is_buy
        if type(changes)!=dict:
            raise Exception("Legacy call detected!")
        self.changes=dict(changes) # WTF: default argument is reused between calls, so we have to copy it.
        # TIL: this is called "mutable default argument" and widely considered evil.
        self.actioncost=actioncost
    def add_change(self, name, amount):
        self.changes.setdefault(name, 0.0)
        self.changes[name]+=amount

    def register(self, actions, cards=None):
        if self.card:
            if self.card in cards:
                cards[self.card].append(self.name)
            else:
                cards[self.card]=[self.name]
            cardname="Card: %s"%self.card
            if cardname not in self.changes:
                self.add_change(cardname, -1)
        if self.name in actions:
            raise Exception("An action named %s is already registered!"
                            %self.name.__repr__())
        actions[self.name]=self

class item:
    def __init__(self, name, category=None):
        self.name=name
        self.category=category
        self.sources=[]
        self.sinks=[]


floatpat="([0-9]+(?:[.][0-9]*)?)"
nrange=re.compile("%s(?:[^0-9.]+%s)?"%(floatpat, floatpat)) 
def parse_num_range(str):
    r=nrange.match(str)
    if not r:
        raise Exception(" '%s' is not an amount or range"%str)
    if (not r.group(2)):
        return float(r.group(1))
    else:
        return 0.5*(float(r.group(1))+float(r.group(2)))
        
def read_actions(fname, actions, item2category, cards):
    cur_cat=""
    # these classes handle the parsing of indented lines, e.g. gains, losses, action costs etc
    class ParseChanges:
        uptore=re.compile("(.*) (\(up to .*\))")
        regex=re.compile(".*You've (gained|lost) +(.*) x (.*)")
        @staticmethod
        def resolve(action, res):
            sign=pow(-1, res.group(1)=="lost")
            item=res.group(3).strip()
            if ParseChanges.uptore.match(item):
                item=ParseChanges.uptore.match(item).group(1)
            if item.startswith("Favours:"):
                action.fav=True
                item2category[item]="Favours"
            amount=parse_num_range(res.group(2))
            cur_action.add_change(item, sign*amount)
            if item.startswith("Meta:"):
                item2category[item]="_meta"
            if item.startswith("Choice:"):
                item2category[item]="_choice"
#            cat=cur_cat
#            if (cat!="" and not item.startswith("Favours:")):
#                if not item in item2category:
#                    item2category[item]=cur_cat
#                elif item2category[item]!=cur_cat:
#                    raise Exception( "Error: item %s is in category %s, will not add to category %s"%(item, item2category[item],cur_cat))
    class ParseCPChanges:
        regex=re.compile("(?:.*[.]png )?(.*) is (dropping|increasing)[^0-9]*(%s) CP.*"%nrange.pattern)
        menaces=["Wounds", "Scandal", "Suspicion", "Nightmares", "Tracklayers' Displeasure", "In Corporate Debt", "Seeing Banditry in the Upper River"]
        @staticmethod
        def resolve(action, res):
            item="CP: "+res.group(1).strip()
            sign=pow(-1, res.group(2)=="dropping")
            amount=parse_num_range(res.group(3))
            if res.group(1).strip() in ParseCPChanges.menaces:
                # we do not generally consider side effects "gains" to be bad.
                # in this case, they are. Thus, we track the negative amount of the negative quality. all confused?
                item="CP Loss: "+res.group(1).strip()
                sign*=-1
                item2category[item]="_Menace Loss"
            else:
                item2category[item]="_Change Points"
            action.add_change(item, sign*amount)
    class ParseActionCost:
        regex=re.compile(".*Action Cost: ?%s"%floatpat)
        @staticmethod
        def resolve(action, res):
            action.actioncost=float(res.group(1))
    class ParseCardName:
        regex=re.compile("Card: (.*)")
        @staticmethod
        def resolve(action, res):
            if cur_action.card:
                raise Exception("multiple card names encountered!")
            action.card=res.group(1).strip()
    indented_parsers=[ParseChanges, ParseCPChanges, ParseActionCost, ParseCardName]
    f=open(fname)
    cur_action=None
    line=0
    for l in list(f) + ["EOF"]:
        try:
            line+=1
            l=l.rstrip()
            l=l.replace(b"\xe2\x80\xa6".decode("utf-8"), "...") # U+2026
            l=l.replace(b"\xef\xbf\xbc".decode("utf-8"), "")
            if l.find("Collapse")!=-1:
                raise Exception("Someone pasted a heading from the wiki without cleaning up.")
            if l.startswith('\xef\xbf\xbc'):
                l=l[3:]
            if len(l)==0:
                continue
            if l[0]=='#':
                continue
            if l[0]=='+':
                cur_cat=l[1:].strip()
                continue
            if l[0]!=' ': # next action
                if reduce(operator.or_, map(lambda p: bool(p.regex.match(l)), indented_parsers)):
                    raise Exception("Non-indented line matches format of an indented line. Are you sure you did not forget a blank in the beginning?")
                if cur_action:
                    cur_action.register(actions, cards)
                cur_action=action(l, file=fname, line=line) # last action in file is registered when l=="EOF"
            else: # indented
                matched=0
                l=l.strip()  # get rid of indention blanks
                if l[0]=="#": # indented comment
                    continue
                for p in indented_parsers:
                    res=p.regex.match(l)
                    if res:
                        p.resolve(cur_action, res)
                        matched+=1
                if matched>1:
                    raise Exception("Indented line matched multiple regex. This is a bug, please report!")
                elif matched==0:
                    raise Exception("Could not parse indented line.")
        except Exception as e:
            print("Error while parsing file %s, line %d: %s"%(fname, line, l))
            print(e.args[0])
            traceback.print_exc()
            exit(-1)

def read_all_actions(actions, item2category, cards):
    for f in filter(lambda f:f.endswith(".txt") and not f.startswith("."),
                    os.listdir("actions")):
        read_actions("actions/"+f, actions, item2category, cards)
    
def items_from_actions(actions, cards, item2category):
    """returns a set of all items mentioned in actions. also creates actions to gain favours."""
    f=open("output/item_warnings.txt", "w")
    items={}
    for a in actions.values():
        for itemname, amount in a.changes.items():
            iteminst=items.setdefault(itemname, item(itemname, item2category.get(item, None)))
            if amount>0:
                iteminst.sources.append(a.name)
            elif amount<0:
                iteminst.sinks.append(a.name)
            else:
                print("Warning: Action %s uses %f of item %s"%(a.name, amount, itemname))
    useless=[]
    for i in items.values():
        if len(i.sources)==1 and i.sources[0].startswith("Buy at ")\
           and len(i.sinks)==0:
            # ignore bazaar items not required for anything
            useless.append(i.name)
            continue
        if (i.name.startswith("Card:")):
            continue
        if len(i.sources)==0 and i.name!="Meta: Impossible":
            print("No source for '%s'"%i.name)
            f.write("No source for '%s'\n"%i.name)
        elif len(i.sources)+len(i.sinks)==1 \
             and not i.name.startswith("Choice:"):
            f.write("Orphaned item: '%s'\n"%i.name)
        elif len(i.sinks)==0:
            f.write("No sinks for item: '%s'\n"%i.name)
    if len(useless):
        print("The following items do not have any uses: %s"%useless)
    return items
