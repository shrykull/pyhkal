#!/usr/bin/env python
# -*- coding: utf-8 -*-

from modules import IRCBotMod

class StfuMod(IRCBotMod):
    regexpattern = r':(.+) PRIVMSG ({0}) :.*(?:(?i)stfu)(\d*).*'
    moderated = False
    defaulttime = 1800
    def __init__(self,head):
        IRCBotMod.__init__(self,head)
        self.regexpattern = self.regexpattern.format(self.head.mainchannel.name)
        self.handleInput = self.stfutrigger
        self.timer = None
    def __del__(self):
        if self.timer:
            self.timer.cancel()
            self.timer = None
    def stfutrigger(self,matchlist,time=defaulttime):
        host = matchlist[0]
        target = matchlist[1]
        if (matchlist[2]):
            time = int(matchlist[2])
        else:
            time = self.defaulttime
        if (not self.moderated):
            self.head.sendMsg(target,"*mute*")
            self.head.sendraw("mode {0} +m".format(self.head.mainchannel.name))
            self.moderated = True
            self.timer = Timer(time,self.unmute)
            self.timer.start()
        else:
            self.head.sendMsg(target,"*unmute*")
            self.unmute()
            if self.timer:
                self.timer.cancel()
                self.timer = None
    def unmute(self):
        self.moderated = False
        self.head.sendraw(("mode {0} -m").format(self.head.mainchannel.name))

