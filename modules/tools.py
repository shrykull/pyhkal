#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import re
from modules import IRCBotMod
from utils import nick, ident

class ToolsMod(IRCBotMod):
    regexpattern = r'(.+)'
    triggerlist = []
    def __init__(self,head):
        IRCBotMod.__init__(self,head)
        self.handleInput = self.handler
    def handler(self,text):
        elementstodelete =  []
        for x in self.triggerlist:
            if (re.match(x[2],text)):
                if (type(x[1]) == type("str")):
                    self.head.sendMsg(x[0],x[1] + re.findall(x[2],text)[0])
                else:
                    self.head.sendMsg(x[0],x[1](*re.findall(x[2],text)))
                elementstodelete.append(x)
        #two loops, to not disturb the first one <.<
        for x in elementstodelete:
            self.triggerlist.remove(x)


        if (re.match(r':(.+) (PRIVMSG|\d+) ([\S]+)(?:$| (.+))',text)):
            matchlist = re.findall(r':(.+) (PRIVMSG|\d+) ([\S]+)(?:$| (.+))',text)
            matchlist = matchlist[0]
            host = matchlist[0]
            target = matchlist[2] if matchlist[2] != self.head.nickname else nick(host)
            text = matchlist[3][1:]
            w = text.split(" ")
            if (len(w) > 1) and (matchlist[1] == "PRIVMSG"):
                if (w[0] == "whois"):
                    self.head.sendraw("whois " + w[1] + " " + w[1])
                    self.addtrigger([target,self.identhost,r'.+ 311 (?:[\S]+) (?:[\S]+) ([\S]+) ([\S]+).+'])
                    self.addtrigger([target,"Real Name: ",r'.+ 311 (?:[\S]+) .+:(.+)'])
                    self.addtrigger([target,"Authnick: ",r'.+ 330 (?:[\S]+) (?:[\S]+) ([\S]+).+'])
                    self.addtrigger([target,self.raw317reply,r'.+ 317 (?:[\S]+) (?:[\S]+) (\d+ \d+)'])
                elif (w[1] == "alive?"):
                    self.head.sendraw("whois " + w[0] + " " + w[0])
                    self.addtrigger([target,self.raw317reply,r'.+ 317 (?:[\S]+) (?:[\S]+) (\d+ \d+)'])
                elif (w[1] == "lag?"):
                    self.head.sendMsg(w[0],chr(1) + "PING " + str(time.time()) + chr(1))
                    self.addtrigger([target,self.pingreply,r':({0}[\S]+) NOTICE (?:[\S]+) :.PING ([\d\.]+).'.format(w[0])])
            elif (matchlist[1] == "PRIVMSG"):
                if (w[0] == "lag?"):
                    self.head.sendMsg(nick(host),chr(1) + "PING " + str(time.time()) + chr(1))
                    self.addtrigger([target,self.pingreply,r':({0}[\S]+) NOTICE (?:[\S]+) :.PING ([\d\.]+).'.format(nick(host))])
    def identhost(self,match):
        return "Address: " + match[0] + "@" + match[1]
    def pingreply(self,match):
        n = nick(match[0])
        t = time.time() - float(match[1])
        return n + " ping reply: " + str(int(t * 1000)) + "ms"
    def raw317reply(self,match):
        idletime = int(str(match).split(" ")[0])
        uptime = int(str(match).split(" ")[1])
        return "Idle: " + str(datetime.timedelta(seconds=idletime)) + " // On Since: " + str(time.ctime(uptime))
    def addtrigger(self,l):
        if (l not in self.triggerlist):
            self.triggerlist.append(l)
