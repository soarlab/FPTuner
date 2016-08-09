
import os
import sys
import time 
from fractions import Fraction
import tft_expr 
import tft_alloc 
import tft_solver 
import tft_utils 
import tft_parser 
import tft_get_first_derivations 
import tft_error_form 
import tft_type_casting_counter 


# ======== 
# global variables 
# ========
FPREFIX_DOT_INPUT  = "__tft_expr." 
FPOSTFIX_DOT_INPUT = ".input" 
VERBOSE            = False 
GID_EPSS           = {}
GID_COUNTS         = {}
GID_WEIGHT         = {} 
CASTING_MAP        = {} 
EQ_GIDS            = [] 
CONSTRAINT_EXPRS   = [] 

ERROR_TYPE         = "abs"
OPT_ERROR_FORM     = True 


# ---- saving the ErrorForms and the relative data ---- 
EFORMS             = None 
E_UPPER_BOUND      = None 
M2                 = None 



# ========
# subroutines 
# ======== 
# ==== generate an Error Form from an expression ==== 
def GenerateErrorTermsFromExpr (context_expr, expr, error_exprs = [], program_exprs = []): 
    assert(len(error_exprs) == len(program_exprs)) 

    if (isinstance(expr, tft_expr.ConstantExpr)): 
        return []

    elif (isinstance(expr, tft_expr.VariableExpr) or isinstance(expr, tft_expr.BinaryExpr) or isinstance(expr, tft_expr.UnaryExpr)): 

        my_et       = None
        gid         = expr.getGid() 

        assert(gid in GID_EPSS.keys()) 
        epss = GID_EPSS[gid] 

        prog_expr  = None 
        error_expr = None 

        if (tft_expr.isPreciseOperation(expr)): 
            error_expr = tft_expr.ConstantExpr(0.0) 
        
        else:
            for i in range(0, len(program_exprs)): 
                pe = program_exprs[i] 
                if (expr.identical(pe)): 
                    prog_expr   = pe 
                    error_expr  = error_exprs[i] 
                    
            if (error_expr is None): 
                print ("<<<< expr >>>>") 
                print (expr.toIRString()) 
                print (expr.toASTString()) 
                print (">>>> program exprs <<<<") 
                for pe in program_exprs: 
                    print (pe.toIRString())
                    print (pe.toASTString()) 
                    print ("------------") 

        assert(error_expr is not None) 

        # get my ErrorTerm 
        my_et = tft_error_form.ErrorTerm(error_expr, 
                                         context_expr.getGid(), 
                                         gid)  

        # get my operands' ErrorTerms and do some more book keeping 
        if (isinstance(expr, tft_expr.VariableExpr)): 
            return [ my_et ]
        
        elif (isinstance(expr, tft_expr.UnaryExpr)): 
            ets_opd = GenerateErrorTermsFromExpr(expr, expr.opd(), error_exprs, program_exprs) 

            return [ my_et ] + ets_opd 

        elif (isinstance(expr, tft_expr.BinaryExpr)): 

            ets_lhs = GenerateErrorTermsFromExpr(expr, expr.lhs(), error_exprs, program_exprs)

            ets_rhs = GenerateErrorTermsFromExpr(expr, expr.rhs(), error_exprs, program_exprs)

            return [ my_et ] + ets_lhs + ets_rhs 

        else: 
            sys.exit("ERROR: broken control flow in GenerateErrorTermsFromExpr...") 

    else:
        sys.exit("ERROR: invlaid expr. type...") 


def GenerateErrorFormFromExpr (expr, error_type, upper_bound, M2, eq_gids = [], constraint_exprs = []): 
    # -- call FPTaylor for first derivation -- 
    text_terms = tft_get_first_derivations.GetFirstDerivations(expr) 

    error_exprs   = [] 
    program_exprs = [] 

    for tt in text_terms: 

        str_error   = tt.text_expr 
        str_program = tt.text_comment 

        if (error_type == "abs"): 
            pass 
        elif (error_type == "rel"): 
            str_error = "(" + str_error + " /$-1 " + str_program + ")" 
        else:
            sys.exit("ERROR: invalid error_type") 

        e_expr = tft_parser.String2Expr(str_error, False) 
        p_expr = tft_parser.String2Expr(str_program, False) 

        error_exprs.append(e_expr) 
        program_exprs.append(p_expr) 

    eterms = GenerateErrorTermsFromExpr(expr, expr, error_exprs, program_exprs) 
    assert(len(eterms) > 0) 

    eform = tft_error_form.ErrorForm(upper_bound, M2) 
    eform.terms = eterms 
    eform.gid2epsilons = GID_EPSS.copy() 
    eform.gid_counts = GID_COUNTS.copy() 
    eform.gid_weight = GID_WEIGHT.copy() 
    eform.casting_map = CASTING_MAP.copy() 
    eform.eq_gids = eq_gids[:] 
    eform.constraints = constraint_exprs[:] 

    if (OPT_ERROR_FORM): 
        eform = tft_error_form.OptimizeErrorFormByGroup(eform)

    return eform 


# ==== solve from ErrorForms ==== 
def SolveErrorForms (eforms = [], optimizers = {}): 
    assert(len(eforms) > 0) 
    assert(all([isinstance(ef, tft_error_form.ErrorForm) for ef in eforms]))
    assert("vrange" in optimizers.keys()) 
    assert("alloc" in optimizers.keys())

    alloc = tft_solver.FirstLevelAllocSolver(optimizers, eforms) 

    return eforms, alloc 


# ==== solve .exprs file ==== 
def SolveExprs (fname_exprs, optimizers = {}): 
    global EFORMS 
    global E_UPPER_BOUND
    global M2

    global GID_EPSS 
    global GID_COUNTS
    global GID_WEIGHT 
    global CASTING_MAP 
    global EQ_GIDS     
    global CONSTRAINT_EXPRS 
    global OPT_ERROR_FORM 

    EFORMS = None 
    E_UPPER_BOUND = None
    M2 = None 

    assert(os.path.isfile(fname_exprs)) 
    assert(ERROR_TYPE in ["abs", "rel"]) 

    # variables
    input_vars = [] 
    target_exprs = [] 
    E_UPPER_BOUND = None 

    # -- read expr file -- 
    if (VERBOSE): 
        print ("==== sol_exprs: read exprs file: " + fname_exprs) 

    tstamp = time.time() 

    ilines = [] 

    efile = open(fname_exprs, "r") 
    for aline in efile: 
        aline = aline.strip() 
        if (aline == ""): 
            continue 
        if (aline.startswith("#")): 
            continue 
        ilines.append(aline) 
    efile.close()


    # options 
    assert(ilines[0] == "options:") 
    ilines = ilines[1:] 
    while True: 
        if (ilines[0] == "upper-bound:"): 
            break 

        tokens = tft_utils.String2Tokens(ilines[0], ":") 
        assert(len(tokens) == 2) 

        if (tokens[0] == "opt-error-form"): 
            OPT_ERROR_FORM = tft_utils.String2Bool(tokens[1]) 
            
        else: 
            sys.exit("ERROR: unknown option setting: " + ilines[0]) 

        ilines = ilines[1:] 

    # read error bound 
    assert(ilines[0] == "upper-bound:") 
    ilines        = ilines[1:] 
    E_UPPER_BOUND = tft_expr.ConstantExpr(float(ilines[0])) 
    ilines        = ilines[1:] 

    # M2 
    M2 = tft_expr.ConstantExpr(0.0) 
    
    # read variable ranges 
    assert(ilines[0] == "var-ranges:") 
    ilines = ilines[1:] 
    while True : 
        if (ilines[0] == "group-epsilons:"):
            break 

        var = tft_parser.String2BoundedVariableExpr(ilines[0]) 

        assert(var not in input_vars) 
        input_vars.append(var) 

        ilines = ilines[1:] 

    # get groups' epsilons 
    assert(ilines[0] == "group-epsilons:") 
    ilines = ilines[1:] 
    while True : 
        if (ilines[0] == "eq-gids:"): 
            break 

        tokens = tft_utils.String2Tokens(ilines[0], ":")
        assert(len(tokens) == 2) 
            
        gid      = int(tokens[0]) 
        str_epss = tokens[1] 

        assert(str_epss.startswith("[") and str_epss.endswith("]")) 
        str_epss = str_epss[1:len(str_epss)-1] 
        str_eps_list = tft_utils.String2Tokens(str_epss, ",")

        eps_list = [] 

        for i in range(0, len(str_eps_list)): 
            try: 
                i = tft_alloc.EpsLabels_String().index(str_eps_list[i]) 
                eps_list.append(tft_expr.ConstantExpr(tft_alloc.EPSILONS[i].value)) 
            except ValueError : 
                expr_eps = tft_parser.String2Expr(str_eps_list[i], True) 
                assert(isinstance(expr_eps, tft_expr.ConstantExpr)) 
                eps_list.append(expr_eps) 
            
        assert(gid not in GID_EPSS.keys()) 
        GID_EPSS[gid] = eps_list

        ilines = ilines[1:] 

    # get equal bit-width groups 
    assert(len(ilines) > 0) 
    assert(ilines[0] == "eq-gids:") 
    ilines = ilines[1:] 
    while True : 
        assert(len(ilines) > 0) 
        if (ilines[0] == "gid-counts:"): 
            break 

        tokens = tft_utils.String2Tokens(ilines[0], "=") 
        assert(len(tokens) == 2) 
        
        gid_1 = int(tokens[0]) 
        gid_2 = int(tokens[1]) 
        
        if (gid_1 == gid_2): 
            ilines = ilines[1:] 
            continue 

        assert(gid_1 in GID_EPSS.keys()) 
        assert(gid_2 in GID_EPSS.keys()) 
        assert(GID_EPSS[gid_1] == GID_EPSS[gid_2]) 
        
        gp12 = (gid_1, gid_2) 
        gp21 = (gid_2, gid_1) 

        if ((gp12 not in EQ_GIDS) and (gp21 not in EQ_GIDS)): 
            EQ_GIDS.append(gp12) 

        ilines = ilines[1:] 

    # get GID_COUNTS
    assert(len(ilines) > 0) 
    assert(ilines[0] == "gid-counts:") 
    ilines = ilines[1:] 
    while True:
        assert(len(ilines) > 0) 
        if (ilines[0] == "casting-counts:"): 
            break 
        
        tokens = tft_utils.String2Tokens(ilines[0], ":") 
        assert(len(tokens) == 2) 

        gid = int(tokens[0]) 
        c   = int(tokens[1]) 

        assert(gid >= 0)
        assert(c   > 0) 
        assert(gid not in GID_COUNTS.keys()) 

        GID_COUNTS[gid] = c 

        ilines = ilines[1:] 

    # get CASTING_MAP 
    assert(len(ilines) > 0) 
    assert(ilines[0] == "casting-counts:") 
    ilines = ilines[1:] 
    while True: 
        assert(len(ilines) > 0) 
        if (ilines[0] == "gid-weight:"): 
            break 

        tokens = tft_utils.String2Tokens(ilines[0], ":") 
        assert(len(tokens) == 2) 

        p = tokens[0] 
        c = int(tokens[1]) 

        assert(c > 0) 
        assert(p.startswith("(") and p.endswith(")")) 
        p = p[1:len(p)-1] 

        tokens = tft_utils.String2Tokens(p, ",")
        assert(len(tokens) == 2) 

        gid_from = int(tokens[0]) 
        gid_to = int(tokens[1]) 
    
        p = (gid_from, gid_to) 

        assert(p not in CASTING_MAP.keys()) 
        CASTING_MAP[p] = c 

        ilines = ilines[1:] 

    # get gid-weight mapping 
    assert(len(ilines) > 0) 
    assert(ilines[0] == "gid-weight:") 
    ilines = ilines[1:] 
    while True: 
        assert(len(ilines) > 0) 
        if (ilines[0] == "exprs:"): 
            break 

        tokens = tft_utils.String2Tokens(ilines[0], ":") 
        assert(len(tokens) == 2) 

        gid    = int(tokens[0]) 
        weight = float(tokens[1]) 
        assert(0 <= gid) 
        assert(0 <= weight) 

        GID_WEIGHT[gid] = weight 

        ilines = ilines[1:] 

    # get expressions 
    assert(len(ilines) > 0) 
    assert(ilines[0] == "exprs:") 
    ilines = ilines[1:] 
    while True : 
        assert(len(ilines) > 0) 
        if (ilines[0] == "constraints:"): 
            break 

        target_expr = tft_parser.String2Expr(ilines[0], False) 
        assert(isinstance(target_expr, tft_expr.ArithmeticExpr)) 

        target_exprs.append(target_expr)

        ilines = ilines[1:] 

    assert(len(target_exprs) > 0)
    assert(all([isinstance(te, tft_expr.Expr) for te in target_exprs]))

    # get constraints 
    assert(len(ilines) > 0)
    assert(ilines[0] == "constraints:") 
    ilines = ilines[1:] 
    while True : 
        if (len(ilines) == 0): 
            break 

        pred_expr = tft_parser.String2Expr(ilines[0], False) 
        assert(isinstance(pred_expr, tft_expr.Predicate)) 

        CONSTRAINT_EXPRS.append(pred_expr) 

        ilines = ilines[1:] 

    tstamp = time.time() - tstamp 

    if (VERBOSE): 
        print ("==== sol_exprs: finished reading exprs file in " + str(tstamp)) 

    # ---- generate the Error Forms ----     
    if (VERBOSE): 
        print ("==== sol_exprs: generate the ErrorForms... ") 
        
    tstamp = time.time() 

    target_alloc = None 
    irstrings = None 

    EFORMS = [] 
    for te in target_exprs: 
        ef = GenerateErrorFormFromExpr(te, ERROR_TYPE, E_UPPER_BOUND, M2, EQ_GIDS, CONSTRAINT_EXPRS) 
        EFORMS.append(ef) 

    assert(len(EFORMS) == len(target_exprs)) 

    tstamp = time.time() - tstamp 
    
    if (VERBOSE): 
        print ("==== sol_exprs: finished generating the ErrorForms in " + str(tstamp)) 

    # ---- solve from the ErrorForms ---- 
    if (VERBOSE):
        print ("==== sol_exprs: solve the ErrorForms...") 

    tstamp = time.time() 

    EFORMS, target_alloc = SolveErrorForms(EFORMS, optimizers) 

    if (VERBOSE): 
        print ("---- Error Forms after solving ----") 
        for ef in EFORMS: 
            print (str(ef))
            print ("------------") 

    if (target_alloc is None): 
        print ("TFT: no available allocation for the main expr...")
        return EFORMS, None

    tstamp = time.time() - tstamp 

    if (VERBOSE): 
        print ("==== sol_exprs: finished solving the ErrorForms in " + str(tstamp)) 

    # ---- some finalize before return ---- 
    if (VERBOSE): 
        stat = {} 
        for te in target_exprs: 
            tft_expr.ExprStatistics(te, stat) 

        assert("# constants"  in stat.keys()) 
        assert("# variables"  in stat.keys()) 
        assert("# operations" in stat.keys()) 
        assert("groups"       in stat.keys()) 

        stat["groups"].sort() 

        print ("---- # constants:  " + str(stat["# constants"]) + "  (# of appearances)") 
        print ("---- # variables:  " + str(stat["# variables"]) + "  (# of appearances)") 
        print ("---- # operations: " + str(stat["# operations"])) 
        print ("---- groups: "       + str(stat["groups"])) 

#        n_opts,n_insts = tft_error_form.countOptsInsts(EFORMS) 
#        print ("---- # of (static) operations: " + str(n_opts)  + " ----") 
#        print ("---- # of (dynamic) instances: " + str(n_insts) + " ----") 

    # ---- return ----
    return EFORMS, target_alloc 

