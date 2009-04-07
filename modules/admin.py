#!/usr/bin/env python
# -*- coding: utf-8 -*-
    
import sys
from modules import IRCBotMod
import modules
from utils import nick

class AdminMod(IRCBotMod):
    adminhosts = []
    storage = {}
    regexpattern = r':(.+) (?:PRIVMSG|NOTICE) ([\S]+) :(!do|!py|!pydo|!auth|!rehash|spam\?)(?: (.+)|$)'
    def __init__(self,head,adminpass="defaultpass"):
        IRCBotMod.__init__(self,head)
        self.handleInput = self.handler
        self.adminpass = adminpass
        self.storage["bot"] = self.head
    def rehashlist(self):
        return [self.adminpass]
        
    def handler(self,matchlist):
        host = matchlist[0]
        target = matchlist[1] if (matchlist[1] != self.head.nickname) else nick(host)
        command = matchlist[2]
        text = matchlist[3]
        if (command == "!auth") and (text == self.adminpass):
            if (host not in self.adminhosts):
                if (self.adminhosts != []):
                    for x in self.adminhosts:
                        self.head.sendMsg(nick(x),"Master added: New admin is " + host)
                self.adminhosts.append(host)
            adminNickList = []
            for x in self.adminhosts:
                adminNickList.append(nick(x))
            self.head.sendMsg(target,"Done. Admins: " + str(adminNickList))
        if (host in self.adminhosts):
            if (command == "!do"):
                self.head.sendraw(text)
            elif (command == "!py"):
                try:
                    self.head.sendMsg(target,"eval> " + str(eval(text,globals(),self.storage)))
                except Exception:
                    try:
                        exec text in globals(), self.storage
                        self.head.sendMsg(target,"exec> Done.")
                    except Exception as inst:
                        self.head.sendErr(target,inst)
            elif (command == "!pydo"):
                try:
                    for x in eval(text,globals(),self.storage):
                        exec x in globals(), self.storage
                    self.head.sendMsg(target,"exec> Done.")
                except Exception as inst:
                    self.head.sendErr(target,inst)
            elif (command == "spam?"):
                self.head.sendraw("PRIVMSG " + target + " :" + str(len(self.head.spamqueue.queue)) + " items in spamqueue.")
            elif (command == "!rehash"):
                self.head.sendraw("PRIVMSG " + target + " :Reimporting code...",)
                if (not text):
                    #rehash the head
                    if ("pyhkal" in sys.modules):
                        sys.modules.pop("pyhkal")
                    instance = self.head
                    import pyhkal
                    instance.__class__ = pyhkal.IRCBot
                    pyhkal.main(instance)
                    # # # dont rehash mods, just rehash core # # # 
                    
                    #and rehash the mods with their new head
                    #for x in self.head.MODLIST:
                    #    #adminmod has to be rehashed last, or it loses its references while its still working
                    #    if (x != "AdminMod"):
                    #        self.rehashModule(self.head.MODLIST[str(x)])
                    #if ("AdminMod" in self.head.MODLIST):
                    #    self.rehashModule(self.head.MODLIST["AdminMod"])
                else:
                    #here you can rehash mods specifically - should be enough for now <.<
                    #TODO: !rehash All
                    self.rehashModule(self.head.MODLIST[text])
                
    def rehashModule(self,module):
        print "reloading", module, "..."
        sys.modules.pop(str(module.__module__))
        newmod = __import__(module.__module__,globals(),locals(),[module.__class__.__name__])
        constructor = newmod.__dict__[module.__class__.__name__]
        globals()[str(module.__module__)] = newmod
        self.head.MODLIST.pop(module.__class__.__name__)
        try:
            #TODO: fix this hack // simplify module reloading with constructorparameters
            self.head.addModule(constructor,module.rehashlist())
        except AttributeError:
            self.head.addModule(constructor)
        print module, "done."
        