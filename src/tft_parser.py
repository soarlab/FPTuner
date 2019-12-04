

from fptuner_logging import Logger

import tft_alloc
import tft_error_form
import tft_expr as EXPR
import tft_utils

import math
import os
import re
import sys
import traceback

from fractions import Fraction

logger = Logger()


COALESCE_CONST   = True
VERBOSE          = False

C_ENV_START = ["("]
C_ENV_END = [")"]
C_END = [" "]
SBUF_FPT_ROUND_KEYS = ["rnd64"]
SBUF_FPT_BLACKOUT_KEYS = ["rnd"]


def sstrip(s):
    assert(type(s) is str)
    s = s.strip()
    assert(len(s) > 0)
    return s


def dumpConsList(cons_list = []):
    logger.dlog("==== construction list dump ====")

    for i in range(0, len(cons_list)):
        elist = cons_list[i]

        logger.dlog("-- level {} --", i)
        for j in range(0, len(elist)):
            logger.dlog(">> {}", elist[j])

    logger.dlog("================================")
    traceback.print_stack()
    sys.exit(1)

def coalesceConstBinaryExpr(opd0, opd1):
    return (COALESCE_CONST
            and isinstance(opd0, EXPR.ConstantExpr)
            and isinstance(opd1, EXPR.ConstantExpr)
            and EXPR.isPreciseConstantExpr(opd0)
            and EXPR.isPreciseConstantExpr(opd1))


def computeConstBinaryExpr(op, opd0, opd1):
    assert(isinstance(op, EXPR.BinaryOp))
    assert(isinstance(opd0, EXPR.ConstantExpr))
    assert(isinstance(opd1, EXPR.ConstantExpr))

    v0 = opd0.value()
    v1 = opd1.value()

    assert(type(v0) in {int, float} or isinstance(v0, Fraction))
    assert(type(v1) in {int, float} or isinstance(v1, Fraction))

    ops = {"+": lambda a,b: a+b,
           "-": lambda a,b: a-b,
           "*": lambda a,b: a*b,
           "/": lambda a,b: a/b,
           "^": lambda a,b: a**b,}

    if op.label not in ops:
        logger.error("Unsupported operation on constants: {}", op.label)
        sys.exit(1)

    val = ops[op.label](v0, v1)
    logger.dlog("Combined {} {} {} -> {}", v0, op.label, v1, val)
    logger.log("")
    return EXPR.ConstExpr(val)


def String2Op(s, op_class, op_labels = []):
    s = sstrip(s)

    gid = -1

    tokens = tft_utils.String2Tokens(s, "$")
    if len(tokens) not in {1, 2}:
        logger.dlog("Rejected: {}", tokens)
        return None

    label = tokens[0]
    if label not in op_labels:
        logger.dlog("Rejected, not in op_labels: {} (op_labels={})",
                    label, op_labels)
        return None

    gid = -1 if len(tokens) == 1 else int(tokens[1])

    logger.dlog("Found: {} (gid={})", label, gid)
    logger.log("")
    return op_class(gid, label)


def String2UnaryOp(s):
    return String2Op(s, EXPR.UnaryOp, EXPR.UnaryOpLabels)


def String2BinaryOp(s):
    return String2Op(s, EXPR.BinaryOp, EXPR.BinaryOpLabels)


def String2BinaryRelation(s):
    s = sstrip(s)

    if s not in EXPR.BinaryRelationLabels:
        logger.dlog("Rejected: {}", s)
        return None

    logger.dlog("Found: {}", s)
    logger.log("")
    return EXPR.BinaryRelation(s)


def String2ConstantExpr(s):
    s = sstrip(s)

    try:
        ret = EXPR.ConstantExpr(int(s))
        logger.dlog("Found int: {}", s)
        logger.log("")
        return ret
    except:
        pass

    try:
        ret = EXPR.ConstantExpr(float(s))
        logger.dlog("Found float: {}", s)
        logger.log("")
        return ret
    except:
        pass

    logger.dlog("Rejected: {}", s)
    return None


def String2VariableExpr(s, reject_internal):
    s = sstrip(s)

    if String2ConstantExpr(s) is not None:
        logger.dlog("Rejected, is a ConstantExpr: {}", s)
        return None

    gid = -1

    tokens = tft_utils.String2Tokens(s, "$")
    assert(len(tokens) in {1, 2, 3})

    label = tokens[0]

    eid = None
    label_eid = tft_utils.String2Tokens(label, "_eid_")
    assert(len(label_eid) in {1, 2})

    if len(label_eid) == 2:
        label = label_eid[0]
        eid = int(label_eid[1])

    if label[0] in "0123456789":
        logger.dlog("Rejected, bad label: {}", label)
        return None

    if len(tokens) in {2, 3}:
        gid = int(tokens[1])


    vtype = Fraction
    if len(tokens) == 3:
        if tokens[2] == "Int":
            vtype = int
        elif tokens[2] == "Real":
            vtype = Fraction
        else:
            logger.error("Rejected, invalid vftype: {}", tokens[2])
            sys.exit(1)

    if reject_internal:
        assert(0 <= gid)

    if eid is None:
        logger.dlog("Found: {} (vtype={}, gid={}", label, vtype, gid)
        logger.log("")
        return EXPR.VariableExpr(label, vtype, gid, reject_internal)

    for ve in EXPR.ALL_VariableExprs:
        if ve.index == eid:
            logger.dlog("Found existing: {}", ve)
            logger.log("")
            return ve

    logger.error("Variable labeled with '{}' with expression id '{}' was "
                 "not defined", label, eid)
    sys.exit(1)


def String2BoundedVariableExpr(s):
    tokens = tft_utils.String2Tokens(s, "in")
    assert(len(tokens) == 2)
    assert(tokens[1].startswith("[") and tokens[1].endswith("]"))

    var    = String2Expr(tokens[0], True)
    assert(isinstance(var, EXPR.VariableExpr))

    ran    = tft_utils.String2Tokens(tokens[1][1:len(tokens[1])-1], ",")
    assert(len(ran) == 2)
    vlb    = EXPR.ConstantExpr(var.type()(ran[0]))
    vub    = EXPR.ConstantExpr(var.type()(ran[1]))
    assert(isinstance(vlb, EXPR.ConstantExpr))
    assert(isinstance(vub, EXPR.ConstantExpr))

    if not var.hasBounds():
        var.setBounds(vlb, vub)
    else:
        # assert(var.lb() == vlb)
        # assert(var.ub() == vub)
        assert(abs(var.lb().value() - vlb.value()) <= float(1e-07))
        assert(abs(var.ub().value() - vub.value()) <= float(1e-07))

    logger.dlog("Found: {}", var)
    logger.log("")
    return var


def ExpandConstPowerExpression(op, e_base, c_power):
    assert((isinstance(op, EXPR.BinaryOp)) and (op.label == "^"))
    assert(isinstance(e_base, EXPR.Expr))
    assert(float(c_power) == int(c_power))

    c_power = int(c_power)
    assert(c_power >= 0)

    if   (c_power == 0):
        logger.dlog("Expanded ({})^{} -> 1.0", e_base, c_power)
        logger.log("")
        return EXPR.ConstantExpr(1.0)

    elif (c_power == 1):
        logger.dlog("Expanded ({})^1 -> {}", e_base, e_base)
        logger.log("")
        return e_base

    else:
        logger.dlog("Expanded ({})^{} -> ({})^{} * ({})",
                   e_base, c_power, e_base, c_power-1, e_base)
        logger.log("")
        return EXPR.BinaryExpr(EXPR.BinaryOp(op.gid, "*"),
                               ExpandConstPowerExpression(op,
                                                          e_base,
                                                          (c_power - 1)),
                               e_base)


def String2ConstBinaryExpr(s):
    opd0 = None
    op   = None
    opd1 = None

    for o in EXPR.BinaryOpLabels:
        i = s.find(o)

        if (i > 0):
            if all([thing is None for thing in [opd0, op, opd1]]):
                opd0 = String2ConstantExpr( s[0:i] )
                op = String2BinaryOp( o )
                opd1 = String2ConstantExpr( s[i+len(o) : ] )

                if (any([(i is None) for i in [opd0, op, opd1]])):
                    logger.dlog("Rejected: {}", s)
                    return None

            else:
                logger.dlog("Rejected: {}", s)
                return None

    if all([thing is None for thing in [opd0, op, opd1]]):
        logger.dlog("Rejected: {}", s)
        return None

    assert(isinstance(opd0, EXPR.ConstantExpr)
           and isinstance(op, EXPR.BinaryOp)
           and isinstance(opd1, EXPR.ConstantExpr))

    if coalesceConstBinaryExpr(opd0, opd1):
        retval = computeConstBinaryExpr(op, opd0, opd1)
        logger.dlog("Combined constants, new const: {}",
                    retval)
        logger.log("")
        return retval

    if op.label == "^":
        assert(isinstance(opd1, EXPR.ConstantExpr))
        retval = ExpandConstPowerExpression(op, opd0, opd1.value())
        logger.dlog("Expanded power, new const: {}",
                    retval)
        logger.log("")
        return retval

    retval = EXPR.BinaryExpr(op, opd0, opd1)
    logger.dlog("Found: {}", retval)
    logger.log("")
    return retval


def EList2UnaryExpr(elist = []):
    assert(len(elist) > 0)

    if (len(elist) != 2
        or not isinstance(elist[0], EXPR.UnaryOp)
        or not isinstance(elist[1], EXPR.ArithmeticExpr)):
        logger.dlog("Rejected: {}", [str(e) for e in elist])
        return None

    retval = EXPR.UnaryExpr(elist[0], elist[1])
    logger.dlog("Found: {}", retval)
    logger.log("")
    return retval


def EList2BinaryExpr(elist = []):
    assert(len(elist) > 0)

    if (len(elist) == 2
        and isinstance(elist[0], EXPR.BinaryOp)
        and elist[0].label == "-"
        and isinstance(elist[1], EXPR.Expr)):
        retval = EList2BinaryExpr([EXPR.ConstantExpr(-1.0),
                                   String2BinaryOp("*"),
                                   elist[1]])
        logger.dlog("Modified: {}", retval)
        logger.log("")
        return retval

    if (len(elist) != 3
        or not isinstance(elist[0], EXPR.ArithmeticExpr)
        or not isinstance(elist[1], EXPR.BinaryOp)
        or not isinstance(elist[2], EXPR.ArithmeticExpr)):
        logger.dlog("Rejected: {}", [str(e) for e in elist])
        return None

    if coalesceConstBinaryExpr(elist[0], elist[2]):
        retval = computeConstBinaryExpr(elist[1], elist[0], elist[2])
        logger.dlog("Combined constants, new const: {}", retval)
        logger.log("")
        return retval

    if elist[1].label == "^":
        assert(isinstance(elist[2], EXPR.ConstantExpr))
        retval = ExpandConstPowerExpression(elist[1], elist[0], elist[2].value())
        logger.dlog("Expanded power, new const: {}", retval)
        logger.log("")
        return retval

    retval = EXPR.BinaryExpr(elist[1], elist[0], elist[2])
    logger.dlog("Found: {}", retval)
    logger.log("")
    return retval


def EList2BinaryPredicate(elist = []):
    assert(len(elist) > 0)

    if (len(elist) != 3
        or not isinstance(elist[0], EXPR.ArithmeticExpr)
        or not isinstance(elist[1], EXPR.BinaryRelation)
        or not isinstance(elist[2], EXPR.ArithmeticExpr)):
        logger.dlog("Rejected: {}", [str(e) for e in elist])
        return None

    retval = EXPR.BinaryPredicate(elist[1], elist[0], elist[2])
    logger.dlog("Found: {}", retval)
    logger.log("")
    return retval


def TokenInterpreter(s, reject_internal):
    s = sstrip(s)

    uop = String2UnaryOp(s)
    bop = String2BinaryOp(s)
    ce  = String2ConstantExpr(s)
    bre = String2BinaryRelation(s)

    # handle the ambiguity of UOp "-" and BiOp "-"
    if (uop is not None
        and uop.label == "-"
        and bop is not None
        and bop.label == "-"):
        uop = None

    # try to return a UOp, BiOp, or a ConstExpr
    rel = [i for i in [uop, bop, ce, bre] if i is not None]
    assert(len(rel) in {0, 1})

    if len(rel) == 1:
        retval = rel[0]
        logger.dlog("Found: {}", retval)
        logger.log("")
        return retval

    cbe = String2ConstBinaryExpr(s)
    ve  = String2VariableExpr(s, reject_internal)

    rel = [i for i in [cbe, ve] if i is not None]
    if len(rel) != 1:
        logger.error("TokenInterpreter failed with string: {}", s)
        sys.exit(1)

    assert(len(rel) == 1)

    retval = rel[0]
    logger.dlog("Found: {}", retval)
    logger.log("")
    return retval


def EListInterpreter(elist = []):
    assert(len(elist) in {1, 2, 3})

    if len(elist) == 1:
        retval = elist[0]
        logger.dlog("Found: {}", retval)
        logger.log("")
        return retval

    ue = EList2UnaryExpr(elist)
    be = EList2BinaryExpr(elist)
    bp = EList2BinaryPredicate(elist)

    rel = [i for i in [ue, be, bp] if i is not None]
    assert(len(rel) == 1)

    retval = rel[0]
    logger.dlog("Found: {}", retval)
    logger.log("")
    return retval


def String2Expr(s, reject_internal):
    logger.log("+" + "-"*78 + "+")
    logger.log("|" + " "*78 + "|")
    logger.dlog("Start: {} (reject_internal={})", s, reject_internal)

    cons_list = [[]]
    sbuf = ""
    fpt_skip = False

    for i in range(len(s)):
        c = s[i]

        # deciding FPT blackout .
        if c in C_ENV_START and sbuf in SBUF_FPT_BLACKOUT_KEYS:
            assert(not fpt_skip)
            sbuf = ""
            fpt_skip = True

        if c in C_ENV_END and fpt_skip:
            fpt_skip = False
            continue

        if fpt_skip:
            continue

        if (not fpt_skip
            and (c in C_ENV_START or c in C_ENV_END or c in C_END)):
            if len(sbuf) > 0:
                if sbuf not in SBUF_FPT_ROUND_KEYS:
                    tok = TokenInterpreter(sbuf, reject_internal)
                    assert(tok is not None)
                    assert(len(cons_list) > 0)
                    cons_list[-1].append(tok)

                sbuf = ""

        else:
            sbuf = sbuf + c

        if c in C_ENV_START:
            cons_list.append([])

        if c in C_ENV_END:
            assert(len(cons_list) > 0)

            if len(cons_list[-1]) not in {1, 2, 3}:
                dumpConsList(cons_list)
            new_e = EListInterpreter(cons_list[-1])

            if new_e is None:
                dumpConsList(cons_list)

            del cons_list[-1]
            assert(len(cons_list) > 0)

            cons_list[-1].append(new_e)

    if len(sbuf) > 0:
        tok = TokenInterpreter(sbuf, reject_internal)
        assert(tok is not None)

        assert(len(cons_list) > 0)
        cons_list[-1].append(tok)

        sbuf = ""

    if len(cons_list) != 1:
        dumpConsList(cons_list)

    if len(cons_list[0]) != 1:
        dumpConsList(cons_list)

    if not isinstance(cons_list[0][0], EXPR.Expr):
        dumpConsList(cons_list)

    retval = cons_list[0][0]
    logger.dlog("Final expr: {}", retval)
    logger.log("|" + " "*78 + "|")
    logger.log("+" + "-"*78 + "+")
    return retval
