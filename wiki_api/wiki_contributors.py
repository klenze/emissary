#!/usr/bin/python3
#
# Cite all contributors to fallenlondon.wiki, as required by CC-BY-SA.
#
import requests

# new wiki, new API. Special:ListUsers does not use the API any more.
# However, 

url="https://fallenlondon.wiki/w/api.php"

params={"action":"query",
        "list":"allusers",
        "format":"json",
        "aulimit":"500",
        "auwitheditsonly":1,
         }


session=requests.Session()
users=[]
start=None
params['aufrom']=""
while True:
    print("fetching users starting from %s"%params['aufrom'])
    reply=session.get(url, params=params).json()
    users+=list(map(lambda n:n['name'],
                           reply['query']['allusers']))
    if  "continue" in reply:
        print("continuing with %s"%reply["continue"])
        params.update(reply["continue"])
    else:
        break
print(users)

users=sorted(users)
f=open("wiki_contributors_%s.txt"%"fallenlondon.wiki", "w")
f.write("The following users have contributed to fallenlondon.wiki:\n")
list(map(lambda u: f.write(" %s\n"%u), users))
f.close()
