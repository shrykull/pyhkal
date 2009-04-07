#!/usr/bin/env python
# -*- coding: utf-8 -*-

from modules import IRCBotMod
from datetime import time
from utils import file2obj, obj2file
from random import randint

class RandquoteMod(IRCBotMod):
    regexpattern = r':(.+)!.+ PRIVMSG {0} :(.+)'
    quotepercentage = 2
    def __init__(self,head,filename):
        IRCBotMod.__init__(self,head)
        #this module has to be limited to the channel due to the possibility of quoting admin logins etc.
        self.regexpattern = self.regexpattern.format(head.mainchannel)
        self.handleInput = self.handler
        self.filename = filename
        try:
            self.quotedict = file2obj(self.filename)
        except IOError:
            self.quotedict = {}
    def rehashlist(self):
        return [self.filename]
        
    def handler(self,matchlist):
        if ((randint(0,100) < self.quotepercentage) or (matchlist[0] not in self.quotedict)):
            self.quotedict[matchlist[0]] = quote(matchlist[0],time(),matchlist[1])
            obj2file(self.quotedict,self.filename)

class quote(object):
    def __init__(self,nick,time,quotestring):
        self.nick = nick
        self.time = time
        self.quotestring = quotestring
