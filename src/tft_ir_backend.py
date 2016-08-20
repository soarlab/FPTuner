
import os
import sys
import random 
from fractions import Fraction
import tft_expr 
import tft_ir_api 
import tft_alloc 



# ========
# global variables 
# ========
VERBOSE     = False 
TYPE_PREFIX = "FPTT_" 
CPP_INSTS   = [] 
NEW_EREF    = 0
EREF_MAP    = {}


# ========
# sub-routines 
# ========
def ExprRef (id_ref): 
    assert(type(id_ref) is int) 
    
    return "_var_expr_" + str(id_ref) 


def TypeExpr (gid): 
    assert(type(gid) is int) 

    return "FPTT_" + str(gid) 


def UnaryOperatorString (uop, bw): 
    assert(type(uop) is str) 

    if   (uop == "exp"):             
        if   (bw == tft_alloc.EPSILON_32): 
            return "expf" 
        elif (bw == tft_alloc.EPSILON_64): 
            return "exp" 
        elif (bw == tft_alloc.EPSILON_128): 
            return "expq" 
        else:
            pass 
        
    elif (uop == "sqrt"): 
        if   (bw == tft_alloc.EPSILON_32): 
            return "sqrtf" 
        elif (bw == tft_alloc.EPSILON_64): 
            return "sqrt" 
        elif (bw == tft_alloc.EPSILON_128): 
            return "sqrtq" 
        else:
            pass 

    elif (uop == "sin"): 
        if   (bw == tft_alloc.EPSILON_32): 
            return "sinf"
        elif (bw == tft_alloc.EPSILON_64): 
            return "sin" 
        elif (bw == tft_alloc.EPSILON_128): 
            return "sinq" 
        else: 
            pass 
            
    elif (uop == "cos"): 
        if   (bw == tft_alloc.EPSILON_32): 
            return "cosf" 
        elif (bw == tft_alloc.EPSILON_64): 
            return "cos" 
        elif (bw == tft_alloc.EPSILON_128): 
            return "cosq" 
        else: 
            pass 

    else: 
        pass

    sys.exit("Error: unsupported unary operation : " + uop) 



def Eps2CtypeString (eps): 
    assert(isinstance(eps, Fraction)) 

    if (eps == tft_alloc.EPSILON_32): 
        return "float" 

    elif (eps == tft_alloc.EPSILON_64): 
        return "double" 

    elif (eps == tft_alloc.EPSILON_128): 
        return "__float128" 

    else: 
        sys.exit("Error: invalid bit-width: " + str(bw)) 



def Expr2Ref (expr): 
    global NEW_EREF 
    global EREF_MAP 

    if   (isinstance(expr, tft_expr.ConstantExpr)): 
        return expr.toCString() 

    elif (isinstance(expr, tft_expr.VariableExpr) and 
          tft_expr.isConstVar(expr)): 
        assert(expr.lb().value() == expr.ub().value()) 

        return str(float(expr.lb().value())) 

    elif (isinstance(expr, tft_expr.VariableExpr) or 
          isinstance(expr, tft_expr.UnaryExpr) or 
          isinstance(expr, tft_expr.BinaryExpr)): 

        for e,eref in EREF_MAP.items(): 
            if (e == expr): 
                return ExprRef(eref) 

        eref     = NEW_EREF 
        NEW_EREF = NEW_EREF + 1 

        EREF_MAP[expr] = eref
        
        return ExprRef(eref) 
        


def Expr2CStatement (expr, alloc): 
    assert(isinstance(expr, tft_expr.Expr))

    assert(alloc.isAssigned(expr.getGid()))

    gid   = expr.getGid() 
    my_bw = alloc[gid]
    stype = TypeExpr(gid) 

    rel = stype + " " + Expr2Ref(expr) + " = " 


    if   (isinstance(expr, tft_expr.ConstantExpr)): 
        sys.exit("Error: Should not call Expr2CStatement with a ConstantExpr") 


    elif (isinstance(expr, tft_expr.VariableExpr)): 
        assert(expr.lb() <= expr.ub()) 
        rel  = rel + str(random.uniform(expr.lb().value(), expr.ub().value())) + ";" 


    elif (isinstance(expr, tft_expr.UnaryExpr)): 
        sopd = "(" + stype + ")" + Expr2Ref(expr.opd()) 
        rel  = rel + UnaryOperatorString(expr.operator.label, my_bw) + "(" + sopd + ");" 


    elif (isinstance(expr, tft_expr.BinaryExpr)):
        slhs = "(" + stype + ")" + Expr2Ref(expr.lhs()) 
        srhs = "(" + stype + ")" + Expr2Ref(expr.rhs()) 
        rel  = rel + slhs + " " + expr.operator.label + " " + srhs + ";" 


    else : 
        assert(False) 


    return rel 



def Expr2CexprString (expr, gid_eps = {}): 
    if (isinstance(expr, tft_expr.ConstantExpr)): 
        return -1, str(float(expr.value())) 

    my_gid = expr.getGid() 
    assert(my_gid in gid_eps.keys()) 
    
    my_bw = gid_eps[my_gid] 

    if (isinstance(expr, tft_expr.VariableExpr)): 
        return my_bw, expr.label()

    elif (isinstance(expr, tft_expr.UnaryExpr)): 
        str_my_type = "(" + Eps2CtypeString(my_bw) + ")" 

        bw_opd, str_opd = Expr2CexprString(expr.opd(), gid_eps) 

        if (my_bw != bw_opd): 
            str_opd = str_my_type + str_opd 

        my_opt = UnaryOperatorString(expr.operator.label, my_bw)

        return my_bw, ("(" + my_opt + "(" + str_opd + "))") 

    elif (isinstance(expr, tft_expr.BinaryExpr)): 
        str_my_type = "(" + Eps2CtypeString(my_bw) + ")" 

        bw_lhs, str_lhs = Expr2CexprString(expr.lhs(), gid_eps) 
        
        bw_rhs, str_rhs = Expr2CexprString(expr.rhs(), gid_eps) 

        if (my_bw != bw_lhs): 
            str_lhs = str_my_type + str_lhs 
            
        if (my_bw != bw_rhs): 
            str_rhs = str_my_type + str_rhs 

        return my_bw, ("(" + str_lhs + " " + expr.operator.label + " " + str_rhs + ")") 
    
    else: 
        sys.exit("Error: unsupported expression type...\n    Expr: " + expr.toCString()) 



def InspectTargetedExpr (expr, gid_cnt = {}): 
    assert(isinstance(expr, tft_expr.Expr)) 

    if (isinstance(expr, tft_expr.ConstantExpr)): 
        return 

    gid = expr.getGid() 
    
    if (gid not in gid_cnt.keys()): 
        gid_cnt[gid] = 0 
        
    gid_cnt[gid] = gid_cnt[gid] + 1 
        
    if (isinstance(expr, tft_expr.VariableExpr)): 
        return 

    if (isinstance(expr, tft_expr.UnaryExpr)): 
        InspectTargetedExpr(expr.opd(), gid_cnt) 
        return 

    if (isinstance(expr, tft_expr.BinaryExpr)): 
        InspectTargetedExpr(expr.lhs(), gid_cnt) 
        InspectTargetedExpr(expr.rhs(), gid_cnt) 
        return 

    print ("ERROR: invalid expr. for InspectTargetedExpr...") 
    assert(False) 



def FPTaylorTypeCastWrap (bw, s): 
    if   (bw == tft_alloc.EPSILON_32): 
        return "rnd32(" + s + ")" 
    elif (bw == tft_alloc.EPSILON_64): 
        return "rnd64(" + s + ")" 
    elif (bw == tft_alloc.EPSILON_128): 
        return "rnd128(" + s + ")" 
    else: 
        assert(False) 


def FPTaylorExpr (expr, alloc): 
    assert(isinstance(expr, tft_expr.Expr)) 
    assert(isinstance(alloc, tft_alloc.Alloc)) 
    
    if (isinstance(expr, tft_expr.ConstantExpr)): 
        return "rnd128(" + str(float(expr.value())) + ")" 

    if (isinstance(expr, tft_expr.VariableExpr)): 
        bw_mine = alloc[expr.getGid()] 

        if (tft_expr.isConstVar(expr)): 
            assert(expr.lb() == expr.ub())
            return FPTaylorTypeCastWrap(bw_mine, expr.ub().toCString())
        else:
            return FPTaylorTypeCastWrap(bw_mine, expr.label()) 

    if (isinstance(expr, tft_expr.UnaryExpr)): 
        go_cast = False 
        bw_mine = alloc[expr.getGid()] 

        if (isinstance(expr.opd(), tft_expr.ConstantExpr)): 
            go_cast = True 
        else: 
            bw_opd = alloc[expr.opd().getGid()] 
            if (bw_opd != bw_mine): 
                go_cast = True 

        str_opd = FPTaylorExpr(expr.opd(), alloc) 

        if (go_cast): 
            if   (bw_mine == tft_alloc.EPSILON_32): 
                str_opd = "rnd32(" + str_opd + ")" 
            elif (bw_mine == tft_alloc.EPSILON_64): 
                str_opd = "rnd64(" + str_opd + ")" 
            elif (bw_mine == tft_alloc.EPSILON_128):
                str_opd = "rnd128(" + str_opd + ")" 
            else:
                assert(False) 

        return FPTaylorTypeCastWrap(bw_mine, 
                                    expr.operator.label + "(" + str_opd + ")")
    
    if (isinstance(expr, tft_expr.BinaryExpr)): 
        cast_lhs = False 
        cast_rhs = False
        bw_mine = alloc[expr.getGid()] 

        if (isinstance(expr.lhs(), tft_expr.ConstantExpr)): 
            cast_lhs = True 
        else: 
            bw_lhs = alloc[expr.lhs().getGid()] 
            if (bw_lhs != bw_mine): 
                cast_lhs = True 

        if (isinstance(expr.rhs(), tft_expr.ConstantExpr)): 
            cast_rhs = True 
        else: 
            bw_rhs = alloc[expr.rhs().getGid()] 
            if (bw_rhs != bw_mine): 
                cast_rhs = True 

        str_lhs = FPTaylorExpr(expr.lhs(), alloc) 
        str_rhs = FPTaylorExpr(expr.rhs(), alloc) 

        if (cast_lhs): 
            if   (bw_mine == tft_alloc.EPSILON_32): 
                str_lhs = "rnd32(" + str_lhs + ")" 
            elif (bw_mine == tft_alloc.EPSILON_64): 
                str_lhs = "rnd64(" + str_lhs + ")" 
            elif (bw_mine == tft_alloc.EPSILON_128):
                str_lhs = "rnd128(" + str_lhs + ")" 
            else:
                assert(False) 

        if (cast_rhs): 
            if   (bw_mine == tft_alloc.EPSILON_32): 
                str_rhs = "rnd32(" + str_rhs + ")" 
            elif (bw_mine == tft_alloc.EPSILON_64): 
                str_rhs = "rnd64(" + str_rhs + ")" 
            elif (bw_mine == tft_alloc.EPSILON_128):
                str_rhs = "rnd128(" + str_rhs + ")" 
            else:
                assert(False) 

        return FPTaylorTypeCastWrap(bw_mine, 
                                    "(" + str_lhs + " " + expr.operator.label + " " + str_rhs + ")")

    sys.exit("Error: not supported expr 4 FPTaylorExpr...") 



# ==== to FPTaylor query ====
def ExportExpr4FPTaylorSanitation (expr, qfname, fname_atext): 
    assert(isinstance(expr, tft_expr.Expr)) 
    
    vs_all = expr.vars() 

    vs = [v for v in vs_all if (not tft_expr.isConstVar(v))] 

    # -- load alloc. text file -- 
    alloc = tft_alloc.Alloc()
    alloc.loadFromStringFile(fname_atext) 

    qfile = open(qfname, "w") 

    # write variables 
    qfile.write("Variables\n") 
    for i in range(0, len(vs)): 
        v = vs[i] 

        qfile.write("  " + v.label() + " in [" + v.lb().toCString() + ", " + v.ub().toCString() + "]") 
        if (i < (len(vs)-1)): 
            qfile.write(",") 
        qfile.write("\n") 
    qfile.write(";\n\n") 

    # write expressions 
    qfile.write("Expressions\n") 
    qfile.write("  __final_resutl = " + FPTaylorExpr(expr, alloc) + "\n") 
    qfile.write(";\n\n") 

    qfile.close() 



# ==== to .cpp file ==== 
def ExportCppInsts (n_repeats, ifname, fname_atext): 
    assert((type(n_repeats) is int) and (1 <= n_repeats)) 
    assert(all([isinstance(expr, tft_expr.Expr) for expr in tft_ir_api.CPP_INSTS])) 

    # -- load alloc. text file -- 
    alloc = tft_alloc.Alloc()
    alloc.loadFromStringFile(fname_atext) 

    type_def_map = {}
    for gid,eps in alloc.gid2eps.items(): 
        assert(TypeExpr(gid) not in type_def_map.keys()) 

        type_def_map[TypeExpr(gid)] = Eps2CtypeString(eps) 

    
    # -- write .cpp file -- 
    ifile = open(ifname, "w")

    ifile.write("#include <iostream>\n")
    ifile.write("#include <math.h>\n") 
    if (Eps2CtypeString(tft_alloc.EPSILON_128) in type_def_map.values()): 
        ifile.write("extern \"C\" { \n#include \"quadmath.h\"\n}\n")

    ifile.write("\n") 

    ifile.write("using namespace std;\n")

    ifile.write("\n") 

    for tr,tv in type_def_map.items(): 
        ifile.write("#define " + tr + " " + tv + "\n")

    ifile.write("\n") 

    ifile.write("int main (int argc, char **argv) {\n") 
    
    ifile.write("\n\tfor(int __r = 0 ; __r < " + str(n_repeats) + " ; __r++) {\n") 

    for expr in tft_ir_api.CPP_INSTS: 
        if (isinstance(expr, tft_expr.VariableExpr) and 
            tft_expr.isConstVar(expr)): 
            continue 

        ifile.write("\t\t" + Expr2CStatement(expr, alloc) + "\n")

    ifile.write("\t}\n")
        
    ifile.write("\n\treturn 0;\n}") 



# ==== to .cpp file ==== 
def ExportExpr2CppFile (expr_or_exprs, n_repeats, ifname, fname_atext): 
    sys.exit("This function will be deprecated...") 
    assert((type(n_repeats) is int) and (1 <= n_repeats)) 

    if (isinstance(expr_or_exprs, tft_expr.Expr)): 
        expr_or_exprs = [expr_or_exprs] 

    assert(all([isinstance(expr, tft_expr.Expr) for expr in expr_or_exprs])) 

    # -- load alloc. text file -- 
    alloc = tft_alloc.Alloc()
    alloc.loadFromStringFile(fname_atext) 
    
    # -- write .cpp file -- 
    ve_vrange = {} 

    for expr in expr_or_exprs: 
        for ve in expr.vars(): 
            assert(ve.getGid() in alloc.gid2eps.keys()) 
            assert(ve.hasBounds()) 
            
            if (ve not in ve_vrange.keys()): 
                ve_vrange[ve] = [ve.lb().value(), ve.ub().value()] 
            
            assert(ve.lb().value() == ve_vrange[ve][0])
            assert(ve.ub().value() == ve_vrange[ve][1]) 

    ifile = open(ifname, "w")

    ifile.write("#include <iostream>\n")
    ifile.write("#include <math.h>\n") 
    ifile.write("\n") 
    ifile.write("using namespace std;\n\n") 

    ifile.write("int main (int argc, char **argv) {\n") 

    for ve,vr in ve_vrange.items(): 
        gid = ve.getGid() 
        ifile.write("\t" + Eps2CtypeString(alloc[gid]) + " " + ve.label() + " = " + str(random.uniform(ve_vrange[ve][0], ve_vrange[ve][1])) + ";\n") 
    ifile.write("\n") 

    ifile.write("\tfor (int ii = 0 ; ii < " + str(n_repeats) + " ; ii++) {\n") 

    id_expr = 0 
    for expr in expr_or_exprs: 
        bw_expr, str_expr = Expr2CexprString(expr, alloc.gid2eps) 
        
        ifile.write("\t" + Eps2CtypeString(bw_expr) + " ____expr_" + str(id_expr) + " = " + str_expr + ";\n") 

        id_expr = id_expr + 1 

    ifile.write("\n}\n\n") 

    ifile.write("\treturn 0;\n}\n") 

    ifile.close() 


# ==== to .input file ====
def ExportExpr2ExprsFile (expr_or_exprs, upper_bound, ifname): 
    tft_ir_api.STAT = False 

    if (tft_ir_api.TUNE_FOR_ALL): 
        assert(len(tft_ir_api.EXTERNAL_GIDS) <= 1) 
        
    if   (tft_ir_api.PREC_CANDIDATES == ["e32", "e64"]): 
        tft_ir_api.GID_EPSS[tft_expr.PRESERVED_CONST_GID] = ["e64"] 
    
    elif (tft_ir_api.PREC_CANDIDATES == ["e64", "e128"]): 
        tft_ir_api.GID_EPSS[tft_expr.PRESERVED_CONST_GID] = ["e128"] 

    else:
        sys.exit("ERROR: invalid setting of tft_ir_api.PREC_CANDIDATES: " + str(tft_ir_api.PREC_CANDIDATES)) 

    exprs = None 
    if (isinstance(expr_or_exprs, tft_expr.Expr)): 
        exprs = [expr_or_exprs]
    else:
        assert(len(expr_or_exprs) > 0) 
        for expr in expr_or_exprs: 
            assert(isinstance(expr, tft_expr.Expr)) 
        exprs = expr_or_exprs 

    # -- check the # of gangs and the # of error terms in the original error form) 
    if (isinstance(upper_bound, tft_expr.ConstantExpr)): 
        pass 
    elif (isinstance(upper_bound, Fraction) or 
          (type(upper_bound) is float)): 
        upper_bound = tft_expr.ConstantExpr(upper_bound) 
    else: 
        sys.exit("ERROR: unsupported type of upper_bound...") 

    assert(isinstance(upper_bound, tft_expr.ConstantExpr)) 

    for v in tft_ir_api.INPUT_VARS: 
        assert(isinstance(v, tft_expr.VariableExpr)) 
        assert(v.hasBounds()) 

    if (os.path.isfile(ifname)): 
        print ("WARNING: delete file : " + ifname) 
        os.system("rm " + ifname) 
    ifile = open(ifname, "w") 

    # write options 
    ifile.write("options:\n") 
    ifile.write("opt-error-form : " + str(tft_ir_api.OPT_ERROR_FORM) + "\n") 
    ifile.write("\n") 

    # write upper-bound 
    ifile.write("upper-bound:\n") 
    ifile.write(upper_bound.toCString() + "\n") 
    ifile.write("\n")

    # write var-ranges 
    ifile.write("var-ranges:\n") 
    for i in range(0, len(tft_ir_api.INPUT_VARS)): 
        v = tft_ir_api.INPUT_VARS[i] 
        ir_var = v.toIRString() 
        assert(ir_var.startswith("(") and ir_var.endswith(")")) 
        ir_var = ir_var[1:len(ir_var)-1]
        ifile.write(ir_var + " in [" + v.lb().toCString() + ", " + v.ub().toCString() + "]\n") 
                    
    ifile.write("\n")
        
    # write group-epsilons
    ifile.write("group-epsilons:\n") 
    for gid in tft_ir_api.EXTERNAL_GIDS: 
        ifile.write(str(gid) + " : ") 

        g_epss = None 
        if (gid in tft_ir_api.GID_EPSS.keys()): 
            g_epss = tft_ir_api.GID_EPSS[gid] 
        else:
            g_epss = tft_ir_api.PREC_CANDIDATES

        for i in range(0, len(g_epss)): 
            str_eps = g_epss[i]
            if (type(str_eps) is str): 
                pass
            elif (type(str_eps) is float): 
                str_eps = "(" + str(str_eps) + ")" 
            else:
                sys.exit("ERROR: invalid type of group epsilon...") 
                    
            if (i == 0): 
                ifile.write("[" + str_eps)
            else:
                ifile.write(", " + str_eps)

        ifile.write("]\n")

    ifile.write("\n") 

    # write equal bit-width gids 
    ifile.write("eq-gids:\n") 
    for gp in tft_ir_api.EQ_GIDS: 
        assert(len(gp) == 2) 
        ifile.write(str(gp[0]) + " = " + str(gp[1]) + "\n") 

    ifile.write("\n") 

    # write gid counts 
    ifile.write("gid-counts:\n") 
    for gid,c in tft_ir_api.GID_COUNTS.items(): 
        ifile.write(str(gid) + " : " + str(c) + "\n") 

    ifile.write("\n") 

    # write casting counts 
    ifile.write("casting-counts:\n") 
    for p,c in tft_ir_api.CAST_COUNTS.items(): 
        ifile.write(str(p) + " : " + str(c) + "\n") 
    ifile.write("\n") 

    # write gid weight 
    ifile.write("gid-weight:\n") 
    for g,w in tft_ir_api.GID_WEIGHT.items(): 
        ifile.write(str(g) + " : " + str(w) + "\n") 
    ifile.write("\n") 
    
    # write exprs 
    ifile.write("exprs:\n") 
    for i in range(0, len(tft_ir_api.INTERVAR_EXPR)): 
        var_expr = tft_ir_api.INTERVAR_EXPR[i] 
        assert(len(var_expr) == 2) 
        assert(isinstance(var_expr[0], tft_expr.VariableExpr))
        assert(isinstance(var_expr[1], tft_expr.Expr)) 
        ir_var = var_expr[0].toIRString() 
        assert(ir_var.startswith("(") and ir_var.endswith(")")) 
        ir_var = ir_var[1:len(ir_var)-1]
        ifile.write(ir_var + " = " + var_expr[1].toIRString() + "\n") 
    for expr in exprs: 
        ifile.write(expr.toIRString() + "\n") 

    ifile.write("\n") 

    # write constraints 
    ifile.write("constraints:\n") 
    for cons in tft_ir_api.CONSTRAINTS: 
        ifile.write(cons.toIRString() + "\n") 

    # finalize 
    ifile.close() 

    
