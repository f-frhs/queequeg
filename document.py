#!/usr/bin/env python
##  $Id: document.py,v 1.2 2003/07/27 13:54:05 euske Exp $
##
##  document.py - Document analyzer (HTML/TeX/PlainText)
##

import re, sys

from texparser import TexParser, TexTokenizer
from sgmllib_rev import SGMLParser
from abstfilter import AbstractFeeder, AbstractFilter, AbstractConsumer


class HTMLProcessor(SGMLParser, AbstractFeeder):
  
  def __init__(self, next_filter):
    AbstractFeeder.__init__(self, next_filter)
    SGMLParser.__init__(self)
    self.t = 0
    self.ok = 1
    return
  
  def handle_data(self, s):
    if not self.ok:
      return
    if s:
      self.feed_next(s)
      self.t = 1
    return
  
  def newline(self):
    if self.t:
      self.t = 0
      self.feed_next(None)
    return
  
  def do_p(self, attrs):
    self.newline()
    return
  def do_br(self, attrs):
    self.newline()
    return
  def do_th(self, attrs):
    self.newline()
    return
  def do_td(self, attrs):
    self.newline()
    return
  def do_li(self, attrs):
    self.newline()
    return
  def do_hr(self, attrs):
    self.newline()
    return
  def do_h1(self, attrs):
    self.newline()
    return
  def do_h2(self, attrs):
    self.newline()
    return
  def do_h3(self, attrs):
    self.newline()
    return
  def do_h4(self, attrs):
    self.newline()
    return
  def do_h5(self, attrs):
    self.newline()
    return
  def do_h6(self, attrs):
    self.newline()
    return
  def do_h5(self, attrs):
    self.newline()
    return
  def start_style(self, attrs):
    self.ok = 0
    return
  def end_style(self):
    self.ok = 1
    return
  def start_script(self, attrs):
    self.ok = 0
    return
  def end_script(self):
    self.ok = 1
    return

  def close(self):
    SGMLParser.close(self)
    AbstractFeeder.close(self)
    return

  def read(self, f):
    while 1:
      s = f.readline()
      if not s: break
      self.feed(s)
    self.close()
    return



class TexProcessor(TexParser, AbstractFeeder):

  def __init__(self, next_filter):
    AbstractFeeder.__init__(self, next_filter)
    TexParser.__init__(self)
    self.next_paragraph = 0
    self.t = 0
    return

  def process_paragraph(self):
    if self.t:
      self.feed_next(None)
    self.next_paragraph = 0
    return

  def handle_data(self, data):
    data1 = data.strip()
    if not data1:
      self.next_paragraph = 1
    if self.next_paragraph:
      self.process_paragraph()
    if data1:
      self.t = 1
      self.feed_next(data)
    return

  def do_documentclass(self, arg):
    return
  def do_usepackage(self, arg):
    return
  def do_bibliography(self, arg):
    return
  def do_includegraphics(self, arg):
    return
  def do_cite(self, arg):
    return
  def do_ref(self, arg):
    return
  def do_label(self, arg):
    return
  def do_unknown_command(self, cmd):
    return

  def begin_tabular(self,arg):
    return
  def end_tabular(self):
    return
  # do not consider inline math expressions as individual sentences.
  def begin_math(self):
    return
  def end_math(self):
    return

  def start_title(self):
    self.next_paragraph = 1
    return
  def start_chapter(self):
    self.next_paragraph = 1
    return
  def startchapter_a(self):
    self.next_paragraph = 1
    return
  def startsection(self):
    self.next_paragraph = 1
    return
  def startsection_a(self):
    self.next_paragraph = 1
    return
  def startsubsection(self):
    self.next_paragraph = 1
    return
  def startsubsection_a(self):
    self.next_paragraph = 1
    return
  def startsubsubsection(self):
    self.next_paragraph = 1
    return
  def startsubsubsection_a(self):
    self.next_paragraph = 1
    return
  def do_tablesep(self):
    self.next_paragraph = 1
    return
  def do_linebreak(self):
    self.next_paragraph = 1
    return
  def do_item(self):
    self.next_paragraph = 1
    return
  def begin_unknown_environment(self, env):
    self.next_paragraph = 1
    return

  def close(self):
    AbstractFeeder.close(self)
    TexParser.close(self)
    if self.next_paragraph:
      self.process_paragraph()
    return

  def read(self, f):
    tokenizer = TexTokenizer(f)
    while 1:
      t = tokenizer.get()
#      print repr(t)
      if not t: break
      self.feed(t)
    self.close()
    return


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
