#!/usr/bin/env python
##  $Id: grammarerror.py,v 1.1.1.1 2003/07/01 23:28:28 euske Exp $
##
##  error.py - Objects representing grammatical errors
##


# abstract one
class GrammarCheckError:
  pass


# number not agreed
class GrammarNounAgreementError(GrammarCheckError):
  msg = "noun_number"
  def __init__(self, mdet, mnoun):
    self.mdet = mdet
    self.mnoun = mnoun
    return
  def __repr__(self):
    return '<GrammarNounAgreementError: det=%s, noun=%s>' % \
           (self.mdet, self.mnoun)

class GrammarVerbAgreementError(GrammarCheckError):
  msg = "verb_number"
  def __init__(self, mng, mvg):
    self.mng = mng
    self.mvg = mvg
    return
  def __repr__(self):
    return '<GrammarVerbAgreementError: det=%s, noun=%s>' % \
           (self.mng, self.mvg)
  
class GrammarNonDeterminerError(GrammarCheckError):
  msg = "no_determiner"
  def __init__(self, mng):
    self.mng = mng
    return
  def __repr__(self):
    return '<GrammarNonDeterminerError: noun=%s>' % \
           (self.mng)

