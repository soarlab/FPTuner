

from ast_modifier import add_method
from fpcore_ast import ASTNode, Atom, Operation
from fpcore_logging import Logger


logger = Logger()


UNARY_PREFIX = {"+", "-"}
INFIX = {"+", "-", "*", "/"}


@add_method(ASTNode)
def infix_str(self, cast=None):
    # Make sure calling infix_str leads to an error if not overridden
    class_name = type(self).__name__
    msg = "infix_str not implemented for class {}".format(class_name)
    raise NotImplementedError(msg)


@add_method(Atom)
def infix_str(self, cast=None):
    # Infixing doesn't change Atoms
    return self.source


@add_method(Operation)
def infix_str(self, cast=None):
    cast = cast or ""

    # Infix arguments
    args = [a.infix_str() for a in self.args]

    # Grab unary prefix operations
    if len(args) == 1 and self.op in UNARY_PREFIX:
        return "({} {}{})".format(self.op, cast, args[0])

    # Grab infix binary operations
    if len(args) == 2 and self.op in INFIX:
        return "({}{} {} {}{})".format(cast, args[0], self.op, cast, args[1])

    # Everything else is a function call
    sep = ", {}".format(cast)
    return "{}({})".format(self.op, cast + sep.join(args))
