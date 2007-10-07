"""Unification functions
"""

def is_var( v ) :
    return v[0] == '{' and v[-1] == '}'


class PathInfo(object):
    def __init__( self, matchtype, numpaths ):
        self.type = matchtype
        self.paths = numpaths

    def __str__( self ):
        return '%s%d' % (self.type, self.paths)

    def __repr__( self ):
        return repr(str(self))

class MatchMatrix(object):
    def __init__( self, s1, s2 ):
        """ Build a match matrix from the input strings

            . : constant-constant match
            r : row var match
            c : col var match
            * : row/col var match (equivalence)

            Rules (everything must match at least one other thing, no empty
            matches):
              - 0 if not a simple match
              - value is sum of inherited values
              - all matches can inherit from upper left diagonal
              - r match may inherit r-match from left
              - c match may inherit c-match from above
              - . match inherits from upper left only

            The number at the bottom right is the number of matches.

        >>> print MatchMatrix("a{b}c{d}e", "abccc{e}e")
        .1 -0 -0 -0 -0 -0 -0
        -0 r1 r1 r1 r1 r1 r1
        -0 -0 .1 .1 .1 c1 -0
        -0 -0 -0 r1 r2 *4 r5
        -0 -0 -0 -0 -0 c6 .4
        >>> print MatchMatrix("a{b}{c}def", "abc{d}{e}f")
        .1 -0 -0 -0 -0 -0
        -0 r1 r1 r1 r1 r1
        -0 -0 r1 r2 r3 r4
        -0 -0 -0 c1 c2 -0
        -0 -0 -0 c1 c3 -0
        -0 -0 -0 c1 c4 .3
        """
        # TODO: Standardize apart?
        ps1 = self.ps1 = parse_match_string(s1)
        ps2 = self.ps2 = parse_match_string(s2)

        matrix = [[PathInfo('-', 0) for col in ps2] for row in ps1]
        self.matrix = matrix
        self.num_rows = len(matrix)
        self.num_cols = len(matrix[0])

        # Start at the upper left corner and make our way down to the lower
        # right.  Assume that the corner matches.
        for row, rval in enumerate(ps1):
            for col, cval in enumerate(ps2):
                info = matrix[row][col]
                diag_source = 0
                # Diagonal is always allowed.  It's also always 1 if we are in
                # the upper left corner.
                if col == 0 and row == 0:
                    diag_source = 1
                elif col > 0 and row > 0:
                    diag_source = matrix[row-1][col-1].paths

                # If we have a constant match, that is the most constrained, so
                # we handle it before doing anything else.
                if not is_var(rval) and not is_var(cval) and rval == cval:
                    info.type = '.'
                    info.paths = diag_source
                    # We can't have variables here, so just skip to the next
                    # one
                    continue

                # If we get this far, we have a variable somewhere
                rvar_source = 0
                cvar_source = 0

                # Row vars can only inherit from left if also a row var
                if is_var(rval) and col > 0 and matrix[row][col-1].type in 'r*':
                    rvar_source = matrix[row][col-1].paths
                # Col vars can only inherit from above if also a col var
                if is_var(cval) and row > 0 and matrix[row-1][col].type in 'c*':
                    cvar_source = matrix[row-1][col].paths

                # If we have two variables, we choose which version we care
                # about based on the surrounding values.
                if is_var(rval) and is_var(cval):
                    if row == 0 and col == 0:
                        info.type = '*'
                        info.paths = 1
                    elif rvar_source and cvar_source:
                        info.type = '*'
                        info.paths = diag_source + rvar_source + cvar_source
                    elif rvar_source:
                        info.type = 'r'
                        info.paths = diag_source + rvar_source
                    elif cvar_source:
                        info.type = 'c'
                        info.paths = diag_source + cvar_source
                elif is_var(rval):
                    info.type = 'r'
                    if row == 0 and col == 0:
                        info.paths = 1
                    else:
                        info.paths = diag_source + rvar_source
                elif is_var(cval):
                    info.type = 'c'
                    if row == 0 and col == 0:
                        info.paths = 1
                    else:
                        info.paths = diag_source + cvar_source

                if info.paths == 0:
                    info.type = '-'

    def paths( self, path=None ):
        """ Get all paths through the matrix that end in "path"

            To produce the actual matches, we start at the bottom and work up:
            - From any match, move diagonally
            - From a 'r' or '*' match, move left if 'r' or '*' match to the left
            - From a 'c' or '*' match, move up if 'c' or '*' match up

            >>> matrix = MatchMatrix("a{b}c{d}e", "abccc{e}e")
            >>> for path in matrix.paths():
            ...     print path
            ((0, 0), (1, 1), (1, 2), (1, 3), (2, 4), (3, 5), (4, 6))
            ((0, 0), (1, 1), (1, 2), (2, 3), (3, 4), (3, 5), (4, 6))
            ((0, 0), (1, 1), (2, 2), (3, 3), (3, 4), (3, 5), (4, 6))
            ((0, 0), (1, 1), (1, 2), (1, 3), (1, 4), (2, 5), (3, 5), (4, 6))
            >>> matrix = MatchMatrix("a{b}{c}def", "abc{d}{e}f")
            >>> for path in matrix.paths():
            ...     print path
            ((0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5))
            ((0, 0), (1, 1), (1, 2), (2, 3), (3, 4), (4, 4), (5, 5))
            ((0, 0), (1, 1), (2, 2), (2, 3), (3, 4), (4, 4), (5, 5))
        """

        # No path to the end, skip out
        if self[-1, -1].paths == 0:
            return

        if path is None:
            path = (self.num_rows - 1, self.num_cols - 1),

        # We have reached the beginning from the end: emit
        row, col = path[0]
        if row == 0 and col == 0:
            yield path
            return

        info = self[row, col]

        path_prefixes = []
        if row > 0 and col > 0 and self[row-1, col-1].paths > 0:
            path_prefixes.append((row-1, col-1))
        if info.type in 'r*' and col > 0 and self[row, col-1].type in 'r*':
            path_prefixes.append((row, col-1))
        if info.type in 'c*' and row > 0 and self[row-1, col].type in 'c*':
            path_prefixes.append((row-1, col))

        for pos in path_prefixes:
            for new_path in self.paths((pos,) + path):
                yield new_path

    def maps( self ):
        """ Build a map for each path through this matrix

            >>> matrix = MatchMatrix("a{b}{c}def", "abc{d}{e}f")
            >>> for map in matrix.maps():
            ...     print map
            [['{b}', 'b'], ['{c}', 'c'], ['{d}', 'd'], ['{e}', 'e']]
            [['{b}', 'bc'], ['{c}', '{d}'], ['{e}', 'de']]
            [['{b}', 'b'], ['{c}', 'c', '{d}'], ['{e}', 'de']]
            >>> matrix = MatchMatrix("a{b}c{d}e", "abccc{e}e")
            >>> for map in matrix.maps():
            ...     print map
            [['{b}', 'bcc'], ['{d}', '{e}']]
            [['{b}', 'bc'], ['{d}', 'c', '{e}']]
            [['{b}', 'b'], ['{d}', 'cc', '{e}']]
            [['{b}', 'bccc'], ['{e}', 'c', '{d}']]
        """
        for path in self.paths():
            prev_row = None
            prev_col = None
            map = []
            for i, (row, col) in enumerate(path):
                # If we move within a row, we need to append to the most recent
                # row variable match.
                if row == prev_row:
                    oldvar = is_var(map[-1][-1])
                    newvar = is_var(self.ps2[col])
                    # If we are interfacing with a variable, then we can't make
                    # a longer string out of the most recent entry.  Otherwise,
                    # we can.
                    if oldvar or newvar:
                        map[-1].append(self.ps2[col])
                    else:
                        map[-1][-1] += self.ps2[col]
                elif col == prev_col:
                    oldvar = is_var(map[-1][-1])
                    newvar = is_var(self.ps1[row])
                    # If we are interfacing with a variable, then we can't make
                    # a longer string out of the most recent entry.  Otherwise,
                    # we can.
                    if oldvar or newvar:
                        map[-1].append(self.ps1[row])
                    else:
                        map[-1][-1] += self.ps1[row]
                else:
                    # Moving diagonally.  If we have a variable type, create a
                    # new match.  This is straightforward for 'r' and 'c' type
                    # matches.
                    info = self[row, col]
                    if info.type == 'r':
                        map.append([self.ps1[row], self.ps2[col]])
                    elif info.type == 'c':
                        map.append([self.ps2[col], self.ps1[row]])
                    elif info.type == '*':
                        # This is the tricky one.  From here there are three
                        # possibilities:
                        #   move down: column var
                        #   move right: row var
                        #   move diagonally or end of path: treat like a row var
                        if i == len(path) - 1:
                            # end of path, treat like a row var:
                            map.append([self.ps1[row], self.ps2[col]])
                        else:
                            future_row, future_col = path[i+1]
                            if future_col == col:
                                map.append([self.ps2[col], self.ps1[row]])
                            else: # diagonal or over
                                map.append([self.ps1[row], self.ps2[col]])
                prev_row = row
                prev_col = col
            yield map

    def __iter__( self ):
        return iter(self.matrix)

    def __getitem__( self, pos ):
        row, col = pos
        return self.matrix[row][col]

    def __str__( self ):
        slist = []
        for row in self.matrix:
            slist.append(" ".join(str(x) for x in row))
        return "\n".join(slist)

    __repr__ = __str__

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

def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    _test()

# vim: sw=4 sts=4 et noic
