"""prolog.py

A simple prolog implementation to give me ideas about how to make the real
engine work.

"""

from itertools import count, izip
from copy import copy

# This is used to do things like standardizing apart variable names.  Every
# variable must have a unique name, but it also has a "preferred" name assigned
# by the user.  This generates the unique name.
def name_generator(prefix):
    """Generates unique names (using numbers as suffixes)"""
    for i in count():
        yield "%s%d" % (prefix, i)

global_varname_factory = name_generator('v')

class Predicate(object):
    def __init__( self, name, args=() ):
        self.name = name
        self.args = [x.copy() for x in args]

    def __str__( self ):
        if len(self.args) > 0:
            argstr = ", ".join(str(x) for x in self.args)
            return "Predicate(%s: %s)" % (self.name, argstr)
        else:
            return "Predicate(%s)" % (self.name,)

    __repr__ = __str__

    def copy( self ):
        return self.__class__( self.name, self.args )

    def standardize_vars( self, factory, mapping ):
        for i, a in enumerate(self.args):
            if mapping.is_var(a):
                if a not in mapping:
                    mapping.add(a, factory())
                self.args[i] = mapping[a]
            else:
                a.standardize_vars(factory, mapping)

    def var_within( self, var, mapping ):
        """Returns True if the variable is somewhere in this predicate"""
        var = mapping[var]

        for a in self.args:
            if mapping.is_var(a):
                a = mapping[a]
                if a.name == var.name:
                    return True
            else:
                if a.var_within(var, mapping):
                    return True
        return False

    def unify( self, other, mapping ):
        """Attempts to do unification with the given predicate and given
        variable mapping.  Returns a boolean success value.

        The mapping will be changed when it comes back, so it should be copied
        before being passed in if rewindability is needed.
        """
        if mapping.is_var(other):
            other = mapping[other]

        # If it's still a variable after asking the map for it, then we defer
        # to that variable's unification routine.
        if mapping.is_var(other)
            return other.unify(self, mapping)

        # Other must be a predicate, so do the predicate matching logic: match
        # names and unify args.
        if self.name != other.name or len(self.args) != len(other.args):
            return False

        # Now attempt to do unification on each of the arguments.  This is
        # recursively defined.  Variables know how to do unification, for
        # example.
        for thisarg, otherarg in izip(self.args, other.args):
            if not thisarg.unify(otherarg, mapping):
                return false
        return true

    def substitute( self, mapping ):
        """Returns a copy of this predicate with all variables resolved"""
        pred = self.copy()
        for i, a in enumerate(pred.args):
            if mapping.is_var(a):
                a = mapping[a]
            # Vars just get inserted, predicates are recursively substituted
            if mapping.is_var(a):
                pred.args[i] = a
            else:
                pred.args[i] = a.substitute(mapping)
        return pred

class Var(object):
    def __init__( self, name ):
        self.name = name

    def __str__( self ):
        return "Var(%s)" % self.name

    __repr__ = __str__

    def copy( self ):
        return self.__class__( self.name )

    def unify( self, other, mapping ):
        # Are we a variable when the map is queried?
        me = mapping[self]

        # If not a variable anymore, defer to the predicate routine
        if not mapping.is_var(me):
            return me.unify(other, mapping)

        # If we are trying to unify with a variable, attempt to get its value
        # out of the mapping first.
        if mapping.is_var(other):
            other = mapping[other]

        # If it's still a variable, then we just add it to the mapping and move
        # on with life; nothing to see here.
        if mapping.is_var(other):
            mapping.add(me, other)
            return True

        # Not a variable?  Must be a predicate!  We can typically just assign
        # these as well, but we first have to ensure that the variable does not
        # appear (recursively) in any of the predicate's arguments.
        if other.var_within(me, mapping):
            return False
        else:
            mapping.add(me, other)
            return True

class  VarMap(object):
    """Contains variable assignment pairs"""
    def __init__( self ):
        self.vardict = {}

    def copy( self ):
        newmap = self.__class__()
        for k, (var, val) in self.vardict.iteritems():
            newmap.vardict[k] = (var.copy(), val.copy())
        return newmap

    def __str__( self ):
        items = []
        for k, (var, val) in self.vardict.iteritems():
            items.append("%s -> %s" % (var, val))
        return "\n".join(items)

    __repr__ = __str__

    def is_var( self, value ):
        return isinstance(value, Var)

    def add( self, var, value ):
        """Adds a new variable mapping to the dictionary.

        Raises ValueError if a mapping already exists.
        """
        if var.name in self.vardict:
            raise ValueError(var.name + " is already in the mapping")

        # No flattening is done at the moment
        self.vardict[var.name] = (var, value)

    def __contains__( self, var ):
        return var.name in self.vardict

    def __getitem__( self, var ):
        return self.deep_get(var)

    def shallow_get(self, var):
        if not self.is_var(var):
            raise ValueError("Got something other than a variable")

        var, val = self.vardict[var.name]
        return val

    def deep_get( self, var ):
        if not self.is_var(var):
            raise ValueError("Got something other than a variable")

        # You would think that the best thing to do in this case would be to
        # fail (the variable isn't in the mapping, right?), but it isn't.  If
        # we ask for a variable that isn't here, then we just return that
        # variable.  The purpose of the mapping is to tell us what stuff is
        # assigned to.  This variable is unassigned and therefore is just
        # itself.
        if var not in self:
            return var

        # If it's in there, then obviously get it and follow the thread.
        var, val = self.vardict[var.name]
        while self.is_var(val) and val in self:
            var, val = self.vardict[val.name]
        return val

class Rule(object):
    def __init__( self,
                  consequent,
                  antecedents,
                  varfactory=global_varname_factory ):

        self.standardized_mapping = VarMap()
        self.consequent = consequent.copy()
        self.consequent.standardize_vars(varfactory, self.standardized_mapping)

        self.antecedents = [a.copy() for a in antecedents]
        for a in self.antecedents:
            a.standardize_vars(varfactory, self.standardized_mapping)

    def __str__( self ):
        if len(self.antecedents) > 0:
            antstr = [str(x) for x in self.antecedents]
            return "Rule (map %s):: %s <- %s" % (
                    self.standardized_mapping, self.consequent, antstr)
        else:
            return "Rule (map %s):: %s" % (
                    self.standardized_mapping, self.consequent)

    __repr__ = __str__

    def copy( self ):
        return self.__class__(self.consequent, self.antecedents)

    def resolve( self, query ):
        """Returns a variable mapping (or None if it doesn't work)"""
        map = VarMap()
        if query.unify(self.consequent, map):

    def test( self ):
        return True

    def commands( self ):
        pass

class Prolog(object):
    def __init__( self ):
        self.rules = []
        # TODO: make sure all rules are unique?  Does it matter?

    def add_rule( self, rule ):
        self.rules.append(rule)

    def answer_iter( self, query ):
        # TODO: this is the meat of everything, right?
        for rule in self.rules:
            map = VarMap()
            # TODO: unify with the consequent.  If success, add to queries and
            # do it all over again....
            #
            # We may want to make this a queries (plural) iterator and allow a
            # (copy of a) map to be passed....
        pass

# vim: et sts=4 sw=4
