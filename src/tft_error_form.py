
import math
import sys
import tft_utils
import tft_expr 
import tft_parser
import tft_alloc 
import tft_ir_api as IR
from fractions import Fraction 


# ==== global variables ==== 
EPS_SCORE = {}
EPS_SCORE[tft_alloc.EPSILON_32]  = 100.0
EPS_SCORE[tft_alloc.EPSILON_64]  = 1.0
EPS_SCORE[tft_alloc.EPSILON_128] = 0.0


# ==== sub-routines ==== 
def UnifyCastingMapAndGid2Epsilons (eforms): 
    uni_casting_map = None 
    uni_gid2epsilons = None 

    for eform in eforms: 
        assert(isinstance(eform, ErrorForm)) 

        if (uni_casting_map is None): 
            assert(uni_gid2epsilons is None) 
            uni_casting_map     = eform.casting_map.copy() 
            uni_gid2epsilons    = eform.gid2epsilons.copy() 

        else: 
            assert(tft_utils.isSameMap(uni_casting_map,  eform.casting_map)) 
            assert(tft_utils.isSameMap(uni_gid2epsilons, eform.gid2epsilons)) 

    return uni_casting_map, uni_gid2epsilons 


def GroupErrorVarName (gid, select): 
    assert(type(gid) is int) 
    assert(type(select) is int) 
    assert(0 <= gid) 
    assert(0 <= select) 
    return tft_expr.GROUP_ERR_VAR_PREFIX + str(gid) + "_" + str(select)     

def GroupErrorVar (gid, select): 
    evar = tft_expr.VariableExpr(GroupErrorVarName(gid, select), int, -1, False) 
    evar.setLB(tft_expr.ConstantExpr(int(0))) 
    evar.setUB(tft_expr.ConstantExpr(int(1))) 
    return evar 

def checkValidEpsilonList (epss): 
    assert(len(epss) > 0) 
    assert(all([isinstance(eps, tft_expr.ConstantExpr) for eps in epss]))
    assert(all([(epss[i] > epss[i+1]) for i in range(0, (len(epss)-1))]))

def checkSameEpsilonList (epss1, epss2): 
    checkValidEpsilonList(epss1) 
    checkValidEpsilonList(epss2) 
    assert(len(epss1) == len(epss2)) 
    assert(all([(epss1[i] == epss2[i]) for i in range(0, len(epss1))])) 

def GroupErrorVarSum (gid, epss=[]): 
    assert((type(gid) is int) and (0 <= gid)) 
    checkValidEpsilonList(epss) 

    expr_sum = None 
    
    for ei in range(0, len(epss)): 
        if (expr_sum is None): 
            expr_sum = GroupErrorVar(gid, ei) 
        else:
            expr_sum = tft_expr.BinaryExpr(tft_expr.BinaryOp(-1, "+"), expr_sum, GroupErrorVar(gid, ei)) 

    return expr_sum 

def CastingNumExprTemplate (func_compare, casting_map = {}, gid2epsilons = {}):
    # generate the casting num. expr. 
    cnum_expr = None 
    for p,c in casting_map.items(): 
        assert(len(p) == 2) 
        assert((type(p[0]) is int) and (type(p[1]) is int)) 

        gid_from = p[0] 
        gid_to = p[1] 

        assert(gid_to != tft_expr.PRESERVED_CONST_GID) 
        if (gid_from == tft_expr.PRESERVED_CONST_GID): 
            continue 
            
        assert(0 <= gid_from) 
        assert(gid_from in gid2epsilons.keys())
        assert(0 <= gid_to)
        assert(gid_to in gid2epsilons.keys())

        epss_from = gid2epsilons[gid_from] 
        epss_to = gid2epsilons[gid_to] 

        this_expr = None 
        for f in range(0, len(epss_from)): 
            sum_expr = None 
            for t in range(0, len(epss_to)): 
                if (func_compare(epss_from[f], epss_to[t])): 
                    if (sum_expr is None): 
                        sum_expr = GroupErrorVar(gid_to, t)
                    else:
                        sum_expr = IR.BE("+", -1, sum_expr, GroupErrorVar(gid_to, t), True) 

            if (sum_expr is None): 
                continue 

            f_expr = IR.BE("*", -1, GroupErrorVar(gid_from, f), sum_expr, True)

            if (this_expr is None): 
                this_expr = f_expr 
            else:
                this_expr = IR.BE("+", -1, this_expr, f_expr, True)

        if (this_expr is None): 
            continue 

        this_expr = IR.BE("*", -1, tft_expr.ConstantExpr(c), this_expr, True) 
        if (cnum_expr is None): 
            cnum_expr = this_expr
        else:
            cnum_expr = IR.BE("+", -1, cnum_expr, this_expr, True) 

    return cnum_expr 

def CastingNumExprH2L (casting_map = {}, gid2epsilons = {}): 
    return CastingNumExprTemplate( (lambda x,y : x < y), casting_map, gid2epsilons )

def CastingNumExprL2H (casting_map = {}, gid2epsilons = {}): 
    return CastingNumExprTemplate( (lambda x,y : x > y), casting_map, gid2epsilons ) 

def CastingNumExpr (casting_map = {}, gid2epsilons = {}): 
    expr_h2l = CastingNumExprH2L(casting_map, gid2epsilons) 
    expr_l2h = CastingNumExprL2H(casting_map, gid2epsilons) 

    if ((expr_h2l is None) and (expr_l2h is None)): 
        return None 
    
    if (expr_h2l is None): 
        return expr_l2h 
    
    if (expr_l2h is None): 
        return expr_h2l 

    return IR.BE("+", -1, expr_h2l, expr_l2h, True) 

def countOptsInsts (eforms):
    assert(len(eforms) > 0)
    assert(all([isinstance(ef, ErrorForm) for ef in eforms])) 
    
    n_insts = 0 

    gids = [] 
    
    for ef in eforms:
        for gid,epss in ef.gid2epsilons.items():
            if (gid not in gids):
                gids.append(gid)
        
        for gid,c in ef.gid_counts.items(): 
            assert(gid in gids) 

            n_insts = n_insts + c 

    return len(gids), n_insts 
    

# ==== classes ==== 
FRESH_ERRORTERM_INDEX = 0 
class ErrorTerm: 
    index                  = None 
    expr                   = None 
    context_gid            = None 
    gid                    = None 
    stored_absexpr         = None 
    stored_overapprox_expr = None 

    def __init__ (self, err_expr, context_gid, gid): 
        global FRESH_ERRORTERM_INDEX 
        assert(FRESH_ERRORTERM_INDEX >= 0) 
        assert(isinstance(err_expr, tft_expr.Expr)) 
        assert((type(gid) is int) and (gid >= 0)) 

        self.index       = FRESH_ERRORTERM_INDEX 
        self.expr        = err_expr
        self.context_gid = context_gid 
        self.gid         = gid 
        
        FRESH_ERRORTERM_INDEX = FRESH_ERRORTERM_INDEX + 1 

    def refVarName (self): 
        assert(type(self.index) is int) 
        assert(self.index >= 0) 
        return tft_expr.ERR_TERM_REF_PREFIX + str(self.index)

    def refVar (self): 
        return tft_expr.VariableExpr(self.refVarName(), Fraction, -1, False)

    def absexpr (self):
        if (self.stored_absexpr is not None): 
            return self.stored_absexpr 

        if (self.expr.hasLB() and self.expr.lb().value() >= Fraction(0, 1)): 
            self.stored_absexpr = self.expr 

        elif (isinstance(self.expr, tft_expr.UnaryExpr) and (self.expr.operator.label == "abs")): 
            self.stored_absexpr = self.expr 

        else: 
            self.stored_absexpr = IR.MakeUnaryExpr("abs", -1, self.expr, True)

        return self.stored_absexpr 

    def overApproxExpr (self, error_expr): 
        assert(isinstance(error_expr, tft_expr.ArithmeticExpr)) 
        
        if (self.stored_overapprox_expr is not None): 
            return self.stored_overapprox_expr 

        expr_abs_expr = self.absexpr() 
        if ((not expr_abs_expr.hasLB()) or (not expr_abs_expr.hasUB())): 
            sys.exit("ERROR: cannot over-approximate expr. without both LB and UB...")             

        value_lb = expr_abs_expr.lb().value() 
        value_ub = expr_abs_expr.ub().value() 
            
        assert(Fraction(0, 1) <= value_lb) 
        assert(value_lb <= value_ub) 
        
        self.stored_overapprox_expr = IR.MakeBinaryExpr("*", -1, 
                                                        tft_expr.ConstantExpr(value_ub), 
                                                        error_expr, 
                                                        True)

        return self.stored_overapprox_expr 

    def __hash__ (self): 
        return hash(self.index) 
        
    def copy (self, specific_epss=None): 
        if (specific_epss is None):
            ret_et = ErrorTerm(self.expr, self.stored_cmt_expr) 
        else: 
            assert(isinstance(specific_epss[i], tft_expr.ConstantExpr) for i in range(0, len(specific_epss))) 
            ret_et = ErrorTerm(self.expr, self.stored_cmt_expr, specific_epss[:]) 

        ret_et.gid = self.gid 
        ret_et.stored_cmt_expr = self.stored_cmt_expr 

        return ret_eform 

    def getGid (self):
        return self.gid 

    def getContextGid (self): 
        return self.context_gid 
        
                
class ErrorForm:
    terms = None
    upper_bound = None 
    M2 = None 

    gid2epsilons = None 
    
    gid_counts = None 

    gid_weight = None 

    casting_map = None 

    eq_gids = None 

    constraints = None 

    def __init__ (self, upper_bound, M2): 
        assert(isinstance(upper_bound, tft_expr.ConstantExpr)) 
        assert(isinstance(M2, tft_expr.ConstantExpr)) 

        self.upper_bound = upper_bound
        self.M2 = M2 

        self.terms = []
        self.casting_map = {} 
        self.gid2epsilons = {} 
        self.gid_counts = {} 
        self.gid_weight = {} 

    def add (self, term): 
        assert(isinstance(term, ErrorTerm))
        assert(term.index >= 0) 

        # check group validity 
        gid = term.getGid() 
        assert(0 <= gid) 
        assert(gid in self.gid2epsilons) 

        # check redundnecy 
        assert(term not in self.terms) 

        # add the ErrorTerm 
        self.terms.append(term)

    def nInstances (self): 
        total_inst = 0 
        for g,c in self.gid_counts.items(): 
            if (g == tft_expr.PRESERVED_CONST_GID): 
                continue 
            total_inst = total_inst + c 
        return total_inst 

    def scalingUpFactor (self):         
        largest_eps = Fraction(0.0) 
        
        for gid,epss in self.gid2epsilons.items(): 
            for eps in epss: 
                assert(eps.value() >= 0.0) 

                if (eps.value() == 0.0): 
                    continue 

                if (largest_eps < eps.value()): 
                    largest_eps = eps.value() 
            
        up_fac = Fraction(largest_eps.denominator, largest_eps.numerator) 
        
        # return tft_expr.ConstantExpr(up_fac) 
        # return tft_expr.ConstantExpr(up_fac * 512.0) 
        return tft_expr.ConstantExpr(up_fac / 8.0 ) # It is just a heuristic to divide by 8.0 

    def errorExpr (self, context_gid, gid): 
        assert(type(context_gid)   is int) 
        assert(type(gid)           is int)
        assert(context_gid         in self.gid2epsilons.keys()) 
        assert(gid                 in self.gid2epsilons.keys()) 
        assert((gid == context_gid) or 
               ((gid, context_gid) in self.casting_map.keys()))

        temp_epss         = self.gid2epsilons[gid]
        temp_context_epss = self.gid2epsilons[context_gid]
        epss              = [] 
        context_epss      = []

        checkValidEpsilonList(temp_epss)
        checkValidEpsilonList(temp_context_epss)

        # scaling up the epsilons 
        scaling_expr = self.scalingUpFactor() 
        for i in range(0, len(temp_epss)): 
            epss.append(         tft_expr.ConstantExpr(temp_epss[i].value() * scaling_expr.value()) )
        for j in range(0, len(temp_context_epss)): 
            context_epss.append( tft_expr.ConstantExpr(temp_context_epss[j].value() * scaling_expr.value()) ) 
                
        error_expr = IR.BE("*", -1, 
                           GroupErrorVar(gid, 0), 
                           epss[0], 
                           True) 

        for i in range(1, len(epss)): 
            error_expr = IR.BE("+", -1, 
                               error_expr, 
                               IR.BE("*", -1, 
                                     GroupErrorVar(gid, i), 
                                     epss[i], 
                                     True), 
                               True) 

        tc_error = None 
        
        if (gid != context_gid): 
            for i in range(0, len(epss)): 
                for j in range(0, len(context_epss)): 
                    if (epss[i] < context_epss[j]): 
                        temp_error = IR.BE("*", -1, 
                                           GroupErrorVar(gid, i), 
                                           GroupErrorVar(context_gid, j), 
                                           True) 
                        temp_error = IR.BE("*", -1, 
                                           temp_error, 
                                           context_epss[j], 
                                           # tft_expr.ConstantExpr(context_epss[j].value() + 
                                           #                       (context_epss[j].value() * epss[i].value())), 
                                           True) 
                        if (tc_error is None): 
                            tc_error = temp_error 
                        else:
                            tc_error = IR.BE("+", -1, 
                                             tc_error, 
                                             temp_error, 
                                             True) 

        if (tc_error is None): 
            return error_expr 
                        
        else: 
            return IR.BE("+", -1, error_expr, tc_error, True) 

    def copy (self, specific_alloc=None): 
        ef_ret = ErrorForm(self.upper_bound) 
        ef_ret.M2 = self.M2
        for et in self.terms: 
            epss = None 
            if (specific_alloc is not None): 
                assert(specific_alloc.isAssigned(et))
                epss = [tft_expr.ConstantExpr(specific_alloc[et])]
            ef_ret.add(et.copy(epss)) 

        ef_ret.gid2epsilons = self.gid2epsilons.copy() 
        ef_ret.gid_counts = self.gid_counts.copy() 
        ef_ret.casting_map = self.casting_map.copy() 

        return ef_ret 

    def __str__ (self): 
        str_ret = "==== error form ====\n" 

        str_ret = str_ret + "-- error terms --\n" 
        for et in self.terms: 

            str_ret = str_ret + "ET[" + str(et.index) +"] [CONTEXT: " + str(et.context_gid) + "] [GID: " + str(et.gid) + "]\n" 
            str_ret = str_ret + str(et.stored_overapprox_expr) + "\n" 

#            str_ret = str_ret + "-- first derivation expr --\n" 
            # str_ret = str_ret + str(et.absexpr()) + "\n" 
#            str_ret = str_ret + et.absexpr().toCString() + "\n" 

            str_ret = str_ret + "--------\n"

        str_ret = str_ret + "-- M2 --\n"
        str_ret = str_ret + str(self.M2) + "\n"

        str_ret = str_ret + "-- scoring expression --\n" 
        str_ret = str_ret + self.scoreExpr().toCString() + "\n" 

        str_ret = str_ret + "-- # instanes " + str(self.nInstances()) + " --\n" 

        str_ret = str_ret + "-- upper bound --\n"
        str_ret = str_ret + str(self.upper_bound) + " * " + str(self.scalingUpFactor()) + "\n"

        str_ret = str_ret + "-- casting map --\n" 
        for p,c in self.casting_map.items(): 
            str_ret = str_ret + str(p) + " : " + str(c) + "\n" 
        
        str_ret = str_ret + "-- gid 2 epsilons --\n" 
        for gid,epss in self.gid2epsilons.items(): 
            str_ret = str_ret + str(gid) + " :  " 
            for e in epss: 
                str_ret = str_ret + e.toCString() + "  "
            str_ret = str_ret + "\n"

        str_ret = str_ret + "-- gid counts --\n" 
        for gid,c in self.gid_counts.items(): 
            str_ret = str_ret + str(gid) + " : " + str(c) + "\n" 

        str_ret = str_ret + "-- eq gids -- \n" 
        for gp in self.eq_gids: 
            assert(len(gp) == 2) 
            str_ret = str_ret + str(gp[0]) + " = " + str(gp[1]) + "\n" 

        str_ret = str_ret + "-- constraints --\n" 
        for cons in self.constraints: 
            str_ret = str_ret + str(cons) + "\n" 
        
        str_ret = str_ret + "# of operation instances: " + str(self.nInstances()) + "\n" 
        str_ret = str_ret + "====================\n"
        return str_ret 

    def scoreExpr (self): 
        ret_se = None 

        if   (len(IR.PREC_CANDIDATES) == 2): 
            for gid,c in self.gid_counts.items(): 
                if (gid == tft_expr.PRESERVED_CONST_GID): 
                    continue 

                checkValidEpsilonList(self.gid2epsilons[gid]) 
            
                group_evar = GroupErrorVar(gid, 0)
                expr_score = IR.BE("*", -1, group_evar, tft_expr.ConstantExpr(int(c)), True) 

                assert(group_evar.hasBounds()) 

                if gid in self.gid_weight.keys(): 
                    weight = self.gid_weight[gid] 
                    assert((type(weight) is float) and (0 <= weight)) 

                    expr_score = IR.BE("*", -1, expr_score, tft_expr.ConstantExpr(weight), True) 
            
                if (ret_se is None): 
                    ret_se = expr_score 
                else: 
                    ret_se = IR.BE("+", -1, ret_se, expr_score, True)

            assert(ret_se is not None)
            return ret_se

        elif (len(IR.PREC_CANDIDATES) >= 3): 
            for gid,c in self.gid_counts.items(): 
                if (gid == tft_expr.PRESERVED_CONST_GID): 
                    continue 

                checkValidEpsilonList(self.gid2epsilons[gid]) 
                
                for ei in range(0, len(self.gid2epsilons[gid])): 
                    expr_score = None 

                    group_evar = GroupErrorVar(gid, ei)
                    assert(group_evar.hasBounds()) 

                    eps = self.gid2epsilons[gid][ei].value()
                    assert(eps in EPS_SCORE.keys())
                    
                    weight = EPS_SCORE[eps]
                    assert(type(weight) is float) 

                    weight = weight * float(c) 

                    if gid in self.gid_weight.keys(): 
                        ext_weight = self.gid_weight[gid]
                        assert((type(ext_weight) is float) and (0 <= ext_weight)) 
                        weight = weight * ext_weight 

                    assert(0 <= weight) 

                    if (weight > 0.0): 
                        expr_score = IR.BE("*", -1, group_evar, tft_expr.ConstantExpr(weight), True) 

                        if (ret_se is None): 
                            ret_se = expr_score 
                        else: 
                            ret_se = IR.BE("+", -1, ret_se, expr_score, True)

                    else: 
                        pass 

            assert(ret_se is not None)
            return ret_se

        else: 
            sys.exit("Error: invalid # of bit-width candidates...") 


# ========
# ErrorForm Optimization 
# ========
def OptimizeErrorFormByGroup (eform): 
    assert(isinstance(eform, ErrorForm))

    opt_eform = ErrorForm(eform.upper_bound, eform.M2) 

    # These are Important!! 
    # Need to overwrite the gid-counts 
    opt_eform.gid_counts = eform.gid_counts.copy() 
    # Need to overwrite the gid-weight 
    opt_eform.gid_weight = eform.gid_weight.copy() 
    # Need to overwrite the map of gid -> epsilons 
    opt_eform.gid2epsilons = eform.gid2epsilons.copy() 
    # Need to overwrite the casting_map!! 
    opt_eform.casting_map = eform.casting_map.copy()
    # Need to overwrite eq_gids 
    opt_eform.eq_gids = eform.eq_gids[:] 
    # Need to overwrite constraints 
    opt_eform.constraints = eform.constraints[:] 

    handled_etids = []

    for et in eform.terms: 
        if (et.index in handled_etids): 
            continue 

        gid         = et.getGid() 
        context_gid = et.getContextGid() 

        assert(0 <= gid) 

        group = [et] 
        handled_etids.append(et.index) 

        for et_p in eform.terms: 
            if (et.index == et_p.index): 
                continue 
            if (et_p.index in handled_etids): 
                continue 

            if ((gid         == et_p.getGid()) and 
                (context_gid == et_p.getContextGid())): 
                group.append(et_p)
                handled_etids.append(et_p.index) 

        assert(len(group) > 0) 

        combined_expr     = group[0].absexpr() 

        for i in range(1, len(group)): 
            combined_expr = tft_expr.BinaryExpr(tft_expr.BinaryOp(-1, "+"), 
                                                combined_expr, 
                                                group[i].absexpr()) 

        combined_expr = tft_expr.UnaryExpr(tft_expr.UnaryOp(-1, "abs"), 
                                           combined_expr) 

        combined_et = ErrorTerm(combined_expr, context_gid, gid) 

        assert(gid in eform.gid_counts.keys()) 
        
        opt_eform.add(combined_et) 

    return opt_eform
        
