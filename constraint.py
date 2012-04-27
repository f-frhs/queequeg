#!/usr/bin/env python
##  $Id: constraint.py,v 1.3 2003/07/03 23:07:42 euske Exp $
##
##  constraint.py - Pattern matching / constraint checker
##

import sys, re
import pstring

from regpat import PatternActionSet, PatCounter
from sentence import Sentence, TextTokenizer, SentenceSplitter, POSTagger
from abstfilter import AbstractFeeder, AbstractFilter, AbstractConsumer
from document import PlainTextProcessor
from unification import Unifier, UnificationError, forall, exists
from postagfix import POSTagFixer
from output import TerminalOutput
from grammarerror import GrammarNounAgreementError, GrammarVerbAgreementError, GrammarNonDeterminerError



def ispos(w, t):
  return w.pos_pref == t or (w.pos_pref == None and t in w.pos)


class ParsePatternActionSet(PatternActionSet):

  def __init__(self, observer, warntypes, debug_action=False):
    self.debug_action = debug_action
    PatternActionSet.__init__(self)
    self.observer = observer
    self.check_determiner = "det" in warntypes
    self.check_plural = "plural" in warntypes
    return

  def compile_item0(self, t):
    return lambda w: not w.processed and ispos(w, t)
    
  def compile_item2(self, s):
    return lambda w: not w.processed and (not isinstance(w.s, Sentence)) and s.lower() == w.s.lower()

  def inherit_prop(self, m, inherit=None):
    if inherit:
      m.prop = inherit.prop
      m.prop.match = m
    else:
      m.prop = Unifier()
    return

  c = PatCounter().inc
  debug_action = True
  
  def action_wrapper(self, n, pat1, action, m):
    print "called:", n, map(str,m.getseq())
    action(m)
    return


  ##  CONSTRAINTS
  ##
  pat_det_pos = c('DT | DT1 | DTS | WDT | PRP$ | WP$')
  def act_det_pos(self, m):
    self.inherit_prop(m)
    w = m.submatch.item
    m.prop["determiner"] = True
    if ispos(w, "DT1"):
      m.prop["plural"] = False
    elif ispos(w, "DTS"):
      m.prop["plural"] = True
    return

  pat_pdts = c('PDT | PDT1 | PDTS')
  def act_pdts(self, m):
    self.inherit_prop(m)
    w = m.submatch.item
    if ispos(w, "PDT1"):
      m.prop["plural"] = False
    elif ispos(w, "PDTS"):
      m.prop["plural"] = True
    return

  pat_modifiers = c('CD | JJ | JJR | JJS | NN | NNR')

  pat_ng_3rdsing = c('<det_pos> <pdts>? <modifiers>* (NN | NNR)')
  def act_ng_3rdsing(self, m):
    self.inherit_prop(m)
    m.prop["3rdsing"] = True
    return

  pat_ng_non3rdsing = c('<det_pos>? <pdts>? <modifiers>* NNS')
  def act_ng_non3rdsing(self, m):
    self.inherit_prop(m)
    m.prop["3rdsing"] = False
    return

  pat_pron = c('WP | PRP | PRP2 | PRPS')
  def act_pron(self, m):
    self.inherit_prop(m)
    w = m.submatch.item
    if ispos(w, "PRP2") or ispos(w, "PRPS"):
      m.prop["3rdsing"] = False
    elif ispos(w, "PRP"):
      m.prop["3rdsing"] = True
    return
  
  pat_ng = c('<ng_non3rdsing> | <pron> | <ng_3rdsing> ')
  def act_ng(self, m):
    self.inherit_prop(m, m.submatch)
    return

  pat_adv1 = c('RB')
  pat_there = c('"there" | "here"')
  pat_have1 = c('"have" | "\'ve"')
  pat_has1 = c('"has" | "\'s"')
  pat_had1 = c('"had" | "\'d"')
  pat_is1 = c('"is" | "isn\'t" | "\'s"')
  pat_are1 = c('"are" | "aren\'t" | "\'re"')
  pat_rel1 = c('"which" | "who" | "whom" | "that"')
  
  pat_vg_ven = c('VBN')
  pat_vg_ving = c('VBG | "being" <vg_ven>')
  pat_vg_perf = c('<adv1>? <vg_ven> | "been" <adv1>? <vg_ven> | "been" <adv1>? <vg_ving>')
  
  # Verb group infinite - ignore
  pat_vg_inf = c('MD <adv1>? "be" <vg_ving> | MD <adv1>? "be" <vg_ven> | MD <adv1>? VB')
  def act_vg_inf(self, m):
    self.inherit_prop(m)
    return
  
  # Verb group past tense - ignore
  pat_vg_past = c('<had1> <vg_perf> | VBD')
  act_vg_past = act_vg_inf

  pat_vg_non3rdsing = c('<have1> <vg_perf> | <are1> <vg_ving> | VBP')
  def act_vg_non3rdsing(self, m):
    self.inherit_prop(m)
    m.prop["3rdsing"] = False
    return

  pat_vg_3rdsing = c('<has1> <vg_perf> | <is1> <vg_ving> | VBZ | ' +
                     'MDZ <adv1>? "be" <vg_ving> | MDZ <adv1>? "be" <vg_ven> | MDZ <adv1>? VB')
  def act_vg_3rdsing(self, m):
    self.inherit_prop(m)
    m.prop["3rdsing"] = True
    return

  pat_be_non3rdsing = c('"are" | "\'re" | "were" | "weren\'t"')
  act_be_non3rdsing = act_vg_non3rdsing
  pat_be_3rdsing = c('"is" | "isn\'t" | "\'s" | "was" | "wasn\'t"')
  act_be_3rdsing = act_vg_3rdsing
  pat_vg_there = c('<there> (<be_non3rdsing> | <be_3rdsing>)')
  def act_vg_there(self, m):
    self.inherit_prop(m, m.subseq[1].submatch)
    return

  pat_vg = c('<vg_inf> | <vg_past> | <vg_non3rdsing> | <vg_3rdsing>')
  def act_vg(self, m):
    self.inherit_prop(m, m.submatch)
    return

  pat_rel = c('IN? <rel1>')
  pat_pp = c('IN <ng>')

  pat_sv1_check = c('<ng> <adv1>? <pp>? <rel>? <vg>')
  def act_sv1_check(self, m):
    self.check_sv(m, m.subseq[0], m.subseq[4])
    return
  
  pat_sv2_check = c('<ng> <adv1>? <rel>? <vg>')
  def act_sv2_check(self, m):
    self.check_sv(m, m.subseq[0], m.subseq[3])
    return

  pat_sv3_check = c('<vg_there> <ng>')
  def act_sv3_check(self, m):
    self.check_sv(m, m.subseq[1], m.subseq[0])
    return


  pat_ng_single = c('(<det_pos>? <pdts>?) (<modifiers>* (NN | NNR))')
  def act_ng_single(self, m):
    if exists(lambda w: w.processed, m.getseq()):
      return
    (mdet, mnoun) = (m.subseq[0], m.subseq[1])
    if mdet.subseq[0].repseq:
      self.inherit_prop(m, mdet.subseq[0].repseq[0]) # inherit <det_pos>
    else:
      self.inherit_prop(m)
    w = mnoun.subseq[1].submatch.item
    if ispos(w, "NNR") or w.is_sent:
      m.prop["determiner"] = True
    if mdet.subseq[1].repseq:
      if self.check_ng(m, mdet, mnoun, mdet.subseq[1].repseq[0].prop["plural"]):
        return
    self.check_ng(m, mdet, mnoun, False)
    return

  pat_ng_plural = c('(<det_pos>? <pdts>?) (<modifiers>* NNS)')
  def act_ng_plural(self, m):
    if exists(lambda w: w.processed, m.getseq()):
      return
    (mdet, mnoun) = (m.subseq[0], m.subseq[1])
    if mdet.subseq[0].repseq:
      self.inherit_prop(m, mdet.subseq[0].repseq[0]) # inherit <det_pos>
    else:
      self.inherit_prop(m)
    m.prop["determiner"] = True
    if mdet.subseq[1].repseq:
      if self.check_ng(m, mdet, mnoun, mdet.subseq[1].repseq[0].prop["plural"]):
        return
    self.check_ng(m, mdet, mnoun, True)
    return

  pat_ng_check = c('<ng_single> | <ng_plural>')
  
  del c

  def check_sv(self, m, ms, mv):
    if exists(lambda w: w.processed, m.getseq()):
      return
    try:
      ms.prop.unify(mv.prop)
    except UnificationError:
      self.observer(GrammarVerbAgreementError(ms, mv))
    for w in m.getseq():
      w.processed = True
    return

  def check_ng(self, m, mdet, mnoun, plural):
    for w in m.getseq():
      w.processed = True
    if self.check_plural:
      try:
        m.prop["plural"] = plural
      except UnificationError:
        self.observer(GrammarNounAgreementError(mdet, mnoun))
        return True
    if self.check_determiner and not m.prop["determiner"]:
      self.observer(GrammarNonDeterminerError(m))
      return True
    return False



##
##
class ConstraintChecker(AbstractFilter):

  def __init__(self, next_filter, warntypes, debug_action=False):
    AbstractFilter.__init__(self, next_filter)
    self.actionset = ParsePatternActionSet(self.notify, warntypes, debug_action)
    self.warntypes = warntypes
    return

  def notify(self, e):
    self.feed_next((self.sent, e))
    return
  
  def feed(self, sent):
    if sent.words[0].s == "[[":
      return
    for w in sent.words:
      if w.is_sent:
        self.feed(w.s)
    self.sent = sent
    if "sv1" in self.warntypes:
      self.actionset.perform_longest_first("sv1_check", sent.words)
    if "sv2" in self.warntypes:
      self.actionset.perform_longest_first("sv2_check", sent.words)
    if "sv3" in self.warntypes:
      self.actionset.perform_longest_first("sv3_check", sent.words)
    self.actionset.perform_longest_first("ng_check", sent.words)
    return


#
if __name__ == "__main__":
  if sys.argv[1] == "-t":
    docproc = TexProcessor
  elif sys.argv[1] == "-l":
    docproc = HTMLProcessor
  elif sys.argv[1] == "-p":
    docproc = PlainTextProcessor
  else:
    assert 0
  import dictionary
  dict = dictionary.Dictionary("LOCAL/dict.txt")
  out = TerminalOutput()
  pipeline = docproc(TextTokenizer(SentenceSplitter(POSTagger(dict, POSTagFixer(ConstraintChecker(out, ["sv1","sv2","sv3","det","plural"]))))))
  pipeline.read(pstring.PFile(sys.stdin))
