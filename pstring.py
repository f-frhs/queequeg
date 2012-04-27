#!/usr/bin/env python
##  $Id: pstring.py,v 1.2 2003/07/27 13:54:05 euske Exp $
##
##  PFile, PString
##
##      PString is a string object which remembers its origin
##      (mainly at a certain location of a file). It preserves its
##      origin across decompositional operations such as slicing,
##      splitting, matching to regexps, etc. This is convenient to
##      track the origin of a string for reporting errors or
##      retrieving original documents which contain the string.
##
##      PFile is a wrapper object of a file-like object,
##      which provides interfaces to obtain PString from a file.
##
##  by Yusuke Shinyama, May 2003
##

from UserString import UserString
import re, string


##  PMatch - Pseudo re.Match objects for PString.
##
##      This class is for regexp matching for PString objects.
##      Instances of this class are to only be referred to by a user.
##      Class instances are internally created by PString.search or
##      PString.match functions and containing equivalent information
##      as re.Match objects. (not 100% compatible though...)
##
class PMatch:
  
  def __init__(self, groups, starts, ends):
    self._groups = groups
    self._starts = starts
    self._ends = ends
    return

  # returns a list of the matching groups. default argument is ignored.
  def groups(self, default=None):
    return self._groups

  # returns the matching group(s).
  def group(self, *args):
    if not args:
      return self._groups[0]
    elif len(args) == 1:
      return self._groups[args[0]]
    else:
      return map(lambda i:self._groups[i], args)

  # returns the beginning location of the match.
  def start(self, i=0):
    return self._starts[i]
  
  # returns the ending location of the match.
  def end(self, i=0):
    return self._ends[i]


##  PString - Position-aware Strings
##
##      This string class can be used in the same manner as
##      normal string, except several functionalities. Although a user
##      can create PString objects from scratch, usually this is
##      obtained from PFile.read() or PFile.readline() functions.
##
##      A PString object holds the folloing public attributes:
##
##          f:      the file-like object which contains the string.
##          pos:    the position in the file at which the string starts.
##          line:   the line number in which the string starts.
##          col:    the column at which the string starts.
##
##      Changing your program to use PString object is not transparent.
##      One major incompatibility of this class is that you
##      have to use re_search() or re_match() to search/match
##      for regexp objects respectively. Otherwise you'll get
##      a coerced string object, which doesn't know its origin at all..
##
##      Note that any compositional operation such as concatination
##      ends up with losting its origin information, since it coerces
##      the object into a normal str object.
##
class PString(UserString):

  # PString: A user can specify the origin of the string.
  def __init__(self, data='', f=None, pos=0, line=0, col=0):
    UserString.__init__(self, data)
    self.f = f
    self.pos = pos
    self.line = line
    self.col = col
    return

  # repr
  def __repr__(self):
    return repr(self.data)+'(%s,pos=%d,line=%d,col=%d)' % \
           (self.f.name, self.pos, self.line, self.col)

  # nonzero
  def __nonzero__(self):
    return len(self.data)

  # slicing preserves the origin.
  def __getslice__(self, start, end):
    if start == 0 and end == len(self.data):
      return self
    # calculate the location of the substring.
    s = self.data[:start]
    try:
      col = len(s) - s.rindex("\n") - 1
    except ValueError:
      col = self.col+len(s)
    return PString(self.data[start:end], self.f, self.pos+start,
                   self.line+s.count("\n"), col)

  def __getitem__(self, start):
    return self.__getslice__(start, start+1)

  def __add__(self, other):
    return PString(self.data+other, self.f, self.pos, self.line, self.col)
  def __radd__(self, other):
    if isinstance(other, PString):
      return PString(other.data+self.data, other.f, other.pos, other.line, other.col)
    elif other == "":
      return self
    else:
      return other + self.data
  def __iadd__(self, other):
    self.data += other
    return self
  def __mul__(self, n):
    return PString(self.data * n, self.f, self.pos, self.line, self.col)
  def __imul__(self, n):
    self.data *= n
    return self
  def copy(self):
    return PString(self.data, self.f, self.pos, self.line, self.col)
  def find(self, c):
    return self.data.find(str(c))
  def index(self, c):
    return self.data.index(str(c))
  
  # internal routine for tailoring re.Match results.
  def _get_pmatch(self, m):
    if not m:
      return m
    groups = []
    starts = []
    ends = []
    for i in range(1+len(m.groups())):    # yeah, I know my inefficiency, forgive me.
      starts.append(m.start(i))
      ends.append(m.end(i))
      groups.append(self[m.start(i):m.end(i)])
    return PMatch(groups, starts, ends)

  # splitting. Python built-in split routine coerces it
  # to a normal str object, so I borrowed this from Python1.5.
  def split(self, sep=' ', maxsplit=0):
    res = []
    nsep = len(sep)
    if nsep == 0:
      return [self]
    ns = len(self)
    if maxsplit <= 0: maxsplit = ns
    i = j = 0
    count = 0
    while j+nsep <= ns:
      if self.data[j:j+nsep] == sep:
        count = count + 1
        res.append(self[i:j])
        i = j = j + nsep
        if count >= maxsplit: break
      else:
        j = j + 1
    res.append(self[i:])
    return res

  # strip: from Python1.5
  def strip(self):
    i, j = 0, len(self)
    while i < j and self.data[i] in string.whitespace: i = i+1
    while i < j and self.data[j-1] in string.whitespace: j = j-1
    return self[i:j]
  # lstrip: from Python1.5
  def lstrip(self):
    i, j = 0, len(self)
    while i < j and self.data[i] in string.whitespace: i = i+1
    return self[i:j]
  # rstrip: from Python1.5
  def rstrip(self):
    i, j = 0, len(self)
    while i < j and self.data[j-1] in string.whitespace: j = j-1
    return self[i:j]

  # regexp search
  def re_search(self, regex, pos=0, endpos=-1):
    if endpos == -1:
      return self._get_pmatch(regex.search(self.data, pos))
    else:
      return self._get_pmatch(regex.search(self.data, pos, endpos))

  # regexp match
  def re_match(self, regex, pos=0, endpos=-1):
    if endpos == -1:
      return self._get_pmatch(regex.match(self.data, pos))
    else:
      return self._get_pmatch(regex.match(self.data, pos, endpos))



##  HACK
def join(words, sep = ' '):
  if not words:
    return ''
  res = words[0]
  for w in words[1:]:
    res = res + sep + w
  return res

string.join = join

class PRegexp:

  def __init__(self, pattern, flags=0):
    self.pattern = pattern
    self.flags = flags
    self.regex = re.compile_orig(pattern, flags)
    return
  
  def match(self, s, pos=0, endpos=-1):
    if isinstance(s, PString):
      return s.re_match(self.regex, pos, endpos)
    elif endpos == -1:
      return self.regex.match(s, pos)
    else:
      return self.regex.match(s, pos, endpos)
  
  def search(self, s, pos=0, endpos=-1):
    if isinstance(s, PString):
      return s.re_search(self.regex, pos, endpos)
    elif endpos == -1:
      return self.regex.search(s, pos)
    else:
      return self.regex.search(s, pos, endpos)
  
  def sub(self, r, s, count=0):
    if isinstance(s, PString):
      s = str(s)
    return self.regex.sub(r, s, count)
  
  def subn(self, r, s, count=0):
    if isinstance(s, PString):
      s = str(s)
    return self.regex.subn(r, s, count)

def re_wrapper_compile(pattern, flags=0):
  return PRegexp(pattern, flags)

def re_wrapper_search(pattern, s, flags=0):
  if isinstance(s, PString):
    return s.re_search(re.compile_orig(pattern, flags), pos)
  else:
    return re.search_orig(pattern, s, flags)

def re_wrapper_match(pattern, s, flags=0):
  if isinstance(s, PString):
    return s.re_match(re.compile_orig(pattern, flags), pos)
  else:
    return re.match_orig(pattern, s, flags)

# only once.
if re.match != re_wrapper_match:
  re.match_orig = re.match
  re.match = re_wrapper_match
if re.search != re_wrapper_search:
  re.search_orig = re.search
  re.search = re_wrapper_search
if re.compile != re_wrapper_compile:
  re.compile_orig = re.compile
  re.compile = re_wrapper_compile




##  PFile - A wrapper object which produces PString objects.
##
##      Probably PFile is the only class you will call whose
##      constructor directly. This is a simple wrapper object
##      for a file-like object and holds the current line numbers
##      and columns. You can obtain PString objects by calling
##      read() or readline() method of this object.
##
class PFile:

  # PFile: takes a file-like object.
  # Optional arguments line and col specify the beginning line number
  # and columns.
  def __init__(self, f, line=0, col=0):
    self.f = f
    try:
      self.pos = f.tell()
    except IOError:                     # in case of sys.stdin
      self.pos = 0
    (self.line, self.col) = (line, col) # cursor
    return

  # repr
  def __repr__(self):
    return "<PString: f=%s, line=%d, col=%d>" % (self.f, self.line, self.col)

  # advences the internal cursor (line number and columns).
  def __proceed(self, s, line, col):
    if line != None:
      self.line = line
    if col != None:
      self.col = col
    self.line += s.count("\n")
    try:
      self.col = len(s) - s.rindex("\n") - 1
    except ValueError:
      self.col += len(s)
    return

  # same as file.readline()
  def readline(self, size=-1, line=None, col=None):
    pos0 = self.pos
    (line0, col0) = (self.line, self.col)
    s = self.f.readline(size)
    self.pos += len(s)
    # if you're handling multibyte characters, convert it to unicode here.
    #s = unicode(s)
    self.__proceed(s, line, col)
    return PString(s, self.f, pos0, line0, col0)

  # seek
  def seek(self, offset, whence=0):
    self.f.seek(offset, whence)
    self.pos = self.f.tell()
    return
  
  # same as file.read()
  def read(self, size=-1, line=None, col=None):
    pos0 = self.pos
    (line0, col0) = (self.line, self.col)
    s = self.f.read(size)
    self.pos += len(s)
    # if you're handling multibyte characters, convert it to unicode here.
    #s = unicode(s)
    self.__proceed(s, line, col)
    return PString(s, self.f, pos0, line0, col0)


#  test sample
#
if __name__ == "__main__":
  import StringIO,re
  f=PFile(StringIO.StringIO("hoge\n12 34 5"))
  s1=f.read(3)
  s2=f.read(10)
  print repr(s1)
  print repr(s2)
  print repr(s1[1:2])
  print repr(s2[4].strip())
  print s2.split(" ")
  print "a" in s1
  m=re.compile("(34)").search(s2)
  print m.groups()
