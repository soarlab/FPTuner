
import os
import sys
import math
import time
from fractions import Fraction
from multiprocessing import Process, Queue

import tft_utils
import tft_expr
import tft_error_form
import tft_ask_gurobi
import tft_ask_glpk
import tft_ask_gelpia
import tft_alloc
import tft_ir_api as IR

import tft_mathprog_backend


# ==== global variables ====
ALL_OPTIMIZERS = ["gurobi", "gelpia", "glpk"]
ID_ERROR_SUM   = 0
VERBOSE        = False

OPTIMIZATION_SKIP_PRECISE_OPTS = False

SEGFAULT_PROTECTION = True



# ========
# sub-routines
# ========
def FreshErrorSumVar ():
    global ID_ERROR_SUM

    var_es = tft_expr.VariableExpr(tft_expr.ERR_SUM_PREFIX+str(ID_ERROR_SUM), Fraction, -1, False)
    ID_ERROR_SUM = ID_ERROR_SUM + 1

    return var_es


def UnifiedCastingNumExpr (eforms):
    uni_casting_map, uni_gid2epsilons = tft_error_form.UnifyCastingMapAndGid2Epsilons(eforms)

    return tft_error_form.CastingNumExpr(uni_casting_map, uni_gid2epsilons)


# ========
# optimizer
# ========
def FindExprBound (optimizer, obj_expr, direction, constraints = []):
    assert(direction in ["max", "min"])
    assert(optimizer in ALL_OPTIMIZERS)
    assert(isinstance(obj_expr, tft_expr.Expr))

    if (isinstance(obj_expr, tft_expr.ConstantExpr)):
        assert(obj_expr.lb().value() == obj_expr.ub().value())
        return obj_expr.lb().value()

    value_bound = None

    if (optimizer == "gelpia"):
        assert(len(constraints) == 0)

        if (direction == "min"):
            obj_expr = IR.MakeBinaryExpr("*", -1, tft_expr.ConstantExpr(Fraction(-1, 1)), obj_expr, True)

        glob_solver = None

        assert(optimizer == "gelpia")

        glob_solver = tft_ask_gelpia.GelpiaSolver()

        max_retries = 3
        n_retries = 0
        value_bound = None
        while (True):
            value_bound = glob_solver.maxObj(obj_expr)
            if (value_bound is not None):
                break
            else:
                n_retries = n_retries + 1
            if (n_retries >= max_retries):
                break

        assert((value_bound is None) or (isinstance(value_bound, Fraction)))

        if ((value_bound is not None) and (direction == "min")):
            value_bound = value_bound * Fraction(-1, 1)

    else:
        sys.exit("ERROR: unknown optimizer: " + optimizer)

    if (value_bound is None):
        return None

    # check and set expr_min
    assert(isinstance(value_bound, Fraction))
    if (direction == "max"):
        obj_expr.setUB(tft_expr.ConstantExpr(value_bound))
    elif (direction == "min"):
        obj_expr.setLB(tft_expr.ConstantExpr(value_bound))
    else:
        sys.exit("ERROR: invalid opt. direction for FindExprBound")

    # return
    assert(type(value_bound) is Fraction)
    return value_bound



# ========
# solver
# ========
# ---- return an alloc. ----
def FirstLevelAllocSolver (optimizers, error_forms = []):
    assert(len(error_forms) > 0)
    assert(("vrange" in optimizers.keys()) and ("alloc" in optimizers.keys()))
    assert(optimizers["vrange"] in ALL_OPTIMIZERS)
    assert(optimizers["alloc"] in ALL_OPTIMIZERS)
    assert(all([isinstance(error_forms[i], tft_error_form.ErrorForm) for i in range(0, len(error_forms))]))

    time_global_opt = time.time()

    tft_utils.VerboseMessage("invoking global optimization to bound first derivatives...")


    # ==== solve expressions' ranges ====
    if (VERBOSE):
        print ("---- val. range opt. in FirstLevelAllocSolver [" + optimizers["vrange"] + "] ----")

   #  unbounded_range = False

    for eform in error_forms: # len(error_forms) == 1
        for et in eform.terms:
            assert(isinstance(et, tft_error_form.ErrorTerm))
            value_max = None
            value_min = None

            # an optimization here: if the only epsilon for the ErrorTerm is 0.0,
            # set arbitrary bounds for the Term's expression since it will contribute 0.0 error anyway
            if (OPTIMIZATION_SKIP_PRECISE_OPTS and (len(et.epsilons) == 1) and (et.epsilons[0].value() == 0.0)):
                et.expr.setBounds(tft_expr.ConstantExpr(0.0), tft_expr.ConstantExpr(0.0))
                et.absexpr().setBounds(tft_expr.ConstantExpr(0.0), tft_expr.ConstantExpr(0.0))

                if (VERBOSE):
                    print ("ErrorTerm[" + str(et.index) + "] which has expression \n" + str(et.expr) + "\nhas an only epsilon 0.0. Therefore, set arbitrary expression bounds for it.")
                    print ("--------------------------------------------------")

                continue

            # find the obj_expr
            obj_expr = et.absexpr()
            obj_expr.setLB(tft_expr.ConstantExpr(Fraction(0, 1)))

            # ---- go solve the expression's range ----
            if (optimizers["vrange"] in ["samplers"]): # parallel solvers
                SAMPLERS.addTask(obj_expr)

            else: # sequential solvers
                if (VERBOSE):
                    print (str(obj_expr) + "  IN...")

                if (obj_expr.hasUB()):
                    value_max = obj_expr.ub().value()

                else:
                    value_max = FindExprBound(optimizers["vrange"], obj_expr, "max", eform.constraints)
                    if (value_max is None):
                        return None
                    obj_expr.setUB(tft_expr.ConstantExpr(value_max))
                assert(value_max is not None)
                if (VERBOSE):
                    print ("    UB: " + str(float(value_max)))

                if (obj_expr.hasLB()):
                    value_min = obj_expr.lb().value()
                else:
                    value_min = FindExprBound(optimizers["vrange"], obj_expr, "min", eform.constraints)
                    if (value_min is None):
                        return None
                    obj_expr.setLB(tft_expr.ConstantExpr(value_min))
                assert(value_min is not None)
                if (VERBOSE):
                    print ("    LB: " + str(float(value_min)))

            if (VERBOSE):
                print ("--------------------------------------------------")

        # ---- for paralllel solvers, solve the expressions' ranges now ----
        if (optimizers["vrange"] in ["samplers"]):
            SAMPLERS.goSample(eform.constraints)

            for et in eform.terms:
                if (OPTIMIZATION_SKIP_PRECISE_OPTS and (len(et.epsilons) == 1) and (et.epsilons[0].value() == 0.0)):
                    continue

                obj_expr = et.absexpr()

                lb, ub = SAMPLERS.getRange(obj_expr)

                if ((lb is None) and (ub is None)):
                    return None

                assert((lb is not None) and (ub is not None))

                assert(lb <= ub)
                obj_expr.setLB(tft_expr.ConstantExpr(lb))
                obj_expr.setUB(tft_expr.ConstantExpr(ub))

                if (VERBOSE):
                    print (str(obj_expr) + "  IN  [", str(float(lb)) + ", " + str(float(ub)) + "]")

                if (VERBOSE):
                    print ("--------------------------------------------------")

    tft_utils.TIME_GLOBAL_OPT = tft_utils.TIME_GLOBAL_OPT + (time.time() - time_global_opt)
    time_allocation           = time.time()

    # ==== dump the bounds of the first derivative expressions ====
#    for et in eform.terms:
#        print ("GID: " + str(et.gid) + " (context: " + str(et.context_gid) + " ) : [" + str(et.absexpr().lb().value()) + ", " + str(float(et.absexpr().ub().value())) + "]")

    tft_utils.VerboseMessage("allocating bit-widths...")


    # ==== solve the allocation problem ====
    mprog_back = tft_mathprog_backend.MathProg_Backend()

    # ---- solve the alloc. problem by using gurobi ----
    alloc_solver = None
    if   (optimizers["alloc"] == "gurobi"):
        alloc_solver = tft_ask_gurobi.GurobiSolver()
    elif (optimizers["alloc"] == "glpk"):
        alloc_solver = tft_ask_glpk.GLPKSolver("__mathprog_glpk.mp")
    else:
        sys.exit("ERROR: unknown alloc. optimizer: " + optimizers["alloc"])

    # ---- solve ----
    for eform in error_forms:
        # -- declare error variables and their range constraints --
        # declare ref. variables
        for et in eform.terms:
            assert(isinstance(et, tft_error_form.ErrorTerm))
            assert(not et.refVar().hasBounds())
            alloc_solver.addVar(et.refVar())

        for gid,epss in eform.gid2epsilons.items():
            for ei in range(0, len(epss)):
                evar = tft_error_form.GroupErrorVar(gid, ei)
                alloc_solver.addVar(evar)

            # add constraints for error variables
            if   (optimizers['alloc'] == 'gurobi'):
                alloc_solver.addConstraint("linear", "==", tft_expr.ConstantExpr(1), tft_error_form.GroupErrorVarSum(gid, epss))
            elif (optimizers['alloc'] == 'glpk'):
                alloc_solver.addConstraint('==',
                                           tft_expr.ConstantExpr(1),
                                           tft_error_form.GroupErrorVarSum(gid, epss))
            else:
                assert(False)

            if (VERBOSE):
                print ("Error Var Constraint: " + tft_error_form.GroupErrorVarSum(gid, epss).toCString() + " == 1")

        # add the optional type casting variables and constraints
        if (tft_utils.LINEAR_TYPE_CASTING_CONSTRAINTS):
            for gid,epss in eform.gid2epsilons.items():
                for cgid, cepss in eform.gid2epsilons.items():
                    for ei in range(0, len(epss)):
                        gvar = tft_error_form.GroupErrorVar(gid, ei)
                        for cei in range(0, len(cepss)):
                            cgvar = tft_error_form.GroupErrorVar(cgid, cei)
                            evar  = tft_error_form.TCastErrorVar(gid, ei, cgid, cei)
                            ubv   = IR.BE("+", -1, tft_expr.ConstantExpr(1), evar, True)
                            lbv   = IR.BE("+", -1, gvar, cgvar, True)

                            alloc_solver.addVar(evar)
                            if   (optimizers['alloc'] == 'gurobi'):
                                alloc_solver.addConstraint("linear", ">=", gvar, evar)
                                alloc_solver.addConstraint("linear", ">=", cgvar, evar)
                                alloc_solver.addConstraint("linear", ">=", ubv, lbv)

                            elif (optimizers['alloc'] == 'glpk'):
                                alloc_solver.addConstraint('<=', evar, gvar)
                                alloc_solver.addConstraint('<=', evar, cgvar)
                                alloc_solver.addConstraint('<=', lbv, ubv)

                            else:
                                assert(False)

        score_expr = eform.scoreExpr()
        for v in score_expr.vars():
            assert(tft_expr.isPseudoBooleanVar(v))
            alloc_solver.addVar(v)

        if (VERBOSE):
            print ("Score Expr: " + score_expr.toCString())

        # add constraints for ref. variables
        ref_sum = None
        expr_up_scaling = eform.scalingUpFactor()
        assert(isinstance(expr_up_scaling, tft_expr.ConstantExpr))

        if (VERBOSE):
            print ("Scaling up Expr: " + str(expr_up_scaling))

        for et in eform.terms:
            # ref. variable
            rvar       = et.refVar()

            error_expr = et.errorExpr(eform.scalingUpFactor(),
                                      eform.gid2epsilons,
                                      eform.casting_map)

            term_expr  = et.overApproxExpr(error_expr)

            assert(all([pvar.isPreservedVar() for pvar in term_expr.vars()]))

            if   (optimizers['alloc'] == 'gurobi'):
                alloc_solver.addConstraint("quadratic", "==", rvar, term_expr)
            elif (optimizers['alloc'] == 'glpk'):
                alloc_solver.addConstraint('==', rvar, term_expr)
            else:
                assert(False)

            if (VERBOSE):
                print ("Ref. Expr.: " + rvar.toCString() + " == " + term_expr.toCString())

            if (ref_sum is None):
                ref_sum = rvar
            else:
                ref_sum = IR.BE("+", -1, ref_sum, rvar, True)

        # add M2 to ref_sum
        M2             = eform.M2
        assert(isinstance(M2,              tft_expr.ConstantExpr))
        assert(isinstance(expr_up_scaling, tft_expr.ConstantExpr))
        expr_scaled_M2 = tft_expr.ConstantExpr(M2.value() * expr_up_scaling.value())
        # expr_scaled_M2 = IR.BE("*", -1, M2, expr_up_scaling, True)
        ref_sum        = IR.BE("+", -1, ref_sum, expr_scaled_M2, True)

        # write error form upper found
        assert(isinstance(eform.upper_bound, tft_expr.ConstantExpr))
        assert(eform.upper_bound > tft_expr.ConstantExpr(0))
        assert(isinstance(ref_sum, tft_expr.Expr))
        expr_scaled_upper_bound = IR.BE("*", -1, eform.upper_bound, expr_up_scaling, True)
        if   (optimizers['alloc'] == 'gurobi'):
            alloc_solver.addConstraint("linear", "<=", ref_sum, expr_scaled_upper_bound)
        elif (optimizers['alloc'] == 'glpk'):
            alloc_solver.addConstraint('<=', ref_sum, expr_scaled_upper_bound)
        else:
            assert(False)

        if (VERBOSE):
            print ("expr_scaled_upper_bound: " + str(expr_scaled_upper_bound))

        if (VERBOSE):
            print ("Reference Constraint: " + ref_sum.toCString() + " <= " + expr_scaled_upper_bound.toCString())

        # write the constraints for equal bit-width groups
        for gp in eform.eq_gids:
            assert(len(gp) == 2)
            gid_1 = gp[0]
            gid_2 = gp[1]

            assert(gid_1 != gid_2)
            assert(gid_1 in eform.gid2epsilons.keys())
            assert(gid_2 in eform.gid2epsilons.keys())
            assert(eform.gid2epsilons[gid_1] == eform.gid2epsilons[gid_2])

            len_epss = len(eform.gid2epsilons[gid_1])

            for j in range(0, len_epss):
                ev_1 = tft_error_form.GroupErrorVar(gid_1, j)
                ev_2 = tft_error_form.GroupErrorVar(gid_2, j)

                if   (optimizers['alloc'] == 'gurobi'):
                    alloc_solver.addConstraint("linear", "==", ev_1, ev_2)
                elif (optimizers['alloc'] == 'glpk'):
                    alloc_solver.addConstraint('==', ev_1, ev_2)

    # ---- generate the constraint for the number of castings ----
    if (tft_utils.N_MAX_CASTINGS is not None):
        assert(type(tft_utils.N_MAX_CASTINGS) is int)
        assert(tft_utils.N_MAX_CASTINGS >= 0)

        cnum_expr = UnifiedCastingNumExpr(error_forms)

        if (cnum_expr is not None):
            assert(isinstance(cnum_expr, tft_expr.Expr))

            cnum_var = tft_expr.VariableExpr(tft_expr.CNUM_PREFIX+"_var", int, -1, False)
            alloc_solver.addVar(cnum_var)
            if   (optimizers['alloc'] == 'gurobi'):
                alloc_solver.addConstraint("quadratic", "==", cnum_expr, cnum_var)
                alloc_solver.addConstraint("linear", "<=", cnum_var, tft_expr.ConstantExpr(tft_utils.N_MAX_CASTINGS))
            elif (optimizers['alloc'] == 'glpk'):
                alloc_solver.addConstraint('==', cnum_expr, cnum_var)
                alloc_solver.addConstraint('<=', cnum_var, tft_expr.ConstantExpr(tft_utils.N_MAX_CASTINGS))
            else:
                assert(False)

            if (VERBOSE):
                print ("Casting Constraint: " + cnum_expr.toCString() + " <= " + str(tft_utils.N_MAX_CASTINGS))

    # ---- add optimization obj. ----
    score_sum = None
    for eform in error_forms:
        if (score_sum is None):
            score_sum = eform.scoreExpr()
        else:
            assert(score_sum == eform.scoreExpr())
            # score_sum = IR.BE("+", -1, score_sum, eform.scoreExpr(), True)

    assert(tft_utils.OPT_METHOD in tft_utils.OPT_METHODS)
    if   (tft_utils.OPT_METHOD == "max-benefit"):
        alloc_solver.setOptObj(score_sum, "max")
    elif (tft_utils.OPT_METHOD == "min-penalty"):
        alloc_solver.setOptObj(score_sum, "min")
    else:
        assert(False), "No such optimization method: " + str(tft_utils.OPT_METHOD)

    if (VERBOSE):
        print ("Tuning Objective: ")
        print (str(score_sum))

    # go opt.
    levar_sum_max = alloc_solver.goOpt()

    alloc = tft_alloc.Alloc()
    if (levar_sum_max is None):
        return None
    else:
        alloc.score = float(levar_sum_max)
        if (VERBOSE):
            print ("==== solver: the optimal score is : " + str(float(levar_sum_max)))

    for eform in error_forms:
        for gid,c in eform.gid_counts.items():
            evvs = []
            assert(gid in eform.gid2epsilons.keys())

            for ei in range(0, len(eform.gid2epsilons[gid])):
                evv = alloc_solver.getOptVarValue(tft_error_form.GroupErrorVar(gid, ei))
                assert(evv is not None)
                assert(isinstance(evv, Fraction))
                # adjust value
                tolerance = 0.01
                if (((1 - tolerance) <= evv) and (evv <= (1 + tolerance))):
                    evv = Fraction(1, 1)
                if (((0 - tolerance) <= evv) and (evv <= (0 + tolerance))):
                    evv = Fraction(0, 1)

                evvs.append(evv)

            if (sum(evvs) != Fraction(1, 1)):
                print ("ERROR:[ " + str(gid) + "] : " + str(evvs) + " : " + str(sum(evvs)))
            assert(sum(evvs) == Fraction(1, 1))
            assert(len(evvs) == len(eform.gid2epsilons[gid]))

            for ei in range(0, len(evvs)):
                if (evvs[ei] == Fraction(1, 1)):
                    eps = eform.gid2epsilons[gid][ei]
                    assert(isinstance(eps, tft_expr.ConstantExpr))
                    alloc[gid] = eps.value()
                    break

    tft_utils.TIME_ALLOCATION = tft_utils.TIME_ALLOCATION + (time.time() - time_allocation)

    return alloc
