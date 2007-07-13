"""engine.py

Implements the main logic engine for Hagoth.

"""

import re

class Predicate(object):
    def __init__( self, name, args=() ):
        self.name = name
        self.args = args

class Var(object):
    def __init__( self, name, constraint=re.compile(".*") ):
        """Create a new variable with the given name and constraints

        args:
            name - name of the variable
            constraint - regular expression intended to match the entire value.
                If the constraint doesn't match, assignment is impossible.
        """
        self.name = name
        self.regex = regex

class Assignment(object):
    """A variable assignment containing a variable and its value
    
    Holds state pertinent to that assignment, like submatches in the
    constraints.  Currently just implemented as a regex with groups, but a more
    general implementation is needed.
    """

    def __init__( self, var, value ):
        """Creates an assigned variable

        args:

            var - a Var object
            value - an assignment to that var (cannot be another variable, that
                sort of thing is handled by the engine in a special way)
        """
        self.var = var
        self.value = value
        # A full match is expected -- no part of the variable may be left
        # unmatched by the regular expression.  This ensures, among other
        # things, that the group assignments are maximally predictable.
        self.match = var.regex.match(value)
        assert self.match is not None

class Rule(object):
    def __init__( self, consequent, antecedents ):
        self.consequent = consequent
        self.antecedents = antecedents
        self.name = self.__class__.__name__

        assert self.consequent.name + "Rule" == self.name

    def concrete_rule( self, assignments ):
        """Returns a rule of the same type, but with values concretized.
        
        The consequents and antecedents of the new rule will be variable-free
        (if possible, otherwise raises an exception)
        """
        # TODO
        pass

    def test( self, assignments ):
        """Returns true if, given satisfied antecedents, the rule is 'true'
        """
        raise NotImplementedError()

    def commands( self, assignments ):
        """Commands that are executed to make the rule true.

        These are executed when the antecedents are satisfied, but the test
        still fails.  The test is run after these to determine ultimate
        satisfiability of the rule.
        """
        raise NotImplementedError()

class FileIsCurrentRule(Rule):
    # TODO: test and commands
    pass


class Engine(object):
    def query( self, target_pred ):
        # TODO
        #
        # For each rule that matches the target:
        #   Unify target with consequent, generating a variable substitution
        #       list.
        #   Add antecedent predicates to targets list
        #   Recur to rule match with a copy of the substitution list, in case
        #       it fails (base case: target is a fact)
        #
        #   Once all antecedents are resolved and the substitution list is good,
        #       Perform substitution
        #       If test fails
        #           Execute build commands
        #           If test fails
        #               Fail
        #       Succeed (for this rule)

        pass

    # TODO:
    #   - Unification
    #   - Substitution
    #   - Resolution
    #   - Special handling of variable-to-variable mappings and assignment
    #       collapsing when appropriate.

# vim: et sts=4 sw=4
