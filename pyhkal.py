#!/usr/bin/env python
# -*- coding: utf-8 -*-
# File: pykhal.py

import asyncore, asynchat
import re, socket
import sys
from random import randint
from threading import Timer
from utils import *

class IRCBot(asynchat.async_chat):
    MODLIST = {}
    performqueue = []
    def __init__(self, server="irc.quakenet.org", port=6667,ident="nexus", password="", nickname="FAiLHKAL" + str(randint(0,9999999)), mainchannel="#ich-sucke", createSocket=True):
        if createSocket:
            asynchat.async_chat.__init__(self)
        self.set_terminator("\n")
        self.data = ""
        self.newmainchannelnicklist = {}
        
        if (not self.importconf()):
            self.server = server
            self.port = port
            self.ident = ident
            self.password = password
            self.nickname = nickname
            self.mainchannel = Channel(mainchannel)
            #overwrites the stuff above, but leaves perform as it is
            self.exportconf()
        
        #provides self to mods on rehash, else MODLIST would be empty and xyzzy
        for x in self.MODLIST:
            self.MODLIST[x].head = self

        self.initcommands = [
            "USER " + self.ident + " " + self.ident + " " + self.ident + " :Python-TiHKAL",
            "PASS " + self.ident + ":" + self.password,
            "NICK " + self.nickname
            ]

        self.spamqueue = SpamQueue(5,5)
        if createSocket:
            self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
            self.connect((self.server,self.port))

    def handle_connect(self):
        print "(INFO) Connected to ", self.server + ":" + str(self.port)
        Timer(5,self.runinitcommands,()).start()
        pass
    def runinitcommands(self):
        for x in self.initcommands:
            self.sendraw(x)
    def handle_expt(self):
        print "(INFO) Connection to ", self.server + ":" + str(self.port), "failed."
        self.close()

    def collect_incoming_data(self, data):
        self.data = self.data + data

    def found_terminator(self):
        data = self.data
        if data.endswith("\r"):
            data = data[:-1]
        self.data = ""
        print "( >> )", data
        if re.match(":(.+) PRIVMSG (.+) :(.+)", data):
            self.onText(*re.match(":(.+) PRIVMSG (.+) :(.+)", data).group(1,2,3))
        for x in self.MODLIST:
            l = re.findall(self.MODLIST[x].regexpattern,data)
            if (l):
                try:
                    self.MODLIST[x].handleInput(l[0])
                except Exception as inst:
                    self.printErr(str(self.MODLIST[x]),inst)
        if re.match("PING :",data):
            self.sendraw("PONG " + data.split(" ")[1])
            return
        if re.match(":(\S+) MODE (\S+) (\S+)(.+?)",data):
            self.onMode(*re.match(":(\S+) MODE (\S+) (\S+)(.+?)",data).group(1,2,3,4))
            return
        if re.match(":(.+) NICK :(.+)",data):
            self.onNick(*re.match(":(.+) NICK :(.+)",data).group(1,2))
            return
        if re.match(":(.+) JOIN :(.+)",data):
            self.onJoin(*re.match(":(.+) JOIN (.+)",data).group(1,2))
            return
        if re.match(":.+ (\d\d\d) (.+)",data):
            self.onRawNumeric(*re.match(":.+ (\d+) (.+)",data).group(1,2))
            return
        if re.match(".*NOTICE .+:.+host.+", data):
            self.runinitcommands()
            return
        if re.match(":(.+) PRIVMSG (.+) :(.+)", data):
            return

    def addModule(self, constructor,params=None):
        if (not params):
            module = constructor(self)
        else:
            module = constructor(self,*params)
        self.MODLIST[module.__class__.__name__] = module
        
    def exportconf(self):
        obj2file((self.server,self.port,self.ident,self.password,self.nickname,self.mainchannel.name,self.performqueue),"pyhkal.conf")
        for x in self.MODLIST:
            try:
                x.exportconf()
            except AttributeError:
                pass #kind of ugly but needed as not every module has a conf file to export
    def importconf(self):
        try:
            (self.server,self.port,self.ident,self.password,self.nickname,self.mainchannelname,self.performqueue) = file2obj("pyhkal.conf")
            self.mainchannel = Channel(self.mainchannelname)
            return True
        except IOError:
            (self.server,self.port,self.ident,self.password,self.nickname,self.mainchannel,self.performqueue) = ("",0,"","","",Channel(""),[])
            return False
        
    def sendraw(self, string):
        if (len(string.split(" ")) > 1):
            if ((string.split(" ")[0].upper() == "NAMES") and (string.split(" ")[1] == self.mainchannel.name)):
                self.prepareNicklist()
        if (string):
            self.push(string + "\r\n")
    
    def onMode(self,host,channel,flags,props):
        print "(MODE)", host, channel, ":", flags, props
        #basic approach, send a NAMES request everytime something changes with the nicklist
        if (channel == self.mainchannel.name):
            self.sendraw("NAMES " + self.mainchannel.name)
        
    
    def onNick(self,oldhost,newnick):
        if (nick(oldhost) == self.nickname):
            self.nickname = newnick
            self.hostname = newnick + "!" + oldhost.split("!")[1:]
        print "(NICK)", nick(oldhost), "=>", newnick
        
    def onJoin(self,host,channel):
        print "(JOIN)", host, "=>", channel
        if ((nick(host) == self.nickname) and (channel == self.mainchannel.name)):
            self.prepareNicklist()
        if (channel == self.mainchannel.name):
            self.mainchannel.nicklist[nick(host)] = nick(host)

    def onRawNumeric(self,numeric,text):
        numeric = int(numeric)
        #adds every user in channel to the temporary nicklist-dict
        if (numeric == 353):
            chanlist = text.split(":")[1].split(" ")
            for pnick in chanlist:
                self.newmainchannelnicklist[re.findall((r'(?:[@\+]|^)(\S+)'),pnick)[0]] = pnick
        if (numeric == 366):
            self.mainchannel.setNicklistdict(self.newmainchannelnicklist)
            self.prepareNicklist()
        elif ((numeric == 376) or (numeric == 422)):
            self.sendraw("join " + self.mainchannel.name)
            for x in self.performqueue:
                self.sendraw(x)

    def onText(self, host,target,text):
        print "(P>>M)", "<" + host + "@" + target + ">", text

    def sendMsg(self,target,text):
        string = "PRIVMSG " + target + " :" + text
        print "(P<<M)", string
        self.spamqueue.add(self.sendraw,[string])

    def sendNotice(self,target,text):
        string = "NOTICE " + target + " :" + text
        print "(P<<N)", string
        self.spamqueue.add(self.sendraw,[string])

    def sendErr(self,target,inst):
        self.sendMsg(target,"err > " + str(type(inst)) + " " + str(inst.args))

    def printErr(self,name,inst):
        print "err in", name + "> " + str(type(inst)) + " " + str(inst.args)
        
    def quit(self):
        self.sendraw("QUIT :... denn #ich-sucke härter als ihr alle zusammen...")
        print "(QUIT)", "Terminating..."
        exit()
    def prepareNicklist(self):
        self.newmainchannelnicklist = {}

class Channel(object):
    def __init__(self,name):
        self.name = name
        self.nicklist = {}
    def isOp(self,nick):
        if (self.nicklist[nick][0] == '@'):
            return True
        return False
    def isVoice(self,nick):
        if (self.nicklist[nick][0] == '+'):
            return True
        return False        
    def isHalfOp(self,nick):
        if (self.nicklist[nick][0] == '%'):
            return True
        return False        
    def isReg(self,nick):
        if ((not self.isOp(nick)) and (not self.isHalfOp(nick)) and (not self.isVoice(nick))):
            return True
        return False        
    def setNicklistdict(self,nickdict):
        self.nicklist = nickdict
        
class SpamQueue(object):
    def __init__(self,pertime,initialamount):
        self.time = pertime
        self.init = initialamount
        self.counter = 0
        self.queue = []
        self.resetter = False
    def next(self):
        if ((self.queue) and (self.counter < self.init)):
            self.counter += 1
            self.do(self.queue.pop(0))
            self.next()
        elif ((self.queue) and (self.counter >= self.init)):
            self.do(self.queue.pop(0))
            Timer(self.time,self.next,()).start()
        elif (not self.queue):
            Timer(self.time * 2,self.resetcounter,()).start()
            self.resetter = True

    def add(self,func,list):
        self.queue.append((func,list))
        if ((not self.counter) or (self.resetter)):
            self.resetter = False
            self.next()
            
    def do(self,tuple):
        tuple[0](*tuple[1])

    def resetcounter(self):
        self.resetter = False
        if (not self.queue):
            self.counter = 0


def main(instance=None):
    global bot

    if instance:
        IRCBot.__init__(instance, instance.server,instance.port,instance.ident,instance.password,instance.nickname,instance.mainchannel, False)
        bot = instance
    else:
        bot = IRCBot()

    from modules.admin import AdminMod
    from modules.decide import DecideMod
    from modules.cube import CubeMod
    from modules.karma import KarmaMod
    from modules.tikkle import TikkleMod
    from modules.timer import TimerMod
    from modules.tools import ToolsMod
    from modules.stfu import StfuMod
    from modules.randquote import RandquoteMod
    from modules.factoid import FactoidMod

    bot.addModule(AdminMod)
    bot.addModule(DecideMod)
    bot.addModule(CubeMod)
    bot.addModule(KarmaMod)
    bot.addModule(TikkleMod)
    bot.addModule(TimerMod)
    bot.addModule(ToolsMod)
    bot.addModule(StfuMod)
    bot.addModule(RandquoteMod)
    bot.addModule(FactoidMod)

    asyncore.loop()

    print "reloading - asyncore dumped"
    main()

if __name__ == '__main__':
    main()
