#!/usr/bin/env python
# -*- coding: utf-8 -*-

from modules import IRCBotMod
import datetime
from utils import file2obj, obj2file
from random import randint

class RandquoteMod(IRCBotMod):
    regexpattern = r':(.+)!.+ PRIVMSG {0} :(.+)'
    quotesaveprobability = 2
    quotepostprobability = 50
    def __init__(self,head):
        IRCBotMod.__init__(self,head)
        #this module has to be limited to the channel due to the possibility of quoting admin logins etc.
        self.regexpattern = self.regexpattern.format(head.mainchannel.name)
        self.handleInput = self.handler
        self.importconf()
    def rehashlist(self):
        return [self.filename]
    def exportconf(self):
        obj2file((self.quotedict),self.configfilename)
    def importconf(self):
        try:
            (self.quotedict) = file2obj(self.configfilename)
        except IOError:
            self.quotedict = {}
    def cleandatabase(self):
        #delete every quote in db which is older than 1 week
        for x in self.quotedict:
            if ((self.quotedict[x].time + datetime.timedelta(7)) < datetime.datetime.now()):
                self.quotedict.pop(x)
                
    def handler(self,matchlist):
        firstword = matchlist[1].split(" ")[0]
        #cleans the database every now and then
        if (randint(0,100) < 2):
            self.cleandatabase()
        #i dont want "lol" or "hmm" to be quoted so i want at least 3 words.
        if (len(matchlist[1].split(" ")) > 2):
            if ((randint(0,100) < self.quotesaveprobability) or (matchlist[0] not in self.quotedict)):
                self.quotedict[matchlist[0]] = quote(matchlist[0],datetime.datetime.now(),matchlist[1])
                self.exportconf()
        #on highlight post randquote - eventually.
        if (firstword in self.head.mainchannel.nicklist):    
            if ((randint(0,100) < self.quotepostprobability) and (matchlist[0] in self.quotedict)):
                quote = self.quotedict[firstword]
                self.head.sendMsg(self.head.mainchannel.name,'<' + quote.nick + '> ' + quote.quotestring)
            

class quote(object):
    def __init__(self,nick,time,quotestring):
        self.nick = nick
        self.time = time
        self.quotestring = quotestring
