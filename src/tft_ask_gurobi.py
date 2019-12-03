
import os
import sys
from fractions import Fraction
from gurobipy import *
import tft_expr
import tft_error_form


# ==== global variables ====
VERBOSE = False


# ==== class ====
class GurobiSolver:
    solver = None
    var_expr_2_gurobi_var = None
    n_linear_cons = 0
    n_quadratic_cons = 0

    opt_obj = None

    gurobi_var_2_opt_val = None

    def __init__ (self):
        self.reset()

    def reset (self):
        self.solver = gurobipy.Model()
        if (not VERBOSE):
            self.solver.setParam('OutputFlag',False)
        self.var_expr_2_gurobi_var = {}
        self.n_linear_cons = 0
        self.n_quadratic_cons = 0
        self.opt_obj = None
        self.gurobi_var_2_opt_val = {}

    def getNewLinearConsName (self):
        ret = "c" + str(self.n_linear_cons)
        self.n_linear_cons = self.n_linear_cons + 1
        return ret

    def getNewQuadraticConsName (self):
        ret = "qc" + str(self.n_quadratic_cons)
        self.n_quadratic_cons = self.n_quadratic_cons + 1
        return ret

    def convertExpr (self, expr):
        assert(isinstance(expr, tft_expr.Expr))

        if (isinstance(expr, tft_expr.ConstantExpr)):
            return float(expr.toCString())
        elif (isinstance(expr, tft_expr.VariableExpr)):
            if (expr not in self.var_expr_2_gurobi_var):
                print ("???? " + str(expr))
            assert(expr in self.var_expr_2_gurobi_var)
            return self.var_expr_2_gurobi_var[expr]

        elif (isinstance(expr, tft_expr.BinaryExpr)):
            tasks = []
            tasks.append(["left", expr.operator.label, expr.lhs(), expr.rhs()])
            convert_rel = None

            while (True):
                this_task = tasks[len(tasks)-1]
                assert(len(this_task) == 4)
                assert(this_task[0] in ["left", "right", "combine"])
                assert(this_task[1] in ["+", "-", "*", "/"])

                tasks = tasks[0:len(tasks)-1]

                if (this_task[0] == "combine"):
                    c_rel = None
                    if (this_task[1] == "+"):
                        c_rel = this_task[2] + this_task[3]
                    elif (this_task[1] == "-"):
                        c_rel = this_task[2] - this_task[3]
                    elif (this_task[1] == "*"):
                        c_rel = this_task[2] * this_task[3]
                    elif (this_task[1] == "/"):
                        c_rel = this_task[2] / this_task[3]
                    else:
                        sys.exit("ERROR: not supported operation for gurobi")
                    assert(c_rel is not None)

                    if (len(tasks) == 0):
                        convert_rel = c_rel
                        break

                    last_task = tasks[len(tasks)-1]
                    if (last_task[0] == "combine"):
                        sys.exit("ERROR: invalid consequent combines...")
                    elif (last_task[0] == "left"):
                        tasks[len(tasks)-1] = ["right", last_task[1], c_rel, last_task[3]]
                    elif (last_task[0] == "right"):
                        tasks[len(tasks)-1] = ["combine", last_task[1], last_task[2], c_rel]
                    else:
                        sys.exit("ERROR: invalid action of task...")

                elif (this_task[0] == "left"):
                    if (isinstance(this_task[2], tft_expr.ConstantExpr) or isinstance(this_task[2], tft_expr.VariableExpr)):
                        tasks.append(["right", this_task[1], self.convertExpr(this_task[2]), this_task[3]])

                    elif (isinstance(this_task[2], tft_expr.BinaryExpr)):
                        tasks.append(this_task)
                        tasks.append(["left", this_task[2].operator.label, this_task[2].lhs(), this_task[2].rhs()])

                    else:
                        assert(False), "Not supported expr. type for Gurobi..."

                elif (this_task[0] == "right"):
                    if (isinstance(this_task[3], tft_expr.ConstantExpr) or isinstance(this_task[3], tft_expr.VariableExpr)):
                        tasks.append(["combine", this_task[1], this_task[2], self.convertExpr(this_task[3])])

                    elif (isinstance(this_task[3], tft_expr.BinaryExpr)):
                        tasks.append(this_task)
                        tasks.append(["left", this_task[3].operator.label, this_task[3].lhs(), this_task[3].rhs()])

                    else:
                        assert("ERROR: not supported expr. type...")

                else:
                    assert("ERROR: not supported expr. type...")

            assert(len(tasks) == 0)
            assert(convert_rel is not None)
            return convert_rel

        else:
            sys.exit("ERROR: invalid expr. type for convertExpr...")

    def getVar (self, ve):
        assert(isinstance(ve, tft_expr.VariableExpr))
        assert(ve in self.var_expr_2_gurobi_var.keys())
        return self.var_expr_2_gurobi_var[ve]

    def addVar (self, ve):
        assert(isinstance(ve, tft_expr.VariableExpr))
        if (ve.label().startswith(tft_expr.GROUP_ERR_VAR_PREFIX) or ve.label().startswith(tft_expr.ERR_VAR_PREFIX)):
            assert(ve.type() == int)
        if (ve in self.var_expr_2_gurobi_var.keys()):
            return

        # add variable
        var = ""
        if (ve.type() == int):
            var = self.solver.addVar(vtype=GRB.INTEGER, name=ve.label())
        elif (ve.type() == Fraction):
            var = self.solver.addVar(name=ve.label())
        else:
            sys.exit("ERROR: invalid type of VariableExpr found when asking gurobi for OptimizeExpr")
        self.var_expr_2_gurobi_var[ve] = var

        self.solver.update()

        # write range
        if (ve.hasBounds()):
            # check lower bound
            if (ve.lb().value() < Fraction(0, 1)):
                sys.exit("ERROR: variable's (" + ve.label() +") lower bound must be greater than 0")
            # add constraint
            self.addConstraint("linear", "<=", ve.lb(), ve)
            self.addConstraint("linear", "<=", ve, ve.ub())

    def addConstraint (self, ctype, comp, lhs_expr, rhs_expr):
        assert(ctype == "linear" or ctype == "quadratic")
        assert(comp == "==" or comp == "<=" or comp == ">=")
        assert(isinstance(lhs_expr, tft_expr.Expr))
        assert(isinstance(rhs_expr, tft_expr.Expr))

        lhs = self.convertExpr(lhs_expr)
        rhs = self.convertExpr(rhs_expr)

        func_adder = ""
        func_namer = ""

        if (ctype == "linear"):
            func_adder = self.solver.addConstr
            func_namer = self.getNewLinearConsName
        elif (ctype == "quadratic"):
            func_adder = self.solver.addQConstr
            func_namer = self.getNewQuadraticConsName
        else:
            sys.exit("ERROR: invalid cons. type")

        if (comp == "=="):
            func_adder(lhs == rhs, func_namer())
        elif (comp == "<"):
            func_adder(lhs < rhs, func_namer())
        elif (comp == "<="):
            func_adder(lhs <= rhs, func_namer())
        elif (comp == ">"):
            func_adder(lhs > rhs, func_namer())
        elif (comp == ">="):
            func_adder(lhs >= rhs, func_namer())
        else:
            sys.exit("ERROR: invalid comparator")

    # set optimization objective
    def setOptObj (self, obj_expr, opt_dir):
        assert(opt_dir == "max" or opt_dir == "min")
        assert(isinstance(obj_expr, tft_expr.Expr))

        self.opt_obj = 0 + self.convertExpr(obj_expr)

        if (opt_dir == "max"):
            self.solver.setObjective(self.opt_obj, GRB.MAXIMIZE)
        elif (opt_dir == "min"):
            self.solver.setObjective(self.opt_obj, GRB.MINIMIZE)
        else:
            sys.exit("ERROR: invalid opt. direction...")

    def goOpt (self):
        assert(not isinstance(self.opt_obj, str))
        self.solver.optimize()
        opt_rel = self.solver.getAttr("Status")

        # get opt. value
        opt_val = None
        if (opt_rel == GRB.OPTIMAL):
            if (VERBOSE):
                print ("-- got opt. solution --")
            opt_val = self.opt_obj.getValue()
            assert(type(opt_val) is float)
        else:
            self.solver.setParam("DualReductions", 0)
            self.solver.optimize()
            if (VERBOSE):
                if (opt_rel == GRB.INFEASIBLE):
                    print ("-- infeasible... --")
                elif (opt_rel == GRB.INF_OR_UNBD):
                    print ("-- infeasible or unbounded... --")
                elif (opt_rel == GRB.UNBOUNDED):
                    print ("-- unbounded... --")
                else:
                    print ("-- ?? solution status... --")
            return None

        if (VERBOSE):
            print ("---- opt. report ----")
            print ('optized obj: %g' % opt_val)
            print ("---------------------")

        # get var. values
        if (VERBOSE):
            print ("---- var. values ----")
        for v in self.solver.getVars():
            var = self.solver.getVarByName(v.varName)
            self.gurobi_var_2_opt_val[var] = Fraction(v.x)

            if (VERBOSE):
                print ('var. : %s = %g' % (v.varName, v.x))
        if (VERBOSE):
            print ("---------------------")

        # return
        return Fraction(opt_val)

    def getOptVarValue (self, ve):
        assert(isinstance(ve, tft_expr.VariableExpr))
        if (ve in self.var_expr_2_gurobi_var.keys()):
            if (self.var_expr_2_gurobi_var[ve] in self.gurobi_var_2_opt_val.keys()):
                return self.gurobi_var_2_opt_val[self.var_expr_2_gurobi_var[ve]]
            else:
                return None
        else:
            return None
