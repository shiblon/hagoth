"""Decorators for logic-based builds

provides::
  indicates that a function provides a particular string (can be a match
  string)

requires::
  indicates that certain dependencies must be met before it makes sense
  to call this function.

A Global registry of rules is created (the knowledge base), keyed on the
consequent (rules are repeated in the registry if they have more than one
consequent).  Essentially, the provides decorator ensures that the function is
in the registry and the requires decorator adds antecedents to it.

The function itself needs access to the variables mentioned in match rules, as
well as a list of antecedents, etc.  All of this must be available to the
function body, which is sort of tricky.  Right now I'm favoring a magic
argument that is always set to an object that holds all of the interesting
things that the function might need.

"""

rule_list = []
rule_map = {}

def parse_match_string(s):
    """ Parse a match string into a list of tokens

      Braces are escaped by doubling.

      >>> parse_match_string("ab{c}d{e}fg{hi}")
      ['a', 'b', '{c}', 'd', '{e}', 'f', 'g', '{hi}']
      >>> parse_match_string("abc{{de{{fg}}")
      ['a', 'b', 'c', '{', 'd', 'e', '{', 'f', 'g', '}']
    """
    if not s:
        return []

    result = []
    s_iter = iter(s)
    cur_var = ''
    prev_is_closing = False
    for c in s_iter:
        if c == '{':
            if not cur_var:
                cur_var = c
            elif len(cur_var) == 1:
                # only one character in the variable, it must be a brace.  Emit
                # a brace and start over with the var.
                result.append(c)
                cur_var = ''
            else:
                raise NameError(cur_var + '{' + " is not a valid variable name")
        elif c == '}':
            if cur_var:
                result.append(cur_var + c)
                cur_var = ''
            else:
                if not prev_is_closing:
                    prev_is_closing = True
                    result.append(c)
        else:
            if cur_var:
                cur_var += c
            else:
                result.append(c)
    if cur_var:
        raise ValueError("Unterminated variable name " + cur_var)
    return result

def iter_string_matches(s1, s2):
    """ Try to build a variable mapping that unifies the two variable-containing
        strings.

        >>> for vmap in iter_string_matches("a{b}c{d}e", "abccc{e}e"):
        ...     print vmap
        None
    """
    import sys

    ps1 = parse_match_string(s1)
    ps2 = parse_match_string(s2)

    def is_var( v ) :
        return len(v) > 1

    matrix = [[None for col in ps2] for row in ps1]
    # Start at the upper right corner and make our way down to the lower left.
    for col, cval in enumerate(ps2):
        for row, rval in enumerate(ps1):
            cur_cost = None
            if is_var(cval) or is_var(rval) or rval == cval:
                cur_cost = 1
            if row == col == 0:
                if cur_cost is None:
                    # No match at beginning, bail
                    return
                else:
                    matrix[row][col] = cur_cost
            else:
                cur_min = None
                for prow, pcol in [(row-1, col), (row-1, col-1), (row, col-1)]:
                    if prow < 0 or pcol < 0:
                        continue
                    past_val = matrix[prow][pcol]
                    if cur_min is None:
                        cur_min = past_val
                    elif past_val is not None and cur_min > past_val:
                        cur_min = past_val
                if cur_min is not None and cur_cost is not None:
                    matrix[row][col] = cur_min + cur_cost

    if matrix[-1][-1] is None:
        return

    # Start at the back and move to the beginning, tracing all possible paths
    row = len(ps1) - 1
    col = len(ps2) - 1

    stack = [((row, col),)]

    while stack:
        path = stack.pop()
        row, col = path[-1]
        if row == col == 0:
            # leaf node.  Yield this path.
            # TODO: transform the path into a variable map, then yield that.
            yield path
            continue
        # Try to push every neigbor onto the stack, but only if its cost is
        # equal to this cost - 1
        cost = matrix[row][col]
        for nrow, ncol in ((row-1, col), (row-1, col-1), (row, col-1)):
            if nrow < 0 or ncol < 0:
                continue
            if matrix[nrow][ncol] == cost - 1:
                stack.append(path + ((nrow, ncol),))

def prepare_func(func):
    if not hasattr(func, 'provides'):
        func.provides = []
    if not hasattr(func, 'requires'):
        func.requires = []

def provides(consequent):
    def add_provision(func):
        prepare_func(func)
        func.provides.append(consequent)
        return func
    return add_provision

def requires(antecedent):
    def add_requirement(func):
        prepare_func(func)
        func.requires.append(antecedent)
        return func
    return add_requirement

class Test(object):
    @provides("filename.o")
    @requires("filename.c")
    def build_filename_o( self, env ):
        print self
        print env

def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    _test()

# vim: sw=4 sts=4 et
