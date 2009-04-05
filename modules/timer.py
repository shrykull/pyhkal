#!/usr/bin/env python
# -*- coding: utf-8 -*-

from modules import IRCBotMod
from utils import nick

class TimerMod(IRCBotMod):
    regexpattern = r':(.+) PRIVMSG ([\S]+) :.*timer:(\d+):(.*)'
    def __init__(self,head):
        IRCBotMod.__init__(self,head)
        self.handleInput = self.handler
    def handler(self,matchlist):
        host = matchlist[0]
        target = matchlist[1] if matchlist[0] != self.head.nickname else nick(host)
        time = matchlist[2]
        text = matchlist[3]
        if (int(time) > 0):
            self.head.sendNotice(nick(host),"Timer started.")
            Timer(int(time),self.head.sendMsg,(target,"timed message by " + nick(host) + ": " + text)).start()
