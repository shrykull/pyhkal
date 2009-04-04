# -*- coding: cp1252 -*-
# File: pykhal.py

import asyncore, asynchat
import re, socket, cPickle, datetime
import sys
import time
from time import strftime
from random import random
from threading import Timer

class IRCBot(asynchat.async_chat):
    MODLIST = []
    performqueue = []
    performfilename = "perform.list"
    def __init__(self, server="irc.quakenet.org", port=6667,ident="nexus", password="", nickname="FAiLHKAL", mainchannel="#ich-sucke"):
        asynchat.async_chat.__init__(self)
        self.set_terminator("\n")
        self.data = ""
        
        self.server = server
        self.port = port
        self.ident = ident
        self.nickname = nickname
        self.mainchannel = mainchannel
        
        self.initcommands = [
            "USER " + self.ident + " " + self.ident + " " + self.ident + " :Python-TiHKAL",
            "PASS " + password,
            "NICK " + self.nickname
            ]
            
        try:
            self.performqueue = file2obj(self.performfilename)
        except IOError:
            self.performqueue = []
            obj2file(self.performqueue,self.performfilename)
            
        self.spamqueue = SpamQueue(5,5)
        self.create_socket(socket.AF_INET,socket.SOCK_STREAM)
        self.connect((server,port))
        
    def handle_connect(self):
        print "(INFO) Connected to ", self.server + ":" + str(self.port)
        pass

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
        for x in self.MODLIST:
            l = re.findall(x.regexpattern,data)
            if (l):
                try: 
                    x.handleInput(l[0])
                except Exception as inst:
                    self.printErr(x.name,inst)
        if re.match("PING :",data):
            self.sendraw("PONG " + data.split(" ")[1])
            return
        if re.match(":(.+) PRIVMSG (.+) :(.+)", data):
            self.onText(*re.match(":(.+) PRIVMSG (.+) :(.+)", data).group(1,2,3))
            return
        if re.match(":(.+) NICK :(.+)",data):
            self.onNick(*re.match(":(.+) NICK :(.+)",data).group(1,2))
            return
        if re.match(":.+ (\d\d\d) (.+)",data):
            self.onRawNumeric(*re.match(":.+ (\d+) (.+)",data).group(1,2))
            return
        if re.match(".*NOTICE .+:.+host.+", data):
            for x in self.initcommands:
                self.sendraw(x)
            return
        print "( >> )", data
                
    def sendraw(self, string):
        if (string):
            self.push(string + "\r\n")

    def onNick(self,oldhost,newnick):
        if (nick(oldhost) == self.nickname):
            self.nickname = newnick
        print "(NICK)", nick(oldhost), "=>", newnick
        
    def quit(self):
        self.sendraw("QUIT :... denn #ich-sucke härter als ihr alle zusammen...")
        print "(QUIT)", "Terminating..."
        exit()

    def onRawNumeric(self,numeric,text):
        numeric = int(numeric)
        if ((numeric == 376) or (numeric == 422)):
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
    

class IRCBotMod(object):
    def __init__(self,head,name,regexpattern):
        self.name = name
        self.head = head
        self.regexpattern = regexpattern
        matcher = re.compile(regexpattern)

class AdminMod(IRCBotMod):
    adminhosts = []
    storage = {}
    def __init__(self,head,name,regex,adminpass="defaultpass"):
        IRCBotMod.__init__(self,head,name,regex)
        self.handleInput = self.handler
        self.adminpass = adminpass
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
                if ("pyhkal" in sys.modules):
                    sys.modules.pop("pyhkal")
                import pyhkal
class CubeMod(IRCBotMod):
    cubers = []
    def __init__(self,head,name,regexpattern):
        IRCBotMod.__init__(self,head,name,regexpattern)
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
class DecideMod(IRCBotMod):
    def __init__(self,head,name,regexpattern):
        IRCBotMod.__init__(self,head,name,regexpattern)
        self.handleInput = self.handler

    def handler(self,matchlist):
        self.head.sendMsg(matchlist[1],"Du solltest dich " + 
                          self.regexdecide(list2string(matchlist[2:]),
                                           num=asciicount("*!*" + ident(matchlist[0]))) +
                          " entscheiden.")

    def regexdecide(self,text, num):
        matchlist = sorted(re.findall(r'(".+?"|(?<!").+?(?!"))(?:\s|$)',text))
        c = asciicount(text) + asciicount(strftime("%d/%m/%Y"))
        if len(matchlist) > 1:
            return "für " + matchlist[(c + (num % 100)) % len(matchlist)]
        else:            
            if ((c  % (num % 100)) % 2 + 1) == 1:
                return "dafür"
            else:
                return "dagegen"
class KarmaMod(IRCBotMod):
    filename = "karma.dict"
    def __init__(self,head,name,regexpattern):
        IRCBotMod.__init__(self,head,name,regexpattern)
        self.handleInput = self.handler
        try:
            self.karmadict = file2obj(self.filename)
        except IOError:
            self.karmadict = {}
    def handler(self,matchlist):
        if (matchlist[1] == self.head.mainchannel):
            karmalist = re.findall(r'(\S\S+\+\+)(?:\s|$)|([\S]\S+--)(?:\s|$)|(\S\S+==)(?:\s|$)',matchlist[2])
            for x in karmalist:
                if x[0]:
                    if not x[0][:-2] in self.karmadict:
                        e = KarmaEntry(x[0][:-2])
                        self.karmadict[x[0][:-2]] = e
                    if not self.karmadict[x[0][:-2]].add(1):
                        self.head.sendMsg(matchlist[1],"Karmaspam - " + x[0][:-2] + " ist noch " + self.karmadict[x[0][:-2]].resttime() + " blockiert.")
                    else:
                        self.head.sendMsg(matchlist[1],x[0][:-2] + " hat nun einen karmawert von " + str(self.karmadict[x[0][:-2]].value))
                if x[1]:
                    if not x[1][:-2] in self.karmadict:
                        e = KarmaEntry(x[1][:-2])
                        self.karmadict[x[1][:-2]] = e
                    if not self.karmadict[x[1][:-2]].add(-1):
                        self.head.sendMsg(matchlist[1],"Karmaspam - " + x[1][:-2] + " ist noch " + self.karmadict[x[1][:-2]].resttime() + " blockiert.")
                    else:
                        self.head.sendMsg(matchlist[1],x[1][:-2] + " hat nun einen karmawert von " + str(self.karmadict[x[1][:-2]].value))
                if x[2]:
                    if not x[2][:-2] in self.karmadict:
                        e = KarmaEntry(x[2][:-2])
                        self.karmadict[x[2][:-2]] = e
                    self.head.sendMsg(matchlist[1],x[2][:-2] + " hat einen karmawert von " + str(self.karmadict[x[2][:-2]].value))
            obj2file(self.karmadict,self.filename)
class KarmaEntry(object):
    karmaspam = datetime.timedelta(0,600)
    def __init__(self,name):
        self.name = name
        self.time = datetime.datetime(1,1,1)
        self.value = 0
    def add(self,value):
        if (datetime.datetime.now() - self.time) > self.karmaspam:
            self.value += value
            self.time = datetime.datetime.now()
            return True
        else:
            return False
    def resttime(self):
        return timedelta2string(self.karmaspam - (datetime.datetime.now() - self.time))[:-4]
            
class TikkleMod(IRCBotMod):
    filename = "tikkle.dict"
    def __init__(self,head,name,regexpattern):
        IRCBotMod.__init__(self,head,name,regexpattern)
        self.handleInput = self.handler
        try:
            self.tikklers = file2obj(self.filename)
        except Exception:
            self.tikklers = {}
        self.head = head
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
		
class timerMod(IRCBotMod):
    def __init__(self,head,name,regex):
        IRCBotMod.__init__(self,head,name,regex)
        self.handleInput = self.handler
    def handler(self,matchlist):
        host = matchlist[0]
        target = matchlist[1] if matchlist[0] != self.head.nickname else nick(host)
        time = matchlist[2]
        text = matchlist[3]
        if (int(time) > 0):
            self.head.sendNotice(nick(host),"Timer started.")
            Timer(int(time),self.head.sendMsg,(target,"timed message by " + nick(host) + ": " + text)).start()
class toolsMod(IRCBotMod):
    triggerlist = []
    def __init__(self,head,name,regex):
        IRCBotMod.__init__(self,head,name,regex)
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
                    #self.addtrigger([target,"Channels: ",r'.+ 319 (?:[\S]+) (?:[\S]+) :(.+)'])
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
def nick(host):
    return host.split("!")[0]
def timedelta2string(r):
    r = str(r)
    while ((r[0] == "0") or (r[0] == ":")):
        r = r[1:]
    return r[0:-3]    
def obj2file(obj,filename):
    f = open(filename,"w")
    cPickle.dump(obj,f)
    f.close()
def file2obj(filename):
    f = open(filename,"r")
    return cPickle.load(f)
    f.close()
def asciicount(text):
    r = 0
    for x in text:
        r += ord(x)
    return r

def ident(text):
    return list2string(text.split("!")[1].split("@")[0],"")

def list2string(l,s = " "):
    r = ""
    for x in l:
        r = r + s+ x
    return r[len(s):]
def rand(min = 1,max = 100):
    return int(round(min + random() * (max - min)))
    
try:
    (SERVER,PORT,IDENT,PASS,NICKNAME,MAINCHANNEL,ADMINAUTHPASS) = file2obj("pyhkal.conf")
except IOError:
    PORT = 6667
    SERVER = "irc.quakenet.org"
    NICKNAME = "FAiLHKAL" + str(rand(1,9999999))
    IDENT = "FAiLHKAL"
    PASS = ""
    MAINCHANNEL = "#ich-sucke"
    ADMINAUTHPASS = "default"
    obj2file((SERVER,PORT,IDENT,PASS,NICKNAME,MAINCHANNEL,ADMINAUTHPASS),"pyhkal.conf")

pyhkal = IRCBot(SERVER,PORT,IDENT,PASS,NICKNAME,MAINCHANNEL)

def exportconf():
    obj2file((SERVER,PORT,IDENT,PASS,NICKNAME,MAINCHANNEL,ADMINAUTHPASS),"pyhkal.conf")
def exportperform():
    obj2file(pyhkal.performqueue,pyhkal.performfilename)

admin = AdminMod(pyhkal,"admin",r':(.+) (?:PRIVMSG|NOTICE) ([\S]+) :(!do|!py|!pydo|!auth|!rehash|spam\?)(?: (.+)|$)',ADMINAUTHPASS)
decide = DecideMod(pyhkal, "decide",r':(.+) PRIVMSG ([\S]+) :!decide (.+)')
cube = CubeMod(pyhkal,"cube",r':(.+) PRIVMSG ([\S]+) :(.+)')
karma = KarmaMod(pyhkal,"karma",r':(.+) PRIVMSG ([\S]+) :(.+)')
tikkle = TikkleMod(pyhkal,"tikkle",r':(.+) PRIVMSG ([\S]+) :(.+)')
timer = timerMod(pyhkal,"tikkle",r':(.+) PRIVMSG ([\S]+) :.*timer:(\d+):(.*)')
tools = toolsMod(pyhkal,"tools",r'(.+)')

pyhkal.MODLIST = [admin, decide, cube, karma, tikkle, timer, tools]

asyncore.loop()
