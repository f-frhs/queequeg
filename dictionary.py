#!/usr/bin/env python
##  $Id: dictionary.py,v 1.2 2003/07/02 06:38:39 euske Exp $
##
##  dictionary.py - 
##

# try to load cdb
try:
  import cdb
except ImportError:
  cdb = None


##  Dictionary
##
class Dictionary:

  max_tokens = 3

  def __init__(self, fname, userdict=None):
    if fname.endswith(".cdb"):
      if not cdb:
        raise RuntimeError("cdb is not supported.")
      self.dict = cdb.init(fname)
    else:
      self.dict = {}
      fp = file(fname)
      while True:
        s = fp.readline()
        if not s: break
        f = s.split("\t")
        self.dict[f[0]] = f[1]
    return

  def lookup_string1(self, s):
    try:
      e = self.dict[s]
    except KeyError:
      s = s[0].lower() + s[1:]          # try lower case
      try:
        e = self.dict[s]
      except KeyError:
        return []
    poss = []
    for x in e.split(","):
      (pos, f) = x.split(":")
      poss.append(pos)
    return poss

