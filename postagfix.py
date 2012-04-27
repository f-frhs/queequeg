#!/usr/bin/env python
##  $Id: postagfix.py,v 1.1.1.1 2003/07/01 23:28:27 euske Exp $
##
##  postagfix.py - POS Tag Fixer
##

import sys, re

from regpat import PatternSet, PatCounter
from sentence import Sentence, Dictionary, TextTokenizer, SentenceSplitter, POSTagger
from abstfilter import AbstractFeeder, AbstractFilter, AbstractConsumer
from document import PlainTextProcessor


##
##
class POSTagFixPatternSet(PatternSet):
  def __init__(self, pats):
    PatternSet.__init__(self)
    self.fixpatterns = map(lambda (p,tags): (self.compile(p), tags), pats)
    return
  
  def compile_item0(self, t):
    return lambda w: w.pos_pref == t
    
  def compile_item1(self, t):
    def pred1(p):
      if p == "capita":
        return lambda w: w.s[0].isupper()
      elif p.startswith("!"):
        p = p[1:]
        return lambda w: p not in w.pos
      else:
        return lambda w: p in w.pos
    return self.combine_preds(map(pred1, t.split(",")))
    
  def compile_item2(self, s):
    return lambda w: (not isinstance(w.s, Sentence)) and s.lower() == w.s.lower()

  def perform(self, seq):
    for (pat, tags) in self.fixpatterns:
      for m in pat.search(seq):
        #print zip(seq[m.start:m.end], tags)
        for (w,t) in zip(seq[m.start:m.end], tags):
          if t:
            w.pos_pref = t
    return


##
##
class POSTagFixer(AbstractFilter):
  
  patternset = POSTagFixPatternSet([
    ('([DT]|[DT1]|[DTS]|[PRP$]|[PDT]|[PDT1]|[PDTS]) [NN,VBP]',
     [None,               "NN"] ),
    
    ('([DT]|[DT1]|[DTS]|[PRP$]|[PDT]|[PDT1]|[PDTS]) [NNS,VBZ]',
     [None,               "NNS"] ),
    
    ('[NN]  [NNS,VBZ] ([DT]|[DT1]|[DTS]|[PDT]|[PDT1]|[PDTS]|[PRP]|[PRPS]|[NN]|[NNS])',
     [None, "VBZ",    None] ),
    
    ('[NN,VB] ([VB]|[VBZ])',
     ["NN",   None] ),
    
    ('"to"  [VB]',
     [None, "VB"] ),
    
    ('[MD]  [VB]',
     ["MD", "VB"] ),
    
    ('[MDZ]  [VB]',
     ["MDZ", "VB"] ),
    ])
  
  def __init__(self, next_filter):
    AbstractFilter.__init__(self, next_filter)
    return
  
  def process(self, sent1):
    for w in sent1.words:
      if len(w.pos) == 1:
        w.pos_pref = w.pos[0]
    self.patternset.perform(sent1.words)
    return sent1


##


#
if __name__ == "__main__":
  class Consumer(AbstractConsumer):
    def feed(self, s):
      print repr(s)
      return
  if sys.argv[1] == "-t":
    docproc = TexProcessor
  elif sys.argv[1] == "-l":
    docproc = HTMLProcessor
  elif sys.argv[1] == "-p":
    docproc = PlainTextProcessor
  else:
    assert 0
  dict = Dictionary("LOCAL/dict.cdb")
  out = Consumer()
  pipeline = docproc(TextTokenizer(SentenceSplitter(POSTagger(dict, POSTagFixer(out)))))
  pipeline.read(sys.stdin)
