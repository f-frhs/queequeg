#!/usr/bin/env python
##  $Id: texparser.py,v 1.1.1.1 2003/07/01 23:28:28 euske Exp $
##
##  TexTokenizer, TexParser
##

import re


##  Exceptions
##

# TexParseError: Base class for all exceptions.
class TexParseError(RuntimeError):
  pass

# TexIllegalCallback: Malformed callback method.
class TexIllegalCallback(TexParseError):
  pass

# TexInsufficientArguments: Insufficient number of arguments.
class TexInsufficientArguments(TexParseError):
  pass

# TexRunwayArgument: Premature end-of-file within arguments.
class TexRunwayArgument(TexParseError):
  pass

# TexEnvironmentMismatch: \begin and \end mismatch.
class TexEnvironmentMismatch(TexParseError):
  pass

# TexUnterminateEnvironment: Missing \end.
class TexUnterminatedEnvironment(TexParseError):
  pass

# TexUnterminatedVerb: Unterminated \verb command.
class TexUnterminatedVerb(TexParseError):
  pass



##  TexTokenizer - Retrieve a sequence of TeX tokens from a file
##
class TexTokenizer:
  
  token = re.compile(r"""
    \s* \\[a-zA-Z]+\*? \s* |            # TeX command (\spam)
    \s* \\. \s* |                       # TeX one-char command (\{)
    \s* %.*$ |                          # TeX comment (%...)
    \s* [()\[\]{}&$_^] \s* |            # TeX special characters
    \s* [^\\%()\[\]{}&$_^\s]+ \s*       # others
    """,
    re.VERBOSE)
  
  token_verb = re.compile(r"\s*\\verb([^a-zA-Z])(.+)")

  # takes a file-like object
  def __init__(self, fp):
    self.fp = fp
    self.s = ""
    self.i = 0
    return

  # obtains a token from the file and returns it.
  # NoneType is returned if it reaches at the end of file.
  def get(self):
    while 1:
      if self.s:
        m = TexTokenizer.token.match(self.s, self.i)
        if m: break
        self.s = ""
        if self.i <= len(self.s):
          return "\n"
      self.s = self.fp.readline()
      if not self.s:
        return None
      self.i = 0
      
    t = m.group(0)
    if t.strip() == "\\verb":
      # \verb hack...grrrr
      v = TexTokenizer.token_verb.match(self.s, self.i)
      if v:
        ind = v.group(2).find(v.group(1))
        if 0 <= ind:
          t = self.s[m.start(0):v.start(2)+ind+1]
          self.i = v.start(2)+ind+1
          return t

    self.i = m.end(0)
    return t


##  TexParser
##
class TexParser:

  command = re.compile(r"\s*\\[a-zA-Z]+\*?")
  charcommand = {
    "\\":"linebreak",
    ";":"thick_space",
    ":":"medium_space",
    ",":"thin_space",
    "!":"negative_thin_space",
    "-":"hyphen_or_tab_unindent",
    "=":"tab_stop",
    "+":"tab_indent",
    "'":"tab_flush",
    "`":"tab_flushright",
    ">":"tab_next",
    "<":"tab_prev",
    "(":"begin_math",
    ")":"end_math",
    "[":"begin_displaymath",
    "]":"end_displaymath",
    }
  groupchars = { "{":"}", "[":"]", "(":")" }
  end_of_verbatim = "\\end{verbatim}"

  #
  def __init__(self):
    self.curtok = None
    self.curenv = None
    self.verbatim_hack = ""
    self.env_stack = []
    self.cmd_stack = []

    self.cmd_method = None
    self.cmd_args = []
    self.cmd_opt_args = []
    self.cmd_reqargs = 0
    self.argtokens = []
    self.within_arg = 0
    self.groupend = ""
    self.finish_grouping_hook = None
    return

  # internal routines
  
  def _save(self):
    self.cmd_stack.append((self.cmd_method,
                           self.cmd_args,
                           self.cmd_opt_args,
                           self.cmd_reqargs,
                           self.argtokens,
                           self.within_arg,
                           self.groupend,
                           self.finish_grouping_hook
                       ))
    self.cmd_method = None
    self.cmd_args = []
    self.cmd_opt_args = []
    self.cmd_reqargs = 0
    self.argtokens = []
    self.within_arg = 0
    self.groupend = ""
    self.finish_grouping_hook = None
    return
  
  def _restore(self):
    x = self.cmd_stack[-1]
    del(self.cmd_stack[-1])
    (self.cmd_method,
     self.cmd_args,
     self.cmd_opt_args,
     self.cmd_reqargs,
     self.argtokens,
     self.within_arg,
     self.groupend,
     self.finish_grouping_hook
     ) = x
    return

  def _setup_callback(self, method):
    self.cmd_reqargs = method.im_func.func_code.co_argcount - 1
    if self.cmd_reqargs < 0:
      raise TexIllegalCallback(t)
    if self.cmd_reqargs == 0:
      self.handle_command(method, [])
    else:
      self.cmd_args = []
      self.cmd_method = method
    return

  def _invoke_command(self, cmd):
    try:
      method = getattr(self, "start_"+cmd)
      self.cmd_start = cmd
      try:
        self.finish_grouping_hook = getattr(self, "finish_"+cmd)
      except AttributeError:
        self.finish_grouping_hook = None
    except AttributeError:
      self.cmd_start = ""
      try:
        method = getattr(self, "do_"+cmd)
      except AttributeError:
        self.do_unknown_command(cmd)
        return
    self._setup_callback(method)
    return

  def _add_cmd_arg(self, arg1, optional=0):
    if len(arg1) == 1:
      arg1 = arg1[0]
    if optional:
      self.cmd_opt_args.append(arg1)
    else:
      self.cmd_args.append(arg1)
      self.cmd_reqargs -= 1
      if self.cmd_reqargs == 0:
        self.handle_command(self.cmd_method, self.cmd_args)
    return

  #
  def _process_data(self, s):
    if self.cmd_reqargs:
      while self.cmd_reqargs and s:
        self._add_cmd_arg(s[0])
        s = s[1:]
      if not s:
        return
    
    if self.groupend:
      if s:
        self.argtokens.append(s)
      return

    if self.finish_grouping_hook:
      if s:
        self.handle_data(s[0])
        s = s[1:]
        self._restore()        
        self.finish_grouping_hook()
        self.finish_grouping_hook = None
        if not s:
          return
    
    self.handle_data(s)
    return

  # Public Methods

  # feed: This is the main routine of the parser.
  # It takes one token and calls appropreate methods according to the token.
  def feed(self, t0):

    # First of all, we have to handle "verbatim" environment.
    # The problem here is how to find the end of the environment.
    # This is done by checking if a few past tokens make up
    # a string "\end{verbatim}". I really don't like this way. Hate Knuth.
    # Here the raw token is not stripped and may have blank characters.
    if self.curenv == "verbatim":
      self.curtok = t0
      self.verbatim_hack = (self.verbatim_hack+t0.strip())[-len(self.end_of_verbatim):]
      if self.verbatim_hack == self.end_of_verbatim:
        self.do_end("verbatim")
        return
      self.handle_data(t0)
      return

    # Strip the token.
    t = t0.strip()
    if (not t) and self.curtok == t:
      # Ignore consecutive blank lines.
      return
    self.curtok = t
    
    # Assert: Here t[0] is not a blank character.

    # Handle comments.
    if t.startswith("%"):
      self.handle_comment(t)
      return

    # Handle parentheses/brackets/braces.
    # In LaTeX, '{', '}' are annoying characters.
    # We distinguish it with the following types:
    #
    #   a. Argument grouping of a command which has a callback method do_CMD.
    #   b. LaTeX grouping command.
    #   c. Boundery of starting/ending of a command which has a callback method start_CMD/finish_CMD \cmd{ .. }
    #

    # Handling case a:
    # If previous commands require arguments, tokens grouped by
    # parentheses/brackets/braces should be processed first.
    
    # Beginning a group.
    if self.groupchars.get(t) and (self.cmd_reqargs or self.within_arg):
      # if the previous command requires any argument,
      # that is the first thing to handle with parentheses.
      self._save()
      self.groupend = self.groupchars[t]
      self.within_arg = 1
      return

    # Completing a group.
    if self.groupend and t == self.groupend:
      # if there's still a required argument,
      # the command which appeared within this grouping doesn't complete.
      if self.cmd_reqargs:
        raise TexInsufficientArguments(t)
      arg = self.argtokens
      self._restore()
      if self.cmd_reqargs:
        # if the previous command still require arguments,
        # the tokens from this group are given as an argument.
        self._add_cmd_arg(arg, t == "]")
      else:
        self.argtokens.append(arg)
      return

    # Handling case b:
    if t == "{":
      self._save()
      self.start_grouping()
      return

    if t == "}":
      self._restore()
      self.finish_grouping()
      if self.finish_grouping_hook:
        self.finish_grouping_hook()
        self.finish_grouping_hook = None
      return

    # Handling commands which begin with a backslash.
    if t.startswith("\\"):
      
      # \verb handling
      v = TexTokenizer.token_verb.match(t)
      if v:
        ind = v.group(2).find(v.group(1))
        if 0 <= ind:
          self._process_data(t[v.start(2):v.start(2)+ind])
        else:
          raise TexUnterminatedVerb(t)
        return
      
      m = TexParser.command.match(t)
      if m:
        cmd = t[1:].replace("*","_a")
      else:
        try:
          cmd = self.charcommand[t[1]]
        except KeyError:
          self._process_data(t[1])
          return
      
      self._invoke_command(cmd)
      return
    
    elif t == "$":
      if self.curenv != "math":
        self.do_begin("math")
      else:
        self.do_end("math")
      return

    elif t == "_":
      self._invoke_command("sub")
      return
      
    elif t == "^":
      self._invoke_command("sup")
      return
      
    elif t == "&":
      self._invoke_command("tablesep")
      return
      
    self._process_data(t0)
    return

  def handle_command(self, method, args):
    #print "handle_command:", method, args
    return apply(method, args)

  def handle_comment(self, cstr):
    return
  
  def handle_data(self, data):
    return

  def do_unknown_command(self, cmd):
    return

  def start_grouping(self):
    return

  def finish_grouping(self):
    return

  def begin_unknown_environment(self, env):
    return

  def end_unknown_environment(self, env):
    return

  def do_begin_math(self):
    self.do_begin("math")
    return
  def do_end_math(self):
    self.do_end("math")
    return
  def do_begin_displaymath(self):
    self.do_begin("displaymath")
    return
  def do_end_displaymath(self):
    self.do_end("displaymath")
    return

  def do_begin(self, env):
    #print "begin_env:", env
    env = env.replace("*","_a")
    if env == "verbatim":
      self.verbatim_hack = ""
    self.env_stack.append(self.curenv)
    self.curenv = env
    try:
      method = getattr(self, "begin_"+env)
    except AttributeError:
      self.begin_unknown_environment(env)
      return
    self._setup_callback(method)
    return
  
  def do_end(self, env):
    env = env.replace("*","_a")
    #print "end_env:", env
    if self.curenv != env:
      raise TexEnvironmentMismatch(self.curtok)
    self.curenv = self.env_stack[-1]
    del(self.env_stack[-1])
    try:
      method = getattr(self, "end_"+env)
    except AttributeError:
      self.end_unknown_environment(env)
      return
    self._setup_callback(method)
    return

  def close(self):
    if self.cmd_stack:
      raise TexRunwayArgument(self.curtok)
    if self.cmd_reqargs:
      raise TexInsufficientArguments(self.curtok)
    if self.curenv:
      raise TexUnterminatedEnvironment(self.curtok)
    return


# testing
if __name__ == "__main__":
  import sys
  
  class TestParser(TexParser):
    def __init__(self):
      TexParser.__init__(self)
      return
    def handle_data(self, data):
      print "handle_data:", repr(data)
      return
    def do_unknown_command(self, cmd):
      print "unknown_command:", cmd
      return
    def do_hoe(self, arg1):
      print "hoe:", arg1
      return
    def do_foo(self, arg1, arg2):
      print "foo:", arg1, arg2
      return
    def start_bar(self, arg1):
      print "start_bar:", arg1
      return
    def finish_bar(self):
      print "finish_bar."
      return

  for n in (sys.argv[1:] or ["-"]):
    if n == "-":
      f = sys.stdin
    else:
      f = file(n)
    tokenizer = TexTokenizer(f)
    parser = TestParser()
    while 1:
      t = tokenizer.get()
      if not t: break
      parser.feed(t)
    parser.close()
    f.close()
    
