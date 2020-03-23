

from fpcore_logging import Logger
from fpcore_lexer import FPCoreLexer
from sly import Parser

import fpcore_ast
import sys


logger = Logger()


class FPCoreParser(Parser):
    tokens = FPCoreLexer.tokens

    # fpcore_plus
    @_("fpcore fpcore_plus")
    def fpcore_plus(self, p):
        return (p.fpcore, *p.fpcore_plus)

    @_("fpcore")
    def fpcore_plus(self, p):
        return (p.fpcore, )

    # fpcore
    @_("LP FPCORE LP argument_plus RP property_plus expr RP")
    def fpcore(self, p):
        return fpcore_ast.FPCore(p.argument_plus, p.property_plus, p.expr)

    @_("LP FPCORE LP RP property_plus expr RP")
    def fpcore(self, p):
        return fpcore_ast.FPCore(None, p.property_plus, p.expr)

    @_("LP FPCORE LP argument_plus RP expr RP")
    def fpcore(self, p):
        return fpcore_ast.FPCore(p.argument_plus, None, p.expr)

    @_("LP FPCORE LP RP expr RP")
    def fpcore(self, p):
        return fpcore_ast.FPCore(p[1], None, None, p.expr)

    # argument
    @_("symbol")
    def argument(self, p):
        return p.symbol

    @_("LP BANG property_plus symbol RP")
    def argument(self, p):
        p.symbol.add_properties(p.property_plus)
        return p.symbol

    @_("LP BANG symbol RP")
    def argument(self, p):
        return p.symbol

    # expr
    @_("number",
       "constant",
       "symbol",
       "operation",
       "if_expr",
       "let",
       "let_star",
       "while_expr",
       "while_star",
       "cast",
       "property_expr")
    def expr(self, p):
        return p[0]

    # number
    @_("RATIONAL",
       "DECNUM",
       "HEXNUM")
    def number(self, p):
        return fpcore_ast.Number(p[0])

    @_("LP DIGITS DECNUM DECNUM DECNUM RP")
    def number(self, p):
        return fpcore_ast.Number(" ".join(p[1:4]))

    # constant
    @_("CONSTANT")
    def constant(self, p):
        return fpcore_ast.Constant(p[0])

    # operation
    @_("LP OPERATION expr_plus RP")
    def operation(self, p):
        return fpcore_ast.Operation(p[1], *p.expr_plus)

    # if_expr
    @_("LP IF expr expr expr RP")
    def if_expr(self, p):
        return fpcore_ast.If(p.expr0, p.expr1, p.expr2)

    # let
    @_("LP LET LP binding_plus RP expr RP")
    def let(self, p):
        return fpcore_ast.Let(p.binding_plus, p.expr)

    @_("LP LET LP RP expr RP")
    def let(self, p):
        return fpcore_ast.Let(None, p.expr)

    # let_star
    @_("LP LET_STAR LP binding_plus RP expr RP")
    def let_star(self, p):
        return fpcore_ast.LetStar(p.binding_plus, p.expr)

    @_("LP LET_STAR LP RP expr RP")
    def let_star(self, p):
        return fpcore_ast.LetStar(None, p.expr)

    # while_expr
    @_("LP WHILE expr LP while_binding_plus RP expr RP")
    def while_expr(self, p):
        return fpcore_ast.While(p.expr0, p.while_binding_plus, p.expr1)

    @_("LP WHILE expr LP RP expr RP")
    def while_expr(self, p):
        return fpcore_ast.While(p.expr0, None, p.expr1)

    # while_star
    @_("LP WHILE_STAR expr LP while_binding_plus RP expr RP")
    def while_star(self, p):
        return fpcore_ast.WhileStar(p.expr0, p.while_binding_plus, p.expr1)

    @_("LP WHILE_STAR expr LP RP expr RP")
    def while_star(self, p):
        return fpcore_ast.WhileStar(p.expr0, None, p.expr1)

    # cast
    @_("LP CAST expr RP")
    def cast(self, p):
        return fpcore_ast.Cast(p.expr)

    # property_expr
    @_("LP BANG property_plus expr RP")
    def property_expr(self, p):
        p.expr.add_properties(p.property_plus)
        return p.expr

    @_("LP BANG expr RP")
    def property_expr(self, p):
        return p.expr

    # property
    @_("COLON symbol data",
       "COLON symbol operation",  # modification
       "COLON symbol let")   # modification
    def property(self, p):
        return fpcore_ast.Property(str(p.symbol), p[2])

    @_("COLON symbol LP binding_plus RP")  # modification
    def property(self, p):
        return fpcore_ast.Property(str(p.symbol), p.binding_plus)

    # data
    @_("symbol")
    def data(self, p):
        return p.symbol

    @_("number")
    def data(self, p):
        return p.number

    @_("STRING")
    def data(self, p):
        return p[0]

    @_("LP data_plus RP")
    def data(self, p):
        return p.data_plus

    @_("LP RP")
    def data(self, p):
        return None

    # binding
    @_("LB symbol expr RB")
    def binding(self, p):
        return fpcore_ast.Binding(p.symbol, p.expr)

    # while_binding
    @_("LB symbol expr expr RB")
    def while_binding(self, p):
        return fpcore_ast.WhileBinding(p.symbol, p.expr0, p.expr1)

    # symbol
    @_("SYMBOL")
    def symbol(self, p):
        return fpcore_ast.Variable(p[0])

    # argument_plus
    @_("argument argument_plus")
    def argument_plus(self, p):
        return (p.argument, *p.argument_plus)

    @_("argument")
    def argument_plus(self, p):
        return (p.argument, )

    # property_plus
    @_("property property_plus")
    def property_plus(self, p):
        return (p.property, *p.property_plus)

    @_("property")
    def property_plus(self, p):
        return (p.property, )

    # binding_plus
    @_("binding binding_plus")
    def binding_plus(self, p):
        return (p.binding, *p.binding_plus)

    @_("binding")
    def binding_plus(self, p):
        return (p.binding, )

    # while_binding_plus
    @_("while_binding while_binding_plus")
    def while_binding_plus(self, p):
        return (p.while_binding, *p.while_binding_plus)

    @_("while_binding")
    def while_binding_plus(self, p):
        return (p.while_binding, )

    # expr_plus
    @_("expr expr_plus")
    def expr_plus(self, p):
        return (p.expr, *p.expr_plus)

    @_("expr")
    def expr_plus(self, p):
        return (p.expr, )

    # data_plus
    @_("data data_plus")
    def data_plus(self, p):
        return (p.data, *p.data_plus)

    @_("data")
    def data_plus(self, p):
        return (p.data, )

    # errors
    def error(self, p):
        if p:
            logger.error("Line {}: Syntax error at {}", p.lineno, str(p))
        else:
            logger.error("Unexpected end of FPCore")
        sys.exit(1)


def main(argv):
    logger.set_log_level(Logger.EXTRA)
    if len(argv) == 1:
        text = sys.stdin.read()
    elif len(argv) == 2:
        with open(argv[1], "r") as f:
            text = f.read()

    lexer = FPCoreLexer()
    parser = FPCoreParser()
    tokens = lexer.tokenize(text)
    parsed = parser.parse(tokens)

    for fpc in parsed:
        print(repr(fpc))
        print()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
