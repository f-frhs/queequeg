#!/usr/bin/env python
##  $Id: regpat.py,v 1.1.1.1 2003/07/01 23:28:27 euske Exp $
##
##  regpat.py - Universal Regular Expression pattern matching
##

from __future__ import generators

import re


##  PatMatch
##
class PatMatch:
  
  def __init__(self, pat, start, end):
    self.pat = pat
    self.start = start
    self.end = end
    return
  
  def __repr__(self):
    return "<Match: %d-%d>" % (self.start, self.end)

  def getseq(self):
    raise NotImplementedError

  def exec_action(self):
    raise NotImplementedError
  


class PatItemMatch(PatMatch):
  def __init__(self, pat, start, end, item):
    PatMatch.__init__(self, pat, start, end)
    self.item = item
    return
  def __repr__(self):
    return "<ItemMatch: %d-%d %s>" % (self.start, self.end, self.item)
  def exec_action(self, *args):
    apply(self.pat.action, (self,)+args)
    return
  def getseq(self):
    return [self.item]

class PatRepeatMatch(PatMatch):
  def __init__(self, pat, start, end, rep, repseq):
    PatMatch.__init__(self, pat, start, end)
    self.rep = rep
    self.repseq = repseq
    return
  def __repr__(self):
    return "<RepeatMatch: %d-%d(x%d) %s>" % (self.start, self.end, self.rep, self.repseq)
  def exec_action(self, *args):
    for m1 in self.repseq:
      apply(m1.exec_action, args)
    apply(self.pat.action, (self,)+args)
    return
  def getseq(self):
    r = []
    for m1 in self.repseq:
      r.extend(m1.getseq())
    return r

class PatSeqMatch(PatMatch):
  def __init__(self, pat, start, end, subseq):
    PatMatch.__init__(self, pat, start, end)
    self.subseq = subseq
    return
  def __repr__(self):
    return "<SeqMatch: %d-%d %s>" % (self.start, self.end, self.subseq)
  def exec_action(self, *args):
    for m1 in self.subseq:
      apply(m1.exec_action, args)
    apply(self.pat.action, (self,)+args)
    return
  def getseq(self):
    r = []
    for m1 in self.subseq:
      r.extend(m1.getseq())
    return r

class PatOrMatch(PatMatch):
  def __init__(self, pat, start, end, alt, submatch):
    PatMatch.__init__(self, pat, start, end)
    self.alt = alt
    self.submatch = submatch
    return
  def __repr__(self):
    return "<OrMatch: %d-%d(%d) %s>" % (self.start, self.end, self.alt, self.submatch)
  def exec_action(self, *args):
    apply(self.submatch.exec_action, args)
    apply(self.pat.action, (self,)+args)
    return
  def getseq(self):
    return self.submatch.getseq()


##  Pattern
##
class Pattern:
  
  def __init__(self):
    self.action = lambda m: None
    return

  def setseq(self, seq):
    self.seq = seq
    return

  #
  def match_single(self, pos):
    raise NotImplementedError

  #
  def match(self, seq, start=0):
    self.setseq(seq)
    return self.match_single(start)

  # 
  def search_single(self, seq, start=0):
    for pos in range(start, len(seq)):
      for m in self.match_single(pos):
        yield m
    return
  
  def search(self, seq, start=0):
    self.setseq(seq)
    return self.search_single(seq, start)
  

##  PatItem
##
class PatItem(Pattern):
  def __init__(self, repr, pred):
    Pattern.__init__(self)
    self.repr = repr
    self.pred = pred
    return
  
  def __repr__(self):
    return "<PatItem: %s>" % (self.repr)
  
  def match_single(self, pos):
    try:
      if self.pred(self.seq[pos]):
        #print "PatItem: match_single: (%d, %d)" % (pos, pos+1)
        return [ PatItemMatch(self, pos, pos+1, self.seq[pos]) ]
    except IndexError:
      pass
    return []


##  PatRepeat
##  this class handles repetition (*, +, {}, and ?).
##
class PatRepeat(Pattern):
  
  def __init__(self, pat1, min_repeat=1, max_repeat=1):
    Pattern.__init__(self)
    self.min_repeat = min_repeat
    self.max_repeat = max_repeat
    self.pat1 = pat1
    return

  def __repr__(self):
    return "<PatRepeat: %s{%d,%d}>" % (self.pat1, self.min_repeat, self.max_repeat)
  
  def setseq(self, seq):
    self.pat1.setseq(seq)
    return
  
  def match_single(self, pos, rep=0):
    if self.max_repeat and self.max_repeat <= rep:
      return
    #print "PatRepeat: match_single: pos=%d, rep=%d, %s" % (pos, rep, self)
    # m1: find single matches
    for m1 in self.pat1.match_single(pos):
      #assert m1.start == pos
      # mnext: longer matches (greedy searching)
      for mnext in self.match_single(m1.end, rep+1):
        #print "PatRepeat: match_single: (%d, %d)+(%d, %d)" % (m1.start, m1.end, mnext.start, mnext.end)
        yield PatRepeatMatch(self, m1.start, mnext.end, rep+1, [m1]+mnext.repseq)
      # Then returns shorter matches
      if self.min_repeat <= rep+1:
        #print "PatRepeat: match_single: (%d, %d)" % (m1.start, m1.end)
        yield PatRepeatMatch(self, m1.start, m1.end, rep, [m1])
    # for empty matching
    if rep == 0 and self.min_repeat == 0:
      yield PatRepeatMatch(self, pos, pos, 0, [])
    return
  

##  PatSeq
##
class PatSeq(Pattern):
  
  def __init__(self, pat_seq):
    Pattern.__init__(self)
    assert 1 < len(pat_seq)
    self.pat_seq = pat_seq
    return
  
  def __repr__(self):
    return "<PatSeq: [%s]>" % (", ".join(map(repr, self.pat_seq)))

  def setseq(self, seq):
    for p in self.pat_seq:
      p.setseq(seq)
    return
  
  # yields a list of PatSeqMatch objects.
  def match_single(self, pos, pat_no=0):
    #assert pat_no < len(self.pat_seq)
    # last one?
    if pat_no == len(self.pat_seq)-1:
      for m1 in self.pat_seq[pat_no].match_single(pos):
        yield PatSeqMatch(self, m1.start, m1.end, [m1])
    else:
      # Obtain the first matches
      for m1 in self.pat_seq[pat_no].match_single(pos):
        # Obtain the next matches
        for mnext in self.match_single(m1.end, pat_no+1):
          #print "PatSeq: match_single:", m1.end, mnext.start
          yield PatSeqMatch(self, m1.start, mnext.end, [m1]+mnext.subseq)
    return


##  PatOr
##
class PatOr(Pattern):
  
  def __init__(self, pat_or):
    Pattern.__init__(self)
    self.pat_or = pat_or
    return
  
  def __repr__(self):
    return "<PatOr: [%s]>" % (" | ".join(map(repr, self.pat_or)))
  
  def setseq(self, seq):
    for p in self.pat_or:
      p.setseq(seq)
    return
  
  # yields a list of matches.
  def match_single(self, pos):
    i = 0
    for p in self.pat_or:
      for m1 in p.match_single(pos):
        #print "PatOr: match_single: (%d, %d)" % (m1.start, m1.end), m1.pat
        yield PatOrMatch(self, m1.start, m1.end, i, m1)
      i += 1
    return


##
##
class PatternCompileError(RuntimeError):
  pass


##
##
class PatCounter:
  def __init__(self):
    self.i = 0
    return
  
  def inc(self, x):
    i = self.i
    self.i += 1
    return (i, x)

class PatternSet:

  token_pat = re.compile(r'''
  \s* ( [,|?*+()] |                     # OPERATORS
        <[^>]*> |                       # CALL
        [^\s,|?*+(){<\["]+ |            # ITEM0
        \[[^\]]*\] |                    # ITEM1
        "(\\.|[^\\"])*" |               # ITEM2
        \{[^}]*\}                       # NREPEAT
        )''',
       re.VERBOSE)

  def __init__(self):
    self.patterns = {}
    return

  def initialize(self):
    self.pat_seq = []
    self.pat_or = []
    self.predicates = []
    self.expecting_pred = 0
    self.last_pat = None
    return

  def push_state(self):
    self.stack.append((self.pat_seq,
                       self.pat_or,
                       self.predicates,
                       self.expecting_pred,
                       self.last_pat))
    self.initialize()
    return

  def pop_state(self):
    (self.pat_seq,
     self.pat_or,
     self.predicates,
     self.expecting_pred,
     self.last_pat) = self.stack[-1]
    del(self.stack[-1])
    return

  def fix_pred(self):
    if self.expecting_pred:
      raise PatternCompileError("a predicate expected after a comma")
    if self.predicates:
      (reprs, specs) = apply(zip, self.predicates)
      self.last_pat = PatItem(",".join(reprs), self.combine_preds(specs))
      self.pat_seq.append(self.last_pat)
      self.predicates = []
      return

  def fix_repeat(self, min_repeat, max_repeat):
    self.fix_pred()
    self.last_pat = PatRepeat(self.last_pat, min_repeat, max_repeat)
    del(self.pat_seq[-1])
    self.pat_seq.append(self.last_pat)
    return
    
  def append_spec(self, repr, spec):
    if not self.expecting_pred:
      self.fix_pred()
    self.predicates.append((repr, spec))
    self.expecting_pred = 0
    return

  def parse_loop(self):
    while self.pos < len(self.tokens):
      t = self.tokens[self.pos]
      #print t
      self.pos += 1
      if t == ",":
        if not self.predicates:
          raise PatternCompileError("a predicate expected before a comma")
        self.expecting_pred = 1
      
      elif t.startswith("["):
        # PAT_ITEM1
        self.append_spec(t, self.compile_item1(t[1:-1]))
        
      elif t.startswith('"'):
        # PAT_ITEM2
        self.append_spec(t, self.compile_item2(t[1:-1]))
        
      elif t.startswith('<'):
        # PAT_CALL
        self.fix_pred()
        self.last_pat = self.patterns[t[1:-1]]
        self.pat_seq.append(self.last_pat)
        
      elif t == "*":
        # ASTERISK
        self.fix_repeat(0, 0)
        
      elif t == "+":
        # PLUS
        self.fix_repeat(1, 0)
      
      elif t == "?":
        # INTERROGATIVE
        self.fix_repeat(0, 1)
      
      elif t.startswith("{"):
        # PAT_NREPEAT
        self.fix_pred()
        x = t[1:-1].split(",")
        if len(x) == 1:
          n = int(x[0])
          self.fix_repeat(n, n)
        elif len(x) == 2:
          self.fix_repeat(int(x[0]), int(x[1]))
        else:
          raise PatternCompileError("illegal range")
        
      elif t == "|":
        self.fix_pred()
        if not self.pat_seq:
          raise PatternCompileError("empty or")
        self.pat_or.append(self.pat_seq)
        self.pat_seq = []
        
      elif t == "(":
        self.fix_pred()
        self.push_state()
        p = self.parse_loop()
        self.pop_state()
        self.last_pat = p
        self.pat_seq.append(self.last_pat)
      
      elif t == ")":
        self.fix_pred()
        if not self.stack:
          raise PatternCompileError("illegal closing parenthesis")
        break
      
      else:
        # PAT_ITEM0
        self.append_spec(t, self.compile_item0(t))

    if self.stack and t != ")":
      raise PatternCompileError("unclosed parenthesis")
    self.fix_pred()
    if not self.pat_seq:
      raise PatternCompileError("empty pattern")
    self.pat_or.append(self.pat_seq)
    def getpat(pat_seq):
      if len(pat_seq) == 1:
        # pat_or[0] == pat_seq
        return pat_seq[0]
      return PatSeq(pat_seq)
    if len(self.pat_or) == 1:
      return getpat(self.pat_seq)    
    return PatOr(map(getpat, self.pat_or))

  def compile(self, patstr):
    def tokenize(s):
      i = 0
      tokens = []
      while True:
        m = self.token_pat.match(s, i)
        if not m:
          if s[i:].strip():
            raise PatternCompileError("Illegal syntax: " + repr(s[i:]))
          return tokens
        tokens.append(m.group(1))
        i = m.end(0)
    self.stack = []
    self.initialize()
    self.tokens = tokenize(patstr)
    self.pos = 0
    return self.parse_loop()

  # dummy functions
  def compile_item0(self, x):
    raise NotImplementedError
  def compile_item1(self, x):
    raise NotImplementedError
  def compile_item2(self, x):
    raise NotImplementedError
  def combine_preds(self, predicates):
    if len(predicates) == 1:
      return predicates[0]
    return lambda x: reduce(lambda r,p: r and p(x), predicates, True)


##
##
class PatternActionSet(PatternSet):
  debug_action = False
  def get_wrapper(self, n, pat, action):
    return lambda m: self.action_wrapper(n, pat, action, m)
  def __init__(self):
    PatternSet.__init__(self)
    actions = {}
    pats = []
    for n in filter(lambda s:s.startswith("pat_"), dir(self)):
      (i, p) = getattr(self, n)
      n = n[4:]
      pats.append((i, n))
      try:
        actions[n] = getattr(self, "act_"+n)
      except AttributeError:
        actions[n] = None
    pats.sort(lambda (i1,n1), (i2,n2): cmp(i1, i2))
    for (i, n) in pats:
      (i, p) = getattr(self, "pat_"+n)
      pat1 = self.compile(p)
      self.patterns[n] = pat1
      if actions[n]:
        pat1.action = actions[n]
      if self.debug_action:
        pat1.action = self.get_wrapper(n, pat1, pat1.action)
    return

  def perform(self, n0, seq):
    pat0 = self.patterns[n0]
    for m in pat0.search(seq):
      m.exec_action()
    return

  def perform_longest_first(self, n0, seq, sieve=lambda x:1):
    pat0 = self.patterns[n0]
    matches = filter(sieve, pat0.search(seq))
    matches.sort(lambda mb,ma: cmp(ma.end-ma.start, mb.end-mb.start))
    for m1 in matches:
      m1.exec_action()
    return




#
if __name__ == "__main__":
  class MyPatternActionSet(PatternActionSet):
    c = PatCounter().inc
    debug_action = True
    def action_wrapper(self, n, pat1, action, m):
      print "called:", n, m
      return action(m)
    def compile_item0(self, x):
      return lambda t: t == x
    pat_x = c("a b? | c")
    def act_x(self, m):
      if m.alt == 0:
        print "x: a:", m.submatch.subseq[0]
      else:
        print "x: c:", m.submatch
      return
    pat_top = c("b <x>+ z?")
    def act_top(self, m):
      print "top is called"
      return
  ps = MyPatternActionSet()
  ps.perform_longest_first("top", "baaabcaaabc")
  #ps.perform_longest("top", "bac")
  
