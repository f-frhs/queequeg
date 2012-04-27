#!/usr/bin/env python
##
##  DeTeX.py
##
##  by Yusuke Shinyama, May 2003
##

import re, sys, getopt
from texparser import TexParser, TexTokenizer


class DeTeXParser(TexParser):
  def __init__(self, output=sys.stdout):
    TexParser.__init__(self)
    self.par = 0
    self.in_table = 0
    self.words = 0
    self.lines = 0
    self.output = output
    return

  def crlf(self):
    if self.output and self.par:
      self.output.write("\n\n")
    self.par = 0
    self.lines += 1
    return
  
  def do_linebreak(self):
    if self.output:
      self.output.write("\n")
      if not self.in_table:
        self.output.write("\n")
    self.lines += 1
    return
  
  def do_documentclass(self, arg):
    return
  def do_usepackage(self, arg):
    return
  def do_bibliography(self, arg):
    return
  
  def start_section(self):
    self.crlf()
    return
  def finish_section(self):
    self.crlf()
    return

  def begin_tabular(self, arg):
    self.in_table = 1
    return
  def end_tabular(self):
    self.in_table = 0
    return

  def handle_data(self, data):
    data = data.strip()
    if data:
      if self.output:
        self.output.write(data+" ")
      self.words += 1
      self.par = 1
    else:
      self.crlf()
    return

  def do_unknown_command(self, cmd):
    return


# main
if __name__ == "__main__":
  def usage():
    print "usage: detex.py [-w] [file.tex ...]"
    sys.exit(2)
  try:
    (opts, args) = getopt.getopt(sys.argv[1:], "w")
  except getopt.GetoptError:
    usage()

  wc = 0
  for (k, v) in opts:
    if k == "-w":
      wc = 1

  for n in (args or ["-"]):
    if n == "-":
      f = sys.stdin
    else:
      f = file(n)
    tokenizer = TexTokenizer(f)
    if wc:
      parser = DeTeXParser(None)
    else:
      parser = DeTeXParser()
    while 1:
      t = tokenizer.get()
      if not t: break
      parser.feed(t)
    parser.close()
    f.close()
    if wc:
      print "%s: words %d, lines %d" % \
            (n, parser.words, parser.lines)
