#!/usr/bin/env python
# -*- coding: utf-8 -*-

import datetime
import re
from modules import IRCBotMod
from utils import list2string, file2obj, obj2file, nick
from random import randint
import textwrap
###

class FactoidMod(IRCBotMod):
    regexpattern = r':(.+) PRIVMSG ([\S]+) :(.+)'
    filename = "factoid.dict"
    factoidprobability = 100 # you definately want to change this
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
                if ((t[1] == "set") and (t[1] == "add")):
                    try:
                        r = re.match(list2string(t[2]),"")
                    except Exception as inst:
                        self.head.sendErr(target,inst)
                    else: # add factoid
                        try:
                            mm = re.match("factoid set \/(.+)\/ (.+)",list2string(t[0:]))
                            regex = mm.group(1)
                            reaction = mm.group(2)
                            cre = re.compile(regex)
                            
                            self.factoids.append( (cre, reaction ) )
                            if (self.head.mainchannel.isOp(nick(host))):
                                self.head.sendMsg(target,"Okay, "+ nick(host)+".")
                            else:
                                self.head.sendMsg(self.head.mainchannel.name, "Added [%s] %s »%s« via non-op" % ((len(self.factoids)-1), t[2], list2string(t[3:])) )

                        except:
                            self.head.sendMsg(target,"Invalid Regex, "+ nick(host)+" :<")
                            
                elif (t[1] == "get"):
                    gets = [ "[%s] %s -> %s" % (i, cre.pattern, subst) for i, (cre, subst) in enumerate(self.factoids) if t[2] in cre.pattern ]
                    if len(gets):
                        answer = list2string(gets,', ')
                        if (len(answer) > 300):
                            answerlist = textwrap.wrap(answer,300)
                            for ans in answerlist:
                                self.head.sendMsg(target, ans)
                        else:
                            self.head.sendMsg(target, answer )
                    else:
                        self.head.sendMsg(target, "No match..")

                elif (t[1] == "find"):

                    gets = [ "[%s] %s -> %s" % (i, cre.pattern, subst) for i, (cre, subst) in enumerate(self.factoids) if t[2] in subst ]
                    if len(gets):
                        answer = list2string(gets,', ')
                        if (len(answer) > 300):
                            answerlist = textwrap.wrap(answer,300)
                            for ans in answerlist:
                                self.head.sendMsg(target, ans)
                        else:
                            self.head.sendMsg(target, answer )
                    else:
                        self.head.sendMsg(target, "No match..")

                elif (t[1] == "num"):
                    if (int(t[2]) <= len(self.factoids)):
                        f = self.factoids[int(t[2])]
                        gets = "[%s] %s -> %s" % (t[2], f[0].pattern, f[1])
                        self.head.sendMsg(target, gets)
                    else:
                        self.head.sendMsg(target, "No match..")

                elif (t[1] == "list"): # 400 max., so we should split here :<

                    self.head.sendMsg(target, "I know %s factoids:" % (len(self.factoids)) )
                    gets = list2string ( [ "[%s] %s -> %s" % (i, cre.pattern, subst) for i, (cre, subst) in enumerate(self.factoids) ] )
                    self.head.sendMsg(target, gets)
                    
                elif ((t[1] == "del") or (t[1] == "rem")) and (self.head.mainchannel.isOp(nick(host))) and (int(t[2]) <= len(self.factoids)) :
                    del(self.factoids[int(t[2])])
                    self.head.sendMsg(target, "Done.")

        elif (randint(0,100) < self.factoidprobability): # give factoid
            for cre, subst in self.factoids:
                m = cre.search(text)
                if m:
                    tmp = cre.sub(subst, m.group(0))
                    matches.append( tmp )
    

            if (len(matches) > 0): # and (len(t[1:]) > 15) and (len(t) > 3):
                rply = matches[randint(0,len(matches)-1)].replace("$who", nick(host)) # choose random factoid, regard replacement of $who
                rply = rply.replace("$someone",random.choice(bot.mainchannel.nicklist.keys())) # replace $someone with ..someone ;)
                rply = rply.replace("\n","\\n") # output validation :)
                if rply.startswith("A:"): # reactions starting with "A:" will be send as /me
                     self.head.sendAction(target, rply[2:]) # strip first two chars
                else:
                     self.head.sendMsg(target, rply)
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
