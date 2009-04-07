#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
from modules import IRCBotMod
from utils import ident, list2string
from time import strftime

class DecideMod(IRCBotMod):
    regexpattern = r':(.+) PRIVMSG ([\S]+) :!decide (.+)'
    def __init__(self,head):
        IRCBotMod.__init__(self,head)
        self.handleInput = self.handler

    def handler(self,matchlist):
        self.head.sendMsg(matchlist[1],"Du solltest dich " +
                          self.regexdecide(list2string(matchlist[2:]),
                                           num=asciicount("*!*" + ident(matchlist[0]))) +
                          " entscheiden.")

    def regexdecide(self,text, num):
        matchlist = sorted(re.findall(r'(".+?"|(?<!").+?(?!"))(?:\s|$)',text))
        c = asciicount(text) + asciicount(strftime("%d/%m/%Y"))
        if len(matchlist) > 1:
            return "für " + matchlist[(c + (num % 100)) % len(matchlist)]
        else:
            if ((c  % (num % 100)) % 2 + 1) == 1:
                return "dafür"
            else:
                return "dagegen"

def asciicount(text):
    r = 0
    for x in text:
        r += ord(x)
    return r
