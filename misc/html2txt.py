#!/usr/bin/env python
##
##  html2txt.py - strip printable texts from html files.
##
##  by Yusuke Shinyama, May 2003
##

import sys, sgmllib

class Parser(sgmllib.SGMLParser):
  def __init__(self):
    sgmllib.SGMLParser.__init__(self)
    self.t = 0
    self.ok = 1
    return
  def handle_data(self, x):
    if not self.ok:
      return
    s = x.strip().replace("\n", " ")
    if s:
      if ord(s[0]) < 128:
        sys.stdout.write(" ")
      sys.stdout.write(s)
      self.t = 1
    return
  def newline(self):
    if self.t:
      self.t = 0
      print
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

if __name__ == "__main__":
  import fileinput
  p = Parser()
  for s in fileinput.input():
    p.feed(s)
