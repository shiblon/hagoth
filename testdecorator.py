"""Decorator functions
"""

def register_antecedent(antecedent, rule, registry):
  pass

def register_consequent(consequent, rule, registry):
  pass

class Var(object):
  """A variable, consisting of a name and potentially an assignment"""
  def __init__( self, name, value=None ):
    """Create a variable with the given name, maybe assigning a value
      
      >>> v = Var('name', 'val')
      >>> v
      Var('name', 'val')
      >>> v.name
      'name'
      >>> v.value
      'val'
      >>> Var('justaname')
      Var('justaname')
    """
    self.name = name
    self.value = value

  def __repr__( self ):
    if self.value is None:
      return "Var('%s')" % self.name
    else:
      return "Var('%s', '%s')" % (self.name, self.value)

class Predicate(object):
  """A predicate.
  
    - Can be matched with other predicates.
    - Can contain variables.
  """
  def __init__( self ):
    self.vars = []

class FilePattern(Predicate):
  def __init__( self, pattern ):
    """Parses the pattern into an internal representation.
    
      The representation can be used for matching, and contains a list of the
      variables in the pattern.  The input is designed to follow the format of
      3.0 substitution strings, e.g.

      "{base}.cc"
      "myfile-{number}.{ext}"

      >>> fp = FilePattern("myfile-{number}.{ext}")
      >>> fp.pattern
      'myfile-{number}.{ext}'
    """
    super(FilePattern, self).__init__()
    self.pattern = pattern
    # TODO: Parse the string

  @staticmethod
  def _components( tokens ):
    """ Returns the main components, split into consts and vars.

      Variable names may not contain braces

      >>> FP = FilePattern
      >>> list(FP._components(FP._tokens("ab{cde}fg}}{{{hi}")))
      ['ab', Var('cde'), 'fg}{', Var('hi')]
      >>> try:
      ...   list(FP._components(FP._tokens("{abc}{}")))
      ... except ValueError, e:
      ...   print e
      Empty variable name
      >>> list(FP._components(FP._tokens("{abc}d")))
      [Var('abc'), 'd']
      >>> list(FP._components(FP._tokens("a{bcd}")))
      ['a', Var('bcd')]
    """
    unmatched_open = False
    unmatched_close = False
    unfilled_var = False
    full_token = ""
    for token in tokens:
      if unmatched_close:
        if token == '}':
          full_token += token
          unmatched_close = False
        else:
          raise ValueError("Unmatched, unescaped '}'")
      elif unmatched_open:
        if token == '{':
          if unfilled_var:
            # This token has just been doubled
            full_token += token
            unmatched_open = False
            unfilled_var = False
          else:
            raise ValueError("'{' within a variable name")
        elif token == '}':
          # Just closed a variable name.  Emit.
          if unfilled_var:
            raise ValueError("Empty variable name")
          else:
            unmatched_open = False
            yield Var(full_token)
            full_token = ""
        else:
          # We have a non-brace token, and are inside of a variable name.  Emit
          # the current token, and make this variable name the new token
          if full_token:
            yield full_token
          full_token = token
          unfilled_var = False
      else:
        # Nothing unmatched.  This is just a token.
        if token == '{':
          unmatched_open = True
          unfilled_var = True
        elif token == '}':
          unmatched_close = True
        else:
          full_token += token

    if full_token:
      yield full_token

  @staticmethod
  def _tokens( s ):
    """Returns an interator over tokens in s.  Mostly just separates braces out.

    >>> list(FilePattern._tokens("ab{cde}fg}}{{{hi}"))
    ['ab', '{', 'cde', '}', 'fg', '}', '}', '{', '{', '{', 'hi', '}']
    """
    open_iter = iter(s.split("{"))
    open_token = open_iter.next()
    close_iter = iter(open_token.split("}"))
    token = close_iter.next()
    if token:
      yield token
    for token in close_iter:
      yield "}"
      if token:
        yield token
    for open_token in open_iter:
      yield "{"
      close_iter = iter(open_token.split("}"))
      token = close_iter.next()
      if token:
        yield token
      for token in close_iter:
        yield "}"
        if token:
          yield token

def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    _test()

