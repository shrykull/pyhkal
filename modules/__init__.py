#!/usr/bin/env python
# -*- coding: utf-8 -*-

class IRCBotMod(object):
    def __init__(self,head):
        self.head = head
        self.configfilename = str(self.__class__.__name__) + ".conf"
