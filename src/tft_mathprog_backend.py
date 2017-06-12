
import tft_expr


class MathProg_Backend (object):
    constraints = None
    variables   = None
    objective   = None 

    def MathProg_Backend (self):
        self.constraints = []
        self.variables   = {}

    def addVar (self, ve):
        assert(isinstance(ve, tft_expr.VariableExpr))

        vlabel = ve.label()
        vtype  = ve.type()
        assert(vtype in [int, float]) 

        if (vlabel not in self.variables.keys()):
            self.variables[vlabel] = vtype
        else:
            assert(vtype is self.variables[vlabel])
            
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
        mathprog = open(fname, 'w')

        # write variables
        for vlabel,vtype in self.variables.items():
            vline = 'var ' + vlabel 
            if (vtype is int): 
                vline = vline + ', integer;\n'
            else:
                vline = vline + ';\n'
            mathprog.write(vline)

        mathprog.write('\n') 

        # write objective
        obj_name = '__opt_obj'
        assert(self.objective is not None)
        assert(obj_name not in self.variables.keys())

        mathprog.write(self.objective[0] + ' ' obj_name + ': ' + self.objective[1].toCString() + ';\n')

        mathprog.write('\n') 

        # write constraints
        for ci in range(0, len(self.constraints)):
            mathprog.write('s.t. c'+str(ci)+': ' + self.constraints[1].toCString() + ' ' + self.constraints[0] + ' ' + self.constraints[2].toCString() +';\n')

        mathprog.write('\n')

        # write ending
        mathprog.write('solve;\n')
        mathprog.write('display ')
        if (len(self.variables.keys()) > 0):
            for vlabel in self.variables.keys():
                mathprog.write(vlabel + ', ')
        mathprog.write(obj_name + ';\n')
        mathprog.write('end;\n')

        mathprog.close() 
