
import tft_expr
from fractions import Fraction


class MathProg_Backend (object):
    constraints  = None
    variables    = None
    objective    = None
    mprog_fname  = None
    obj_var_name = None

    def __init__ (self):
        self.constraints = []
        self.variables   = {}

    def addVar (self, ve):
        assert(isinstance(ve, tft_expr.VariableExpr))

        vlabel = ve.label()
        vtype  = ve.type()
        lb     = None
        if (ve.hasLB()):
            lb = ve.lb().value()
        ub     = None
        if (ve.hasUB()):
            ub = ve.ub().value() 
        assert(vtype in [int, float, Fraction])

        if (vlabel not in self.variables.keys()):
            self.variables[vlabel] = [vtype, lb, ub]
        else:
            assert(vtype is self.variables[vlabel][0])
            assert(lb is self.variables[vlabel][1])
            assert(ub is self.variables[vlabel][2])
            
    def setOptObj (self, obj_expr, opt_dir):
        assert(isinstance(obj_expr, tft_expr.Expr))

        if (opt_dir == 'min'): 
            self.objective = ['minimize', obj_expr]
        elif (opt_dir == 'max'):
            self.objective = ['maximize', obj_expr]
        else:
            assert(False) 

    def addConstraint (self, comp, lhs, rhs):
        assert(comp in ['<=', '=='])
        assert(isinstance(lhs, tft_expr.Expr))
        assert(isinstance(rhs, tft_expr.Expr))

        vars_lhs = lhs.vars()
        for ve in vars_lhs:
            self.addVar(ve)
            
        vars_rhs = rhs.vars() 
        for ve in vars_rhs:
            self.addVar(ve)

        self.constraints.append([comp, lhs, rhs])

    def exportMathProg (self, fname):
        self.mprog_fname = fname 
        mathprog = open(self.mprog_fname, 'w')

        # write variables
        for vlabel,tlu in self.variables.items():
            vline = 'var ' + vlabel
            vtype = tlu[0] 
            if (vtype is int): 
                vline = vline + ', integer;\n'
            else:
                vline = vline + ';\n'
            mathprog.write(vline)

        mathprog.write('\n') 

        # write objective
        self.obj_var_name = '__opt_obj'
        assert(self.objective is not None)
        assert(self.obj_var_name not in self.variables.keys())

        mathprog.write(self.objective[0] + ' ' + self.obj_var_name + ': ' + self.objective[1].toCString() + ';\n')

        mathprog.write('\n')

        # write variable ranges
        n_conss = 0 
        for vlabel,tlu in self.variables.items():
            if (tlu[1] is not None):
                mathprog.write('s.t. c'+str(n_conss)+': '+str(float(tlu[1]))+' <= '+vlabel+';\n')
                n_conss += 1
            if (tlu[2] is not None):
                mathprog.write('s.t. c'+str(n_conss)+': '+vlabel+' <= '+str(float(tlu[2]))+';\n')                
                n_conss += 1 

        mathprog.write('\n') 

        # write constraints
        for cons in self.constraints: 
            mathprog.write('s.t. c'+str(n_conss)+': ' + cons[1].toCString() + ' ' + cons[0] + ' ' + cons[2].toCString() +';\n')
            n_conss += 1

        mathprog.write('\n')

        # write ending
        mathprog.write('solve;\n')
        mathprog.write('display ')
        if (len(self.variables.keys()) > 0):
            for vlabel in self.variables.keys():
                mathprog.write(vlabel + ', ')
        mathprog.write(self.obj_var_name + ';\n')
        mathprog.write('end;\n')

        mathprog.close() 
