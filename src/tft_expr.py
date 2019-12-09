

from fptuner_logging import Logger

import color_printing
import tft_utils

from fractions import Fraction

import sys
import math


logger = Logger(color=color_printing.blue)

CNUM_PREFIX = "__cum"
ERR_SUM_PREFIX = "__errsum_"
ERR_TERM_REF_PREFIX = "__eterm_"
ERR_VAR_PREFIX = "__err_"
GROUP_ERR_VAR_PREFIX = "__g_err_"
TCAST_ERR_VAR_PREFIX = "__tc_err_"
PRESERVED_VAR_LABEL_PREFIXES = [
    CNUM_PREFIX,
    ERR_SUM_PREFIX,
    ERR_TERM_REF_PREFIX,
    ERR_VAR_PREFIX,
    GROUP_ERR_VAR_PREFIX,
    TCAST_ERR_VAR_PREFIX,
]

PRESERVED_CONST_VPREFIX = "__const"
PRESERVED_CONST_GID     = 9999

ALL_VariableExprs = []

ExprCounter = 0

UnaryOpLabels = ["sqrt", "abs", "-", "sin", "cos", "exp", "log"]

BinaryOpLabels = ["+", "-", "*", "/", "^"]

BinaryRelationLabels = ["=", "<", "<="]


def isConstVar(var):
    if not isinstance(var, VariableExpr):
        return False

    return var.label().startswith(PRESERVED_CONST_VPREFIX)


def isPseudoBooleanVar(var):
    return (isinstance(var, VariableExpr)
            and var.hasBounds()
            and var.lb() == ConstantExpr(0)
            and var.ub() == ConstantExpr(1))


def RegisterVariableExpr(var):
    global ALL_VariableExprs

    assert(isinstance(var, VariableExpr))

    if var.isPreservedVar():
        logger.dlog("Refused to register: {}", var)
        return None

    was_registered = False

    for v in ALL_VariableExprs:
        assert(v.hasBounds())

        if v.identical(var):
            was_registered = True

        if var == v:
            if var.hasBounds():
                assert(var.lb().value() == v.lb().value())
                assert(var.ub().value() == v.ub().value())

            else:
                var.setBounds(v.lb(), v.ub())

    if not was_registered:
        logger.dlog("Registered: {}", var)
        ALL_VariableExprs.append(var)


def ExprStatistics(expr, stat={}):
    assert(isinstance(expr, Expr))

    if "# constants"  not in stat.keys():
        stat["# constants"]  = 0
    if "# variables"  not in stat.keys():
        stat["# variables"]  = 0
    if "# operations" not in stat.keys():
        stat["# operations"] = 0
    if "groups"       not in stat.keys():
        stat["groups"]       = []

    if isinstance(expr, ConstantExpr):
        logger.error("Should not do statistics with expression containing real "
                     "ConstantExprs.")
        sys.exit(1)

    if isinstance(expr, VariableExpr):
        if isConstVar(expr):
            stat["# constants"] += 1

        else:
            assert(expr.getGid() != PRESERVED_CONST_GID)

            gid = expr.getGid()

            if gid not in stat["groups"]:
                stat["groups"].append(gid)

            stat["# variables"] += 1

    elif isinstance(expr, UnaryExpr):

        gid = expr.getGid()

        if gid not in stat["groups"]:
            stat["groups"].append(gid)

        stat["# operations"] += 1

        ExprStatistics(expr.opd(), stat)

    elif isinstance(expr, BinaryExpr):

        gid = expr.getGid()

        if gid not in stat["groups"]:
            stat["groups"].append(gid)

        stat["# operations"] += 1

        ExprStatistics(expr.lhs(), stat)
        ExprStatistics(expr.rhs(), stat)


class Expr (object):
    index        = None
    operands     = None
    lower_bound  = None
    upper_bound  = None
    gid          = None

    def __init__(self, set_index=True):
        global ExprCounter
        if set_index:
            self.index = ExprCounter
        self.operands = []
        lower_bound = ""
        upper_bound = ""
        ExprCounter = ExprCounter + 1


class ArithmeticExpr (Expr):
    def __init__(self, set_index=True):
        super().__init__(set_index)


class Predicate (Expr):
    def __init__(self, set_index=True):
        super().__init__(set_index)


class ConstantExpr (ArithmeticExpr):
    def __init__(self, val):
        assert(type(val) in {int, float} or isinstance(val, Fraction))
        if type(val) is float:
            val = Fraction(val)
        super().__init__(False)
        self.operands.append(val)
        self.lower_bound = val
        self.upper_bound = val
        self.gid        = -1

    def value(self):
        assert(len(self.operands) == 1)
        return self.operands[0]

    def type(self):
        return type(self.value())

    def rational_value(self):
        if self.type() == int:
            return Fraction(self.value(), 1)

        if self.type() == Fraction:
            return self.value()

        logger.error("Invalid value type for ConstantExpr: {}", self.type())
        sys.exit(1)

    def lb(self):
        return self

    def ub(self):
        return self

    def setLB(self, expr):
        assert(isinstance(expr, Expr))
        assert(expr.value() <= self.value())

    def setUB(self, expr):
        assert(isinstance(expr, Expr))
        assert(self.value() <= expr.value())

    def __str__(self):
        if self.type() == int:
            return "([Const:int] " + str(self.value()) + ")"
        elif self.type() == Fraction:
            return "([Const:Fraction] " + str(float(self.value())) + ")"
        else:
            logger.error("Invalid type of ConstantExpr found in __str__: {}",
                         self.type())
            sys.exit(1)

    def toCString(self, const_inline=False):
        if self.type() == int:
            return str(self.value())

        if self.type() == Fraction:
            assert(isinstance(self.value(), Fraction))
            return str(float(self.value()))

        logger.error("Invalid type of ConstantExpr: {}", self.type())
        sys.exit(1)

    def toIRString(self):
        return "(" + self.toCString() + ")"

    def toASTString(self):
        return self.toIRString()

    def toFPCoreString(self):
        return self.toCString()

    def __eq__(self, rhs):
        if not isinstance(rhs, ConstantExpr):
            return False
        if self.type() == rhs.type():
            return self.value() == rhs.value()
        if self.type() == int and rhs.type() == Fraction:
            return Fraction(self.value(), 1) == rhs.value()
        if self.type() == Fraction and rhs.type() == int:
            return self.value() == Fraction(rhs.value(), 1)

        logging.error("Invalid __eq__ scenario of ConstExpr: {} __eq__ {}",
                      self.type(), rhs.type())
        sys.exit(1)

    def identical(self, rhs):
        retval = (isinstance(rhs, ConstantExpr)
                  and self.index == rhs.index)
        if retval:
            assert(self.value() == rhs.value())

        return retval

    def __ne__(self, rhs):
        return not self == rhs

    def __gt__(self, rhs):
        if not isinstance(rhs, ConstantExpr):
            return False
        if self.type() == rhs.type():
            return self.value() > rhs.value()
        if self.type() == int and rhs.type() == Fraction:
            return (Fraction(self.value(), 1) > rhs.value())
        if self.type() == Fraction and rhs.type() == int:
            return (self.value() > Fraction(rhs.value(), 1))

        logging.error("Invalid __gt__ scenario of ConstExpr: {} __gt__ {}",
                      self.type(), rhs.type())
        sys.exit(1)

    def __lt__(self, rhs):
        if not isinstance(rhs, ConstantExpr):
            return False
        if self.type() == rhs.type():
            return (self.value() < rhs.value())
        if self.type() == int and rhs.type() == Fraction:
            return (Fraction(self.value(), 1) < rhs.value())
        if self.type() == Fraction and rhs.type() == int:
            return (self.value() < Fraction(rhs.value(), 1))

        logging.error("Invalid __lt__ scenario of ConstExpr: {} __lt__ {}",
                      self.type(), rhs.type())
        sys.exit(1)

    def __ge__(self, rhs):
        return self == rhs or self > rhs

    def __le__(self, rhs):
        return self == rhs or self < rhs

    def hasLB(self):
        return True

    def hasUB(self):
        return True

    def hasBounds(self):
        return True

    def vars(self, by_label=True):
        return []

    def __hash__(self):
        return hash(self.value())

    def getGid(self):
        return self.gid

    def includedGids(self):
        return [self.getGid()]

    def concEval(self, vmap = {}):
        retv = self.value()
        assert((type(retv) in {int, float} or isinstance(retv, Fraction)))
        return retv

    def getCastings(self):
        return []

    def listCrisis(self):
        return []

    def copy(self, check_prefix=True):
        return ConstantExpr(self.value())


class VariableExpr (ArithmeticExpr):
    vtype = None

    def __init__(self, label, vtype, gid, check_prefix=True):
        assert(isinstance(label, str))
        assert(vtype == int or vtype == Fraction)
        assert(type(gid) is int)

        super().__init__()

        if gid == PRESERVED_CONST_GID:
            assert(label.startswith(PRESERVED_CONST_VPREFIX))

        self.operands.append(label)
        self.vtype = vtype
        self.gid = gid

        if check_prefix and self.isPreservedVar():
            logging.error("The given label '{}' has a preserved prefix", label)
            sys.exit(1)

        RegisterVariableExpr(self)

    def isPreservedVar(self):
        return any([self.label().startswith(pre) for pre in
                    PRESERVED_VAR_LABEL_PREFIXES])

    def label(self):
        assert(len(self.operands) == 1)
        assert(isinstance(self.operands[0], str))
        return self.operands[0]

    def __str__(self):
        return "([Var] {})".format(self.toIRString())

    def idLabel(self):
        return "{}_eid_{}".format(self.label(), self.index)

    def toCString(self, const_inline=False):
        if isConstVar(self):
            assert(self.lb().value() == self.ub().value())
            return self.lb().toCString()
        return self.label()

    def toIRString(self):
        suff = "$Int" if self.vtype == int else ""
        return "({}${}{})".format(self.label(), self.gid, suff)

    def toASTString(self):
        return self.idLabel()

    def toFPCoreString(self):
        if isConstVar(self):
            assert(self.hasLB()
                   and self.hasUB()
                   and self.lb().value() == self.ub().value())
            return str(float(self.lb().value()))
        return self.label()

    def __eq__(self, rhs):
        if not isinstance(rhs, VariableExpr):
            return False
        return (self.label() == rhs.label()
                and self.type() == rhs.type()
                and self.getGid() == rhs.getGid())

    def identical(self, rhs):
        retval = (isinstance(rhs, VariableExpr)
                  and self.index == rhs.index)
        if retval:
            assert(self == rhs)

        return retval

    def setLB(self, lb):
        assert(isinstance(lb, ConstantExpr)
               or isinstance(lb, Fraciton)
               or (type(lb) in {int, float}))

        if not isinstance(lb, ConstantExpr):
            lb = ConstantExpr(lb)

        if self.lower_bound is None:
            self.lower_bound = lb

        assert(self.lower_bound.value() == lb.value())

    def setUB(self, ub):
        assert(isinstance(ub, ConstantExpr)
               or isinstance(ub, Fraciton)
               or (type(ub) in {int, float}))

        if not isinstance(ub, ConstantExpr):
            ub = ConstantExpr(ub)

        if self.upper_bound is None:
            self.upper_bound = ub

        assert(self.upper_bound.value() == ub.value())

    def setBounds(self, lb, ub):
        self.setLB(lb)
        self.setUB(ub)

    def hasLB(self):
        return isinstance(self.lower_bound, ConstantExpr)

    def hasUB(self):
        return isinstance(self.upper_bound, ConstantExpr)

    def hasBounds(self):
        return self.hasLB() and self.hasUB()

    def lb(self):
        assert(self.hasLB())
        assert(isinstance(self.lower_bound, ConstantExpr))
        return self.lower_bound

    def ub(self):
        assert(self.hasUB())
        assert(isinstance(self.upper_bound, ConstantExpr))
        return self.upper_bound

    def type(self):
        assert(self.vtype in {int, Fraction})
        return self.vtype

    def vars(self, by_label=True):
        return [self]

    def __hash__(self):
        return hash(self.label())

    def getGid(self):
        return self.gid

    def includedGids(self):
        return [self.getGid()]

    def concEval(self, vmap = {}):
        assert(self in vmap.keys())
        retv = vmap[self]
        assert(type(retv) in {int, float} or isinstance(retv, Fraction))
        return retv

    def getCastings(self):
        return []

    def listCrisis(self):
        return []

    def copy(self, check_prefix=True):
        ret = VariableExpr(self.label(), self.type(), self.getGid(),
                           check_prefix)

        if self.hasLB():
            ret.setLB(self.lb())
        if self.hasUB():
            ret.setUB(self.ub())

        return ret


class UnaryOp:
    gid   = None
    label = None

    def __init__(self, gid, label):
        assert(type(gid)   is int)
        assert(type(label) is str)
        assert(label in UnaryOpLabels)

        self.gid   = gid
        self.label = label

    def toCString(self):
        return self.label

    def toIRString(self):
        return str(self)

    def toASTString(self):
        return self.label

    def __str__(self):
        return self.label

    def __eq__(self, rhs):
        assert(isinstance(rhs, UnaryOp))
        return self.label == rhs.label

    def identical(self, rhs):
        return self == rhs

    def __ne__(self, rhs):
        return not self == rhs


class UnaryExpr (ArithmeticExpr):
    operator = None

    def __init__(self, opt, opd0):
        assert(isinstance(opt, UnaryOp))
        assert(opt.gid is not None)
        assert(isinstance(opd0, Expr))

        if opt.label == "-":
            logging.error("Cannot directly create UnaryExpr '-'.")
            logging.error("It must be properly transfered to an expression tree.")
            sys.exit(1)

        super().__init__()

        self.gid         = opt.gid
        self.operator    = opt
        self.operands.append(opd0)

    def opd(self):
        assert(len(self.operands) == 1)
        assert(isinstance(self.operands[0], Expr))
        return self.operands[0]

    def __str__(self):
        return "([UExpr] {} {})".format(self.operator, self.opd())

    def toCString(self, const_inline=False):
        return "{}({})".format(self.operator.toCString(),
                               self.opd().toCString(const_inline))

    def toIRString(self):
        return "({}${}({}))".format(self.operator.toIRString(),
                                    self.getGid(),
                                    self.opd().toIRString())

    def toASTString(self):
        return "({}({}))".format(self.operator.toASTString(),
                                 self.opd().toASTString())

    def toFPCoreString(self):
        logging.error("toFPCoreString doesn't support for Unary Expression")
        sys.exit(1)

    def __eq__(self, rhs):
        if not isinstance(rhs, UnaryExpr):
            return False
        assert(isinstance(self.operator, UnaryOp))
        assert(isinstance(rhs.operator, UnaryOp))

        return (self.operator == rhs.operator
                and self.getGid() == rhs.getGid()
                and self.opd() == rhs.opd())

    def identical(self, rhs):
        if not isinstance(rhs, UnaryExpr):
            return False
        assert(isinstance(self.operator, UnaryOp))
        assert(isinstance(rhs.operator, UnaryOp))

        return (self.operator.identical(rhs.operator)
                and self.opd().identical(rhs.opd()))

    def setLB(self, lb):
        assert(isinstance(lb, ConstantExpr))
        if self.operator.label in {"abs", "sqrt"}:
            assert(lb.value() >= Fraction(0, 1))
        self.lower_bound = lb

    def setUB(self, ub):
        assert(isinstance(ub, ConstantExpr))
        if self.operator.label in {"abs", "sqrt"}:
            assert(ub.value() >= Fraction(0, 1))
        self.upper_bound = ub

    def setBounds(self, lb, ub):
        self.setLB(lb)
        self.setUB(ub)

    def hasLB(self):
        return isinstance(self.lower_bound, ConstantExpr)

    def hasUB(self):
        return isinstance(self.upper_bound, ConstantExpr)

    def hasBounds(self):
        return self.hasLB() and self.hasUB()

    def lb(self):
        assert(self.hasLB())
        assert(isinstance(self.lower_bound, ConstantExpr))
        return self.lower_bound

    def ub(self):
        assert(self.hasUB())
        assert(isinstance(self.upper_bound, ConstantExpr))
        return self.upper_bound

    def vars(self, by_label=True):
        return self.opd().vars(by_label)

    def getGid(self):
        return self.gid

    def includedGids(self):
        return tft_utils.unionSets([self.getGid()], self.opd(). includedGids())

    def concEval(self, vmap = {}):
        retv = self.opd().concEval(vmap)
        assert(type(retv) in {int, float} or isinstance(retv, Fraction))

        if self.operator.label == "abs":
            return abs(retv)
        if self.operator.label == "sqrt":
            return math.sqrt(retv)
        if self.operator.label == "-":
            if type(retv) is int:
                return -1 * retv
            if type(retv) is float or isinstance(retv, Fraction):
                return -1.0 * retv
            logging.error("Invalid type for unary negation: {}", type(retv))
            sys.exit(-1)

        logging.error("Unknown unary operator: {}", self.operator.label)
        sys.exit(1)

    def getCastings(self):
        if self.operator.label in {"abs", "-"}:
            return []
        if self.operator.label == "sqrt":
            if isinstance(self.opd(), ConstantExpr):
                return []
            return [(self.opd().getGid(), self.getGid())]

        logging.error("Unknown unary operator: {}", self.operator.label)
        sys.exit(1)

    def listCrisis(self):
        return self.opd().listCrisis()

    def copy(self, check_prefix=True):
        ret = UnaryExpr(self.operator, self.opd().copy(check_prefix))

        if self.hasLB():
            ret.setLB(self.lb())
        if self.hasUB():
            ret.setUB(self.ub())

        return ret


class BinaryOp:
    gid   = None
    label = None

    def __init__(self, gid, label):
        assert(type(gid)   is int)
        assert(type(label) is str)
        if label not in BinaryOpLabels:
            logging.error("Invalid binary operator: {}", label)
            sys.exit(1)

        self.gid   = gid
        self.label = label

    def toCString(self):
        return self.label

    def toIRString(self):
        return str(self)

    def toASTString(self):
        return self.label

    def __str__(self):
        return self.label

    def __eq__(self, rhs):
        assert(isinstance(rhs, BinaryOp))
        return self.label == rhs.label

    def identical(self, rhs):
        return self == rhs

    def __ne__(self, rhs):
        return not self == rhs


class BinaryExpr (ArithmeticExpr):
    operator = None

    def __init__(self, opt, opd0, opd1):
        assert(isinstance(opt, BinaryOp))
        assert(opt.gid is not None)
        assert(isinstance(opd0, Expr))
        assert(isinstance(opd1, Expr))

        if opt.label == "^":
            logging.error("Cannot directly create power expression.")
            logging.error("It must be properly transfered to an expression"
                          " tree.")
            sys.exit(1)

        super().__init__()

        self.gid         = opt.gid
        self.operator    = opt
        self.operands.append(opd0)
        self.operands.append(opd1)

    def lhs(self):
        assert(len(self.operands) == 2)
        assert(isinstance(self.operands[0], Expr))
        return self.operands[0]

    def rhs(self):
        assert(len(self.operands) == 2)
        assert(isinstance(self.operands[1], Expr))
        return self.operands[1]

    def __str__(self):
        return "([BiExpr] {} {} {})".format(self.operator,
                                            self.lhs(),
                                            self.rhs())

    def toCString(self, const_inline=False):
        return "({} {} {})".format(self.lhs().toCString(const_inline),
                                   self.operator.toCString(),
                                   self.rhs().toCString(const_inline))

    def toIRString(self):
        return "({} {}${} {})".format(self.lhs().toIRString(),
                                      self.operator.toIRString(),
                                      self.getGid(),
                                      self.rhs().toIRString())

    def toASTString(self):
        return "({} {} {})".format(self.lhs().toASTString(),
                                   self.operator.toASTString(),
                                   self.rhs().toASTString())

    def toFPCoreString(self):
        str_opt = self.operator.toCString()
        if str_opt not in {'+', '-', '*', '/'}:
            logging.error("toFPCoreString doesn't support operator: {}", str_opt)
            sys.exit(1)
        return "({} {} {})".format(str_opt,
                                   self.lhs().toFPCoreString(),
                                   self.rhs().toFPCoreString())

    def __eq__(self, rhs):
        if not isinstance(rhs, BinaryExpr):
            return False
        assert(isinstance(self.operator, BinaryOp))
        assert(isinstance(rhs.operator, BinaryOp))

        if self.operator != rhs.operator or self.getGid() != rhs.getGid():
            return False

        if self.operator.label in {"+", "*"}:
            return ((self.lhs() == rhs.lhs() and self.rhs() == rhs.rhs())
                    or (self.lhs() == rhs.rhs() and self.rhs() == rhs.lhs()))

        if self.operator.label in {"-", "/", "^"}:
            return self.lhs() == rhs.lhs() and self.rhs() == rhs.rhs()

        logging.error("Unknown binary operator: {}", self.operator.label)
        sys.exit(1)

    def identical(self, rhs):
        if not isinstance(rhs, BinaryExpr):
            return False
        assert(isinstance(self.operator, BinaryOp))
        assert(isinstance(rhs.operator, BinaryOp))

        if not self.operator.identical(rhs.operator):
            return False

        if self.operator.label in ["+", "*"]:
            return ((self.lhs().identical(rhs.lhs())
                     and self.rhs().identical(rhs.rhs()))
                    or (self.lhs().identical(rhs.rhs())
                        and self.rhs().identical(rhs.lhs())))

        if self.operator.label in ["-", "/", "^"]:
            return (self.lhs().identical(rhs.lhs())
                    and self.rhs().identical(rhs.rhs()))

        logging.error("Unknown binary operator: {}", self.operator.label)
        sys.exit(1)

    def setLB(self, lb):
        assert(isinstance(lb, ConstantExpr))
        self.lower_bound = lb

    def setUB(self, ub):
        assert(isinstance(ub, ConstantExpr))
        self.upper_bound = ub

    def setBounds(self, lb, ub):
        self.setLB(lb)
        self.setUB(ub)

    def hasLB(self):
        return isinstance(self.lower_bound, ConstantExpr)

    def hasUB(self):
        return isinstance(self.upper_bound, ConstantExpr)

    def hasBounds(self):
        return self.hasLB() and self.hasUB()

    def lb(self):
        assert(self.hasLB())
        assert(isinstance(self.lower_bound, ConstantExpr))
        return self.lower_bound

    def ub(self):
        assert(self.hasUB())
        assert(isinstance(self.upper_bound, ConstantExpr))
        return self.upper_bound

    def vars(self, by_label=True):
        vars_lhs = self.lhs().vars(by_label)
        vars_rhs = self.rhs().vars(by_label)

        ret = vars_lhs[:]

        for v in vars_rhs:
            was_there = False

            for rv in ret:
                if by_label:
                    if v.label() == rv.label():
                        was_there = True
                        break
                else:
                    if v.index == rv.index:
                        logging.error("Duplicate vars in different subexpressions: {}", v)
                        sys.exit(1)

            if not was_there:
                ret.append(v)

        return ret

    def getGid(self):
        return self.gid

    def includedGids(self):
        temp = tft_utils.unionSets(self.lhs().includedGids(),
                                   self.rhs().includedGids())
        return tft_utils.unionSets([self.getGid()], temp)

    def concEval(self, vmap = {}):
        retv_lhs = self.lhs().concEval(vmap)
        assert(type(retv_lhs) in {int, float} or isinstance(retv_lhs, Fraction))
        retv_rhs = self.rhs().concEval(vmap)
        assert(type(retv_rhs) in {int, float} or isinstance(retv_rhs, Fraction))

        ops = {"+": lambda a,b: a+b,
               "-": lambda a,b: a-b,
               "*": lambda a,b: a*b,
               "/": lambda a,b: a/b,
               "^": lambda a,b: a**b,}

        if self.operator.label not in ops:
            logging.error("Unknown operator: {}", self.operator.label)
            sys.exit(1)

        return ops[self.operator.label](retv_lhs, retv_rhs)

    def getCastings(self):
        if self.operator.label in {"+", "-", "*", "/"}:
            ret_castings = []
            if not isinstance(self.lhs(), ConstantExpr):
                ret_castings.append((self.lhs().getGid(), self.getGid()))
            if not isinstance(self.rhs(), ConstantExpr):
                ret_castings.append((self.rhs().getGid(), self.getGid()))
            return ret_castings
        if self.operator.label == "^":
            if isinstance(self.lhs(), ConstantExpr):
                return []
            return [(self.lhs().getGid(), self.getGid())]

        logging.error("Unknown operator: {}", self.operator.label)
        sys.exit(-1)

    def listCrisis(self):
        lc = self.lhs().listCrisis() + self.rhs().listCrisis()
        if self.operator.label == "/":
            return [self.rhs().toCString()] + lc
        return lc

    def copy(self, check_prefix=True):
        ret = BinaryExpr(self.operator,
                         self.lhs().copy(check_prefix),
                         self.rhs().copy(check_prefix))

        if self.hasLB():
            ret.setLB(self.lb())
        if self.hasUB():
            ret.setUB(self.ub())

        return ret


class BinaryRelation:
    label = None

    def __init__(self, label):
        assert(label in BinaryRelationLabels)
        self.label = label

    def __eq__(self, rhs):
        return (isinstance(rhs, BinaryRelation)
                and self.label == rhs.label)

    def toIRString(self):
        return self.label

    def __str__(self):
        return self.toIRString()


class BinaryPredicate (Predicate):
    relation = None

    def __init__(self, relation, opd0, opd1):
        assert(isinstance(relation, BinaryRelation))
        assert(relation.label in BinaryRelationLabels)

        super().__init__(False)

        self.relation = relation
        self.operands.append(opd0)
        self.operands.append(opd1)

        if self.relation.label in {"=", "<", "<="}:
            assert(isinstance(self.lhs(), ArithmeticExpr))
            assert(isinstance(self.rhs(), ArithmeticExpr))

    def lhs(self):
        assert(len(self.operands) == 2)

        if self.relation.label in {"=", "<", "<="}:
            assert(isinstance(self.operands[0], Expr))
            assert(isinstance(self.operands[1], Expr))
            return self.operands[0]

        logger.error("Invalid binary predicate: {}", self.relation.label)
        sys.exit(1)

    def rhs(self):
        assert(len(self.operands) == 2)

        if self.relation.label in {"=", "<", "<="}:
            assert(isinstance(self.operands[0], Expr))
            assert(isinstance(self.operands[1], Expr))
            return self.operands[1]

        logger.error("Invalid binary predicate: {}", self.relation.label)
        sys.exit(1)

    def vars(self):
        return tft_utils.unionSets(self.lhs().vars(), self.rhs().vars())

    def concEval(self, vmap = {}):
        vlhs = self.lhs().concEval(vmap)
        vrhs = self.rhs().concEval(vmap)

        rels = {"=": lambda a,b: a == b,
                "<": lambda a,b: a < b,
                "<=": lambda a,b: a <= b,}

        if self.relation.label not in rels:
            logger.error("Invalid binary predicate: {}", self.relation.label)
            sys.exit(1)

        return rels[self.relation.label](vlhs, vrhs)

    def __eq__(self, rhs):
        if (not isinstance(rhs, BinaryPredicate)
            or not (self.relation == rhs.relation)):
            return False

        if self.relation.label == "=":
            return ((self.lhs() == rhs.lhs() and self.rhs() == rhs.rhs())
                    or (self.lhs() == rhs.rhs() and self.rhs() == rhs.lhs()))

        if self.relation.label in {"<", "<="}:
            return self.lhs() == rhs.lhs() and self.rhs() == rhs.rhs()

        logger.error("Invalid binary predicate: {}", self.relation.label)
        sys.exit(1)

    def toIRString(self):
        return "({} {} {})".format(self.lhs().toIRString(),
                                   self.relation.toIRString(),
                                   self.rhs().toIRString())

    def __str__(self):
        return self.toIRString()


def isPowerOf2(f):
    assert(type(f) is float)
    af = abs(f)
    log2 = math.log(af, 2)
    low = math.floor(log2)
    high = math.ceil(log2)
    return low == high


def isPreciseConstantExpr(expr):
    assert(isinstance(expr, ConstantExpr))
    f = float(expr.value())
    low = math.floor(f)
    high = math.ceil(f)
    return low == high


def isPreciseOperation(expr):
    assert(isinstance(expr, Expr))

    if isinstance(expr, ConstantExpr):
        return isPreciseConstantExpr(expr)

    if isinstance(expr, VariableExpr):
        if expr.getGid() == PRESERVED_CONST_GID:
            assert(expr.hasBounds())
            assert(expr.lb() == expr.ub())
            return isPreciseConstantExpr(expr.lb())

        if expr.hasBounds() and expr.lb() == expr.ub():
            return isPreciseConstantExpr(expr.lb())

        return False

    if isinstance(expr, UnaryExpr):
        return expr.operator.label in {"-", "abs"}

    if isinstance(expr, BinaryExpr):
        if expr.operator.label in {"+", "-"}:
            return ((isinstance(expr.lhs(), ConstantExpr)
                     and float(expr.lhs().value()) == 0.0)
                    or (isinstance(expr.rhs(), ConstantExpr)
                        and float(expr.rhs().value()) == 0.0)
                    or (isinstance(expr.lhs(), VariableExpr)
                        and expr.lhs().hasBounds()
                        and float(expr.lhs().lb().value()) == 0.0
                        and float(expr.lhs().ub().value()) == 0.0)
                    or (isinstance(expr.rhs(), VariableExpr)
                        and expr.rhs().hasBounds()
                        and float(expr.rhs().lb().value()) == 0.0
                        and float(expr.rhs().ub().value()) == 0.0))

        if expr.operator.label == "*":
            return ((isinstance(expr.lhs(), ConstantExpr)
                     and isPowerOf2(float(expr.lhs().value())))
                    or (isinstance(expr.rhs(), ConstantExpr)
                        and isPowerOf2(float(expr.rhs().value())))
                    or (isinstance(expr.lhs(), VariableExpr)
                        and expr.lhs().hasBounds()
                        and expr.lhs().lb() == expr.lhs().ub()
                        and isPowerOf2(float(expr.lhs().lb().value())))
                    or (isinstance(expr.rhs(), VariableExpr)
                        and expr.rhs().hasBounds()
                        and expr.rhs().lb() == expr.rhs().ub()
                        and isPowerOf2(float(expr.rhs().lb().value()))))

        if expr.operator.label in ["/"]:
            return ((isinstance(expr.rhs(), ConstantExpr)
                     and isPowerOf2(float(expr.rhs().value())))
                    or (isinstance(expr.rhs(), VariableExpr)
                        and expr.rhs().hasBounds()
                        and expr.rhs().lb() == expr.rhs().ub()
                        and isPowerOf2(float(expr.rhs().lb().value()))))

        return False

    logger.error("Unknown expression type: {}", expr)
    sys.exit(1)
