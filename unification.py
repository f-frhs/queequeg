#!/usr/bin/env python
##  $Id: unification.py,v 1.1.1.1 2003/07/01 23:28:28 euske Exp $
##
##  unification.py - Unification
##

import sys


##  Utility functions
##
def forall(pred, elements):
  return reduce(lambda r,x: r and pred(x), elements, True)

def exists(pred, elements):
  return reduce(lambda r,x: r or pred(x), elements, False)


##  Exceptions
##
class UnificationError(RuntimeError):
  pass

class UnificationTypeError(UnificationError):
  pass

class UnificationValueError(UnificationError):
  pass

class UnificationStructureError(UnificationError):
  pass


##  Unifier
##
class Unifier:
  
  def __init__(self, **args):
    self.slots = args
    return

  def __repr__(self):
    keys = self.slots.keys()
    keys.sort()
    return '<Unifier: %s>' % (", ".join(map(lambda k: "%s=%s" % (k, self.slots[k]), keys)))

  # deep copy
  def copy(self):
    new = Unifier()
    for (k, v) in self.slots:
      if isinstance(v, Unifier):
        v = v.copy()
      new.slots[k] = v
    return new

  def assign(self, k, v):
    #print "assign:", self, k, v
    self.slots[k] = v
    return

  def type_mismatch(self, k, v):
    raise UnificationTypeError(self, k, v)

  def value_mismatch(self, k, v):
    raise UnificationValueError(self, k, v)

  def structure_mismatch(self, k, v, e):
    raise UnificationStructureError(self, k, v, e)
  
  def unify(self, other):
    assert isinstance(other, Unifier)
    self_items = self.slots.items()
    other_items = other.slots.items()
    for (k, v) in other_items:
      try:
        self[k] = v
      except UnificationError, e:
        self.structure_mismatch(k, v, e)
    for (k, v) in self_items:
      try:
        other[k] = v
      except UnificationError, e:
        other.structure_mismatch(k, v, e)
    return
  
  def __getitem__(self, k):
    return self.slots.get(k, None)

  def __setitem__(self, k, v):
    #print "setitem: %s [%s] = %s" % (self, k, v)
    if self.slots.get(k, None) == None:
      self.assign(k, v)
      return
    if v == None:
      return
    # assert: self.slots[k] does exist and is not None.
    if self.slots[k] is v:
      return
    if type(self.slots[k]) != type(v):
      # type mismatch
      self.type_mismatch(k, v)
      return
    # assert: self.slots[k] and v has the same type.
    if not isinstance(v, Unifier):
      if self.slots[k] != v:
        # value mismatch
        self.value_mismatch(k, v)
      return
    # assert: self.slots[k] and v is both a Unifier.
    self.slots[k].unify(v)
    return

    
#
if __name__ == "__main__":
  x = Unifier(a=1, b=0, z=Unifier(c=5))
  y = Unifier(a=1, c=3, z=Unifier(c=4), b=None)
  x.unify(y)
  print x
  print y
