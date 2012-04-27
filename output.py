#!/usr/bin/env python
##  $Id: output.py,v 1.1.1.1 2003/07/01 23:28:27 euske Exp $
##
##  output.py - 
##

import sys, re

from abstfilter import AbstractFeeder, AbstractFilter, AbstractConsumer
from grammarerror import GrammarNounAgreementError, GrammarVerbAgreementError, GrammarNonDeterminerError




class TerminalOutput(AbstractConsumer):

  CONTEXT = 2
  ESC = "\033"
  TERM_RED = ESC+"[31m"                   # red
  TERM_GREEN = ESC+"[32m"                 # green
  TERM_YELLOW = ESC+"[33m"                # yellow
  TERM_NORMAL = ESC+"[m"

  def __init__(self, verbosity=0, out=sys.stdout):
    self.out = out
    self.verbosity = verbosity
    return

  def disp_pos(self, m, msg):
    w = m.getseq()[0]
    while w.is_sent:
      w = w.s.words[0]
    self.out.write("%s:%d: " % (w.s.f.name, w.s.line))
    if 1 <= self.verbosity:
      self.out.write("[%14s] " % (msg))
    return
  
  def disp_context(self, sent, start, end):
    if start < end:
      self.out.write(" ".join(map(str, sent.words[start:end]))+" ")
    return

  def disp_pre(self, sent, end):
    start = end - self.CONTEXT
    if start < 0: start = 0
    if 0 < start: self.out.write("... ")
    self.disp_context(sent, start, end)
    return

  def disp_post(self, sent, start):
    end = start + self.CONTEXT
    if len(sent.words) < end: end = len(sent.words)
    self.disp_context(sent, start, end)
    if end < len(sent.words): self.out.write("... ")
    return

  def disp_highlight(self, c, header, m, footer):
    self.out.write(c+header+" ".join(map(str, m.getseq()))+footer+self.TERM_NORMAL)
    return
  
  def feed(self, (sent, e)):
    
    if isinstance(e, GrammarNonDeterminerError):
      self.disp_pos(e.mng, e.msg)
      self.disp_pre(sent, e.mng.start)
      self.disp_highlight(self.TERM_RED, "(", e.mng, ") ")
      self.disp_post(sent, e.mng.end)
      
    elif isinstance(e, GrammarNounAgreementError):
      self.disp_pos(e.mdet, e.msg)
      self.disp_pre(sent, e.mdet.start)
      self.disp_highlight(self.TERM_GREEN, "(Det:", e.mdet, ") ")
      if e.mnoun:
        self.disp_highlight(self.TERM_GREEN, "(N:", e.mnoun, ") ")
        self.disp_post(sent, e.mnoun.end)
      else:
        self.disp_post(sent, e.mdet.end)
      
    elif isinstance(e, GrammarVerbAgreementError):
      (f1, f2) = ("S", "V")
      (m1, m2) = (e.mng, e.mvg)
      if e.mvg.start < e.mng.start:
        (f1, f2) = (f2, f1)
        (m1, m2) = (m2, m1)
      self.disp_pos(m1, e.msg)
      self.disp_pre(sent, m1.start)
      self.disp_highlight(self.TERM_YELLOW, "("+f1+":", m1, ") ")
      self.disp_context(sent, m1.end, m2.start)
      self.disp_highlight(self.TERM_YELLOW, "("+f2+":", m2, ") ")
      self.disp_post(sent, m2.end)
    else:
      assert False, "unknown error class: "+repr(e)

    print
    return
