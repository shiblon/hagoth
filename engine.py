"""engine.py

Implements the main logic engine for Hagoth.

"""

class Predicate(object):
    def __init__( self, name, args=() ):
        assert name

        self.name = name
        self.args = args

class Rule(object):
    def __init__( self, consequent, antecedents ):
        self.consequent = consequent
        self.antecedents = antecedents
        self.name = self.__class__.__name__

        assert self.consequent.name + "Rule" == self.name

    def test( self, assignments ):
        raise NotImplementedError()

    def commands( self, assignments ):
        raise NotImplementedError()

class FileIsCurrentRule(Rule):
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

# vim: et sts=4 sw=4
