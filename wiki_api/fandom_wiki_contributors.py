#!/usr/bin/python3
#
# Cite all contributors to fallenlondon.fandom.com, as required by CC-BY-SA.
#
import requests

#
# API call based on js get request sent by
# https://fallenlondon.fandom.com/wiki/Special:ListUsers

url="https://fallenlondon.fandom.com/api.php"

params={"action":"listuserssearchuser",
        "format":"json",
        "username":"",
        "groups":"",
        "contributed":"1",
        "limit":500,
        "order":"edits",
        "sort":"asc",
         }


session=requests.Session()
offset=0
users=[]
while True:
    print("fetching users starting from %d"%offset)
    params["offset"]=offset
    reply=session.get(url, params=params).json()
    users+=list(map(lambda n:n[1]['username'],
                    filter(lambda n: n[0]!="result_count",
                           reply['listuserssearchuser'].items())))
    offset+=params['limit']
    count=reply['listuserssearchuser']["result_count"]
    if (count==len(users)):
        break
    if offset>count:
        raise Exception("Fetched %d usernames out of %d?!"%(len(users), count))

users=sorted(users)
f=open("wiki_contributors.txt", "w")
f.write("The following users have contributed to fallenlondon.fandom.com:\n")
list(map(lambda u: f.write(" %s\n"%u), users))
f.close()
