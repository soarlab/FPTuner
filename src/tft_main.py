#!/usr/bin/env python

import os
import sys
import tft_tuning
import tft_utils
import tft_expr
import tft_sol_exprs
import tft_error_form

import tft_parser



# ========
# sub-routines
# ========
def FinalizeAlloc (fname_atext, alloc, eforms = []) :
    fatext = open(fname_atext, "w")
    fatext.write(str(alloc))
    fatext.close()

    print ("==== FINAL TUNING RESULT ====")
    if (alloc is None):
        print (str(alloc))
    else:
        tft_tuning.PrintAlloc(alloc, eforms)
    print ("=============================")



# ========
# main
# ========
assert(len(sys.argv) >= 3)

# alloc text file
FNAME_ATEXT = "__tft_alloc_text"

# get config file
CONFIG_FILE_NAME = os.path.abspath(sys.argv[1])
tft_tuning.LoadConfig(CONFIG_FILE_NAME)

# get input file name
INPUT_FILE_NAME = sys.argv[2]
eforms, alloc = tft_tuning.TFTRun(INPUT_FILE_NAME)


# -- the first tuning --

FinalizeAlloc(FNAME_ATEXT, alloc, eforms)


# -- additional tuning with more error thresholds --
if (alloc is None):
    print ("WARNING: no additional tuning when the \"base\" allocation is None...")
    exit(1)

assert(tft_sol_exprs.EFORMS is not None)
assert(len(tft_sol_exprs.EFORMS) > 0)
assert(all([isinstance(ef, tft_error_form.ErrorForm) for ef in tft_sol_exprs.EFORMS]))
assert(len(tft_tuning.OPTIMIZERS) > 0)

for ai in range(3, len(sys.argv)):
    af = None
    try:
        af = float(sys.argv[ai])
    except:
        print ("ERROR: invalid additional error threshold: " + str(sys.argv[ai]))

    new_eup = tft_expr.ConstantExpr(af)

    for ef in tft_sol_exprs.EFORMS :
        ef.upper_bound = new_eup

    # solve the error form
    eforms, alloc = tft_sol_exprs.SolveErrorForms(tft_sol_exprs.EFORMS, tft_tuning.OPTIMIZERS)

    print ("==== Additional Allocation with Error Threshold: " + str(new_eup) + " ====")
    FinalizeAlloc(FNAME_ATEXT+"-"+sys.argv[ai], alloc, eforms)
