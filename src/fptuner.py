#!/usr/bin/env python 

import os 
import sys 

import tft_utils 
import tft_ir_api as IR 
import tft_ir_backend 
import tft_tuning 

import imp 



# ========
# main 
# ========

# ==== get parameters ====
INPUT_FILE   = None 
CONFIG_FILE  = "default.fptconf" 
ERROR_BOUNDS = [] 

i = 1
while True: 
    if (i >= len(sys.argv)): 
        break 

    arg_in = sys.argv[i] 

    if   (arg_in == "-c"): 
        i = i + 1 
        if (i >= len(sys.argv)): 
            sys.exit("Error: missing configuration file") 

        arg_in      = sys.argv[i] 
        CONFIG_FILE = arg_in

    elif (arg_in == "-e"): 
        i = i + 1 

        tokens       = tft_utils.String2Tokens(sys.argv[i], " ") 
        ERROR_BOUNDS = [float(tokens[ii]) for ii in range(0, len(tokens))] 
        
        assert(all([ERROR_BOUNDS[ii] > 0.0 for ii in range(0, len(ERROR_BOUNDS))]))
        
    else: 
        assert(INPUT_FILE is None) 
        INPUT_FILE = arg_in 

    i = i + 1


# ==== check parameters ====
assert(os.path.isfile(INPUT_FILE)) 
assert(INPUT_FILE.endswith(".py")) 

if (len(ERROR_BOUNDS) == 0): 
    sys.exit("Error: no error bound is specified... Please use -e to specify error bounds.") 

assert(os.path.isfile(CONFIG_FILE)) 


# ==== load the input file as a module ====
tokens      = tft_utils.String2Tokens(INPUT_FILE, "/") 
assert(len(tokens) >= 1) 

module_name = tokens[-1]
assert(module_name.endswith(".py")) 
module_name = module_name[0:len(module_name)-3] 

module_in   = imp.load_source(module_name, INPUT_FILE) 
if (IR.TARGET_EXPR is None): 
    sys.exit("Warning: no tuning target expression was specified...") 


# ==== tune the targeted expression ==== 
# generate the .exprs file 
EXPRS_NAME  = INPUT_FILE + ".exprs"
if (os.path.isfile(EXPRS_NAME)): 
    print ("Warning: rewrite existed file: " + EXPRS_NAME) 
    os.system("rm " + EXPRS_NAME) 

tft_ir_backend.ExportExpr2ExprsFile(IR.TARGET_EXPR, 
                                    ERROR_BOUNDS[0], 
                                    EXPRS_NAME) 

# go tunine 
eforms, alloc = tft_tuning.TFTRun(EXPRS_NAME) 
