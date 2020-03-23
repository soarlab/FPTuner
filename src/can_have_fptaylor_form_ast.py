

from fpcore_logging import Logger
from ast_modifier import add_method
from fpcore_ast import ASTNode, Number, Operation
from fractions import Fraction


logger = Logger()


def is_positive_power_of_two(n):
    # Either a Number or int are expected
    if type(n) == Number:
        frac = Fraction(n.source)
        # If frac is not an integer it can't be a power of two
        if frac.denominator != 1:
            return False
        n = frac.numerator
    elif type(n) == int:
        pass
    else:
        return False

    # Negative values cannot be a power of two
    if n <= 0:
        return False

    # Check if there is only a single bit set to 1
    return n & (n - 1) == 0


def is_power_of_two(n):
    # Either a Number or int are expected
    if type(n) == Number:
        frac = Fraction(n.source)
    elif type(n) == int:
        frac = Fraction(n)
    else:
        return False

    # Negative values cannot be a power of two
    if frac <= 0:
        return False

    # If we have n/1 check if n is a positive power of two
    if frac.denominator == 1:
        return is_positive_power_of_two(frac.numerator)

    # If we have 1/n check if n is a positive power of two
    if frac.numerator == 1:
        return is_positive_power_of_two(frac.denominator)

    # No other fractions are a power of two
    return False


@add_method(ASTNode)
def can_have_fptaylor_form(self, ssa):
    # Assume everything can have an FPTaylor form by default
    return True


@add_method(Number)
def can_have_fptaylor_form(self, ssa):
    frac = Fraction(self.source)

    # FPTaylor does not create error forms for whole numbers under a certain
    # size
    # todo: magic number
    if frac.denominator == 1 and frac.numerator < 2**26:
        return False

    # FPTaylor does not create error forms for negative powers of two
    if frac.denominator != 1 and is_power_of_two(frac.denominator):
        return False

    # Assume all other literals have an associated error form
    return True


@add_method(Operation)
def can_have_fptaylor_form(self, ssa):
    # Negation does not introduce error
    if self.op == "-" and len(self.args) == 1:
        return False

    # Multiplication by a power of two does not introduce error
    if self.op == "*":
        expanded = self.expand(ssa)
        args = expanded.args
        if is_power_of_two(args[0]) or is_power_of_two(args[1]):
            return False

    # Division by a whole power of two does not introduce error
    if self.op == "/":
        expanded = self.expand(ssa)
        is_num = type(expanded.args[1]) == Number
        if is_num and is_positive_power_of_two(expanded.args[1]):
            return False

    # Assume all other operations have an associated error form
    return True
