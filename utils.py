#!/usr/bin/env python
# -*- coding: utf-8 -*-

import cPickle
import time
from time import strftime
from random import random

def obj2file(obj,filename):
    f = open(filename,"w")
    cPickle.dump(obj,f)
    f.close()

def file2obj(filename):
    f = open(filename,"r")
    return cPickle.load(f)
    f.close()

def nick(host):
    return host.split("!")[0]

def ident(text):
    return list2string(text.split("!")[1].split("@")[0],"")

def list2string(l,s = " "):
    r = ""
    for x in l:
        r = r + s+ x
    return r[len(s):]

def rand(min = 1,max = 100):
    return int(round(min + random() * (max - min)))
