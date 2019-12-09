

from fptuner_logging import Logger
from tft_lexer import FptunerLexer

import tft_expr as EXPR

from fractions import Fraction

import sys

try:
    from sly import Parser
except ModuleNotFoundError:
    logger.error("SLY must be installed for python3")
    sys.exit(-1)


logger = Logger()


class FptunerParser(Parser):
    tokens = FptunerLexer.tokens


    # expression
    @_("expression add term",
       "expression sub term")
    def expression(self, p):
        logger.log(" expression : expression {} term", p._slice[-2].type)
        logger.log("              {} {} {}",
                   p.expression, p[1], p.term)
        return EXPR.BinaryExpr(p[1], p.expression, p.term)

    @_("term")
    def expression(self, p):
        logger.log(" expression : term")
        logger.log("              {}", p.term)
        return p.term

    # term
    @_("term mul factor",
       "term div factor")
    def term(self, p):
        logger.log(" term : term {} factor", p._slice[-1].type)
        logger.log("        {} {} {}", p.term, p[1], p.factor)
        return EXPR.BinaryExpr(p[1], p.term, p.factor)

    @_("factor")
    def term(self, p):
        logger.log(" term : factor")
        logger.log("       {}", p.factor)
        return p.factor


    # factor
    @_("const",
       "variable",
       "func")
    def factor(self, p):
        logger.log(" factor : {}", p._slice[-1].type)
        logger.log("          {}", p[0])
        return p[0]

    @_("LPAREN expression RPAREN")
    def factor(self, p):
        logger.log(" factor : LPAREN expression RPAREN")
        logger.log("          ( {} )", p.expression)
        return p.expression


    # add
    @_("PLUS")
    def add(self, p):
        logger.log(" add : PLUS")
        logger.log("       {}", p[0])
        gid = -1
        return EXPR.BinaryOp(gid, p[0])

    @_("PLUS DOLLAR_SIGN INTEGER")
    def add(self, p):
        logger.log(" add : PLUS DOLLAR_SIGN INTEGER")
        logger.log("       {}${}", p[0], p[2])
        gid = int(p[2])
        return EXPR.BinaryOp(gid, p[0])


    # sub
    @_("MINUS")
    def sub(self, p):
        logger.log(" sub : MINUS")
        logger.log("       {}", p[0])
        gid = -1
        return EXPR.BinaryOp(gid, p[0])

    @_("MINUS DOLLAR_SIGN INTEGER")
    def sub(self, p):
        logger.log(" sub : MINUS DOLLAR_SIGN INTEGER")
        logger.log("       {}${}", p[0], p[2])
        gid = int(p[2])
        return EXPR.BinaryOp(gid, p[0])


    # mul
    @_("TIMES")
    def mul(self, p):
        logger.log(" mul : TIMES")
        logger.log("       {}", p[0])
        gid = -1
        return EXPR.BinaryOp(gid, p[0])

    @_("TIMES DOLLAR_SIGN INTEGER")
    def mul(self, p):
        logger.log(" mul : TIMES DOLLAR_SIGN INTEGER")
        logger.log("       {}${}", p[0], p[2])
        gid = int(p[2])
        return EXPR.BinaryOp(gid, p[0])


    # div
    @_("DIVIDE")
    def div(self, p):
        logger.log(" div : DIVIDE")
        logger.log("       {}", p[0])
        gid = -1
        return EXPR.BinaryOp(gid, p[0])

    @_("DIVIDE DOLLAR_SIGN INTEGER")
    def div(self, p):
        logger.log(" div : DIVIDE DOLLAR_SIGN INTEGER")
        logger.log("       {}${}", p[0], p[2])
        gid = int(p[2])
        return EXPR.BinaryOp(gid, p[0])


    # # infix_pow
    # @_("INFIX_POW")
    # def infix_pow(self, p):
    #     logger.log(" infix_pow : INFIX_POW")
    #     logger.log("             {}", p[0])
    #     gid = -1
    #     return EXPR.BinaryOp(gid, p[0])

    # @_("INFIX_POW DOLLAR_SIGN INTEGER")
    # def infix_pow(self, p):
    #     logger.log(" infix_pow : INFIX_POW DOLLAR_SIGN INTEGER")
    #     logger.log("             {}${}", p[0], p[2])
    #     gid = int(p[2])
    #     return EXPR.BinaryOp(gid, p[0])


    # const
    @_("float",
       "integer")
    def const(self, p):
        logger.log(" const : {}", p._slice[-1])
        logger.log("         {}", p[0])
        return p[0]


    # func
    @_("binop",
       "unop",
       "round")
    def func(self, p):
        logger.log(" func : {}", p._slice[-1])
        logger.log("        {}", p[0])
        return p[0]


    # binop
    @_("BINOP LPAREN expression COMMA expression RPAREN")
    def binop(self, p):
        logger.log(" binop : BINOP LPAREN expression COMMA expression RPAREN")
        logger.log("         {}({}, {})",
                   pp[0], p.expression0, p.expression1)
        sys.exit(1)
        return something


    # unop
    @_("UNOP LPAREN expression RPAREN")
    def unop(self, p):
        logger.log("func: BINOP LPAREN expression RPAREN")
        logger.log("      BINOP LPAREN {} RPAREN", p.expression)
        sys.exit(1)
        return something


    # round
    @_("ROUND LBRACE INTEGER COMMA NAME COMMA FLOAT COMMA INTEGER COMMA INTEGER RBRACE LPAREN expression RPAREN")
    def round(self, p):
        logger.log(" round : <full spec>")
        logger.log("         {}[{},{},{},{},{}]()",
                   p[0], p[2], p[4], p[6], p[8], p[10], p.expression)
        return p.expression

    @_("ROUND LBRACE INTEGER COMMA NAME COMMA FLOAT COMMA MINUS INTEGER COMMA INTEGER RBRACE LPAREN expression RPAREN")
    def round(self, p):
        logger.log(" round : <full spec>")
        logger.log("         {}[{},{},{},{},{}]",
                   p[0], p[2], p[4], p[6], p[9], p[11])
        return p.expression

    @_("ROUND LPAREN expression RPAREN")
    def round(self, p):
        logger.log(" round : ROUND LPAREN expression RPAREN")
        logger.log("         {}({})",
                   p[0], p.expression)
        return p.expression


    # float
    @_("FLOAT")
    def float(self, p):
        logger.log(" float : FLOAT")
        logger.log("         {}", p[0])
        return EXPR.ConstantExpr(float(p[0]))


    # integer
    @_("INTEGER")
    def integer(self, p):
        logger.log(" integer : INTGER")
        logger.log("           {}", p[0])
        return EXPR.ConstantExpr(int(p[0]))


    # variable
    @_("NAME")
    def variable(self, p):
        logger.log("variable : NAME")
        logger.log("           {}", p[0])
        vtype = Fraction
        gid = -1
        return EXPR.VariableExpr(p[0], vtype, gid, True)

    @_("NAME DOLLAR_SIGN INTEGER")
    def variable(self, p):
        logger.log("variable : NAME DOLLAR_SIGN INTEGER")
        logger.log("           {}${}", p[0], p[2])
        vtype = Fraction
        gid = int(p[2])
        return EXPR.VariableExpr(p[0], vtype, gid, True)

    @_("NAME EID INTEGER")
    def variable(self, p):
        logger.log("variable : NAME EID INTEGER")
        logger.log("           {}_eid_{}", p[0], p[2])
        eid = int(p[2])
        for ve in EXPR.ALL_VariableExprs:
            if ve.index == eid:
                return ve
        logger.error("Variable labeled with eid {} was not defined", eid)
        sys.exit(1)


    # errors
    def error(self, p):
        if p:
            logger.error("Line {}: Syntax error at {}".format(p.lineno, str(p)))
        else:
            logger.error("Unexpected end of function")
        sys.exit(-1)



parser = FptunerParser()
