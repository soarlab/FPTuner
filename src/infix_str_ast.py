

from ast_modifier import add_method
from fpcore_ast import ASTNode, Atom, Operation
from fpcore_logging import Logger


logger = Logger()


UNARY_PREFIX = {"+", "-"}
INFIX = {"+", "-", "*", "/"}


@add_method(ASTNode)
def infix_str(self):
    # Make sure calling infix_str leads to an error if not overridden
    class_name = type(self).__name__
    msg = "infix_str not implemented for class {}".format(class_name)
    raise NotImplementedError(msg)


@add_method(Atom)
def infix_str(self):
    # Infixing doesn't change Atoms
    return self.source


@add_method(Operation)
def infix_str(self):
    # Infix arguments
    args = [a.infix_str() for a in self.args]

    # Grab unary prefix operations
    if len(args) == 1 and self.op in UNARY_PREFIX:
        return "({} {})".format(self.op, args[0])

    # Grab infix binary operations
    if len(args) == 2 and self.op in INFIX:
        return "({} {} {})".format(args[0], self.op, args[1])

    # Everything else is a function call
    return "{}({})".format(self.op, ", ".join(args))
