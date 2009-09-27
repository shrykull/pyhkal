#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import re
from modules import IRCBotMod
from utils import list2string, file2obj, obj2file, nick
from random import randint

###

class FactoidMod(IRCBotMod):
    regexpattern = r':(.+) PRIVMSG ([\S]+) :(.+)'
    filename = "factoid.dict"
    factoidprobability = 100
    def __init__(self,head):
        IRCBotMod.__init__(self,head)
        self.handleInput = self.handler
        self.importconf()
    def exportconf(self):
        obj2file((self.factoids),self.configfilename)  
    def importconf(self):
        try:
            (self.factoids) = file2obj(self.configfilename)
        except IOError:
            self.factoids = []
    def handler(self,matchlist):
        host = matchlist[0]
        target = matchlist[1] if matchlist[1] != self.head.nickname else nick(host)
        text = matchlist[2]
        t = matchlist[2].split(" ")
        matches = [] # factoid-matching :s
        if (t[0] == "factoid"):
            if (len(t) > 2):
                if (t[1] == "set"):
                    try:
                        r = re.match(list2string(t[2]),"")
                    except Exception as inst:
                        self.head.sendErr(target,inst)
                    else: # add factoid
                        try:
                            print "--"
                            mm = re.match("factoid set \/(.+)\/ (.+)",list2string(t[0:]))
                            regex = mm.group(1)
                            reaction = mm.group(2)
                            print regex
                            print reaction
                            print "--"
                            cre = re.compile(regex)
                            
                            self.factoids.append( (cre, reaction ) )
                            self.head.sendMsg(target,"Okay, "+ nick(host)+".")
                        except:
                            self.head.sendMsg(target,"Invalid Regex, "+ nick(host)+" :<")
                            
                elif (t[1] == "get"):
                    gets = [ "[%s] %s -> %s" % (i, cre.pattern, subst) for i, (cre, subst) in enumerate(self.factoids) if t[2] in cre.pattern ]
                    if len(gets):
                        self.head.sendMsg(target, list2string(gets,', ') )
                    else:
                        self.head.sendMsg(target, "No match..")

                elif (t[1] == "del") and (self.head.mainchannel.isOp(nick(host))) and (int(t[2]) <= len(self.factoids)) :
                    del(self.factoids[int(t[2])])
                    self.head.sendMsg(target, "Done.")

        elif (randint(0,100) < self.factoidprobability): # give factoid
            for cre, subst in self.factoids:
                if cre.search(text):
                    matches.append( cre.sub(subst, text) )

            if (len(matches) > 0): #and (len(t[1:]) > 15) and (len(t) > 3):
                 self.head.sendMsg(target, matches[randint(0,len(matches)-1)].replace("$who", nick(host)) ) # choose random factoid, of all matching
 #               except ValueError:
 #                   pass
            #print(list2string(matches,","))
            matches = []

        self.exportconf()

class factoid(object):
    def __init__(self,regex,reaction):
        self.regex = regex
        self.reaction = reaction
    def __str__(self): return self.regex + " -> "+ self.reaction
    def __repr__(self): return self.regex + " -> "+ self.reaction
