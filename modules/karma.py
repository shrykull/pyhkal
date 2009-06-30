#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import re
from modules import IRCBotMod
from utils import obj2file, file2obj, nick

class KarmaMod(IRCBotMod):
    regexpattern = r':(.+) PRIVMSG ([\S]+) :(.+)'
    def __init__(self,head):
        IRCBotMod.__init__(self,head)
        self.handleInput = self.handler
        self.importconf()
    def exportconf(self):
        obj2file((self.karmadict),self.configfilename)
    def importconf(self):
        try:
            (self.karmadict) = file2obj(self.configfilename)
        except IOError:
            self.karmadict = {}
    def handler(self,matchlist):
        if ((matchlist[1] == self.head.mainchannel.name) and (not self.head.mainchannel.isReg(nick(matchlist[0])))):
            karmalist = re.findall(r'(\S\S+\+\+)(?:\s|$)|([\S]\S+--)(?:\s|$)|(\S\S+==)(?:\s|$)',matchlist[2])
            for x in karmalist:
                if x[0]:
                    if not x[0][:-2] in self.karmadict:
                        e = KarmaEntry(x[0][:-2])
                        self.karmadict[x[0][:-2]] = e
                    if not self.karmadict[x[0][:-2]].add(1):
                        self.head.sendMsg(matchlist[1],"Karmaspam - " + x[0][:-2] + " ist noch " + self.karmadict[x[0][:-2]].resttime() + " blockiert.")
                    else:
                        self.head.sendMsg(matchlist[1],x[0][:-2] + " hat nun einen karmawert von " + str(self.karmadict[x[0][:-2]].value))
                if x[1]:
                    if not x[1][:-2] in self.karmadict:
                        e = KarmaEntry(x[1][:-2])
                        self.karmadict[x[1][:-2]] = e
                    if not self.karmadict[x[1][:-2]].add(-1):
                        self.head.sendMsg(matchlist[1],"Karmaspam - " + x[1][:-2] + " ist noch " + self.karmadict[x[1][:-2]].resttime() + " blockiert.")
                    else:
                        self.head.sendMsg(matchlist[1],x[1][:-2] + " hat nun einen karmawert von " + str(self.karmadict[x[1][:-2]].value))
                if x[2]:
                    if not x[2][:-2] in self.karmadict:
                        e = KarmaEntry(x[2][:-2])
                        self.karmadict[x[2][:-2]] = e
                    self.head.sendMsg(matchlist[1],x[2][:-2] + " hat einen karmawert von " + str(self.karmadict[x[2][:-2]].value))
            if (karmalist != []):
                self.exportconf()
class KarmaEntry(object):
    karmaspam = datetime.timedelta(0,600)
    def __init__(self,name):
        self.name = name
        self.time = datetime.datetime(1,1,1)
        self.value = 0
    def add(self,value):
        if (datetime.datetime.now() - self.time) > self.karmaspam:
            self.value += value
            self.time = datetime.datetime.now()
            return True
        else:
            return False
    def resttime(self):
        return timedelta2string(self.karmaspam - (datetime.datetime.now() - self.time))[:-4]

def timedelta2string(r):
    r = str(r)
    while ((r[0] == "0") or (r[0] == ":")):
        r = r[1:]
    return r[0:-3]
