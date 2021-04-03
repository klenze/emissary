#!/usr/bin/env python3.7
print("Content-type: text/html\n\n")
print("Hello <br/>")

import scipy
import cgitb
cgitb.enable()
import cgi, re
import emissary
from xml.etree import ElementTree as ET

parser=emissary.mk_parser()
form=cgi.FieldStorage( ) # keep_blank_values=True
#for k in form.keys():
#    print("%s : %s <br />"%(k,form[k].value))

args=parser.parse_form(form)
args["HTML"]=True
# complain about unknown arguments
for k in form.keys():
    if not k in args:
        raise ValueError("No such argument: k")

print("<html><head><title>The Emissary %s web interface</title></head><body>"%emissary.__version__)
print(ET.tostring(parser.mk_form(), method="html").decode("utf-8"))
print("Note: some options are disabled from the web interface.<br/>")
print("<pre>")
emissary.run(args)
print("</pre></html>")
