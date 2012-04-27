#!/usr/bin/env python
##  $Id: document.py,v 1.2 2003/07/27 13:54:05 euske Exp $
##
##  document.py - Document analyzer (HTML/TeX/PlainText)
##

import re, sys

from abstfilter import AbstractFeeder, AbstractFilter, AbstractConsumer

class PlainTextProcessor(AbstractFeeder):

  def __init__(self, next_filter):
    AbstractFeeder.__init__(self, next_filter)
    self.t = 0
    return

  def read(self, f):
    while 1:
      s = f.readline()
      if not s: break
      if not s.strip() and self.t:
        self.feed_next(None)
      else:
        self.t = 1
        self.feed_next(s)
    self.close()
    return
  

# main
if __name__ == "__main__":
  class Consumer(AbstractConsumer):
    def feed(self, s):
      if s == None:
        print "-"
      else:
        print repr(s)
      return
  if sys.argv[1] == "-t":
    proc = TexProcessor
  elif sys.argv[1] == "-l":
    proc = HTMLProcessor
  elif sys.argv[1] == "-p":
    proc = PlainTextProcessor
  else:
    assert 0
  proc(Consumer()).read(sys.stdin)
