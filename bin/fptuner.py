#!/usr/bin/env python3 

import os 
import sys 

import tft_expr 
import tft_utils 
import tft_sol_exprs 
import tft_error_form 
import tft_ir_api as IR 
import tft_ir_backend 
import tft_tuning 
import tft_alloc 

import imp 



# ========
# main 
# ========

# ==== get parameters ====
INPUT_FILE   = None 

i = 1
while True: 
    if (i >= len(sys.argv)): 
        break 

    arg_in = sys.argv[i] 

    if   (arg_in == "-v"): 
        tft_utils.FPTUNER_VERBOSE = True 

    elif (arg_in == "-debug"): 
        tft_utils.FPTUNER_VERBOSE = True
        tft_utils.FPTUNER_DEBUG   = True

    elif (arg_in == "-no-m2-check"): 
        tft_utils.NO_M2_CHECK     = True  
        
    elif (arg_in == "-maxc"):
        i = i + 1
        assert(i < len(sys.argv)), "No maximum number of type casts is given." 

        tft_utils.N_MAX_CASTINGS = int(sys.argv[i])
        assert(type(tft_utils.N_MAX_CASTINGS) is int and
               tft_utils.N_MAX_CASTINGS >= 0), "The number of maximum type casts must be a non-negative integer."

    elif (arg_in == "-optm"):
        i = i + 1

        tft_utils.OPT_METHOD = sys.argv[i].strip()
        assert(tft_utils.OPT_METHOD in tft_utils.OPT_METHODS), "Invalid optimization method: " + str(tft_utils.OPT_METHOD)

    elif (arg_in == "-e"): 
        i = i + 1 

        tokens                  = tft_utils.String2Tokens(sys.argv[i], " ") 
        tft_tuning.ERROR_BOUNDS = [float(tokens[ii]) for ii in range(0, len(tokens))] 
        
        assert(all([tft_tuning.ERROR_BOUNDS[ii] > 0.0 for ii in range(0, len(tft_tuning.ERROR_BOUNDS))])),"Invalid form of error threshold list. Please refer to the reference for the accepted form." 

    elif (arg_in == "-b"): 
        i = i + 1 
        
        tokens = tft_utils.String2Tokens(sys.argv[i], " ") 
        bwidths = [int(tokens[ii]) for ii in range(0, len(tokens))] 
        bwidths.sort()

        if   (bwidths == [32, 64]): 
            IR.PREC_CANDIDATES = ["e32", "e64"] 
        elif (bwidths == [64, 128]): 
            IR.PREC_CANDIDATES = ["e64", "e128"]
        elif (bwidths == [32, 64, 128]): 
            IR.PREC_CANDIDATES = ["e32", "e64", "e128"]
        else: 
            sys.exit("Error: not supported bit-width candidates: " + str(bwidths))

    elif (arg_in == "-fix-const-type"):
        tft_utils.FIX_CONST_TYPE = True 

    else: 
        assert(INPUT_FILE is None), "No expression specification is given." 
        INPUT_FILE = arg_in 

    i = i + 1


# ==== check parameters ====
if (INPUT_FILE is None): 
    sys.exit("Error: no input file is specified...") 
if (not os.path.isfile(INPUT_FILE)): 
    sys.exit("Error: input expression file doesn't exist: " + INPUT_FILE)
assert(INPUT_FILE.endswith(".py")), "Non-python expression specification is given." 

if (len(tft_tuning.ERROR_BOUNDS) == 0): 
    sys.exit("Error: no error bound is specified... Please use -e to specify error bounds.") 


# ==== load the input file as a module ====
tokens      = tft_utils.String2Tokens(INPUT_FILE, "/") 
assert(len(tokens) >= 1) 

module_name = tokens[-1]
assert(module_name.endswith(".py")) 
module_name = module_name[0:len(module_name)-3] 

IR.LOAD_CPP_INSTS = True 
module_in         = imp.load_source(module_name, INPUT_FILE) 
if (IR.TARGET_EXPR is None): 
    sys.exit("Error: no tuning target expression was specified...") 
IR.LOAD_CPP_INSTS = False 


# ==== tune the targeted expression ====
# reset the timers
tft_utils.TIME_PARSING           = 0
tft_utils.TIME_FIRST_DERIVATIVES = 0
tft_utils.TIME_GLOBAL_OPT        = 0
tft_utils.TIME_ALLOCATION        = 0
tft_utils.TIME_CHECK_M2          = 0

# possibly remove the .exprs file 
EXPRS_NAME  = INPUT_FILE + ".exprs"
if (os.path.isfile(EXPRS_NAME)): 
    tft_utils.VerboseMessage("Warning: rewrite existed file: " + EXPRS_NAME) 
    os.system("rm " + EXPRS_NAME) 

# go tuning 
for i in range(0, len(tft_tuning.ERROR_BOUNDS)): 
    eforms = None 
    alloc  = None 

    # Tune for the first error bound. 
    # Need to generate the .exprs file first. 
    if (i == 0): 
        tft_ir_backend.ExportExpr2ExprsFile(IR.TARGET_EXPR, 
                                            tft_tuning.ERROR_BOUNDS[0], 
                                            EXPRS_NAME) 

        # tune! 
        eforms, alloc = tft_tuning.TFTRun(EXPRS_NAME) 

    # otherwise, do some reset tasks 
    else: 
        tft_sol_exprs.ReadyToTune() 

        new_eup = tft_expr.ConstantExpr(tft_tuning.ERROR_BOUNDS[i]) 

        for ef in tft_sol_exprs.EFORMS : 
            ef.upper_bound = new_eup 

        # solve the error form 
        eforms, alloc = tft_sol_exprs.SolveErrorForms(tft_sol_exprs.EFORMS, tft_tuning.OPTIMIZERS) 

    # show the allocation 
    print ("==== error bound : " + str(tft_tuning.ERROR_BOUNDS[i]) + " ====") 
    tft_tuning.PrintAlloc(alloc, eforms) 
    print ("") 
    tft_ir_backend.ExportColorInsts(alloc)
    print ("") 
    
    # -- synthesize the mixed precision cpp file -- 
    if   (alloc is None): 
        print ("Warning: no allocation was generated... Thus no .cpp file will be generated...") 
    else: 
        assert(isinstance(alloc, tft_alloc.Alloc))
        assert(eforms is not None) 

        str_error_bound = str(float(tft_tuning.ERROR_BOUNDS[i])) 
        fname_cpp = module_name.strip() + "." + str_error_bound + ".cpp" 
        
        if (os.path.isfile(fname_cpp)): 
            tft_utils.VerboseMessage("Warning: overwrite the existed .cpp file: " + fname_cpp) 
        
        tft_ir_backend.ExportCppInsts(alloc, fname_cpp) 

# show the timers
tft_utils.VerboseMessage("Total Parsing time          : " + str(float(tft_utils.TIME_PARSING)))
tft_utils.VerboseMessage("    First Dev.              : " + str(float(tft_utils.TIME_FIRST_DERIVATIVES)))
tft_utils.VerboseMessage("Time for global optimization: " + str(float(tft_utils.TIME_GLOBAL_OPT)))
tft_utils.VerboseMessage("Time for solving QCQP       : " + str(float(tft_utils.TIME_ALLOCATION)))
tft_utils.VerboseMessage("Time for checking M2        : " + str(float(tft_utils.TIME_CHECK_M2)))
