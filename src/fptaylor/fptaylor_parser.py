

from exceptions import FPTaylorParseError
from fpcore_logging import Logger
from fptaylor_lexer import FPTaylorLexer
from sly import Parser

import all_modifications_ast
import fpcore_ast
import sys


logger = Logger()


class FPTaylorParser(Parser):
    tokens = FPTaylorLexer.tokens

    precedence = (("left", "PLUS", "MINUS"),
                  ("left", "TIMES", "DIVIDE"),
                  ("right", "UMINUS"),)

    # expression
    @_("expression PLUS expression",
       "expression MINUS expression",
       "expression TIMES expression",
       "expression DIVIDE expression")
    def expression(self, p):
        return fpcore_ast.Operation(p[1], p.expression0, p.expression1)

    @_("MINUS expression %prec UMINUS")
    def expression(self, p):
        if type(p.expression) == fpcore_ast.Number:
            if p.expression.source[0] == "-":
                return fpcore_ast.Number(p.expression.source[1:])
            return fpcore_ast.Number("-" + p.expression.source)
        return fpcore_ast.Operation(p[0], p.expression)

    @_("base")
    def expression(self, p):
        return p.base

    # base
    @_("symbol",
       "number",
       "group",
       "operation",
       "round")
    def base(self, p):
        return p[0]

    # symbol
    @_("SYMBOL")
    def symbol(self, p):
        return fpcore_ast.Variable(p[0])

    # number
    @_("RATIONAL",
       "DECNUM")
    def number(self, p):
        return fpcore_ast.Number(p[0])

    # group
    @_("LP expression RP")
    def group(self, p):
        return p.expression

    # operation
    # TODO add more arity
    @_("OPERATION LP expression RP")
    def operation(self, p):
        return fpcore_ast.Operation(p[0], p.expression)

    # round
    @_("ROUND LP expression RP")
    def round(self, p):
        return p.expression

    @_("ROUND LB DECNUM C SYMBOL C DECNUM C DECNUM C DECNUM RB LP expression RP")
    def round(self, p):
        rndop = "rnd[{},{},{},{},{}]({}".format(
            p[2], p[4], p[6], p[8], p[10], p.expression.op)
        if rndop not in all_modifications_ast.FPTaylorToOperation:
            return p.expression
        op = all_modifications_ast.FPTaylorToOperation[rndop]
        p.expression.op = op
        return p.expression

    # errors
    def error(self, p):
        raise FPTaylorParseError(p)


def main(argv):
    logger.set_log_level(Logger.EXTRA)
    if len(argv) == 1:
        text = sys.stdin.read()
    elif len(argv) == 2:
        with open(argv[1], "r") as f:
            text = f.read()

    lexer = FPTaylorLexer()
    parser = FPTaylorParser()
    tokens = lexer.tokenize(text)
    parsed = parser.parse(tokens)

    print(repr(parsed))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
