#!/usr/bin/env python
##  $Id: sentence.py,v 1.3 2003/07/27 13:54:05 euske Exp $
##
##  sentence.py - Sentence Analyzer
##

import sys, re, string
import pstring


from dictionary import Dictionary
from abstfilter import AbstractFeeder, AbstractFilter, AbstractConsumer
from document import PlainTextProcessor


# I'm a ``hoge'' rat-a-tat.
# -> "I'm", "a", "``", hoge, "''", "rat-a-tat", "."
#
class TextTokenizer(AbstractFilter):

  # 
  token = re.compile(r"""
  (\s*) ( `` | '' |                     # TeX quotations
          [0-9]*[A-Za-z]+[0-9]* |       # ordinary words, like "spam", "7th" ...
          [-0-9]+(\.[0-9]+)? |          # numeric
          \[\[ | \]\] |                 # special parenthesis
          \S                            # other stuff (except those included in wordparts)
          )""",
          re.VERBOSE)
  # 
  wordpart = [ "`", "'", "/", "-" ]

  def __init__(self, next_filter):
    AbstractFilter.__init__(self, next_filter)
    self.t = ""
    return

  def feed(self, s):
    if s == None:
      if self.t:
        self.feed_next(self.t)
        self.t = ""
      self.feed_next(None)
      return
    while 1:
      m = self.token.match(s)
      if not m:
        if self.t:
          self.feed_next(self.t)
          self.t = ""
        break
      t = m.group(2)
      #print "%s,%s,%s,%s,'%s'" % (s,m.group(0), m.group(1), m.group(2), s[len(m.group(0)):])
      if t.isalpha():
        if self.t.isalpha() or (self.t and m.group(1)):
          self.feed_next(self.t)
          self.t = t
        else:
          self.t = self.t + t
      elif self.t and t in self.wordpart:
        self.t = self.t + t
      else:
        if self.t:
          self.feed_next(self.t)
          self.t = ""
        self.feed_next(t)
      s = s[len(m.group(0)):]
    return

  def close(self):
    self.feed(None)
    AbstractFilter.close(self)
    return


#
class SentenceSplitter(AbstractFilter):

  eos = [ ".", ":", ";" ]
  paren = { "[[":"]]", "(":")", "[":"]", "{":"}", "``":"''", '"':'"' }

  def __init__(self, next_filter):
    AbstractFilter.__init__(self, next_filter)
    self.init()
    return

  def init(self):
    self.stack = []
    self.initsent()
    return

  def initsent(self):
    self.sents = []
    self.tokens = []
    self.closing = None
    return

  def open_paren(self, p):
    self.stack.append((self.sents, self.tokens, self.closing))
    self.initsent()
    self.sents.append(p)
    self.closing = self.paren[p]
    return

  def close_paren(self):
    if self.tokens:
      self.sents.append(self.tokens)
    period = self.tokens and self.tokens[-1] == "."
    self.sents.append(self.closing)
    t = self.sents
    (self.sents, self.tokens, self.closing) = self.stack[-1]
    del(self.stack[-1])
    self.tokens.append(t)
    # handle '."' case
    if period:
      self.tokens.append(".")
    return

  def feed(self, t):
    # t == None: force paragraph boundary
    if not t:
      r = reduce(lambda r,x: r+x, map(lambda (s,t,c): s, self.stack), []) + self.tokens
      self.init()
      if r:
        self.feed_next(r)
      return

    # assert: self.tokens contain either strs or lists.
    if t == self.closing:
      self.close_paren()
    elif self.paren.get(t):
      self.open_paren(t)
      return
    else:
      #print "add:", t
      self.tokens.append(t)
    if len(self.tokens) < 2:
      return
    
    # assert: self.tokens[-1] and self.tokens[-2] exist.
    if 3 <= len(self.tokens):
      (prev, cur, next) = self.tokens[-3:]
    else:
      (cur, next) = self.tokens[-2:]
      prev = ""

    # skip the period as a part of noun groups.
    if cur not in self.eos:
      return
    if (type(prev) != list and cur == "." and type(next) != list) and \
       (prev.isalpha() and next.isalpha()) and \
       ((len(prev) == 1 and prev[0].isupper()) or (not next[0].isupper())):
      return
    
    r = self.tokens[:-1]
    self.tokens = [next]
    if r:
      if self.closing:
        self.sents.append(r)
      else:
        self.feed_next(r)
    return

  def close(self):
    self.feed(None)
    AbstractFilter.close(self)
    return


##  WordToken
##
class WordToken:
  def __init__(self, sent, wid, s, pos):
    self.sent = sent
    self.s = s
    self.wid = wid
    self.pos = pos
    self.pos_pref = None
    self.is_sent = isinstance(s, Sentence)
    self.processed = False
    return
  
  def __repr__(self):
    if self.is_sent:
      return repr(self.s)
    else:
      if self.pos_pref:
        return '"%s"(%s:%s)' % (self.s, self.pos_pref, "|".join(self.pos))
      else:
        return '"%s"(%s)' % (self.s, "|".join(self.pos))

  def __str__(self):
    return str(self.s)


class Sentence:
  
  sid_base = 0
  
  def __init__(self, parent):
    self.sid = Sentence.sid_base
    Sentence.sid_base += 1
    self.words = []
    self.parent = parent
    return
  
  def add_word(self, t, pos):
    self.words.append(WordToken(self, len(self.words), t, pos))
    return
  
  def __repr__(self):
    return '<Sentence: %s>' % (" ".join(map(repr, self.words)))

  def __str__(self):
    return " ".join(map(str, self.words))

##
##
class POSTagger(AbstractFilter):

  max_tokens = 3
  is_number_pdt = re.compile("^-?[0-9]+(\.[0-9]+)?$")
  is_number_cd = re.compile("^[0-9]+th$")
  special_ends = re.compile(r"(.+)('(s|m|d|re|ve|ll|em|cause))")

  def __init__(self, dict, next_filter):
    AbstractFilter.__init__(self, next_filter)
    self.dict = dict
    return

  def lookup_longest_seq(self, seq, i):
    x = seq[i]
    if self.is_number_pdt.match(x):
      return (i+1, [(x, ["PDT", "num"])])
    if self.is_number_cd.match(x):
      return (i+1, [(x, ["CD", "num"])])
    if len(x) == 1 and not x.isalpha():
      return (i+1, [(x, ["."])])
    if 0 < i and x[0].isupper():
      return (i+1, [(x, ["NNR", "cap"])])
    # lookup dict
    for n in range(self.max_tokens, 0, -1):
      if filter(lambda t: type(t) == list, seq[i:i+n]):
        continue
      x = string.join(seq[i:i+n], "_")
      pos = self.dict.lookup_string1(str(x))
      if pos:
        return (i+n, [(x, pos)])
    # special end - lookup again
    if x.endswith("s'"):
      (x, words1) = self.lookup_longest_seq([x[:-2]], 0)
      (x, words2) = self.lookup_longest_seq(["'s"], 0)
      return (i+1, words1+words2)
    elif x.endswith("n'"):
      (x, words) = self.lookup_longest_seq([x[:-2]+"ng"], 0)
      return (i+1, words)
    else:
      m = self.special_ends.match(x)
      if m:
        (x, words1) = self.lookup_longest_seq([m.group(1)], 0)
        (x, words2) = self.lookup_longest_seq([m.group(2)], 0)
        return (i+1, words1+words2)
    # unknown word
    if x.endswith("s"):
      return (i+1, [(x, ["NNS", "unknown"])])
    return (i+1, [(x, ["NN", "unknown"])])

  def process(self, tokens, parent=None):
    i = 0
    sent1 = Sentence(parent)
    while i < len(tokens):
      t = tokens[i]
      if type(t) == list:
        sent1.add_word(self.process(t, self), ["NNR"])
        i += 1
      else:
        (i, words) = self.lookup_longest_seq(tokens, i)
        for (t, pos) in words:
          sent1.add_word(t, pos)
    return sent1


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
  #pipeline = docproc(TextTokenizer(out))
  #pipeline = docproc(TextTokenizer(SentenceSplitter(out)))
  pipeline = docproc(TextTokenizer(SentenceSplitter(POSTagger(dict, out))))
  pipeline.read(pstring.PFile(sys.stdin))
