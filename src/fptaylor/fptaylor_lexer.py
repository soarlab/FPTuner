

from exceptions import FPTaylorLexError
from fpcore_logging import Logger
from sly import Lexer

import sys


logger = Logger()


class FPTaylorLexer(Lexer):
    tokens = {
        # Literals
        RATIONAL,
        DECNUM,

        # Symbols
        SYMBOL,

        # Operations
        PLUS,
        MINUS,
        TIMES,
        DIVIDE,
        OPERATION,
        ROUND,

        # Delimitors
        LP,  # left paren
        RP,  # right paren
        LB,  # left square bracket
        RB,  # right square bracket
        C,   # comma
    }

    # Ignored input
    @_(r"\n+")
    def ignore_newline(self, t):
        self.lineno += t.value.count('\n')
    ignore_space = r"\s"

    # From https://fpbench.org/spec/fpcore-1.2.html
    RATIONAL = r"[+-]?[0-9]+/[0-9]*[1-9][0-9]*"

    # From https://fpbench.org/spec/fpcore-1.2.html
    DECNUM = r"[-+]?([0-9]+(\.[0-9]+)?|\.[0-9]+)(e[-+]?[0-9]+)?"

    # From https://fpbench.org/spec/fpcore-1.2.html
    #     modified to not allow ':' or '!' as the first character to
    #     disambiguate properties
    # todo: match fptaylor symbol definition
    SYMBOL = r"[a-zA-Z~@$%^&_=<>.?][a-zA-Z0-9~!@$%^&*_\-+=<>.?/:]*"

    PLUS = r"\+"
    MINUS = r"-"
    TIMES = r"\*"
    DIVIDE = r"/"

    # todo: flesh out operations
    OPERATIONS = sorted([
        "acos",
        "asin",
        "atan",
        "cos",
        "exp",
        "log",
        "sin", "zero_sin", "one_sin", "m_one_sin", "taylor_1_sin", "taylor_3_sin",
        "sqrt",
        "tan",
    ], key=len)
    for i in range(len(OPERATIONS)):
        SYMBOL[OPERATIONS[i]] = OPERATION
    OPERATION = "({})".format(")|(".join(OPERATIONS))

    # todo: flesh out rounding modes
    ROUNDS = sorted([
        "rnd32", "rnd64", "rnd"
    ], key=len)
    for i in range(len(ROUNDS)):
        SYMBOL[ROUNDS[i]] = ROUND
    ROUND = "({})".format(")|(".join(ROUNDS))

    LP = r"\("
    RP = r"\)"
    LB = r"\["
    RB = r"\]"
    C = r","

    def error(self, t):
        raise FPTaylorLexError(self.lineno, t)


def main(argv):
    logger.set_log_level(Logger.EXTRA)
    if len(argv) == 1:
        text = sys.stdin.read()
    elif len(argv) == 2:
        with open(argv[1], "r") as f:
            text = f.read()

    lexer = FPTaylorLexer()
    for token in lexer.tokenize(text):
        pass


if __name__ == "__main__":
    sys.exit(main(sys.argv))
