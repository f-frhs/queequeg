#!/usr/bin/env python
##
##  convdict.py - WordNet Dictionary converter
##

from __future__ import generators
import re

# try to load cdb
import sys
try:
  import cdb
except ImportError:
  cdb = None


# cut off postags which account less than 3% of all occurrences.
POS_THRESHOLD = 0.03


pat_ys = re.compile(r".*[^auieo]y$")

# Crude pluralizer

def get_s(s):
  if s.endswith("s"):
    return s[:-1]+"ses"
  elif s.endswith("x"):
    return s[:-1]+"xes"
  elif s.endswith("z"):
    return s[:-1]+"zes"
  elif pat_ys.match(s):
    return s[:-1]+"ies"
  elif s.endswith("ch"):
    return s[:-2]+"ches"
  elif s.endswith("sh"):
    return s[:-2]+"shes"
  elif s.endswith("man"):
    return s[:-3]+"men"
  else:
    return s+"s"

def get_plural(s, exc):
  x = exc.get(s)
  if x: return x
  return get_s(s)

def get_mw(w, f, exc):
  return f(w[0], exc)+"_"+"_".join(w[1:])

def get_pres3rd(s, exc):
  x = exc.get(s)
  if x: return x
  w = s.split("_")
  if 1 < len(w):
    return get_mw(w, get_pres3rd, exc)
  return get_s(s)

def get_past(s, exc):
  x = exc.get(s)
  if x: return x
  w = s.split("_")
  if 1 < len(w):
    return get_mw(w, get_past, exc)
  if s.endswith("e"):
    return s+"d"
  else:
    return s+"ed"

def get_pastpart(s, exc):
  x = exc.get(s)
  if x: return x
  w = s.split("_")
  if 1 < len(w):
    return get_mw(w, get_pastpart, exc)
  return get_past(s, exc)

def get_gerund(s, exc):
  x = exc.get(s)
  if x: return x
  if s == "see":
    return "seeing"
  elif s.endswith("e"):
    return s[:-1]+"ing"
  else:
    return s+"ing"

def get_comparative(s, exc):
  x = exc.get(s)
  if x: return x
  if s.endswith("e"):
    return s+"r"
  elif s.endswith("y"):
    return s+"ier"
  else:
    return s+"er"

def get_superlative(s, exc):
  x = exc.get(s)
  if x: return x
  if s.endswith("e"):
    return s+"st"
  elif s.endswith("y"):
    return s+"iest"
  else:
    return s+"est"

  
class DictionaryConverter:

  comment = re.compile(r"#.*$")
  cntlist_pat = re.compile(r"^([^%]+)%\d+:(\d+):\d+:[^ ]* +\d+ +(\d+)$")

  def __init__(self, verbose=1):
    self.dict = {}
    self.special = {}
    self.wordnet_dir = None
    self.verbose = verbose
    return

  def msg(self, *args):
    if self.verbose:
      print >>sys.stderr, " ".join(map(str, args))
    return

  def add_pos_forcibly(self, s, pos, freq=0):
    try:
      self.dict[s][pos] = self.dict[s].get(pos, 0) + freq
    except KeyError:
      self.dict[s] = { pos: freq }
    return

  def add_pos(self, s, pos, freq):
    try:
      if pos not in self.special[s]:
        self.msg('Skipped: "%s": %s' % (s, pos))
        return
    except KeyError:
      self.add_pos_forcibly(s, pos, freq)
    return

# Read the .exc files in the wordnet distribution.

  def read_exc(self, fname):
    fname = self.wordnet_dir+"/"+fname+".exc"
    self.msg("Reading: %s..." % (fname))
    fp = file(fname)
    while True:
      s = fp.readline()
      if not s: break
      s = self.comment.sub("", s).strip()
      if not s: continue
      f = s.split(" ")
      yield (f[1], f[0])
    fp.close()
    return

  def read_noun_exc(self):
    self.nns_exc = {}
    for (s0, s1) in self.read_exc("noun"):
      self.nns_exc[s0] = s1
    return
    
  def read_adj_exc(self):
    self.jjr_exc = {}
    self.jjs_exc = {}
    for (s0, s1) in self.read_exc("adj"):
      if s1.endswith("r"):
        self.jjr_exc[s0] = s1
      elif s1.endswith("t"):
        self.jjs_exc[s0] = s1
    return

  def read_adv_exc(self):
    self.rbr_exc = {}
    self.rbs_exc = {}
    for (s0, s1) in self.read_exc("adv"):
      if s1.endswith("r"):
        self.rbr_exc[s0] = s1
      elif s1.endswith("t"):
        self.rbs_exc[s0] = s1
    return

  pat_past = re.compile(r"[^_]+([deklmtwy]|ang?|on)_")
  pat_pastpart = re.compile(r"[^_]+(ne|ung|en|ain|rn|un|wn)_")
  pat_gerund = re.compile(r"[^_]+ing_")
  def read_verb_exc(self):
    self.vbz_exc = {}
    self.vbd_exc = {}
    self.vbn_exc = {}
    self.vbg_exc = {}
    for (s0, s1) in self.read_exc("verb"):
      if s1.endswith("s"):
        self.vbz_exc[s0] = s1
      elif self.pat_past.match(s1+"_") and not s1.endswith("ne"):
        self.vbd_exc[s0] = s1
      elif self.pat_pastpart.match(s1+"_"):
        self.vbn_exc[s0] = s1
      elif self.pat_gerund.match(s1+"_"):
        self.vbg_exc[s0] = s1
    return

  def read_cntlist_rev(self):
    fname = self.wordnet_dir+"/cntlist.rev"
    self.msg("Reading: %s..." % (fname))
    fp = file(fname)
    while True:
      s = fp.readline()
      if not s: break
      m = self.cntlist_pat.match(s.strip())
      if not m: continue
      yield (m.group(1), int(m.group(2)), int(m.group(3)))
    fp.close()
    return

  def read_special(self, fname):
    self.msg("Reading: %s..." % (fname))
    fp = file(fname)
    while True:
      s = fp.readline()
      if not s: break
      s = self.comment.sub("", s).strip()
      if not s: continue
      f = s.split("\t")
      yield (f[0], f[1])
    fp.close()
    return

  def read(self, special_file, wordnet_dir):
    self.wordnet_dir = wordnet_dir

    for (s, pos) in self.read_special(special_file):
      if pos.startswith("!"):
        pos = pos[1:]
        try:
          self.special[s].append(pos)
        except KeyError:
          self.special[s] = [pos]
      self.add_pos_forcibly(s, pos)
    
    self.read_noun_exc()
    self.read_adj_exc()
    self.read_adv_exc()
    self.read_verb_exc()
    
    for (s, n, freq) in self.read_cntlist_rev():
      if n == 0 or n == 1 or n == 44:   # adj
        if "_" in s: continue
        self.add_pos(s, "JJ", freq)
        self.add_pos(get_comparative(s, self.jjr_exc), "JJR", freq)
        self.add_pos(get_superlative(s, self.jjs_exc), "JJS", freq)
      elif n == 2:                      # adv
        if "_" in s: continue
        self.add_pos(s, "RB", freq)
        self.add_pos(get_comparative(s, self.rbr_exc), "RBR", freq)
        self.add_pos(get_superlative(s, self.rbs_exc), "RBS", freq)
      elif 3 <= n and n <= 28:          # noun
        self.add_pos(s, "NN", freq)
        self.add_pos(get_plural(s, self.nns_exc), "NNS", freq)
      elif 29 <= n and n <= 43:         # verb
        self.add_pos(s, "VB", freq)
        self.add_pos(s, "VBP", freq)
        self.add_pos(get_pres3rd(s, self.vbz_exc), "VBZ", freq)
        self.add_pos(get_past(s, self.vbd_exc), "VBD", freq)
        self.add_pos(get_pastpart(s, self.vbn_exc), "VBN", freq)
        if not "_" in s:
          self.add_pos(get_gerund(s, self.vbg_exc), "VBG", freq)
      else:
        assert 0, (s, n, freq)
        
    return self

  def filter_unusual(self):
    for (w, poss) in self.dict.iteritems():
      t = reduce(lambda r,x: r+x, poss.itervalues())
      if t == 0: continue
      for (pos, f) in poss.items():
        if f and float(f)/t < POS_THRESHOLD:
          self.msg('Removed: "%s": %s (%d/%d)' % (w, pos, f, t))
          del(poss[pos])
    return

  def write(self, outfile=""):
    if outfile.endswith(".cdb"):
      self.msg("Writing to CDB: %s..." % (outfile))
      out = cdb.cdbmake(outfile, outfile+".tmp")
      for (w, poss) in self.dict.iteritems():
        s = map(lambda pf:"%s:%s" % pf, poss.iteritems())
        out.add(w, ",".join(s))
      out.finish()
    else:
      self.msg("Writing to plaintext: %s..." % (outfile))
      if outfile:
        fp = file(outfile, "w")
      else:
        fp = sys.stdout
      for (w, poss) in self.dict.iteritems():
        s = map(lambda pf:"%s:%s" % pf, poss.iteritems())
        fp.write(w+"\t"+",".join(s)+"\n")
      fp.close()
    return


# main
if __name__ == "__main__":
  if len(sys.argv) < 3:
    print >>sys.stderr, "usage: convdict.py special wordnet_dir [outfile ...]"
    sys.exit(2)

  (special_file, wordnet_dir, outfiles) = (sys.argv[1], sys.argv[2], sys.argv[3:])
  if not cdb and filter(lambda n: n.endswith(".cdb"), outfiles):
    print >>sys.stderr, "cdb is not supported."
    sys.exit(3)
    
  d = DictionaryConverter()
  d.read(special_file, wordnet_dir)
  if not outfiles:
    if cdb:
      print >>sys.stderr, "cdb is supported. writing to dict.cdb."
      outfiles = ["dict.cdb"]
    else:
      print >>sys.stderr, "cdb is not supported. writing to dict.txt."
      outfiles = ["dict.txt"]
  d.filter_unusual()
  for outfile1 in outfiles:
    d.write(outfile1)
  
