

from fptuner_logging import Logger

import color_printing
import sys

try:
    from sly import Lexer
except ModuleNotFoundError:
    logger.error("SLY must be installed for python3")
    sys.exit(-1)


logger = Logger(color=color_printing.yellow)


class FptunerLexer(Lexer):
    tokens = {
        # Variables
        NAME,

        # Prefix operators
        BINOP,
        UNOP,
        ROUND,

        # Literals
        FLOAT,
        INTEGER,

        # Infix Operators
        PLUS,
        MINUS,
        TIMES,
        DIVIDE,
        #INFIX_POW,

        # Assignment
        # EQUALS,

        # Deliminators
        LPAREN,
        RPAREN,
        LBRACE,
        RBRACE,
        COMMA,
        DOLLAR_SIGN,
        EID,
    }

    # Ignored input
    @_(r"\n+")
    def ignore_newline(self, t):
        self.lineno += t.value.count('\n')
    ignore_space = r"\s"
    ignore_comment = r"\#.*"

    # Variables
    NAME = r"[a-zA-Z][a-zA-Z0-9]*"

    # BINOP
    NAME["pow"] = BINOP

    # UNOP
    NAME["abs"] = UNOP
    NAME["cos"] = UNOP
    NAME["exp"] = UNOP
    NAME["log"] = UNOP
    NAME["sin"] = UNOP
    NAME["sqrt"] = UNOP

    # ROUND
    NAME["rnd64"] = ROUND
    NAME["rnd"] = ROUND

    # Literals
    FLOAT = (r"("                  # match all floats
             r"("                  # | match float with '.'
             r"("                  # |  match a number base
             r"(\d+\.\d+)"         # |   <num.num>
             r"|"                  # |   or
             r"(\d+\.)"            # |   <num.>
             r"|"                  # |   or
             r"(\.\d+)"            # |   <.num>
             r")"                  # |
             r"("                  # |  then match an exponent
             r"(e|E)(\+|-)?\d+"    # |   <exponent>
             r")?"                 # |   optionally
             r")"                  # |
             r"|"                  # | or
             r"("                  # | match float without '.'
             r"\d+"                # |  <num>
             r"((e|E)(\+|-)?\d+)"  # |  <exponent>
             r")"
             r")")
    INTEGER = r"\d+"


    # Infix Operators
    PLUS = r"\+"
    MINUS = r"-"
    TIMES = r"\*"
    DIVIDE = r"/"
    #INFIX_POW = r"\^"

    # Assignment
    #EQUALS = r"="

    # Deliminators
    LPAREN = r"\("
    RPAREN = r"\)"
    LBRACE = r"\["
    RBRACE = r"\]"
    COMMA = r","
    DOLLAR_SIGN = r"\$"
    EID = r"_eid_"

    def error(self, t):
        logger.error("Line {}: Bad character '{}'", self.lineno, t.value[0])
        sys.exit(-1)

    if logger.should_log:
        def FLOAT(self, t):
            logger.dlog("{}", t)
            return t
        def INTEGER(self, t):
            logger.dlog("{}", t)
            return t
        def PLUS(self, t):
            logger.dlog("{}", t)
            return t
        def MINUS(self, t):
            logger.dlog("{}", t)
            return t
        def TIMES(self, t):
            logger.dlog("{}", t)
            return t
        def DIVIDE(self, t):
            logger.dlog("{}", t)
            return t
        def LPAREN(self, t):
            logger.dlog("{}", t)
            return t
        def RPAREN(self, t):
            logger.dlog("{}", t)
            return t
        def LBRACE(self, t):
            logger.dlog("{}", t)
            return t
        def RBRACE(self, t):
            logger.dlog("{}", t)
            return t
        def COMMA(self, t):
            logger.dlog("{}", t)
            return t
        def DOLLAR_SIGN(self, t):
            logger.dlog("{}", t)
            return t
        def EID(self, t):
            logger.dlog("{}", t)
            return t

lexer = FptunerLexer()
