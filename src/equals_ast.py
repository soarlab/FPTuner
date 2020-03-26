

from ast_modifier import add_method
from fpcore_ast import ASTNode, Atom, Operation, Number
from fpcore_logging import Logger
from fractions import Fraction


logger = Logger()


@add_method(ASTNode)
def __eq__(self, other):
    # Make sure calling __eq__ leads to an error if not overridden
    class_name = type(self).__name__
    msg = "__eq__ not implemented for class {}".format(class_name)
    raise NotImplementedError(msg)


@add_method(Atom)
def __eq__(self, other):
    # Variables and Constants can be checked by string equality
    return type(self) == type(other) and self.source == other.source


@add_method(Number)
def __eq__(self, other):
    # Use Fraction so that Variable("0.125") == Variable("1/8") is True
    return (type(self) == type(other)
            and Fraction(self.source) == Fraction(other.source))


@add_method(Operation)
def __eq__(self, other):
    # Check that the operation and arguments are equal
    return (type(self) == type(other)
            and self.op == other.op
            and all(a1 == a2 for a1, a2 in zip(self.args, other.args)))
