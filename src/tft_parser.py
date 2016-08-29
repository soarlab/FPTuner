
import os 
import sys
import math 
import re 
import tft_expr as EXPR 
import tft_error_form 
import tft_utils 
import tft_alloc 
from fractions import Fraction 


# ========
# global variables 
# ========
BIAS_FLOAT_CONST = False 
COALESCE_CONST   = True 
VERBOSE          = False


# ========
# sub-routines 
# ========
def sstrip (s): 
    assert(type(s) is str) 
    s = s.strip() 
    assert(len(s) > 0)
    return s 

def dumpConsList (cons_list = []): 
    print ("==== construction list dump ====") 

    for i in range(0, len(cons_list)): 
        elist = cons_list[i]
        
        print ("-- level " + str(i) + " --") 
        for j in range(0, len(elist)): 
            print (">> " + str(elist[j])) 

    print ("================================") 

def coalesceConstBinaryExpr (opd0, opd1): 
    if (not COALESCE_CONST): 
        return False 

    if ((not isinstance(opd0, EXPR.ConstantExpr)) or (not isinstance(opd1, EXPR.ConstantExpr))): 
        return False 

    if ((not EXPR.isPreciseConstantExpr(opd0)) or (not EXPR.isPreciseConstantExpr(opd1))): 
        return False 

    return True 

def computeConstBinaryExpr (op, opd0, opd1): 
    assert(isinstance(op, EXPR.BinaryOp)) 
    assert(isinstance(opd0, EXPR.ConstantExpr)) 
    assert(isinstance(opd1, EXPR.ConstantExpr))
    
    v0 = opd0.value() 
    v1 = opd1.value() 
    
    assert((type(v0) is int) or (type(v0) is float) or isinstance(v0, Fraction)) 
    assert((type(v1) is int) or (type(v1) is float) or isinstance(v1, Fraction)) 

    if   (op.label == "+"): 
        return EXPR.ConstantExpr(v0 + v1) 
    elif (op.label == "-"): 
        return EXPR.ConstantExpr(v0 - v1) 
    elif (op.label == "*"): 
        return EXPR.ConstantExpr(v0 * v1) 
    elif (op.label == "/"):
        return EXPR.ConstantExpr(v0 / v1) 
    elif (op.label == "^"): 
        return EXPR.ConstantExpr(v0 ** v1) 
    else: 
        assert(False) 


# ========
# string to operator 
# ========
def String2Op (s, op_class, op_labels = []): 
    s = sstrip(s) 

    gid = -1 

    tokens = tft_utils.String2Tokens(s, "$") 
    if (len(tokens) not in [1, 2]): 
        return None 

    label = tokens[0] 
    
    if (label in op_labels): 
        if (len(tokens) == 2): 
            gid = int(tokens[1]) 

        return op_class(gid, label) 

    else:
        return None 

def String2UnaryOp (s): 
    return String2Op(s, EXPR.UnaryOp, EXPR.UnaryOpLabels) 

def String2BinaryOp (s): 
    return String2Op(s, EXPR.BinaryOp, EXPR.BinaryOpLabels) 


def String2BinaryRelation (s): 
    s = sstrip(s) 

    if (s in EXPR.BinaryRelationLabels): 
        return EXPR.BinaryRelation(s) 

    else: 
        return None 



# ========
# string to constant expression 
# ========
def String2ConstantExpr (s): 
    s = sstrip(s) 

    if ((s.find(".") >= 0) or (s.find("e") > 0)): 
        try: 
            v = float(s) 
            return EXPR.ConstantExpr(v) 
        except: 
            return None 

    else: 
        try: 
            v = int(s) 
            if (not BIAS_FLOAT_CONST): 
                v = float(s) 
            return EXPR.ConstantExpr(v)
        except: 
            return None 


# ========
# string to variable expression 
# ========
def String2VariableExpr (s, reject_internal): 
    s = sstrip(s) 

    if (String2ConstantExpr(s) is not None): 
        return None 

    gid = -1 

    tokens = tft_utils.String2Tokens(s, "$") 
    assert(len(tokens) in [1, 2, 3]) 

    # get label 
    label = tokens[0] 
    
    eid = None 
    label_eid = tft_utils.String2Tokens(label, "_eid_") 
    assert(len(label_eid) in [1, 2]) 

    if (len(label_eid) == 2): 
        label = label_eid[0] 
        eid = int(label_eid[1]) 

    # check label validity 
    if (label[0] in ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]): 
        return None 
    
    # get gid 
    if (len(tokens) in [2, 3]): 
        gid = int(tokens[1]) 

    # get vtype 
    vtype = Fraction 

    if (len(tokens) in [3]): 
        if (tokens[2] == "Int"): 
            vtype = int 
        elif (tokens[2] == "Real"):
            vtype = Fraction 
        else: 
            assert(False) 

    # create expression 
    if (reject_internal): 
        assert(0 <= gid)

    if (eid is not None): 
        for ve in EXPR.ALL_VariableExprs: 
            if (ve.index == eid): 
                return ve 

        print ("ERROR: variable labeled with [" + label + "] " + 
               "with expression id [" + str(eid) + "] was not defined...") 
        assert(False) 

    else : 
        return EXPR.VariableExpr(label, vtype, gid, reject_internal) 


# parse for 
# var in [lb, ub]
def String2BoundedVariableExpr (s): 
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

        if (not var.hasBounds()): 
            var.setBounds(vlb, vub) 
        else:
            # assert(var.lb() == vlb) 
            # assert(var.ub() == vub) 
            assert(abs(var.lb().value() - vlb.value()) <= float(1e-07)) 
            assert(abs(var.ub().value() - vub.value()) <= float(1e-07)) 

        return var 


# ========
# expand power expression 
# E.g., expand x^3 to ((x * x) * x) 
# ========
def ExpandConstPowerExpression (op, e_base, c_power): 
    assert((isinstance(op, EXPR.BinaryOp)) and (op.label == "^"))
    assert(isinstance(e_base, EXPR.Expr))
    assert(float(c_power) == int(c_power)) 

    c_power = int(c_power)
    assert(c_power >= 0) 

    if   (c_power == 0): 
        return EXPR.ConstantExpr(1.0) 

    elif (c_power == 1): 
        return e_base

    else: 
        return EXPR.BinaryExpr(EXPR.BinaryOp(op.gid, "*"), 
                               ExpandConstPowerExpression(e_base, (c_power - 1)), 
                               e_base) 


# ========
# string to constant consisted binary expression
# ======== 
def String2ConstBinaryExpr (s): 
    opd0 = None 
    op   = None 
    opd1 = None 
    
    for o in EXPR.BinaryOpLabels: 
        i = s.find(o) 
        
        if (i > 0): 
            if ((opd0 is None) and (op is None) and (opd1 is None)): 
                opd0 = String2ConstantExpr( s[0:i] ) 
                op = String2BinaryOp( o )
                opd1 = String2ConstantExpr( s[i+len(o) : ] )
                
                if (any([(i is None) for i in [opd0, op, opd1]])): 
                    return None 

            else: 
                return None 

    if ((opd0 is None) and (op is None) and (opd1 is None)): 
        return None 
    
    else: 
        assert(isinstance(opd0, EXPR.ConstantExpr) and isinstance(op, EXPR.BinaryOp) and isinstance(opd1, EXPR.ConstantExpr)) 

        if (coalesceConstBinaryExpr(opd0, opd1)): 
            return computeConstBinaryExpr(op, opd0, opd1) 

        else: 
            if (op.label == "^"): 
                assert(isinstance(opd1, EXPR.ConstantExpr)) 
                return ExpandConstPowerExpression(op, opd0, opd1.value()) 
            else: 
                return EXPR.BinaryExpr(op, opd0, opd1) 


# ========
# expr list to expr 
# ========
def EList2UnaryExpr (elist = []): 
    assert(len(elist) > 0) 
    
    if (len(elist) != 2): 
        return None 

    else: 
        if (not isinstance(elist[0], EXPR.UnaryOp)): 
            return None 
        if (not isinstance(elist[1], EXPR.ArithmeticExpr)): 
            return None 

        return EXPR.UnaryExpr(elist[0], elist[1]) 

def EList2BinaryExpr (elist = []): 
    assert(len(elist) > 0) 

    if ((len(elist) == 2) and isinstance(elist[0], EXPR.BinaryOp) and (elist[0].label == "-") and isinstance(elist[1], EXPR.Expr)): 
        revised_bop = String2BinaryOp("*") 
        return EList2BinaryExpr([EXPR.ConstantExpr(-1.0), revised_bop, elist[1]])

    if (len(elist) != 3): 
        return None 

    else: 
        if (not isinstance(elist[0], EXPR.ArithmeticExpr)): 
            return None 
        if (not isinstance(elist[1], EXPR.BinaryOp)): 
            return None 
        if (not isinstance(elist[2], EXPR.ArithmeticExpr)): 
            return None 

        if (coalesceConstBinaryExpr(elist[0], elist[2])): 
            return computeConstBinaryExpr(elist[1], elist[0], elist[2]) 

        else:
            if (elist[1].label == "^"): 
                assert(isinstance(elist[2], EXPR.ConstantExpr)) 
                return ExpandConstPowerExpression(elist[1], elist[0], elist[2].value()) 
            else: 
                return EXPR.BinaryExpr(elist[1], elist[0], elist[2]) 


def EList2BinaryPredicate (elist = []): 
    assert(len(elist) > 0) 

    if (len(elist) != 3): 
        return None 

    else: 
        if (not isinstance(elist[0], EXPR.ArithmeticExpr)): 
            return None 
        if (not isinstance(elist[1], EXPR.BinaryRelation)): 
            return None 
        if (not isinstance(elist[2], EXPR.ArithmeticExpr)): 
            return None 

        return EXPR.BinaryPredicate(elist[1], elist[0], elist[2]) 



# ========
# token interpretation 
# ========
def TokenInterpreter (s, reject_internal): 
    s = sstrip(s) 

    # try UOp, BiOp, and ConstExpr
    uop = String2UnaryOp(s) 

    bop = String2BinaryOp(s) 

    ce  = String2ConstantExpr(s) 

    bre = String2BinaryRelation(s)

    # handle the ambiguity of UOp "-" and BiOp "-" 
    if ((uop is not None) and (uop.label == "-") and (bop is not None) and (bop.label == "-")): 
        uop = None 

    # try to return a UOp, BiOp, or a ConstExpr 
    rel = [i for i in [uop, bop, ce, bre] if (i is not None)] 
    assert(len(rel) in [0, 1]) 
    
    if (len(rel) == 1): 
        return rel[0] 

    # try ConstBinaryExpr and VariableExpr 
    cbe = String2ConstBinaryExpr(s) 
    ve  = String2VariableExpr(s, reject_internal) 

    # try to return a ConstBinaryExpr or a VariableExpr 
    rel = [i for i in [cbe, ve] if (i is not None)] 
    if (len(rel) != 1): 
        print ("ERROR: TokenInterpreter failed with string: ") 
        print (s) 
    assert(len(rel) == 1) 
    
    return rel[0] 


# ========
# expression list interpreter 
# ========
def EListInterpreter (elist = []): 
    assert(len(elist) in [1, 2, 3]) 

    if (len(elist) == 1): 
        return elist[0] 

    ue = EList2UnaryExpr(elist) 

    be = EList2BinaryExpr(elist) 

    bp = EList2BinaryPredicate(elist)

    rel = [i for i in [ue, be, bp] if (i is not None)] 
    assert(len(rel) == 1) 

    return rel[0] 


# ========
# consuming input string 
# ========
C_ENV_START = ["("] 
C_ENV_END = [")"] 
C_END = [" "] 
SBUF_FPT_ROUND_KEYS = ["rnd64"] 
SBUF_FPT_BLACKOUT_KEYS = ["rnd"] 

def String2Expr (s, reject_internal): 
    if (VERBOSE): 
        print ("==== parser, String2Expr handles : " + s) 

    cons_list = [[]] 
    
    sbuf = "" 

    fpt_skip = False 

    for i in range(0, len(s)): 
        c = s[i] 

        # deciding FPT blackout ... 
        if (c in C_ENV_START): 
            if (sbuf in SBUF_FPT_BLACKOUT_KEYS): 
                assert(not fpt_skip) 
                sbuf = "" 
                fpt_skip = True 

        if (c in C_ENV_END): 
            if (fpt_skip): 
                fpt_skip = False 
                continue 

        # normal parsing 
        if (fpt_skip): 
            continue 

        if ((not fpt_skip) and ((c in C_ENV_START) or (c in C_ENV_END) or (c in C_END))): 
            if (len(sbuf) > 0): 
                if (sbuf not in SBUF_FPT_ROUND_KEYS): 
                    tok = TokenInterpreter(sbuf, reject_internal)
                    assert(tok is not None) 

                    if (VERBOSE): 
                        print ("-- parser, GEN: " + str(tok)) 
                
                    assert(len(cons_list) > 0) 
                    cons_list[-1].append(tok) 
                
                sbuf = "" 

        else: 
            sbuf = sbuf + c 
            
        if (c in C_ENV_START): 
            if (VERBOSE): 
                print ("-- parser, ADD ENV") 

            cons_list.append([]) 

        if (c in C_ENV_END): 
            assert(len(cons_list) > 0) 
            
            if (len(cons_list[-1]) not in [1, 2, 3]): 
                dumpConsList(cons_list) 
            new_e = EListInterpreter(cons_list[-1]) 

            if (new_e is None): 
                dumpConsList(cons_list) 
            assert(new_e is not None) 

            if (VERBOSE): 
                print ("-- parser, END ENV with " + str(new_e)) 
            
            del cons_list[-1] 

            assert(len(cons_list) > 0) 
            
            cons_list[-1].append(new_e) 

    if (len(sbuf) > 0): 
        tok = TokenInterpreter(sbuf, reject_internal) 
        assert(tok is not None) 
                
        assert(len(cons_list) > 0) 
        cons_list[-1].append(tok) 

        sbuf = "" 

    if (len(cons_list) != 1): 
        dumpConsList(cons_list) 
    assert(len(cons_list) == 1)
 
    if (len(cons_list[0]) != 1): 
        dumpConsList(cons_list)
    assert(len(cons_list[0]) == 1) 

    if (not isinstance(cons_list[0][0], EXPR.Expr)):
        dumpConsList(cons_list) 
    assert(isinstance(cons_list[0][0], EXPR.Expr)) 

    return cons_list[0][0] 


