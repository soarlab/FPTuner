
import sys
import math 
from fractions import Fraction 
import tft_utils 

GROUP_ERR_VAR_PREFIX = "__g_err_" 
ERR_VAR_PREFIX = "__err_" 
ERR_SUM_PREFIX = "__errsum_" 
ERR_TERM_REF_PREFIX = "__eterm_" 
CNUM_PREFIX = "__cum" 
PRESERVED_VAR_LABEL_PREFIXES = [GROUP_ERR_VAR_PREFIX, ERR_VAR_PREFIX, ERR_SUM_PREFIX, ERR_TERM_REF_PREFIX, CNUM_PREFIX] 

PRESERVED_CONST_VPREFIX = "__const" 
PRESERVED_CONST_GID     = 9999


ALL_VariableExprs = [] 



# ======== 
# sub-routines 
# ========
def isConstVar (var): 
    if (not isinstance(var, VariableExpr)): 
        return False 

    if (var.label().startswith(PRESERVED_CONST_VPREFIX)): 
        return True 
    else: 
        return False 


def RegisterVariableExpr (var): 
    global ALL_VariableExprs 

    assert(isinstance(var, VariableExpr)) 

    if (var.isPreservedVar()): 
        return 

    was_registered = False 

    for v in ALL_VariableExprs:
        assert(v.hasBounds()) 

        if (v.identical(var)): 
            was_registered = True 

        if (var == v): 

            if (var.hasBounds()): 
                assert(var.lb().value() == v.lb().value())
                assert(var.ub().value() == v.ub().value()) 

            else: 
                var.setBounds(v.lb(), v.ub()) 

    if (not was_registered): 
        ALL_VariableExprs.append(var) 
        

def ExprStatistics (expr, stat={}): 
    assert(isinstance(expr, Expr)) 

    # initialize stat 
    if ("# constants"  not in stat.keys()): 
        stat["# constants"]  = 0 
    if ("# variables"  not in stat.keys()): 
        stat["# variables"]  = 0 
    if ("# operations" not in stat.keys()): 
        stat["# operations"] = 0 
    if ("groups"       not in stat.keys()): 
        stat["groups"]     = []

    if   (isinstance(expr, ConstantExpr)): 
        print ("ERROR: should not do statistics with expression containing real ConstantExprs...") 

    elif (isinstance(expr, VariableExpr)): 

        if    (isConstVar(expr)): 
            stat["# constants"] = stat["# constants"] + 1 

        else: 
            assert(expr.getGid() != PRESERVED_CONST_GID) 
            
            gid = expr.getGid() 

            if (gid not in stat["groups"]): 
                stat["groups"].append(gid) 

            stat["# variables"] = stat["# variables"] + 1 

    elif (isinstance(expr, UnaryExpr)): 

        gid = expr.getGid() 

        if (gid not in stat["groups"]): 
            stat["groups"].append(gid) 

        stat["# operations"] = stat["# operations"] + 1 

        ExprStatistics(expr.opd(), stat) 

    elif (isinstance(expr, BinaryExpr)): 
        
        gid = expr.getGid() 

        if (gid not in stat["groups"]): 
            stat["groups"].append(gid) 

        stat["# operations"] = stat["# operations"] + 1 

        ExprStatistics(expr.lhs(), stat) 
        ExprStatistics(expr.rhs(), stat) 
            
            

# ========
# class definitions 
# ========

# ==== the base class of expression ==== 
ExprCounter = 0 
class Expr (object): 
    index        = None
    operands     = None
    lower_bound  = None 
    upper_bound  = None
    gid          = None 

    def __init__ (self, set_index=True): 
        global ExprCounter 
        if (set_index):
            self.index = ExprCounter 
        self.operands = [] 
        lower_bound = "" 
        upper_bound = "" 
        ExprCounter = ExprCounter + 1 

class ArithmeticExpr (Expr): 
    def __init__ (self, set_index=True): 
        if (sys.version_info.major == 2): 
            sys.exit("Error: FPTuner is currently based on Python3 only...") 
            super(ArithmeticExpr, self).__init__(set_index) 
        elif (sys.version_info.major == 3):
            super().__init__(set_index) 
        else:
            sys.exit("ERROR: not supported python version: " + str(sys.version_info)) 

class Predicate (Expr):     
    def __init__ (self, set_index=True): 
        if (sys.version_info.major == 2): 
            sys.exit("Error: FPTuner is currently based on Python3 only...") 
            super(Predicate, self).__init__(set_index) 
        elif (sys.version_info.major == 3):
            super().__init__(set_index) 
        else:
            sys.exit("ERROR: not supported python version: " + str(sys.version_info)) 



# ==== constant expression ==== 
class ConstantExpr (ArithmeticExpr): 
    def __init__ (self, val): 
        assert((type(val) is int) or (isinstance(val, Fraction)) or (type(val) is float))
        if (type(val) is float): 
            val = Fraction(val)

        if (sys.version_info.major == 2): 
            sys.exit("Error: FPTuner is currently based on Python3 only...") 
            super(ConstantExpr, self).__init__(False) 
        elif (sys.version_info.major == 3):
            super().__init__(False) 
        else:
            sys.exit("ERROR: not supported python version: " + str(sys.version_info)) 

        self.operands.append(val)
        self.lower_bound = val 
        self.upper_bound = val 
        self.gid        = -1 
        
    def value (self):
        assert(len(self.operands) == 1) 
        return self.operands[0]
    
    def type (self): 
        return type(self.value()) 

    def rational_value (self): 
        if (self.type() == int): 
            return Fraction(self.value(), 1) 
        elif (self.type() == Fraction): 
            return self.value() 
        else: 
            sys.exit("ERROR: invalid value type for ConstantExpr") 

    def lb (self): 
        return self

    def ub (self): 
        return self

    def setLB (self, expr): 
        assert(isinstance(expr, Expr))
        assert(expr.value() <= self.value()) 
    
    def setUB (self, expr): 
        assert(isinstance(expr, Expr)) 
        assert(self.value() <= expr.value())

    def __str__ (self): 
        if (self.type() == int): 
            return "([Const:int] " + str(self.value()) + ")"
        elif (self.type() == Fraction): 
            return "([Const:Fraction] " + str(float(self.value())) + ")"
        else: 
            sys.exit("ERROR: invalid type of ConstantExpr found in __str__") 

    def toCString (self, const_inline=False): # to int or float string 
        if (self.type() == int): 
            return str(self.value()) 
        elif (self.type() == Fraction): 
            assert(isinstance(self.value(), Fraction)) 
            # return str(float(self.value().numerator) / float(self.value().denominator)) 
            return str(float(self.value()))
        else: 
            sys.exit("ERROR: invalid type of ConstantExpr: " + str(self)) 

    def toIRString (self): 
        return "(" + self.toCString() + ")"

    def toASTString (self): 
        return self.toIRString() 

    def __eq__ (self, rhs): 
        if (not isinstance(rhs, ConstantExpr)): 
            return False 
        if (self.type() == rhs.type()): 
            return (self.value() == rhs.value()) 
        elif (self.type() == int and rhs.type() == Fraction): 
            return (Fraction(self.value(), 1) == rhs.value())
        elif (self.type() == Fraction and rhs.type() == int): 
            return (self.value() == Fraction(rhs.value(), 1))
        else:
            sys.exit("ERROR: invlaid __eq__ scenario of ConstExpr") 

    def identical (self, rhs): 
        if (not isinstance(rhs, ConstantExpr)): 
            return False 
        if (self.index == rhs.index): 
            assert(self.value() == rhs.value()) 
            return True 
        else: 
            return False 

    def __ne__ (self, rhs): 
        return (not self == rhs) 

    def __gt__ (self, rhs): 
        if (not isinstance(rhs, ConstantExpr)): 
            return False 
        if (self.type() == rhs.type()): 
            return (self.value() > rhs.value()) 
        elif (self.type() == int and rhs.type() == Fraction): 
            return (Fraction(self.value(), 1) > rhs.value())
        elif (self.type() == Fraction and rhs.type() == int): 
            return (self.value() > Fraction(rhs.value(), 1))
        else:
            sys.exit("ERROR: invlaid __gt__ scenario of ConstExpr") 
        
    def __lt__ (self, rhs):
        if (not isinstance(rhs, ConstantExpr)): 
            return False 
        if (self.type() == rhs.type()): 
            return (self.value() < rhs.value()) 
        elif (self.type() == int and rhs.type() == Fraction): 
            return (Fraction(self.value(), 1) < rhs.value())
        elif (self.type() == Fraction and rhs.type() == int): 
            return (self.value() < Fraction(rhs.value(), 1))
        else:
            sys.exit("ERROR: invlaid __lt__ scenario of ConstExpr") 

    def __ge__ (self, rhs): 
        return ((self == rhs) or (self > rhs)) 
    
    def __le__ (self, rhs): 
        return ((self == rhs) or (self < rhs)) 

    def hasLB (self): 
        return True 

    def hasUB (self): 
        return True 

    def hasBounds (self): 
        return True

    def vars (self, by_label=True): 
        return [] 

    def __hash__ (self): 
        return hash(self.value()) 

    def getGid (self):
        return self.gid  

    def includedGids (self): 
        return [self.getGid()] 

    def concEval (self, vmap = {}): 
        retv = self.value() 
        assert((type(retv) is int) or (type(retv) is float) or (isinstance(retv, Fraction))) 
        return retv  

    def getCastings (self): 
        return [] 

    def listCrisis (self): 
        return [] 

    def copy (self, check_prefix=True): 
        return ConstantExpr(self.value()) 

        

# ==== variable expression ==== 
class VariableExpr (ArithmeticExpr):
    vtype = None 

    def __init__ (self, label, vtype, gid, check_prefix=True): 
        assert(isinstance(label, str))
        assert(vtype == int or vtype == Fraction)
        assert(type(gid) is int) 
        
        if (sys.version_info.major == 2): 
            sys.exit("Error: FPTuner is currently based on Python3 only...") 
            super(VariableExpr, self).__init__() 
        elif (sys.version_info.major == 3):
            super().__init__() 
        else:
            sys.exit("ERROR: not supported python version: " + str(sys.version_info)) 

        if (gid == PRESERVED_CONST_GID): 
            assert(label.startswith(PRESERVED_CONST_VPREFIX)) 
 
        self.vtype       = vtype 
        self.operands.append(label) 
        self.gid         = gid 

        if (check_prefix): 
            if (self.isPreservedVar()): 
                print("ERROR: the given label \"" + label + "\" has a preserved prefix...")
                assert(False) 

        RegisterVariableExpr(self)

    def isPreservedVar (self): 
        for pre in PRESERVED_VAR_LABEL_PREFIXES: 
            if (self.label().startswith(pre)): 
                return True
        return False 

    def label (self): 
        assert(len(self.operands) == 1)
        assert(isinstance(self.operands[0], str))
        return self.operands[0] 
    
    def __str__ (self):
        return "([Var] " + self.toIRString() + ")" 

    def idLabel (self): 
        return self.label() + "_eid_" + str(self.index) 

    def toCString (self, const_inline=False): 
        if (isConstVar(self)): 
            assert(self.lb().value() == self.ub().value())
            return self.lb().toCString()
        return self.label() 

    def toIRString (self):
        if (self.vtype is int): 
            return "(" + self.label() + "$" + str(self.gid) + "$Int)"
        else:
            return "(" + self.label() + "$" + str(self.gid) + ")"

    def toASTString (self): 
        return self.idLabel()

    def __eq__ (self, rhs): 
        if (not isinstance(rhs, VariableExpr)): 
            return False 
        return (self.label() == rhs.label() and self.type() == rhs.type() and self.getGid() == rhs.getGid()) 

    def identical (self, rhs): 
        if (not isinstance(rhs, VariableExpr)): 
            return False 
        if (self.index == rhs.index):
            assert(self == rhs) 
            return True 
        else: 
            return False 

    def setLB (self, lb): 
        assert(isinstance(lb, ConstantExpr) or (type(lb) in [int, float]) or isinstance(lb, Fraciton))

        if (not isinstance(lb, ConstantExpr)): 
            lb = ConstantExpr(lb) 

        if (self.lower_bound is None): 
            self.lower_bound = lb

        assert(self.lower_bound.value() == lb.value()) 

    def setUB (self, ub): 
        assert(isinstance(ub, ConstantExpr) or (type(ub) in [int, float]) or isinstance(ub, Fraciton))

        if (not isinstance(ub, ConstantExpr)): 
            ub = ConstantExpr(ub) 

        if (self.upper_bound is None): 
            self.upper_bound = ub 

        assert(self.upper_bound.value() == ub.value()) 

    def setBounds (self, lb, ub): 
        self.setLB(lb) 
        self.setUB(ub) 

    def hasLB (self): 
        return (isinstance(self.lower_bound, ConstantExpr)) 

    def hasUB (self): 
        return (isinstance(self.upper_bound, ConstantExpr)) 

    def hasBounds (self): 
        return (self.hasLB() and self.hasUB()) 

    def lb (self): 
        assert(self.hasLB()) 
        assert(isinstance(self.lower_bound, ConstantExpr))
        return self.lower_bound 

    def ub (self): 
        assert(self.hasUB()) 
        assert(isinstance(self.upper_bound, ConstantExpr)) 
        return self.upper_bound 

    def type (self): 
        assert(self.vtype == int or self.vtype == Fraction)
        return self.vtype 

    def vars (self, by_label=True): 
        return [self] 
    
    def __hash__ (self): 
        return hash(self.label()) 

    def getGid (self): 
        return self.gid 

    def includedGids (self): 
        return [self.getGid()] 

    def concEval (self, vmap = {}): 
        assert(self in vmap.keys()) 
        retv = vmap[self] 
        assert((type(retv) is int) or (type(retv) is float) or (isinstance(retv, Fraction))) 
        return retv 

    def getCastings (self): 
        return [] 

    def listCrisis (self): 
        return [] 

    def copy(self, check_prefix=True): 
        ret = VariableExpr(self.label(), self.type(), self.getGid(), check_prefix) 

        if (self.hasLB()): 
            ret.setLB(self.lb()) 
        if (self.hasUB()):
            ret.setUB(self.ub())

        return ret 



# ==== unary operator ==== 
UnaryOpLabels = ["sqrt", "abs", "-", "sin", "cos", "exp"] 
class UnaryOp: 
    gid   = None 
    label = None 

    def __init__ (self, gid, label): 
        assert(type(gid)   is int) 
        assert(type(label) is str) 
        assert(label in UnaryOpLabels)

        self.gid   = gid 
        self.label = label 

    def toCString (self): 
        return self.label 

    def toIRString (self): 
        return str(self)

    def toASTString (self): 
        return self.label 

    def __str__ (self): 
        return self.label 

    def __eq__ (self, rhs):
        assert(isinstance(rhs, UnaryOp))
        return (self.label == rhs.label) 

    def identical (self, rhs): 
        assert(isinstance(rhs, UnaryOp))
        return (self.label == rhs.label) 

    def __ne__ (self, rhs):
        return (not (self == rhs)) 


# ==== unary expression ==== 
class UnaryExpr (ArithmeticExpr): 
    operator = None 

    def __init__ (self, opt, opd0): 
        assert(isinstance(opt, UnaryOp)) 
        assert(isinstance(opd0, Expr)) 

        if (opt.label == "-"): 
            sys.exit("ERROR: cannot directly create UnaryExpr -. It must be properly transfered to an expression tree...") 

        if (sys.version_info.major == 2): 
            sys.exit("Error: FPTuner is currently based on Python3 only...") 
            super(UnaryExpr, self).__init__() 
        elif (sys.version_info.major == 3):
            super().__init__() 
        else:
            sys.exit("ERROR: not supported python version: " + str(sys.version_info)) 

        self.gid         = opt.gid
        self.operator    = opt
        self.operands.append(opd0) 

        assert(self.gid is not None) 

    def opd (self): 
        assert(len(self.operands) == 1) 
        assert(isinstance(self.operands[0], Expr)) 
        return self.operands[0] 

    def __str__ (self): 
        return "([UExpr] " + str(self.operator) + " " + str(self.opd()) + ")" 

    def toCString (self, const_inline=False):         
        return self.operator.toCString() + "(" + self.opd().toCString(const_inline) + ")" 

    def toIRString (self): 
        return "(" + self.operator.toIRString() + "$" + str(self.getGid()) + "(" + self.opd().toIRString() + "))" 

    def toASTString (self): 
        return "(" + self.operator.toASTString() + "(" + self.opd().toASTString() + "))" 

    def __eq__ (self, rhs): 
        if (not isinstance(rhs, UnaryExpr)): 
            return False 
        assert(isinstance(self.operator, UnaryOp))
        assert(isinstance(rhs.operator, UnaryOp)) 

        if (not (self.operator == rhs.operator)): 
            return False

        if (self.getGid() != rhs.getGid()): 
            return False 

        if (self.opd() == rhs.opd()): 
            return True 
        else: 
            return False 

    def identical (self, rhs): 
        if (not isinstance(rhs, UnaryExpr)): 
            return False 
        assert(isinstance(self.operator, UnaryOp))
        assert(isinstance(rhs.operator, UnaryOp)) 

        if (not (self.operator.identical( rhs.operator ))): 
            return False 

        if (self.opd().identical( rhs.opd() )): 
            return True 
        else: 
            return False 
        
    def setLB (self, lb): 
        assert(isinstance(lb, ConstantExpr)) 
        if (self.operator.label in ["abs", "sqrt"]): 
            assert(lb.value() >= Fraction(0, 1))             
        self.lower_bound = lb 

    def setUB (self, ub): 
        assert(isinstance(ub, ConstantExpr)) 
        if (self.operator.label in ["abs", "sqrt"]): 
            assert(ub.value() >= Fraction(0, 1)) 
        self.upper_bound = ub 

    def setBounds (self, lb, ub): 
        self.setLB(lb) 
        self.setUB(ub) 

    def hasLB (self): 
        return (isinstance(self.lower_bound, ConstantExpr)) 

    def hasUB (self): 
        return (isinstance(self.upper_bound, ConstantExpr)) 

    def hasBounds (self): 
        return (self.hasLB() and self.hasUB()) 

    def lb (self):
        assert(self.hasLB())            
        assert(isinstance(self.lower_bound, ConstantExpr))
        return self.lower_bound 
    
    def ub (self):
        assert(self.hasUB()) 
        assert(isinstance(self.upper_bound, ConstantExpr))
        return self.upper_bound 

    def vars (self, by_label=True): 
        return self.opd().vars(by_label)

    def getGid (self): 
        return self.gid 

    def includedGids (self): 
        return tft_utils.unionSets([self.getGid()], self.opd().includedGids()) 

    def concEval (self, vmap = {}): 
        retv = self.opd().concEval(vmap)
        assert((type(retv) is int) or (type(retv) is float) or (isinstance(retv, Fraction))) 
        if (self.operator.label == "abs"): 
            return abs(retv) 
        elif (self.operator.label == "sqrt"): 
            return math.sqrt(retv) 
        elif (self.operator.label == "-"): 
            if (type(retv) is int): 
                return (-1 * retv)
            elif ((type(retv) is float) or (isinstance(retv, Fraction))): 
                return (-1.0 * retv) 
            else: 
                assert(False) 
        else: 
            sys.exit("ERROR: unknwon operator found in function \"concEval\" of a UnaryExpr") 

    def getCastings (self): 
        if (self.operator.label in ["abs", "-"]): 
            return [] 
        elif (self.operator.label == "sqrt"): 
            if (isinstance(self.opd(), ConstantExpr)): 
                return [] 
            else: 
                return [(self.opd().getGid(), self.getGid())]
        else: 
            sys.exit("ERROR: unknown operator found in function \"getCastings\" of a UnaryExpr") 

    def listCrisis (self): 
        return self.opd().listCrisis() 

    def copy(self, check_prefix=True): 
        ret = UnaryExpr(self.operator, self.opd().copy(check_prefix)) 
        
        if (self.hasLB()):
            ret.setLB(self.lb())
        if (self.hasUB()):
            ret.setUB(self.ub())

        return ret 

        

# ==== binary operator ==== 
BinaryOpLabels = ["+", "-", "*", "/", "^"] 
class BinaryOp: 
    gid   = None 
    label = None 

    def __init__ (self, gid, label): 
        assert(type(gid)   is int) 
        assert(type(label) is str) 
        if (label not in BinaryOpLabels):
            print ("ERROR: invalid label for BinaryOp: " + label) 
        assert(label in BinaryOpLabels) 

        self.gid   = gid 
        self.label = label 

    def toCString (self):
        return self.label 

    def toIRString (self):
        return str(self) 

    def toASTString (self): 
        return self.label 

    def __str__ (self): 
        return self.label 

    def __eq__ (self, rhs):
        assert(isinstance(rhs, BinaryOp))
        return (self.label == rhs.label) 
    
    def identical (self, rhs): 
        assert(isinstance(rhs, BinaryOp))
        return (self.label == rhs.label) 

    def __ne__ (self, rhs):
        return (not (self == rhs)) 


# ==== binary expression ==== 
class BinaryExpr (ArithmeticExpr): 
    operator = None 

    def __init__ (self, opt, opd0, opd1): 
        assert(isinstance(opt, BinaryOp))
        assert(isinstance(opd0, Expr))
        assert(isinstance(opd1, Expr)) 

        if (opt.label == "^"): 
            sys.exit("ERROR: cannot directly create BinaryExpr ^. It must be properly transfered to an expression tree...") 

        if (sys.version_info.major == 2): 
            sys.exit("Error: FPTuner is currently based on Python3 only...") 
            super(BinaryExpr, self).__init__() 
        elif (sys.version_info.major == 3):
            super().__init__() 
        else:
            sys.exit("ERROR: not supported python version: " + str(sys.version_info)) 

        self.gid         = opt.gid 
        self.operator    = opt 
        self.operands.append(opd0) 
        self.operands.append(opd1) 

        assert(self.gid is not None) 

    def lhs (self): 
        assert(len(self.operands) == 2) 
        assert(isinstance(self.operands[0], Expr))
        return self.operands[0] 

    def rhs (self): 
        assert(len(self.operands) == 2)
        assert(isinstance(self.operands[1], Expr))
        return self.operands[1] 

    def __str__ (self): 
        return "([BiExpr] " + str(self.operator) + " " + str(self.lhs()) + " " + str(self.rhs()) + ")" 

    def toCString (self, const_inline=False):         
        return "(" + self.lhs().toCString(const_inline) + " " + self.operator.toCString() + " " + self.rhs().toCString(const_inline) + ")" 

    def toIRString (self):
        return "(" + self.lhs().toIRString() + " " + self.operator.toIRString() + "$" + str(self.getGid()) + " " + self.rhs().toIRString() + ")" 

    def toASTString (self): 
        return "(" + self.lhs().toASTString() + " " + self.operator.toASTString() + " " + self.rhs().toASTString() + ")" 
    
    def __eq__ (self, rhs): 
        if (not isinstance(rhs, BinaryExpr)): 
            return False 
        assert(isinstance(self.operator, BinaryOp))
        assert(isinstance(rhs.operator, BinaryOp))

        if (not (self.operator == rhs.operator)): 
            return False 

        if (self.getGid() != rhs.getGid()): 
            return False 

        if (self.operator.label in ["+", "*"]): 
            if   ((self.lhs() == rhs.lhs()) and (self.rhs() == rhs.rhs())): 
                return True 
            elif ((self.lhs() == rhs.rhs()) and (self.rhs() == rhs.lhs())): 
                return True 
            else: 
                return False 

        elif (self.operator.label in ["-", "/", "^"]): 
            if   ((self.lhs() == rhs.lhs()) and (self.rhs() == rhs.rhs())): 
                return True 
            else: 
                return False 
        
        else: 
            sys.exit("ERROR: unknown binary operator... " + str(self.operator.label)) 

    def identical (self, rhs): 
        if (not isinstance(rhs, BinaryExpr)): 
            return False 
        assert(isinstance(self.operator, BinaryOp))
        assert(isinstance(rhs.operator, BinaryOp))

        if (not (self.operator.identical( rhs.operator ))): 
            return False 

        if (self.operator.label in ["+", "*"]): 
            if (self.lhs().identical( rhs.lhs() ) and self.rhs().identical( rhs.rhs() )): 
                return True 
            elif (self.lhs().identical( rhs.rhs() ) and self.rhs().identical( rhs.lhs() )): 
                return True 
            else: 
                return False 

        elif (self.operator.label in ["-", "/", "^"]): 
            if (self.lhs().identical( rhs.lhs() ) and self.rhs().identical( rhs.rhs() )): 
                return True 
            else: 
                return False 
        
        else: 
            sys.exit("ERROR: unknown binary operator... " + str(self.operator.label)) 
        
    def setLB (self, lb): 
        assert(isinstance(lb, ConstantExpr)) 
        self.lower_bound = lb 

    def setUB (self, ub): 
        assert(isinstance(ub, ConstantExpr)) 
        self.upper_bound = ub 

    def setBounds (self, lb, ub): 
        self.setLB(lb) 
        self.setUB(ub) 

    def hasLB (self): 
        return (isinstance(self.lower_bound, ConstantExpr)) 

    def hasUB (self): 
        return (isinstance(self.upper_bound, ConstantExpr)) 

    def hasBounds (self): 
        return (self.hasLB() and self.hasUB()) 

    def lb (self):
        assert(self.hasLB())
        assert(isinstance(self.lower_bound, ConstantExpr)) 
        return self.lower_bound 
    
    def ub (self):
        assert(self.hasUB()) 
        assert(isinstance(self.upper_bound, ConstantExpr))
        return self.upper_bound 

    def vars (self, by_label=True): 
        vars_lhs = self.lhs().vars(by_label) 
        vars_rhs = self.rhs().vars(by_label) 

        ret = vars_lhs[:] 

        for v in vars_rhs: 
            was_there = False 

            if (by_label): 
                for rv in ret: 
                    if (v.label() == rv.label()): 
                        was_there = True 
                        break 

            else: 
                for rv in ret: 
                    if (v.index == rv.index): 
                        print ("ERROR: duplicated vars in different subexpressions...") 
                        assert(False) 
            
            if (not was_there): 
                ret.append(v) 

        return ret 

    def getGid (self):
        return self.gid 

    def includedGids (self): 
        return tft_utils.unionSets([self.getGid()], tft_utils.unionSets(self.lhs().includedGids(), self.rhs().includedGids())) 

    def concEval (self, vmap = {}): 
        retv_lhs = self.lhs().concEval(vmap) 
        assert((type(retv_lhs) is int) or (type(retv_lhs) is float) or (isinstance(retv_lhs, Fraction))) 
        retv_rhs = self.rhs().concEval(vmap) 
        assert((type(retv_rhs) is int) or (type(retv_rhs) is float) or (isinstance(retv_rhs, Fraction))) 
        
        if (self.operator.label == "+"): 
            return (retv_lhs + retv_rhs) 
        elif (self.operator.label == "-"): 
            return (retv_lhs - retv_rhs)
        elif (self.operator.label == "*"): 
            return (retv_lhs * retv_rhs) 
        elif (self.operator.label == "/"): 
            return (retv_lhs / retv_rhs) 
        elif (self.operator.label == "^"): 
            assert(type(retv_rhs) is int) 
            return math.pow(retv_lhs, retv_rhs) 
        else: 
            sys.exit("ERROR: unknown operator found in function \"similar\" of a BinaryExpr")

    def getCastings (self): 
        if (self.operator.label in ["+", "-", "*", "/"]): 
            ret_castings = [] 
            if (isinstance(self.lhs(), ConstantExpr)): 
                pass
            else: 
                ret_castings.append((self.lhs().getGid(), self.getGid())) 
            if (isinstance(self.rhs(), ConstantExpr)): 
                pass
            else: 
                ret_castings.append((self.rhs().getGid(), self.getGid())) 
            return ret_castings 
        elif (self.operator.label in "^"): 
            if (isinstance(self.lhs(), ConstantExpr)): 
                return [] 
            else: 
                return [(self.lhs().getGid(), self.getGid())] 
        else: 
            sys.exit("ERROR: unknown operator found in function \"getCastings\" of a BinaryExpr") 

    def listCrisis (self): 
        lc = self.lhs().listCrisis() + self.rhs().listCrisis() 
        if (self.operator.label == "/"): 
            return [self.rhs().toCString()] + lc 
        else: 
            return lc 

    def copy(self, check_prefix=True): 
        ret = BinaryExpr(self.operator, 
                         self.lhs().copy(check_prefix), 
                         self.rhs().copy(check_prefix)) 
        
        if (self.hasLB()):
            ret.setLB(self.lb()) 
        if (self.hasUB()):
            ret.setUB(self.ub()) 

        return ret 



# ==== class predicate ==== 
BinaryRelationLabels = ["=", "<", "<="]
class BinaryRelation: 
    label = None 

    def __init__ (self, label): 
        assert(label in BinaryRelationLabels) 
        self.label = label 

    def __eq__ (self, rhs):
        if (not isinstance(rhs, BinaryRelation)): 
            return False 
        return (self.label == rhs.label) 

    def toIRString (self): 
        return self.label 

    def __str__ (self): 
        return self.toIRString() 

class BinaryPredicate (Predicate): 
    relation = None 
    
    def __init__ (self, relation, opd0, opd1): 
        assert(isinstance(relation, BinaryRelation)) 
        assert(relation.label in BinaryRelationLabels)

        if (sys.version_info.major == 2): 
            sys.exit("Error: FPTuner is currently based on Python3 only...") 
            super(BinaryPredicate, self).__init__(False) 
        elif (sys.version_info.major == 3):
            super().__init__(False) 

        self.relation = relation 
        self.operands.append(opd0)
        self.operands.append(opd1)

        if (self.relation.label in ["=", "<", "<="]): 
            assert(isinstance(self.lhs(), ArithmeticExpr)) 
            assert(isinstance(self.rhs(), ArithmeticExpr)) 

    def lhs (self): 
        assert(len(self.operands) == 2) 
        
        if (self.relation.label in ["=", "<", "<="]): 
            assert(isinstance(self.operands[0], Expr))
            assert(isinstance(self.operands[1], Expr))
            return self.operands[0]
        
        else: 
            sys.exit("ERROR: invalid BinaryPredicate") 

    def rhs (self): 
        assert(len(self.operands) == 2) 
        
        if (self.relation.label in ["=", "<", "<="]): 
            assert(isinstance(self.operands[0], Expr))
            assert(isinstance(self.operands[1], Expr))
            return self.operands[1]
        
        else: 
            sys.exit("ERROR: invalid BinaryPredicate") 

    def vars (self): 
        return tft_utils.unionSets(self.lhs().vars(), self.rhs().vars()) 

    def concEval (self, vmap = {}):
        vlhs = self.lhs().concEval(vmap) 
        vrhs = self.rhs().concEval(vmap) 
        
        if (self.relation.label == "="): 
            return (vlhs == vrhs) 

        elif (self.relation.label == "<"): 
            return (vlhs < vrhs) 

        elif (self.relation.label == "<="): 
            return (vlhs <= vrhs) 

        else: 
            sys.exit("Error: unhandled relation in concEval...") 

    def __eq__ (self, rhs): 
        if (not isinstance(rhs, BinaryPredicate)): 
            return False 

        if (not (self.relation == rhs.relation)): 
            return False 

        if (self.relation.label in ["="]): 
            return (((self.lhs() == rhs.lhs()) and (self.rhs() == rhs.rhs())) or ((self.lhs() == rhs.rhs()) and (self.rhs() == rhs.lhs())))
            
        elif (self.relation.label in ["<", "<="]): 
            return ((self.lhs() == rhs.lhs()) and (self.rhs() == rhs.rhs()))
        
        else: 
            sys.exit("ERROR: not handled binary relation for __eq__") 

    def toIRString (self): 
        return "(" + self.lhs().toIRString() + " " + self.relation.toIRString() + " " + self.rhs().toIRString() + ")" 

    def __str__ (self): 
        return self.toIRString() 



# ==== some expression judgements ====
def isPowerOf2 (f): 
    assert(type(f) is float) 

    log2 = math.log(abs(f), 2.0)
    return (int(log2) == log2) 

def isPreciseConstantExpr (expr): 
    assert(isinstance(expr, ConstantExpr)) 
    f = float(expr.value())

    if (f == 0.0): 
        return True
    if (int(f) == f): 
        return True 

    return False 

def isPreciseOperation (expr): 
    assert(isinstance(expr, Expr)) 

    if (isinstance(expr, ConstantExpr)): 
        return isPreciseConstantExpr(expr)

    elif (isinstance(expr, VariableExpr)): 
        if (expr.getGid() == PRESERVED_CONST_GID): 
            assert(expr.hasBounds()) 
            assert(expr.lb() == expr.ub()) 
            return isPreciseConstantExpr(expr.lb()) 

        if (expr.hasBounds() and (expr.lb() == expr.ub())): 
            return isPreciseConstantExpr(expr.lb()) 

        return False 

    elif (isinstance(expr, UnaryExpr)): 
        if (expr.operator.label in ["-", "abs"]): 
            return True
        else:
            return False 

    elif (isinstance(expr, BinaryExpr)): 
        if (expr.operator.label in ["+", "-"]): 
            if (isinstance(expr.lhs(), ConstantExpr) and 
                (float(expr.lhs().value()) == 0.0)): 
                return True 
            if (isinstance(expr.rhs(), ConstantExpr) and 
                (float(expr.rhs().value()) == 0.0)): 
                return True 
            if (isinstance(expr.lhs(), VariableExpr) and 
                  (expr.lhs().hasBounds() and 
                   (float(expr.lhs().lb().value()) == 0.0) and 
                   (float(expr.lhs().ub().value()) == 0.0))): 
                return True 
            if (isinstance(expr.rhs(), VariableExpr) and 
                  (expr.rhs().hasBounds() and 
                   (float(expr.rhs().lb().value()) == 0.0) and 
                   (float(expr.rhs().ub().value()) == 0.0))): 
                return True

        elif (expr.operator.label in ["*"]): 
            if (isinstance(expr.lhs(), ConstantExpr) and 
                isPowerOf2(float(expr.lhs().value()))): 
                return True
            if (isinstance(expr.rhs(), ConstantExpr) and 
                isPowerOf2(float(expr.rhs().value()))): 
                return True 
#            if (isinstance(expr.lhs(), ConstantExpr) and 
#                (float(expr.lhs().value()) in [1.0, -1.0])): 
#                return True 
#            if (isinstance(expr.rhs(), ConstantExpr) and 
#                (float(expr.rhs().value()) in [1.0, -1.0])): 
#                return True 
            if (isinstance(expr.lhs(), VariableExpr) and 
                (expr.lhs().hasBounds() and 
                 (expr.lhs().lb() == expr.lhs().ub()) and 
                 isPowerOf2(float(expr.lhs().lb().value())))): 
                return True 
            if (isinstance(expr.rhs(), VariableExpr) and 
                (expr.rhs().hasBounds() and 
                 (expr.rhs().lb() == expr.rhs().ub()) and 
                 isPowerOf2(float(expr.rhs().lb().value())))): 
                return True 

        elif (expr.operator.label in ["/"]): 
            if (isinstance(expr.rhs(), ConstantExpr) and 
                (isPowerOf2(float(expr.rhs().value())))): 
                return True 
            if (isinstance(expr.rhs(), VariableExpr) and 
                (expr.rhs().hasBounds() and 
                 (expr.rhs().lb() == expr.rhs().ub()) and 
                 isPowerOf2(float(expr.rhs().lb().value())))): 
                return True 

        else:
            pass

        return False 

    else: 
        sys.exit("ERROR: unknown expression type...")


        
            

