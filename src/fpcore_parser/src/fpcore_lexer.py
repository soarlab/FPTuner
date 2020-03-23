

from fpcore_logging import Logger
from sly import Lexer

import sys


logger = Logger()


class FPCoreLexer(Lexer):
    tokens = {
        # Literals
        RATIONAL,
        DECNUM,
        HEXNUM,
        STRING,

        # Symbols
        SYMBOL,

        # Keywords
        FPCORE,
        IF,
        LET,
        LET_STAR,
        WHILE,
        WHILE_STAR,
        CAST,
        DIGITS,

        # Constants
        CONSTANT,

        # Operations
        OPERATION,

        # Delimitors
        LP,  # left paren
        RP,  # right paren
        LB,  # left square bracket
        RB,  # right square bracket
        COLON,
        BANG,
    }

    # Ignored input
    @_(r"\n+")
    def ignore_newline(self, t):
        self.lineno += t.value.count('\n')
    ignore_space = r"\s"
    ignore_comment = r"\;.*"

    # From https://fpbench.org/spec/fpcore-1.2.html
    RATIONAL = r"[+-]?[0-9]+/[0-9]*[1-9][0-9]*"

    # From https://fpbench.org/spec/fpcore-1.2.html
    DECNUM = r"[-+]?([0-9]+(\.[0-9]+)?|\.[0-9]+)(e[-+]?[0-9]+)?"

    # From https://fpbench.org/spec/fpcore-1.2.html
    #     modified to be used in a case sensitive environment
    HEXNUM = r"[+-]?0[xX]([0-9a-fA-F]+(\.[0-9a-fA-F]+)?|\.[0-9a-fA-F]+)([pP][-+]?[0-9]+)?"

    # From https://fpbench.org/spec/fpcore-1.2.html
    #     modified to allow multiline strings
    STRING = r'"([\x20-\x21\x23-\x5b\x5d-\x7e\n]|\\["\\])*"'

    # From https://fpbench.org/spec/fpcore-1.2.html
    # modification            | reason
    # ------------------------+--------------
    # first char can't be ':' | disambiguate property
    # first char can't be '!' | disambiguate property
    SYMBOL = r"[a-zA-Z~@$%^&*_\+=<>.?/][a-zA-Z0-9~!@$%^&*_\-+=<>.?/:]*"

    SYMBOL["FPCore"] = FPCORE
    FPCORE = "FPCore"

    SYMBOL["if"] = IF
    IF = "if"

    SYMBOL["let"] = LET
    LET = "let"

    SYMBOL["let*"] = LET_STAR
    LET_STAR = "let*"

    SYMBOL["while"] = WHILE
    WHILE = "while"

    SYMBOL["while*"] = WHILE_STAR
    WHILE_STAR = "while*"

    SYMBOL["cast"] = CAST
    CAST = "cast"

    SYMBOL["digits"] = DIGITS
    DIGITS = "digits"

    CONSTANTS = sorted([
        "E", "LOG2E", "LOG10E", "LN2", "LN10",
        "PI", "PI_2", "PI_4", "M_1_PI", "M_2_PI",
        "M_2_SQRTPI", "SQRT2", "SQRT1_2", "INFINITY", "NAN",
        "TRUE", "FALSE",
    ], key=len)
    for i in range(len(CONSTANTS)):
        SYMBOL[CONSTANTS[i]] = CONSTANT
    CONSTANT = "({})".format(")|(".join(CONSTANTS))

    UNARY_OPERATIONS = {
        "+", "-", "fabs", "exp", "exp2", "expm1", "log",
        "log10", "log2", "log1p", "sqrt",
        "cbrt",  "sin", "cos", "tan",
        "asin", "acos", "atan", "sinh",
        "cosh", "tanh", "asinh", "acosh", "atanh",
        "erf", "erfc", "tgamma", "lgamma", "ceil",
        "floor",
        "trunc", "round", "nearbyint",
        "not", "isfinite",
        "and", "or",
        "isinf", "isnan", "isnormal", "signbit",
    }
    BINARY_OPERATIONS = {
        "+", "-", "*", "/",
        "pow",
        "hypot",
        "atan2",
        "fmod", "remainder", "fmax", "fmin",
        "fdim", "copysign",
        "<", ">", "<=", ">=", "==",
        "!=", "and", "or",
        "=>",  # added to support parsing of rosa postconditions
    }
    TERNARY_OPERATIONS = {
        "fma",
        "<", ">", "<=", ">=", "==",
        "!=", "and", "or",
        "=>",  # added to support parsing of rosa postconditions
    }
    NARY_OPERATIONS = {
        "<", ">", "<=", ">=", "==",
        "!=", "and", "or",
        "=>",  # added to support parsing of rosa postconditions
    }
    OPERATIONS = sorted(list(UNARY_OPERATIONS
                             | BINARY_OPERATIONS
                             | TERNARY_OPERATIONS
                             | NARY_OPERATIONS),
                        key=len)
    for i in range(len(OPERATIONS)):
        SYMBOL[OPERATIONS[i]] = OPERATION
    _not_regex = "({})".format(")|(".join(OPERATIONS))
    OPERATION = _not_regex.replace("+", "\\+").replace("*", "\\*")

    LP = r"\("
    RP = r"\)"
    LB = r"\["
    RB = r"\]"
    COLON = r":"
    BANG = r"!"

    def error(self, t):
        logger.error("Line {}: Bad character '{}'", self.lineno, t.value[0])
        sys.exit(1)


def main(argv):
    logger.set_log_level(Logger.EXTRA)
    if len(argv) == 1:
        text = sys.stdin.read()
    elif len(argv) == 2:
        with open(argv[1], "r") as f:
            text = f.read()

    lexer = FPCoreLexer()
    for token in lexer.tokenize(text):
        pass


if __name__ == "__main__":
    sys.exit(main(sys.argv))
