

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


logger = Logger(level=Logger.HIGH)

# need to change: add non-tft-expr rules for const building
#                 add unary minus
#
# desired prescidence:
#   left-to-right: + -
#   left-to-right: * /
#   right-to-left: ^
#   not-applicable: () functions

# <entry> ::= <variable_definition>
#           | <add_sub>
#
# <variable_definition> ::= <variable> in [ <literal> , <literal> ]
#
# <add_sub> ::= <add_sub> <add> <mul_div>
#             | <add_sub> <sub> <mul_div>
#             | <mul_div>
#
# <mul_div> ::= <mul_div> <mul> <negation>
#             | <mul_div> <div> <negation>
#             | <negation>
#
# <negation> ::= <sub> <negation>
#              | <power>
#
# <power> ::= <group_func> <pow> <power>
#           | <group_func>
#
# <group_func> ::= ( <add_sub> )
#                | BINOP ( <add_sub> , <add_sub> )
#                | BINOP $ <literal_integer> ( <add_sub> , <add_sub> )
#                | UNOP ( <add_sub> )
#                | UNOP $ <literal_integer> ( <add_sub> )
#                | <round>
#                | <atom>
#
# <round> ::= ROUND [ <literal_integer> , ROUND_MODE , <literal_float> , <literal_integer> , <literal_integer> ] ( <expression> )
#           | ROUND ( <expression> )
#
# <atom> ::= <const>
#          | <variable>
#
# <const> ::= <float>
#           | <integer>
#
#
# <variable> ::= NAME
#              | NAME $ <literal_integer>
#              | NAME _eid_ <literal_integer>
#              | __const_ INTEGER $ <literal_integer>
#              | __const_ INTEGER _eid_ <literal_integer>
#
# <add> ::= +
#         | + $ <literal_integer>
#
# <sub> ::= -
#         | - $ <literal_integer>
#
# <mul> ::= *
#         | * $ <literal_integer>
#
# <div> ::= /
#         | / $ <literal_integer>
#
# <pow> ::= ^
#         | ^ $ <literal_integer>
#
# <float> ::= FLOAT
#
# <integer> ::= INTEGER
#
# <literal> ::= <literal_integer>
#             | <literal_float>
#
# <literal_integer> ::= - <literal_integer>
#                     | INTEGER
#
# <literal_float> ::= - <literal_float>
#                     | FLOAT

class FptunerParser(Parser):
    tokens = FptunerLexer.tokens

    # entry
    @_("variable_definition")
    def entry(self, p):
        logger.log(" <entry> ::= <variable_definition>")
        logger.log("             {}", p.variable_definition)
        return p.variable_definition

    @_("add_sub")
    def entry(self, p):
        logger.log(" <entry> ::= <add_sub>")
        logger.log("             {}", p.add_sub)
        return p.add_sub


    # variable_definition
    @_("variable IN LBRACE literal COMMA literal RBRACE")
    def variable_definition(self, p):
        logger.log(" <variable_definition> ::= <variable> in [ <literal> , <literal> ]")
        logger.log("                           {} in [ {} , {} ]",
                   p.variable, p.literal0, p.literal1)
        lower = EXPR.ConstantExpr(p.literal0)
        upper = EXPR.ConstantExpr(p.literal1)
        p.variable.setBounds(lower, upper)
        return p.variable


    # add_sub
    @_("add_sub add mul_div",
       "add_sub sub mul_div")
    def add_sub(self, p):
        logger.log(" <add_sub> ::= <add_sub> <{}> <mul_div>", p._slice[-2].type)
        logger.log("              {} {} {}",
                   p.add_sub, p[1], p.mul_div)
        op = p[1]
        return EXPR.BinaryExpr(op, p.add_sub, p.mul_div)

    @_("mul_div")
    def add_sub(self, p):
        logger.log(" <add_sub> ::= <mul_div>")
        logger.log("               {}", p.mul_div)
        return p.mul_div


    # mul_div
    @_("mul_div mul negation",
       "mul_div div negation")
    def mul_div(self, p):
        logger.log(" <mul_div> ::= <mul_div> <{}> <negation>", p._slice[-1].type)
        logger.log("               {} {} {}", p.mul_div, p[1], p.negation)
        op = p[1]
        return EXPR.BinaryExpr(op, p.mul_div, p.negation)

    @_("negation")
    def mul_div(self, p):
        logger.log(" <mul_div> : <negation>")
        logger.log("             {}", p.negation)
        return p.negation


    # negation
    @_("sub negation")
    def negation(self, p):
        logger.log(" <negation> ::= <sub> <negation>")
        logger.log("                {} {}", p.sub, p.negation)
        neg_one = EXPR.ConstantExpr(-1)
        op = EXPR.BinaryOp(p.sub.gid, "*")
        return EXPR.BinaryExpr(op, neg_one, p.negation)

    @_("power")
    def negation(self, p):
        logger.log(" <negation> ::= <power>")
        logger.log("                {}", p.power)
        return p.power


    # power
    @_("group_func pow power")
    def power(self, p):
        logger.log(" <power> ::= <group_func> <pow> <power>")
        logger.log("             {} {} {}", p.group_func, p.pow, p.power)
        return EXPR.BinaryExpr(p.pow, p.group_func, p.power)

    @_("group_func")
    def power(self, p):
        logger.log(" <power> ::= <group_func>")
        logger.log("             {}", p.group_func)
        return p.group_func


    # group_func
    @_("LPAREN add_sub RPAREN")
    def group_func(self, p):
        logger.log(" <group_func> ::= ( <add_sub> )")
        logger.log("                  ( {} )", p.add_sub)
        return p.add_sub

    @_("BINOP LPAREN add_sub COMMA add_sub RPAREN")
    def group_func(self, p):
        logger.log(" <group_func> ::= BINOP ( <add_sub> , <add_sub> )")
        logger.log("                  {} ( {} , {} )",
                   p[0], p.add_sub0, p.add_sub1)
        gid = -1
        op = EXPR.BinaryOp(gid, p[0])
        return EXPR.BinaryExpr(op, p.add_sub0, p.add_sub1)

    @_("BINOP DOLLAR_SIGN literal_integer LPAREN add_sub COMMA add_sub RPAREN")
    def group_func(self, p):
        logger.log(" <group_func> ::= BINOP $ <literal_integer> ( <add_sub> , <add_sub> )")
        logger.log("                  {} $ {} ( {} , {} )",
                   p[0], p.literal_integer, p.add_sub0, p.add_sub1)
        gid = p.literal_integer
        op = EXPR.BinaryOp(gid, p[0])
        return EXPR.BinaryExpr(op, p.add_sub0, p.add_sub1)

    @_("UNOP LPAREN add_sub RPAREN")
    def group_func(self, p):
        logger.log(" <group_func> ::= UNOP ( <add_sub> )")
        logger.log("                  {} ( {} )",
                   p[0], p.add_sub)
        gid = -1
        op = EXPR.UnaryOp(gid, p[0])
        return EXPR.UnaryExpr(op, p.add_sub)

    @_("UNOP DOLLAR_SIGN literal_integer LPAREN add_sub RPAREN")
    def group_func(self, p):
        logger.log(" <group_func> ::= UNOP $ <literal_integer> ( <add_sub> )")
        logger.log("                  {} $ {} ( {} )",
                   p[0], p.literal_integer, p.add_sub)
        gid = p.literal_integer
        op = EXPR.UnaryOp(gid, p[0])
        return EXPR.UnaryExpr(op, p.add_sub)

    @_("round")
    def group_func(self, p):
        logger.log(" <group_func> ::= <round>")
        logger.log("                  {}", p.round)
        return p.round

    @_("atom")
    def group_func(self, p):
        logger.log(" <group_func> ::= <atom>")
        logger.log("                  {}", p.atom)
        return p.atom


    # round
    @_("ROUND LBRACE literal_integer COMMA ROUND_MODE COMMA literal_float COMMA literal_integer COMMA literal_integer RBRACE LPAREN add_sub RPAREN")
    def round(self, p):
        logger.log(" <round> : ROUND [ <literal_integer> , ROUND_MODE , <literal_float> , <literal_integer> , <literal_integer> ] ( <add_sub> )")
        logger.log("           {} [ {} , {} , {} , {} , {} ] ( {} )",
                   p[0], p.literal_integer0, p[4], p.literal_float, p.literal_integer1, p.literal_integer2, p.add_sub)
        return p.add_sub

    @_("ROUND LPAREN add_sub RPAREN")
    def round(self, p):
        logger.log(" <round> : ROUND LPAREN <add_sub> RPAREN")
        logger.log("         {}({})",
                   p[0], p.add_sub)
        return p.add_sub


    # atom
    @_("float",
       "integer")
    def atom(self, p):
        logger.log(" <atom> ::= <{}>", p._slice[-1].type)
        logger.log("            {}", p[0])
        return p[0]

    @_("variable")
    def atom(self, p):
        logger.log(" <atom> ::= <variable>")
        logger.log("            {}", p.variable)
        return p.variable


    # variable
    @_("NAME")
    def variable(self, p):
        logger.log(" <variable> ::= NAME")
        logger.log("                {}", p[0])
        label = p[0]
        vtype = Fraction
        gid = -1
        return EXPR.VariableExpr(label, vtype, gid, True)

    @_("NAME DOLLAR_SIGN literal_integer")
    def variable(self, p):
        logger.log(" <variable> ::= NAME $ <literal_integer>")
        logger.log("                {} $ {}", p[0], p.literal_integer)
        label = p[0]
        vtype = Fraction
        gid = int(p.literal_integer)
        return EXPR.VariableExpr(label, vtype, gid, True)

    @_("NAME EID literal_integer")
    def variable(self, p):
        logger.log(" <variable> ::= NAME _eid_ <literal_integer>")
        logger.log("                {} _eid_ {}", p[0], p.literal_integer)
        eid = int(p.literal_integer)
        for ve in EXPR.ALL_VariableExprs:
            if ve.index == eid:
                return ve
        logger.error("Variable labeled with eid {} was not defined", eid)
        sys.exit(1)

    @_("CONST INTEGER DOLLAR_SIGN literal_integer")
    def variable(self, p):
        logger.log(" <variable> ::= __const_ INTEGER $ <literal_integer>")
        logger.log("                {} {} $ {}", p[0], p[1], p.literal_integer)
        label = p[0] + p[1]
        vtype = Fraction
        gid = int(p.literal_integer)
        return EXPR.VariableExpr(label, vtype, gid, True)

    @_("CONST INTEGER EID literal_integer")
    def variable(self, p):
        logger.log("variable ::= __const_ INTEGER _eid_ literal_integer")
        logger.log("             {} {} ${}", p[0], p[1], p.literal_integer)
        eid = int(p.literal_integer)
        for ve in EXPR.ALL_VariableExprs:
            if ve.index == eid:
                return ve
        logger.error("Variable labeled with eid {} was not defined", eid)
        sys.exit(1)


    # add
    @_("PLUS")
    def add(self, p):
        logger.log(" <add> ::= +")
        logger.log("           {}", p[0])
        gid = -1
        return EXPR.BinaryOp(gid, p[0])

    @_("PLUS DOLLAR_SIGN literal_integer")
    def add(self, p):
        logger.log(" <add> ::= + DOLLAR_SIGN literal_integer")
        logger.log("           {} $ {}", p[0], p.literal_integer)
        gid = int(p.literal_integer)
        return EXPR.BinaryOp(gid, p[0])


    # sub
    @_("MINUS")
    def sub(self, p):
        logger.log(" <sub> ::= -")
        logger.log("           {}", p[0])
        gid = -1
        return EXPR.BinaryOp(gid, p[0])

    @_("MINUS DOLLAR_SIGN literal_integer")
    def sub(self, p):
        logger.log(" <sub> ::= - $ <literal_integer>")
        logger.log("           {} $ {}", p[0], p.literal_integer)
        gid = int(p.literal_integer)
        return EXPR.BinaryOp(gid, p[0])


    # mul
    @_("TIMES")
    def mul(self, p):
        logger.log(" <mul> ::= *")
        logger.log("           {}", p[0])
        gid = -1
        return EXPR.BinaryOp(gid, p[0])

    @_("TIMES DOLLAR_SIGN literal_integer")
    def mul(self, p):
        logger.log(" <mul> ::= * $ <literal_integer>")
        logger.log("           {} $ {}", p[0], p.literal_integer)
        gid = int(p.literal_integer)
        return EXPR.BinaryOp(gid, p[0])


    # div
    @_("DIVIDE")
    def div(self, p):
        logger.log(" <div> ::= /")
        logger.log("           {}", p[0])
        gid = -1
        return EXPR.BinaryOp(gid, p[0])

    @_("DIVIDE DOLLAR_SIGN literal_integer")
    def div(self, p):
        logger.log(" <div> ::= / $ literal_integer")
        logger.log("           {} $ {}", p[0], p.literal_integer)
        gid = int(p.literal_integer)
        return EXPR.BinaryOp(gid, p[0])


    # pow
    @_("INFIX_POW")
    def pow(self, p):
        logger.log(" <pow> ::= ^")
        logger.log("           {}", p[0])
        gid = -1
        return EXPR.BinaryOp(gid, p[0])

    @_("INFIX_POW DOLLAR_SIGN literal_integer")
    def pow(self, p):
        logger.log(" <pow> ::= ^ $ literal_integer")
        logger.log("           {} $ {}", p[0], p.literal_integer)
        gid = int(p.literal_integer)
        return EXPR.BinaryOp(gid, p[0])


    # float
    @_("FLOAT")
    def float(self, p):
        logger.log(" <float> ::= FLOAT")
        logger.log("         {}", p[0])
        return EXPR.ConstantExpr(float(p[0]))


    # integer
    @_("INTEGER")
    def integer(self, p):
        logger.log(" <integer> ::= INTGER")
        logger.log("               {}", p[0])
        return EXPR.ConstantExpr(int(p[0]))


    # literal
    @_("literal_integer",
       "literal_float")
    def literal(self, p):
        logger.log(" <literal> ::= <{}>", p._slice[-1].type)
        logger.log("               {}", p[0])
        return p[0]


    # literal_integer
    @_("MINUS literal_integer")
    def literal_integer(self, p):
        logger.log(" <literal_integer> ::= - <literal_integer>")
        logger.log("                       {} {}", p[0], p[1])
        return - p.literal_integer

    @_("INTEGER")
    def literal_integer(self, p):
        logger.log(" <literal_integer> ::= INTEGER")
        logger.log("                       {}", p[0])
        return int(p[0])


    # literal_float
    @_("MINUS literal_float")
    def literal_float(self, p):
        logger.log(" <literal_float> ::= - <literal_float>")
        logger.log("                     {} {}", p[0], p[1])
        return - p.literal_float

    @_("FLOAT")
    def literal_float(self, p):
        logger.log(" <literal_float> ::= FLOAT")
        logger.log("                     {}", p[0])
        return float(p[0])


    # errors
    def error(self, p):
        if p:
            logger.error("Line {}: Syntax error at {}".format(p.lineno, str(p)))
        else:
            logger.error("Unexpected end of function")
        sys.exit(-1)



parser = FptunerParser()
