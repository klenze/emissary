#!/usr/bin/python3
from functions import dict_hash

try:
    from custom_char import *
except:
    print("Note: custom_char.py does not exist. Using default_char.py")
    from default_char import *


def _hash_char():
    return dict_hash(attributes, dict_hash(choices)).hexdigest()[0:40]

char_hash=_hash_char()

try:
    import _gen_costs as costs_file
except:
    print("Note: _gen_costs.py does not exist. Using default_costs.py")
    import default_costs as costs_file

if hasattr(costs_file, "char_hash") and costs_file.char_hash != char_hash:
    print("Note: _gen_costs.py is not up to date. Consider regenerating it.")

costs=costs_file.actioncosts
