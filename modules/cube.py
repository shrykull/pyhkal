#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import re
from modules import IRCBotMod

class CubeMod(IRCBotMod):
    regexpattern = r':(.+) PRIVMSG ([\S]+) :(.+)'
    cubers = []
    def __init__(self,head):
        IRCBotMod.__init__(self,head)
        self.handleInput = self.handler
    def handler(self,matchlist):
        host = matchlist[0]
        target = matchlist[1]
        text = matchlist[2]
        if target == self.head.mainchannel:
            if (text[0:2] == ".3"):
                s = re.findall("(\d+)",text)
                num = 25
                if (len(s) > 1):
                    num = int(s[1])
                if ((num > 50) or (num < 1)):
                    num = 1
                self.head.sendMsg(target,"Try " + self.cubescramble(num))
            elif (re.match(r'.*\*cube.*',text)):
                x = cubetimer(host)
                self.cubers.append(x)
            else:
                i = 0
                for x in self.cubers:
                    if (host == x.name):
                        self.head.sendMsg(target,host.split("!")[0] + ": " + x.elapsed())
                        del self.cubers[i]
                    i += 1

    def cubescramble(self,num):
        axis = [["U","D"],["R","L"],["F","B"]]
        movemods = ["2","'"]
        lastAxis = 5
        lastMoveOnLastAxis = 5
        blockedAxis = 5
        curAxis = 5
        curMoveOnCurAxis = 5
        scramble = ""
        for x in xrange(0,num):
            curAxis = rand(0,2)
            while (curAxis == blockedAxis):
                curAxis = rand(0,2)
            if (lastAxis != curAxis):
                curMoveOnCurAxis = rand(0,1)
                blockedAxis = 5
            else:
                curMoveOnCurAxis = 1 if (lastMoveOnLastAxis == 0) else 0
                blockedAxis = curAxis
            lastMoveOnLastAxis = curMoveOnCurAxis
            lastAxis = curAxis
            scramble += axis[curAxis][curMoveOnCurAxis]
            if (rand(0,1)):
                scramble += movemods[rand(0,1)]
            scramble += " "
        return scramble

class cubetimer(object):
    def __init__(self,name):
        self.dt = datetime.datetime.now()
        self.name = name
    def elapsed(self):
        r = str(datetime.datetime.now() - self.dt)
        while ((r[0] == "0") or (r[0] == ":")):
            r = r[1:]
        return r[0:-3]
