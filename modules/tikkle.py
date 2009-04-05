#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import re
from modules import IRCBotMod
from utils import list2string, file2obj, obj2file, nick

class TikkleMod(IRCBotMod):
    regexpattern = r':(.+) PRIVMSG ([\S]+) :(.+)'
    filename = "tikkle.dict"
    def __init__(self,head):
        IRCBotMod.__init__(self,head)
        self.handleInput = self.handler
        try:
            self.tikklers = file2obj(self.filename)
        except Exception:
            self.tikklers = {}
    def handler(self,matchlist):
        host = matchlist[0]
        target = matchlist[1] if matchlist[1] != self.head.nickname else nick(host)
        text = matchlist[2]
        t = matchlist[2].split(" ")
        if (t[0] == "tikkle"):
            if (len(t) > 2):
                if (t[1] == "hi"):
                    try:
                        r = re.match(list2string(t[2:]),"")
                    except Exception as inst:
                        self.head.sendErr(target,inst)
                    else:
                        if nick(host) in self.tikklers:
                            x = self.tikklers[nick(host)]
                            x.regex = list2string(t[2:])
                            self.head.sendNotice(nick(host),"Ok "+ x.name + ", regex updated.")
                        else:
                            self.tikklers[nick(host)] = tikkleuser(nick(host),list2string(t[2:]))
                            self.head.sendNotice(nick(host),"Welcome to tikkle.")
                if (t[1] == "friend"):
                    try:
                        if (self.tikklers[t[2]] not in self.tikklers[nick(host)].friendlist):
                            self.tikklers[nick(host)].friendlist.append(self.tikklers[t[2]])
                            self.head.sendNotice(nick(host),"Friend added.")
                        else:
                            self.tikklers[nick(host)].friendlist.remove(self.tikklers[t[2]])
                            self.head.sendNotice(nick(host),"Friend deleted.")
                    except KeyError:
                        self.head.sendNotice(nick(host),"Couldn't befriend you. Either you or " + t[2] + " isn't registered.")
                if (t[1] == "tikkle"):
                    try:
                        self.tikklers[t[2]].mailbox.append([datetime.datetime.now(),"<" + nick(host) + "> " + list2string(t[3:]) if len(t) > 2 else "*tikkle*"])
                        self.head.sendMsg(nick(host),"Message sent.")
                    except Exception:
                        self.head.sendNotice(nick(host),"Couldnt send message. Either you or the target isnt registered.")
        if nick(host) in self.tikklers:
            x = self.tikklers[nick(host)]
            if re.match(x.regex,text) and (x.name in nick(host)):
                target = nick(host)
                self.head.sendNotice(nick(host),"Hi.")
                x.greet(text)
                for y in x.friendlist:
                    self.head.sendNotice(nick(host),y.greettime.strftime("%A@%H:%M") + " <" + y.name + "> " + y.greeting)
                for y in x.mailbox:
                    self.head.sendNotice(target,y[0].strftime("%d %b@%H:%M") + " " + y[1])
                x.mailbox = []
        obj2file(self.tikklers,self.filename)
class tikkleuser(object):
    def __init__(self,name,regex):
        self.name = name
        self.regex = regex
        self.greettime = datetime.datetime.now()
        self.friendlist = []
        self.mailbox = []
        self.greeting = "tikkle hi " + str(regex)
    def greet(self,t):
        self.greettime = datetime.datetime.now()
        self.greeting = t
