
import os
import sys
import random
from fractions import Fraction
import tft_expr
import tft_ir_api
import tft_alloc
import tft_utils


# ========
# global variables
# ========
VERBOSE       = False
TYPE_PREFIX   = "FPTT_"
NEW_EREF      = 0
EREF_LIST     = []
N_CPP_REPEATS = 1000000


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

    if (uop == "abs"):
        if   (bw == tft_alloc.EPSILON_32):
            return "absf"
        elif (bw == tft_alloc.EPSILON_64):
            return "abs"
        elif (bw == tft_alloc.EPSILON_128):
            return "absq"
        else:
            pass
    elif (uop == "exp"):
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



def Expr2Ref (expr, alloc):
    global NEW_EREF
    global EREF_LIST

    assert(isinstance(alloc, tft_alloc.Alloc))

    if   (isinstance(expr, tft_expr.ConstantExpr)):
        return expr.toCString()

    elif (isinstance(expr, tft_expr.VariableExpr) and
          tft_expr.isConstVar(expr)):
        assert(expr.lb().value() == expr.ub().value())

        vstr = str(float(expr.lb().value()))

        my_bw = alloc[expr.getGid()]

        if   (my_bw == tft_alloc.EPSILON_32):
            vstr = vstr + "f"
        elif (my_bw == tft_alloc.EPSILON_64 or
              my_bw == tft_alloc.EPSILON_128):
            vstr = vstr
        else:
            sys.exit("Error: unsupported constant bit-width: " + str(my_bw))

        return vstr

    elif (isinstance(expr, tft_expr.VariableExpr) or
          isinstance(expr, tft_expr.UnaryExpr) or
          isinstance(expr, tft_expr.BinaryExpr)):

        for e_eref in EREF_LIST:
            assert(len(e_eref) == 2)
            e    = e_eref[0]
            eref = e_eref[1]

            if (e == expr):
                return ExprRef(eref)

        eref     = NEW_EREF
        NEW_EREF = NEW_EREF + 1

        EREF_LIST.append([expr, eref])

        return ExprRef(eref)



def Expr2CStatement (expr, alloc):
    assert(isinstance(expr, tft_expr.Expr))

    assert(alloc.isAssigned(expr.getGid()))

    gid   = expr.getGid()
    my_bw = alloc[gid]
    stype = TypeExpr(gid)

    rel = stype + " " + Expr2Ref(expr, alloc) + " = "


    if   (isinstance(expr, tft_expr.ConstantExpr)):
        sys.exit("Error: Should not call Expr2CStatement with a ConstantExpr")


    elif (isinstance(expr, tft_expr.VariableExpr)):
        assert(expr.lb() <= expr.ub())
        rel  = rel + str(random.uniform(expr.lb().value(), expr.ub().value())) + ";"


    elif (isinstance(expr, tft_expr.UnaryExpr)):
        sopd = "(" + stype + ")" + Expr2Ref(expr.opd(), alloc)
        rel  = rel + UnaryOperatorString(expr.operator.label, my_bw) + "(" + sopd + ");"


    elif (isinstance(expr, tft_expr.BinaryExpr)):
        slhs = "(" + stype + ")" + Expr2Ref(expr.lhs(), alloc)
        srhs = "(" + stype + ")" + Expr2Ref(expr.rhs(), alloc)
        rel  = rel + slhs + " " + expr.operator.label + " " + srhs + ";"


    else :
        assert(False)


    return rel


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

    sys.exit("Error: not supported expr 4 FPTaylorExpr.")

def color(plain, my_bw, exp):
    if plain:
        return exp
    if   (my_bw == tft_alloc.EPSILON_32):
        return tft_utils.tx32bit(exp)
    elif (my_bw == tft_alloc.EPSILON_64):
        return tft_utils.tx64bit(exp)
    elif (my_bw == tft_alloc.EPSILON_128):
        return tft_utils.tx128bit(exp)
    else:
        sys.exit("Error: unsupported bit-width: " + str(my_bw))

def ColorExpr(expr, alloc, plain=False):
    def _ColorExpr(expr, alloc):
        assert(isinstance(expr, tft_expr.Expr))
        assert(isinstance(alloc, tft_alloc.Alloc))

        if (isinstance(expr, tft_expr.ConstantExpr)):
            return color(plain, tft_alloc.EPSILON_128, str(float(expr.value())))

        bw_mine = alloc[expr.getGid()]
        if (isinstance(expr, tft_expr.VariableExpr)):
            if (tft_expr.isConstVar(expr)):
                assert(expr.lb() == expr.ub())
                return color(plain, bw_mine, expr.ub().toCString())
            else:
                return color(plain, bw_mine, expr.label())

        if (isinstance(expr, tft_expr.UnaryExpr)):
            str_opd = _ColorExpr(expr.opd(), alloc)
            str_opd = color(plain, bw_mine, "(") + str_opd + color(plain, bw_mine, ")")
            return color(plain, bw_mine, expr.operator.label+" ") + str_opd

        if (isinstance(expr, tft_expr.BinaryExpr)):
            str_lhs = _ColorExpr(expr.lhs(), alloc)
            str_rhs = _ColorExpr(expr.rhs(), alloc)
            str_lhs = color(plain, bw_mine, "(") + str_lhs + color(plain, bw_mine, ")")
            str_rhs = color(plain, bw_mine, "(") + str_rhs + color(plain, bw_mine, ")")
            return color(plain, bw_mine, expr.operator.label+" ") + str_lhs + " \n" + str_rhs

        sys.exit("Error: not supported expr 4 ColorExpr.")
    bw_mine = alloc[expr.getGid()]
    return color(plain, bw_mine, "(") + _ColorExpr(expr, alloc) + color(plain, bw_mine, ")")


# ==== to FPTaylor query ====
def ExportExpr4FPTaylorSanitation (expr, alloc, qfname):
    assert(isinstance(expr, tft_expr.Expr))
    assert(isinstance(alloc, tft_alloc.Alloc))

    vs_all = expr.vars()

    vs = [v for v in vs_all if (not tft_expr.isConstVar(v))]

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
    qfile.write("  __final_result = " + FPTaylorExpr(expr, alloc) + "\n")
    qfile.write(";\n\n")

    qfile.close()


# ==== to colored s-expression ====
def ExportColorInsts(alloc):
    print(alloc)
    assert((type(N_CPP_REPEATS) is int) and (1 <= N_CPP_REPEATS))
    assert(isinstance(alloc, tft_alloc.Alloc))
    assert(all([isinstance(expr, tft_expr.Expr) for expr in tft_ir_api.CPP_INSTS]))

    print("Expression:")
    # colored version for printing
    s = ColorExpr(tft_ir_api.CPP_INSTS[-1], alloc)
    color_s = s.splitlines()
    # uncolored version for calculating indentation
    # (ansi escape code mess up len(str))
    s = ColorExpr(tft_ir_api.CPP_INSTS[-1], alloc, True)
    plain_s = s.splitlines()
    indent = 0
    cline = ""
    line = ""
    for s,cs in zip(plain_s, color_s):
        if len(line) + len(s) > 80-indent:
            print(' '*indent + cline)
            indent += line.count("(") - line.count(")")
            cline = cs
            line = s
        else:
            cline += cs
            line += s

    print(" "*indent + cline)


# ==== to .cpp file ====
def ExportCppInsts (alloc, ifname):
    assert((type(N_CPP_REPEATS) is int) and (1 <= N_CPP_REPEATS))
    assert(isinstance(alloc, tft_alloc.Alloc))
    assert(all([isinstance(expr, tft_expr.Expr) for expr in tft_ir_api.CPP_INSTS]))


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

#    ifile.write("void computation () {\n")
#
#    for expr in tft_ir_api.CPP_INSTS:
#        if (isinstance(expr, tft_expr.VariableExpr) and
#            tft_expr.isConstVar(expr)):
#            continue
#
#        ifile.write("\t" + Expr2CStatement(expr, alloc) + "\n")
#
#    ifile.write("}\n")
#
#    ifile.write("\n")

    ifile.write("int main (int argc, char **argv) {\n")

    ifile.write("\n\tfor(int __r = 0 ; __r < " + str(N_CPP_REPEATS) + " ; __r++) {\n")

#    ifile.write("\t\tcomputation();\n")
    for expr in tft_ir_api.CPP_INSTS:
        if (isinstance(expr, tft_expr.VariableExpr) and
            tft_expr.isConstVar(expr)):
            continue

        ifile.write("\t\t" + Expr2CStatement(expr, alloc) + "\n")

    ifile.write("\t}\n")

    ifile.write("\n\treturn 0;\n}")



# ==== to .input file ====
def ExportExpr2ExprsFile (expr_or_exprs, upper_bound, ifname):
    tft_ir_api.STAT = False

    if (tft_ir_api.TUNE_FOR_ALL):
        assert(len(tft_ir_api.EXTERNAL_GIDS) <= 1)

    if   (tft_ir_api.PREC_CANDIDATES == ["e32", "e64"]):
        tft_ir_api.GID_EPSS[tft_expr.PRESERVED_CONST_GID] = ["e64"]

    elif (tft_ir_api.PREC_CANDIDATES == ["e64", "e128"] or
          tft_ir_api.PREC_CANDIDATES == ["e32", "e64", "e128"]):
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
        sys.exit("ERROR: unsupported type of upper_bound.")

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
                sys.exit("ERROR: invalid type of group epsilon.")

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
