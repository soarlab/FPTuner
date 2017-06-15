
import os

from fractions import Fraction

import tft_expr
import tft_mathprog_backend as MPBackend 


class GLPKSolver (object):
    mathprog_input_fname = None
    mpbackend            = None
    opt_vlabel_value     = None

    def __init__ (self, mathprog_input_fname):
        assert(type(mathprog_input_fname) is str)

        self.mathprog_input_fname = mathprog_input_fname
        self.mpbackend            = MPBackend.MathProg_Backend()
        self.opt_vlabel_value     = {} 

    def addVar (self, ve):
        self.mpbackend.addVar(ve)
            
    def setOptObj (self, obj_expr, opt_dir):
        self.mpbackend.setOptObj(obj_expr, opt_dir) 

    def addConstraint (self, comp, lhs, rhs):
        self.mpbackend.addConstraint(comp, lhs, rhs)

    def goOpt (self):
        if (os.path.isfile(self.mathprog_input_fname)):
            os.system("rm " + self.mathprog_input_fname)

        self.mpbackend.exportMathProg(self.mathprog_input_fname)
        assert(os.path.isfile(self.mathprog_input_fname))

        # run GLPK
        out_fname = self.mathprog_input_fname + '.output'
        os.system("glpsol --math " + self.mathprog_input_fname + " > " + out_fname)

        # read output file
        ofile = open(out_fname, 'r')

        get_display = False
        
        for aline in ofile:
            aline = aline.strip()
            if (aline == ''):
                continue

            if (get_display):
                s_mid = '.val = '
                i_mid = aline.find(s_mid)
                if (i_mid > 0):
                    vlabel = aline[0:i_mid].strip()
                    value  = Fraction(aline[i_mid+len(s_mid):])

                    assert(vlabel not in self.opt_vlabel_value.keys())
                    self.opt_vlabel_value[vlabel] = value 

            else:
                if (aline.startswith('Display statement at line ')):
                    get_display = True
                    
        ofile.close() 

        # return the optimal value
        assert(self.mpbackend.obj_var_name in self.opt_vlabel_value.keys())
        return self.opt_vlabel_value[self.mpbackend.obj_var_name]

    def getOptVarValue (self, ve): 
        assert(isinstance(ve, tft_expr.VariableExpr))
        vlabel = ve.label()
        
        if (vlabel in self.opt_vlabel_value.keys()):
            return self.opt_vlabel_value[vlabel]
        else:
            return None
