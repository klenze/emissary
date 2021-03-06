#!/usr/bin/python3
import sys,os
if os.path.dirname(sys.argv[0])==".":
    raise Exception("Please run this script from the parent directory.")
sys.path+=[".", "./sim/"]
import read_char

def preamble(f):
    f.write("## autogenerated by %s\n"%sys.argv[0].replace("./", ""))
    f.write('## char_hash: %s\n'%read_char.char_hash)
    f.write("#  Do not edit!\n")
    f.write("##  Generated for attributes:\n")
    for k,v in read_char.attributes.items():
        f.write("#  %30s: %2d\n"%(k,v))
    for k,v in read_char.choices.items():
        f.write("#  %30s: %s\n"%(k,v))
    
