#!/usr/bin/python3
import sys,os
if os.path.dirname(sys.argv[0])==".":
    raise Exception("Please run this script from the parent directory.")
sys.path+=[".", "./sim/"]
