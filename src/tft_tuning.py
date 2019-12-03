#!/usr/bin/env python 

import os 
import sys
import tft_expr
import tft_parser
import tft_alloc 
import tft_error_form 
import tft_solver 
import tft_utils 
import tft_ask_gelpia 
import tft_ask_gurobi 
import tft_sol_exprs 
import tft_get_first_derivations 
import tft_dat_def 
import tft_ir_backend 


# ==== global variables ==== 
OPTIMIZERS = {} 
OPTIMIZERS["vrange"] = "gelpia" 
OPTIMIZERS["alloc"]  = "gurobi" 

ERROR_BOUNDS         = [] 


# ========
# sub-routines 
# ======== 
def CountCastingsTemplate (func_comp, alloc, eforms = []): 
    assert(all([isinstance(ef, tft_error_form.ErrorForm) for ef in eforms])) 
    assert(isinstance(alloc, tft_alloc.Alloc)) 

    n_c = 0 

    uni_casting_map, uni_gid2epsilons = tft_error_form.UnifyCastingMapAndGid2Epsilons(eforms) 

    for p,c in uni_casting_map.items(): 
        assert(len(p) == 2) 
        assert(alloc.isAssigned(p[0]) and alloc.isAssigned(p[1])) 

        assert(p[1] != tft_expr.PRESERVED_CONST_GID) 
        if (p[0] == tft_expr.PRESERVED_CONST_GID): 
            continue 

        if (func_comp(alloc[p[0]], alloc[p[1]])): 
            n_c = n_c + c 
    
    return n_c 


def CountCastingsL2H (alloc, eforms = []): 
    return CountCastingsTemplate( (lambda f,t : (f > t)) , alloc, eforms ) 

def CountCastingsH2L (alloc, eforms = []): 
    return CountCastingsTemplate( (lambda f,t : (f < t)) , alloc, eforms ) 

def CountCastings (alloc, eforms): 
    return CountCastingsL2H(alloc, eforms) + CountCastingsH2L(alloc, eforms) 


def LoadConfig (fname_config): 
    global OPTIMIZERS

    # default settings 
    tft_ask_gurobi.VERBOSE = False 
    tft_ask_markian.VERBOSE = False 
    tft_solver.VERBOSE = False 
    tft_parser.VERBOSE = False 
    tft_get_first_derivations.VERBOSE = False 

    # -- beginning of loading config. file -- 
    cfile = open(fname_config, "r")

    for aline in cfile: 
        aline = aline.strip() 
        if (aline == ""): 
            continue 
        if (aline.startswith("#")): 
            continue 

        tokens = tft_utils.String2Tokens(aline, "=") 
        assert(len(tokens) == 2) 

        opt = tokens[0] 
        val = tokens[1] 

        if (opt == "OPT_VRANGE"): 
            assert(val in tft_solver.ALL_OPTIMIZERS) 
            OPTIMIZERS["vrange"] = val
        elif (opt == "OPT_ALLOC"): 
            assert(val in tft_solver.ALL_OPTIMIZERS) 
            OPTIMIZERS["alloc"] = val 

        elif (opt == "VERBOSE_GUROBI"): 
            tft_ask_gurobi.VERBOSE = tft_utils.String2Bool(val) 
        elif (opt == "VERBOSE_SAMPLER"):
            tft_ask_sampler.VERBOSE = tft_utils.String2Bool(val) 
        elif (opt == "VERBOSE_SAMPLERS"):
            tft_ask_samplers.VERBOSE = tft_utils.String2Bool(val) 
        elif (opt == "VERBOSE_SOLVER"): 
            tft_solver.VERBOSE = tft_utils.String2Bool(val) 
        elif (opt == "VERBOSE_PARSER"):
            tft_parser.VERBOSE = tft_utils.String2Bool(val) 
        elif (opt == "VERBOSE_GET_FIRST_DERIVATIONS"):
            tft_get_first_derivations.VERBOSE = tft_utils.String2Bool(val) 
        elif (opt == "ERROR_TYPE"): 
            tft_sol_exprs.ERROR_TYPE = val 
        elif (opt == "VERBOSE_SOL_EXPRS"):
            tft_sol_exprs.VERBOSE = tft_utils.String2Bool(val) 

        elif (opt == "GELPIA_TIMEOUT"): 
            tft_ask_gelpia.TIMEOUT = tft_utils.String2Int(val) 
            assert(tft_ask_gelpia.TIMEOUT > 0)
        elif (opt == "GELPIA_TOLERANCE"): 
            tft_ask_gelpia.DEFAULT_TOLERANCE = tft_utils.String2Float(val) 
            assert(tft_ask_gelpia.DEFAULT_TOLERANCE >= 1e-07) 

        elif (opt == "N_GELPIAS"): 
            tft_ask_gelpias.N_GELPIAS = tft_utils.String2Int(val) 
            assert(tft_ask_gelpias.N_GELPIAS > 0) 

        elif (opt == "SOLVER_N_SAMPLES"):
            tft_solver.N_SAMPLES = tft_utils.String2Int(val) 
            assert(tft_solver.N_SAMPLES > 0) 
        elif (opt == "SOLVER_ADDRESS_CASTINGS"): 
            tft_solver.ADDRESS_CASTINGS = tft_utils.String2Bool(val) 
        elif (opt == "SOLVER_LIMIT_N_CASTINGS"): 
            tft_solver.LIMIT_N_CASTINGS = tft_utils.String2Bool(val) 
        elif (opt == "SOLVER_N_MAX_CASTINGS"): 
            tft_solver.N_MAX_CASTINGS = tft_utils.String2Int(val) 
            assert(0 <= tft_solver.N_MAX_CASTINGS) 

        elif (opt == "SAMPLERS_N_SAMPLERS"): 
            tft_ask_samplers.N_SAMPLERS = tft_utils.String2Int(val) 
            assert(tft_ask_samplers.N_SAMPLERS > 0) 

        elif (opt.startswith("DAT_")): 
            continue 
            
        else: 
            sys.exit("ERROR: invalid option: " + opt) 
            
    cfile.close() 
    # -- ending of loading config. file -- 


# --------
def TFTSystemReset (): 
    # reset sampler 
    os.system("rm -f " + tft_ask_sampler.CPP_EXE_SIM_PREFIX + "*.cpp") 
    os.system("rm -f " + tft_ask_sampler.CPP_EXE_SIM_PREFIX + "*.input") 
    os.system("rm -f " + tft_ask_sampler.CPP_EXE_SIM_PREFIX + "*.output") 

    # reset tft_error_form 
    tft_error_form.FRESH_ERRORTERM_INDEX = 0 

    if (tft_dat_def.BASE_EFORMS is not None): 
        for ef in tft_dat_def.BASE_EFORMS: 
            assert(isinstance(ef, tft_error_form.ErrorForm)) 
            
            for et in ef.terms: 
                et.expr.lower_bound       = None 
                et.expr.upper_bound       = None 
                et.stored_absexpr         = None 
                et.stored_overapprox_expr = None 

    # reset tft_sol_exprs 
    tft_sol_exprs.GID_EPSS = {} 
    tft_sol_exprs.GID_COUNTS = [] 
    tft_sol_exprs.CAST_COUNTS = [] 

    # reset tft_solver 
    tft_solver.SAMPLER  = tft_ask_sampler.Sampler(tft_solver.N_SAMPLES) 
    tft_solver.SAMPLERS = tft_ask_samplers.Samplers(tft_solver.N_SAMPLES)  
    tft_solver.ID_ERROR_SUM = 0


# --------
def TFTRun (fname_input): 
    eforms, alloc = tft_sol_exprs.SolveExprs(fname_input, OPTIMIZERS)  

    return eforms, alloc 


def PrintAlloc (alloc, eforms = []): 
    if (alloc is None): 
        print (str(alloc)) 
        return 
    
    assert(isinstance(alloc, tft_alloc.Alloc)) 
    assert(len(eforms) > 0) 
    assert(all([isinstance(ef, tft_error_form.ErrorForm) for ef in eforms])) 

    for ef in eforms: 
        ef.SummarizeOperatorBitwidths(alloc) 
        print("") 

    print (str(alloc))
    if (alloc is not None):  
        print ("# L2H castings: " + str(CountCastingsL2H(alloc, eforms))) 
        print ("# H2L castings: " + str(CountCastingsH2L(alloc, eforms))) 
        print ("# Castings: " + str(CountCastings(alloc, eforms))) 


