"""engine.py

Implements the main logic engine for Hagoth.  The idea is basically this:

    A build request is like a first order logic query.  You ask the system if
    it can create a particular file (or condition) and it tries to comply while
    answering.

    There are elements of standard make that are inevitably borrowed: each rule
    is not only a statement of what is possible, but also a set of instructions
    that can make it happen if the antecedents are satisfiable.  The way make
    does it is somewhat inflexible and not really extensible at all, and this
    system is intended to solve some of that.

    One of make's biggest shortcomings is the fact that it cannot really handle
    complex logic by itself.  It is not, by itself, Turing complete.  One might
    argue that this is a good thing, that it was not built to be a programming
    language, but a build system.  As time goes on, however, it gains more and
    more complex features, but it can never support computation natively in an
    elegant way because of the need for backward compatibility.

    Hagoth, like make, is made to process facts (the existence of files), rules
    (dependencies between files), and queries (targets).  It also supports
    instructions for making dependencies hold true, of course, since that is
    the essence of performing a build: a relationship is possible, but only
    after the execution of compilation or build logic.

    Consider for a moment the basic logic of standard make, written in
    pseudo-Prolog:

    test(Target, Dep1, ..., DepN) :- exec(testlogic, Target, Dep1, ..., DepN).
    test(Target, Dep1, ..., DepN) :- exec(buildlogic, Target, Dep1, ..., DepN).

    where

      - exec is a special primitive predicate that executes its first argument
        in the environment provided by the remaining arguments

      - test is simply a predicate

      - testlogic is a set of imperative commands that resolves to true when
        all dependencies are "true" and the target is also "true" (e.g., all
        dependencies exist and the target is newer than all of them)

      - buildlogic is a set of imperative commands that, given a set of
        satisfied dependencies, will at least attempt to satisfy the whole
        relationship, resulting in a valid target.

      - the first rule is attempted first, and if it is successfully applied,
        the second does not need to be.  For example, if the target is already
        built, then the build logic does not need to be run and the test
        returns true.

    This file implements the main engine, which matches a query (please build
    this target) to a rule, forming other queries and matching them until all
    conditions are met or something breaks down somewhere along the line.  The
    implementation of actual testlogic and buildlogic rules that can accept
    targets and dependencies is part of the build specification and may be
    idiosyncratic.  A standard ruleset is provided, however, and it works like
    standard make.  The syntax is geared toward this most common case, making
    it very simple to specify obvious things while allowing arbitrarily less
    obvious things to still be done.

    There are four basic fundamentals in this build system.  They are

    predicates::

        A predicate is something that is either true or false.  It can contain
        arguments, like FileIsCurrent(filename).  This predicate would evaluate
        to true if "filename" is up to date.  What that means is specified in
        rules.

    variables::

        A variable is simply an unknown.  It will take on a predicate value at
        some point during build evaluation and execution, or the build will
        fail due to unresolved queries.

    rules::

        A rule is a target predicate and a list of dependency predicates.  The
        truth value o the taret predicate (whether it is satisfiable or not) is
        dependent on the satisfiability of the dependencies.  Typically the
        target is called the "consequent" and the dependencies are called
        "antecedents" in first order logic.

    commands::

        A command is an imperative that does something.  This represents an
        important departure from pure first order logic, because it is not
        declarative.  It is an instruction that, if executed, can return a
        value and cause side effects, like the creation of a file or the
        setting of a variable.

    
    Basic "make" behavior involves the matching of predicates (file names) with
    targets of rules.  When a match is found, the dependencies are evaluated as
    predicates in need of matching until they all represent files that exist.
    If the dependencies all exist but the target is either older than them or
    does not exist at all, the specified commands are executed.  This system
    *can* have precisely the same behavior, but can also have more complex
    behavior. The default behavior is to treat filenames as
    FileIsCurrent(filename) predicates and rules as similar in spirit to make,
    as described above.

    A common query, then, would be something like this:

    ?- FileIsCurrent("executable").

    It would match against rules like these:

        FileIsCurrent("executable") :- FileIsCurrent("main.o").
        FileIsCurrent("main.o") :-
            FileIsCurrent("main.c"), FileIsCurrent("main.h").
        FileIsCurrent("main.h") :- Exists("main.h").
        FileIsCurrent("main.c") :- Exists("main.c").

    The Exists predicate could be treated as a special primitive that actually
    queries the file system.  The ability to create such primitives that
    perform imperative commands to determine truth values is one of the
    powerful features of this system.

    The syntax for the above set of rules will be much simpler than what is
    shown.  They are simply shown to indicate what the system wiil do.

    Matching can also be expressed in these rules, but is much harder to think
    about in terms of pure Prolog.  Instead, it is best to think of Hagoth
    rules as generalizations of the above: a single rule can have a consequent
    and multiple antecedents, and it can impose arbitrary conditions on the
    variables.  For example, it might impose a regular expression on any
    filename that would be valid for a particular rule:

        FileIsCurrent("^\(.*\)\.o") :-
            FileIsCurrent("\1\.c"), FileIsCurrent("\1\.h).

    The actual syntax, of course, would not be like that.  The fact is that
    anything is possible, since a rule has intimate knowledge of all aspects of
    the consequents and antecedents and can therefore impose any restrictions
    or perform any information blending that it likes.

"""

class Predicate(object):
    """Predicates are things that can be true or false, satisfied or not

    This is the predicate base class.  A predicate can match other predicates,
    has a name, and can take a list of arguments.
    """

    def __init__( self, args ):
        self.args = args

    def name( self ):
        return self.__classname__

    def args( self ):
        return self.args

    def matches( self, other ):
        if self.name() != other.name():
            return False

        if len(self.args()) != len(other.args()):
            return False

        # TODO: standardize variables apart and perform resolution on args
        # Also return match results.  This means variable settings, but can
        # also mean arbitrary things, like portions of regular expressions,
        # etc.  These will be used when evaluating dependencies.
    
    def __call__( self ):
        """Some predicates can act like functions that return truth values.
        
        If a predicate is callable, then it is a leaf predicate; it knows how
        to evaluate its own truth value.  The default is not callable."""

        raise NotImplementedError()

class FileIsCurrent(Predicate):
    """FileIsCurrent predicate; one of the most fundamental predicates

    This is an indication that a file is current, meaning that it does not need
    to be rebuilt.  This is a very important predicate because it embodies one
    of the most common tests when building files: whether or not those files
    are up to date.
    """
    def __init__( self, args ):
        if len(args) != 1:
            raise TypeError()

        super(FileIsCurrent, self).__init__( args )

class FileExists(Predicate):
    def __init__( self, args ):
        if len(args) != 1:
            raise TypeError("Only one argument, a filename, is accepted")

    def __call__( self ):
        """Returns the result of looking for the filename.  Error if it's a
        variable"""
        # TODO
        raise NotImplementedError()

class Rule(object):
    def __init__( self, consequent, antecedents ):
        """Create a build/test rule

        args:
            - consequent: the target predicate
            - antecedents: an iterable of dependency predicates

        """
        self.consequent = consequent
        self.antecedents = antecedents

    def matches( self, target ):
        return self.consequent.matches(target)

    def test( self ):
        raise NotImplementedError()

    def commands( self ):
        raise NotImplementedError()

class Engine(object):
    """Evaluation engine -- all build logic is embodied here.

    This is the main build logic, the central engine.  It contains a set of
    rules and can accept "queries".
    
    """

    def __init__( self, rules ):
        self.rules = rules

    def query_target( self, target ):
        """Essentially performs a build of a given target.

        Does the following:
            Find next rule whose target matches the query.
            Concretize dependencies and resolve each of them.
            if they are all satisfied: 
                if "test" returns true:
                    target is satisfied
                elif "commands" run successfully:
                    if "test" returns true:
                        target is satisfied
                    else:
                        target is not satisfiable - give up entirely
                else:
                    target is not satisfiable - give up entirely
            else:
                dependencies are not satisfiable, keep trying other rules
        """
        # TODO
        # the target is a predicate.  Try matching it against each of the rules
        # (this might be sped up with a reasonable data structure).  Do the
        # above logic.

# vim: sw=4 sts=4 et
