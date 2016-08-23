
import sys
import tft_expr 
import math 
import tft_alloc 
from fractions import Fraction 


EXTERNAL_GIDS = [] 

GID_COUNTS    = {} 
CAST_COUNTS   = {} 

GID_WEIGHT    = {} 
GID_WEIGHT[tft_expr.PRESERVED_CONST_GID] = 0 # set the weight of the constants to 0 

INTERVAR_EXPR = [] 
INPUT_VARS    = [] 
GID_EPSS      = {} 

EQ_GIDS       = [] 

# COALESCE_CONST = True 
COALESCE_CONST = False 

CONSTRAINTS    = [] 
CONST_ID       = 0 


OPT_ERROR_FORM  = True 
TUNE_FOR_ALL    = False 
PREC_CANDIDATES = ["e32", "e64"] 


LOAD_CPP_INSTS  = False 
CPP_INSTS       = []


TARGET_EXPR     = None 


def VarEIndex (eid): 
    return "evar_" + str(eid) 


def CountGID (gid, n=1): 
    global GID_COUNTS 

    assert(type(gid) is int)
    assert(0 <= gid)

    if (gid not in GID_COUNTS.keys()): 
        GID_COUNTS[gid] = 0 

    GID_COUNTS[gid] = GID_COUNTS[gid] + n


def AppendCppInst (expr): 
    global CPP_INSTS 

    assert(isinstance(expr, tft_expr.Expr)) 
    
    if (LOAD_CPP_INSTS): 
        CPP_INSTS.append(expr) 


def CountCasting (from_opd, to_gid): 
    global CAST_COUNTS 

    assert(isinstance(from_opd, tft_expr.Expr)) 
    assert((type(to_gid) is int) and (0 <= to_gid)) 

    from_gid = from_opd.getGid() 
    assert(type(from_gid) is int) 
    assert((0 <= from_gid) or isinstance(from_opd, tft_expr.ConstantExpr))
    
    p = (from_gid, to_gid) 
    if (p not in CAST_COUNTS.keys()): 
        CAST_COUNTS[p] = 0

    CAST_COUNTS[p] = CAST_COUNTS[p] + 1 


# set precision candidates 
def SetPrecCandidates (cands = []): 
    global PREC_CANDIDATES 

    PREC_CANDIDATES = cands 

    assert((PREC_CANDIDATES == ["e32", "e64"]) or 
           (PREC_CANDIDATES == ["e64", "e128"])) 


# set TUNE_FOR_ALL flag 
def SetTuneForAll (flag): 
    global TUNE_FOR_ALL 

    assert(type(flag) is bool) 

    TUNE_FOR_ALL = flag


#set OPT_ERROR_FORM flag 
def SetOptErrorForm (flag): 
    global OPT_ERROR_FORM 

    assert(type(flag) is bool) 

    OPT_ERROR_FORM = flag 


# WARNING: FConst doesn't give you a ConstantExpr 
# Instead, it gives you a VariableExpr which represents a certain constant. 
def FConst (fpn): 
    global CONST_ID 

    assert((type(fpn) is float) or (isinstance(fpn, Fraction))) 
    # return tft_expr.ConstantExpr(fpn)
    
    const_value = tft_expr.ConstantExpr( fpn ) 
    const_name  = tft_expr.PRESERVED_CONST_VPREFIX + "_" + str(CONST_ID) 
    CONST_ID    = CONST_ID + 1 

    return DeclareBoundedVar(const_name, 
                             Fraction, 
                             tft_expr.PRESERVED_CONST_GID, 
                             const_value, const_value, 
                             True)                              


# NOTE: Please don't call this function internally... 
def DeclareBoundedVar (label, vtype, gid, lb, ub, check_prefix=True): 
    global EXTERNAL_GIDS 
    global INPUT_VARS 

    if (TUNE_FOR_ALL): 
        gid = 0 

    CountGID(gid) 

    assert(type(gid) is int)
    assert(0 <= gid)

    if (gid not in EXTERNAL_GIDS): 
        EXTERNAL_GIDS.append(gid) 

    if ((type(lb) is float) or (type(lb) is int)): 
        lb = tft_expr.ConstantExpr(lb)
    elif (isinstance(lb, tft_expr.ConstantExpr)): 
        pass 
    else: 
        sys.exit("ERROR: invalid type of var's lower bound") 

    if ((type(ub) is float) or (type(ub) is int)): 
        ub = tft_expr.ConstantExpr(ub)
    elif (isinstance(ub, tft_expr.ConstantExpr)):
        pass
    else:
        sys.exit("ERROR: invalid type of var's upper bound") 
    assert(lb <= ub) 

    var = tft_expr.VariableExpr(label, vtype, gid, check_prefix)
    var.setBounds(lb, ub)

    if (var not in INPUT_VARS): 
        INPUT_VARS.append(var) 
        
    AppendCppInst(var) 

    return var

def RealVE (label, gid, lb, ub, check_prefix=True): 
    return DeclareBoundedVar(label, Fraction, gid, lb, ub, check_prefix) 



def MakeUnaryExpr (op_label, op_gid, opd0, internal=False): 
    global EXTERNAL_GIDS 

    if ((not internal) and (TUNE_FOR_ALL)): 
        op_gid = 0 

    assert(type(op_label) is str) 
    assert(type(op_gid) is int) 
    assert(isinstance(opd0, tft_expr.Expr)) 

    if (COALESCE_CONST): 
        if (isinstance(opd0, tft_expr.ConstantExpr)): 
            if (op_label == "abs"): 
                eret = tft_expr.ConstantExpr(abs(opd0.value()))
                AppendCppInst(eret) 
                return eret 

            elif (op_label == "-"): 
                eret = tft_expr.ConstantExpr(-1.0 * opd0.value()) 
                AppendCppInst(eret) 
                return eret 

            elif (op_label == "sqrt"): 
                cv = opd0.value() 
                assert(cv >= 0.0) 
                eret = tft_expr.ConstantExpr(math.sqrt(cv)) 
                AppendCppInst(eret) 
                return eret 

            else: 
                sys.exit("ERROR: unknown Unary Operator: " + op_label) 

    # possibly bind the constant type 
    if (tft_expr.isConstVar(opd0)): 
        if   (opd0.getGid() == tft_expr.PRESERVED_CONST_GID): 
            CountGID(tft_expr.PRESERVED_CONST_GID, -1) 
            opd0.gid = op_gid 
        else: 
            if (opd0.getGId() != op_gid): 
                print ("Warning: conflicting constant type...") 

    if (not internal): 
        CountGID(op_gid) 
        CountCasting(opd0, op_gid) 

    if (internal): 
        assert(-1 == op_gid) 
    else: 
        assert(0 <= op_gid) 
    if (op_gid not in EXTERNAL_GIDS): 
        EXTERNAL_GIDS.append(op_gid) 
    
    ret_expr = None 
    if (op_label == "-"): 
        ret_expr = BE("*", op_gid, FConst(-1.0), opd0) 

    else:
        ret_expr = tft_expr.UnaryExpr(tft_expr.UnaryOp(op_gid, op_label), opd0.copy((not internal))) 

        AppendCppInst(ret_expr) 

    return ret_expr 

def UE (op_label, op_gid, opd0, internal=False): 
    return MakeUnaryExpr(op_label, op_gid, opd0, internal) 



def MakeBinaryExpr (op_label, op_gid, opd0, opd1, internal=False):
    global EXTERNAL_GIDS 

    if ((not internal) and (TUNE_FOR_ALL)): 
        op_gid = 0 

    assert(type(op_label) is str) 
    assert(type(op_gid) is int) 
    assert(isinstance(opd0, tft_expr.Expr))
    assert(isinstance(opd1, tft_expr.Expr)) 

    if (COALESCE_CONST): 
#        if (isinstance(opd0, tft_expr.ConstantExpr) and isinstance(opd1, tft_expr.ConstantExpr)): 
        if (isinstance(opd0, tft_expr.ConstantExpr) and isinstance(opd1, tft_expr.ConstantExpr) and tft_expr.isPreciseConstantExpr(opd0) and tft_expr.isPreciseConstantExpr(opd1)): 
            v0 = opd0.value() 
            v1 = opd1.value() 

            if (op_label == "+"): 
                eret = tft_expr.ConstantExpr(v0 + v1) 
                AppendCppInst(eret) 
                return eret 
        
            elif (op_label == "-"): 
                eret = tft_expr.ConstantExpr(v0 - v1)
                AppendCppInst(eret) 
                return eret 
            
            elif (op_label == "*"):
                eret = tft_expr.ConstantExpr(v0 * v1) 
                AppendCppInst(eret) 
                return eret 

            elif (op_label == "/"): 
                eret = tft_expr.ConstantExpr(v0 / v1) 
                AppendCppInst(eret) 
                return eret 

            else: 
                sys.exit("ERROR: unknown Binary Operator: " + op_label) 

    # possibly bind the constant type 
    if (tft_expr.isConstVar(opd0)): 
        if   (opd0.getGid() == tft_expr.PRESERVED_CONST_GID): 
            CountGID(tft_expr.PRESERVED_CONST_GID, -1) 
            opd0.gid = op_gid 
        else: 
            if (opd0.getGid() != op_gid): 
                print ("Warning: conflicting constant type...") 
    if (tft_expr.isConstVar(opd1)): 
        if   (opd1.getGid() == tft_expr.PRESERVED_CONST_GID): 
            CountGID(tft_expr.PRESERVED_CONST_GID, -1)
            opd1.gid = op_gid 
        else:
            if (opd1.getGid() != op_gid): 
                print ("Warning: conflicting constant type...") 

    if (not internal): 
        CountGID(op_gid) 
        CountCasting(opd0, op_gid) 
        CountCasting(opd1, op_gid) 

    if (internal): 
        assert(-1 == op_gid)
    else:
        assert(0 <= op_gid) 
    if (op_gid not in EXTERNAL_GIDS): 
        EXTERNAL_GIDS.append(op_gid) 

    ret_expr = tft_expr.BinaryExpr(tft_expr.BinaryOp(op_gid, op_label), opd0.copy((not internal)), opd1.copy((not internal))) 

    AppendCppInst(ret_expr) 

    return ret_expr 

def BE (op_label, op_gid, opd0, opd1, internal=False): 
    return MakeBinaryExpr(op_label, op_gid, opd0, opd1, internal) 



def SetGroupEpsilons (gid, in_epss = []): 
    global GID_EPSS 
    
    assert(type(gid) is int) 
    assert(0 <= gid) 
    assert(len(in_epss) > 0) 
    assert(all([((type(in_epss[i]) is str) or (type(in_epss[i]) is float)) for i in range(0, len(in_epss))]))
    assert(gid not in GID_EPSS.keys()) 
    assert(gid in EXTERNAL_GIDS) 

    if (TUNE_FOR_ALL): 
        gid = 0 

    last_eps = 1000000.0 
    epss = [] 

    for e in in_epss: 
        if (type(e) is float): 
            assert(e >= 0)
            assert(last_eps > e) 

            epss.append(e) 
            last_eps = e 

        elif (type(e) is str):
            try: 
                i = tft_alloc.EpsLabels_String().index(e) 
                this_eps = tft_alloc.EPSILONS[i].value 

                assert(last_eps > this_eps) 

                epss.append(e) 
                last_eps = this_eps 

            except ValueError : 
                sys.exit("Error: unknown epsilons string : " + str(e)) 

        else: 
            sys.exit("Error: unknown type of epsilons... " + str(e)) 

    assert(len(epss) > 0) 

    GID_EPSS[gid] = epss

def AddBinaryPredicate (relation, opd0, opd1): 
    global CONSTRAINTS  

    assert(type(relation) is str) 
    assert(relation in tft_expr.BinaryRelationLabels) 
    assert(isinstance(opd0, tft_expr.ArithmeticExpr))
    assert(isinstance(opd1, tft_expr.ArithmeticExpr)) 

    bp = tft_expr.BinaryPredicate(tft_expr.BinaryRelation(relation), opd0.copy(), opd1.copy()) 
    
    CONSTRAINTS.append(bp) 

def AddBP (relation, opd0, opd1): 
    return AddBinaryPredicate(relation, opd0, opd1) 


def SetGroupWeight (gid, weight): 
    global GID_WEIGHT 

    assert((type(gid) is int) and (0 <= gid)) 
    assert((type(weight) is float) and (0 <= weight)) 

    GID_WEIGHT[gid] = weight 


def TuneExpr (expr): 
    global TARGET_EXPR 
    
    assert(isinstance(expr, tft_expr.ArithmeticExpr)) 

    TARGET_EXPR = expr 
    


