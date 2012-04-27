#!/usr/bin/env python
##
##  latex2html.py (very poor version)
##
##  by Yusuke Shinyama, May 2003
##

import re, sys, getopt
from texparser import TexParser, TexTokenizer


class ConvHTMLParser(TexParser):
  def __init__(self):
    TexParser.__init__(self)
    self.in_table = 0
    self.in_table_tr = 0
    self.in_table_td = 0
    self.chapter = 0
    self.section = 0
    self.subsection = 0
    self.hook = ""
    self.ok = 1
    return

  def cr(self):
    if self.ok:
      print "<p>"
      self.ok = 0
    return

  def do_linebreak(self):
    if self.in_table:
      if self.in_table_td:
        print "</td>"
        self.in_table_td = 0
      if self.in_table_tr:
        print "</tr>"
        self.in_table_tr = 0
    else:
      self.cr()
    return

  def do_tablesep(self):
    if self.in_table and self.in_table_td:
      print "</td>"
      self.in_table_td = 0
    return
  
  def do_documentclass(self, arg):
    return
  def do_usepackage(self, arg):
    return
  def do_bibliography(self, arg):
    return

  def do_includegraphics(self, arg):
    print '<img src="%s">' % arg.replace(".eps",".png")
    return
  def do_cite(self, arg):
    print '[%s]' % arg
    return
  def do_ref(self, arg):
    print '[%s]' % arg
    return
  def do_label(self, arg):
    print '...[%s]' % arg
    return

  def start_title(self):
    print "<h1>"
    return
  def finish_title(self):
    print "</h1>"
    return

  def start_grouping(self):
    return
  def finish_grouping(self):
    print self.hook
    self.hook = ""
    return

  def do_it(self):
    print "<i>"
    self.hook = "</i>"+self.hook
    return
  def do_bf(self):
    print "<b>"
    self.hook = "</b>"+self.hook
    return
  def do_tt(self):
    print "<tt>"
    self.hook = "</tt>"+self.hook
    return
  
  def start_underline(self):
    print "<u>"
    return
  def finish_underline(self):
    print "</u>"
    return
  
  def start_chapter(self):
    self.chapter += 1
    self.section = 0
    print "<h2>", self.chapter, "."
    return
  def finish_chapter(self):
    print "</h2>"
    return
  def start_chapter_a(self):
    print "<h2>"
    return
  def finish_chapter_a(self):
    print "</h2>"
    return
  
  def start_section(self):
    self.section += 1
    self.subsection = 0
    print "<h3>", self.section, "."
    return
  def finish_section(self):
    print "</h3>"
    return
  def start_section_a(self):
    print "<h3>"
    return
  def finish_section_a(self):
    print "</h3>"
    return

  def start_subsection(self):
    self.subsection += 1
    print "<h4>", self.subsection, "."
    return
  def finish_subsection(self):
    print "</h4>"
    return
  def start_subsection_a(self):
    print "<h4>"
    return
  def finish_subsection_a(self):
    print "</h4>"
    return

  def begin_center(self):
    print "<center>"
    return
  def end_center(self):
    print "</center>"
    return
  
  def begin_math(self):
    print "<i>"
    return
  def end_math(self):
    print "</i>"
    return
  
  def begin_displaymath(self):
    print "<center><i>"
    return
  def end_displaymath(self):
    print "</i></center>"
    return
  
  def begin_equation(self):
    print "<center><i>"
    return
  def end_equation(self):
    print "</i></center>"
    return
  
  def begin_enumerate(self):
    print "<ol>"
    return
  def end_enumerate(self):
    print "</ol>"
    return
  def begin_itemize(self):
    print "<ul>"
    return
  def end_itemize(self):
    print "</ul>"
    return
  def do_item(self):
    print "<li>"
    return
  
  def begin_tabular(self, arg):
    print "<table border>"
    self.in_table = 1
    self.in_table_tr = 0
    self.in_table_td = 0
    return
  def end_tabular(self):
    self.in_table = 0
    if self.in_table_td:
      print "</td>"
    if self.in_table_tr:
      print "</tr>"
    print "</table>"
    return

  def handle_data(self, data):
    if data.strip():
      if self.in_table:
        if not self.in_table_tr:
          print "<tr>"
          self.in_table_tr = 1
        if not self.in_table_td:
          print "<td>"
          self.in_table_td = 1
      sys.stdout.write(str(data))
      self.ok = 1
    else:
      self.cr()
    return

  def do_unknown_command(self, cmd):
    return


# main
if __name__ == "__main__":
  def usage():
    print "usage: latex2html.py [file.tex ...]"
    sys.exit(2)
  try:
    (opts, args) = getopt.getopt(sys.argv[1:], "")
  except getopt.GetoptError:
    usage()

  for n in (args or ["-"]):
    if n == "-":
      f = sys.stdin
    else:
      f = file(n)
    tokenizer = TexTokenizer(f)
    parser = ConvHTMLParser()
    print "<html>"
    while 1:
      t = tokenizer.get()
      if not t: break
      parser.feed(t)
    parser.close()
    print "</html>"
    f.close()
