#!/usr/bin/env python 

import os
import sys 
import random
import imp  
import tft_utils 
import tft_expr 
import tft_parser
import tft_alloc
import tft_sol_exprs 
import tft_get_first_derivations 
from fractions import Fraction 
import tft_tuning 

import tft_dat_def as DEF 
import tft_dat_sampling 
import tft_dat_cluster 
import tft_dat_train
import tft_dat_testing 



# ========
# global variables 
# ========
# -- switch for verbose -- 
VERBOSE = True 



# ========
# main -- training 
# ========
# ---- get arguments ---- 
assert(len(sys.argv) >= 3) 
if (len(sys.argv) > 3): 
    print ("WARNING: only the first three arguments in sys.argv will be considered...") 

FNAME_CONFIG = sys.argv[1].strip() 
assert(os.path.isfile(FNAME_CONFIG)) 
FNAME_EXPRS = sys.argv[2].strip() 
assert(os.path.isfile(FNAME_EXPRS)) 

if (not FNAME_EXPRS.endswith(".exprs")): 
    sys.exit("ERROR: DAT only takes .exprs file...") 


# ---- pre-processing ----
# reset FPTyalor queryer in order to reuse the results 
tft_get_first_derivations.ResetGetFirstDerivations() 
# set reuse of FPTaylor's results 
tft_get_first_derivations.REUSE_FPT_REL = True 


# ---- load config file ---- 
DEF.LoadDATConfig(FNAME_CONFIG) 
tft_tuning.LoadConfig(FNAME_CONFIG) 


# ---- automatically silient some procedures... ---- 
if (tft_sol_exprs.VERBOSE): 
    print ("WARNING: silient sol_exprs by default...") 
    tft_sol_exprs.VERBOSE = False 


# ---- create the BASE_EFORMs ---- 
if (DEF.STEP_SAMPLE or DEF.STEP_TEST): 
    tft_dat_sampling.LoadExprsFile(FNAME_EXPRS) 

    if (DEF.REUSE_EFORMS): 
        DEF.BASE_EFORMS, base_alloc = tft_tuning.TFTRun(FNAME_EXPRS) 



# ======== 
# main -- sampling
# ======== 
if (DEF.STEP_SAMPLE): 
    tft_dat_sampling.SamplePartitions() 



# ========
# main -- clustering 
# ========
if (DEF.STEP_CLUSTER): 
    # -- clustering -- 
    tft_dat_cluster.Cluster() 



# ========
# main -- train SVM model 
# ========
if (DEF.STEP_TRAIN): 
    tft_dat_train.DATTrain(DEF.FNAME_SVM_TRAIN_FEATURE_CLUSTER)



# ========
# main -- testing in small-scale 
# ========
if (DEF.STEP_TEST): 
    print ("==== testing in mode : " + DEF.TEST_MODE + " ====") 
    tft_dat_testing.Testing() 



tft_get_first_derivations.REUSE_FPT_REL = False 
    
    
