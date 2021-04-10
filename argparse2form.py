import argparse, os
from xml.etree import ElementTree as ET
pytype=type

class FormArgumentParser(argparse.ArgumentParser):
    """
    a class to generate ugly HTML forms instead out of a nice ArgumentParser
    """
    def __init__(self, *args, **kwargs):
        self.options={}
        super().__init__(*args, **kwargs)
    def parse_form(self, form):
        res=vars(self.parse_args([]))
        form=form
        for name, (node, type, default, webmax) in self.options.items():
            if name in form:
                x=form[name].value
            else:
                x=default

            if not x and default==None:
                res[name]=None
            else:
                res[name]=type(x)
            if webmax and abs(res[name])>webmax:
                raise ValueError("absolute of %s must be smaller"
                                 " or equal than %s"%(name, webmax))
            # also set that as a new default.
            input=node[1]
            if type==bool:
                if res[name]:
                    input.set("checked","1")
                else:
                    input.attrib.pop("checked", None)
            else:
                input.set("value", self._defaultstr(res[name]))
#            print("<code>")
#            print(name, res[name])
#            print(pytype(res[name]).__name__)
#            print("</code>")
        return res
    def _defaultstr(self, default):
        if default==None:
            return ""
        else:
            return str(default)

    def add_argument(self, shortname, longname, noweb=False, webmax=None,
                     **kwargs):
        super().add_argument(shortname, longname, **kwargs)
        longname=longname[2:]
        if noweb:
            return
        type=None
        type=kwargs.get("type", type)
        default=kwargs.get("default", None)
        help=kwargs.get("help", "")
        metavar=kwargs.get("metavar", "")
        if kwargs.get("action", "")=="store_true":
            type=bool
            default=0
        div=ET.Element("div", {"style":"display: table-row;"})
        label=ET.Element("label", {"for":longname, "title":help,
                                   "style":"display: table-cell;"})
        label.text=longname
        div.append(label)
        self.options[longname]=label
        input=ET.Element("input", {"name":longname, "id":longname,
                                   "value":self._defaultstr(default),
                                   "style":"display: table-cell;"})
        if type==bool:
             input.attrib.update({"type":"checkbox", "value":"1"})
             if (default):
                 input.set("checked", "1")
        elif type==int or type==float:
            input.attrib.update({"type":"number"})
            if webmax:
                input.set("min", str(-webmax))
                input.set("max",  str(webmax))
                input.set("step", ["0.001","1"][int(type==int)])
        elif type==str:
            input.attrib.update({"type":"text", "size":"100"})
        div.append(input)
        self.options[longname]=(div, type, default, webmax)
        
    def mk_form(self):
        res=ET.Element("form", {"method":"get", "style":"display: table;"})
        for name, (node, type, default, webmax) in self.options.items():
            res.append(node)
            ET.SubElement(res, "br")
        ET.SubElement(res, "input", {"type":"submit", "value":"Go"})
        return res

