
import os
import sys
from fractions import Fraction 
import tft_expr 
import tft_utils 
import subprocess as subp 


# ========
# global variables 
# ========
FNAME_FPT_QUERY = "__fpt_query" 
FNAME_FPT_REL = "./tft_func_form"

# please set this flag carefully... 
# by setting this flag as true, function "ResetGetFirstDerivations" must be called somewhere 
# in order to query FPTaylor at the first time. 
# Therefore, the reused results are the desired results... 
REUSE_FPT_REL = False 

CACHE_TEXT_TERMS = {} 

VERBOSE = False 


# ========
# classes 
# ========
class TextTerm: 
    text_expr = None 
    text_comment = None 

    def __init__ (self, text_expr, text_comment): 
        assert(type(text_expr) is str)
        assert(type(text_comment) is str) 
        self.text_expr = text_expr
        self.text_comment = text_comment 


# ========
# subroutines 
# ========
def ResetGetFirstDerivations (): 
    global CACHE_TEXT_TERMS 

    if (os.path.isfile(FNAME_FPT_QUERY)): 
        os.system("rm " + FNAME_FPT_QUERY) 
    if (os.path.isfile(FNAME_FPT_REL)): 
        os.system("rm " + FNAME_FPT_REL) 
    CACHE_TEXT_TERMS = {} 


def WriteGetFirstDerivationQueryFile (expr, vs=[]): 
    # -- create query file -- 
    if (os.path.isfile(FNAME_FPT_QUERY)): 
        if (VERBOSE): 
            print ("WARNING: over-write FPTaylor query file : " + FNAME_FPT_QUERY) 
        os.system("rm " + FNAME_FPT_QUERY)
    qfile = open(FNAME_FPT_QUERY, "w") 
    vname_rel = "tft_rel" 
    
    # write variables 
    qfile.write("Variables\n") 
    str_vs = "" 
    for v in vs: 
        assert(v.hasBounds()) 
        assert(v.label() != vname_rel) 
        str_vs = str_vs + v.toASTString() + " in [" + str(float(v.lb().value())) + ", " + str(float(v.ub().value())) + "],\n"
    str_vs = str_vs.strip() 
    if (len(vs) > 0): 
        assert(str_vs[len(str_vs)-1:] == ",") 
        str_vs = str_vs[0:len(str_vs)-1] + ";\n" 
    else:
        str_vs = str_vs + "dummy_variable in [0.0, 1.0];\n" 

    str_vs = str_vs + "\n" 
    qfile.write(str_vs) 

    # write definition
    qfile.write("Definitions\n") 
    qfile.write(vname_rel + " rnd64= ") 
    qfile.write(expr.toASTString() + ";\n") 

    # write expression 
    qfile.write("Expressions\n") 
    qfile.write(vname_rel + ";\n") 

    # finalize 
    qfile.close() 


def ParseFPTaylorResults (cstr_expr, vs=[]): 
    global CACHE_TEXT_TERMS
    if (REUSE_FPT_REL): 
        assert(cstr_expr not in CACHE_TEXT_TERMS.keys()) 
    
    # -- read result file -- 
    assert(os.path.isfile(FNAME_FPT_REL)) 
    rfile = open(FNAME_FPT_REL, "r") 

    TEXT_TERMS = [] 
    for aline in rfile: 
        aline = aline.strip() 
        tokens = tft_utils.String2Tokens(aline, ":") 
        assert(len(tokens) == 3) 

        str_index = tokens[0] 
        str_raw_expr = tokens[1] 
        str_comment = tokens[2] 

        # modify str_raw_expr 
        str_expr = str_raw_expr 

        TEXT_TERMS.append(TextTerm(str_expr, str_comment)) 

    rfile.close() 
    CACHE_TEXT_TERMS[cstr_expr] = TEXT_TERMS 


def GetFirstDerivations (expr): 
    assert(isinstance(expr, tft_expr.Expr)) 

    # -- precondition(s) --
    vs = expr.vars(False) 
#    assert(len(vs) > 0) 
    cstr_expr = expr.toCString() 
    
    if (REUSE_FPT_REL and (cstr_expr in CACHE_TEXT_TERMS.keys())): 
        assert(len(CACHE_TEXT_TERMS[cstr_expr]) > 0)
    else: 
        # -- create query file -- 
        WriteGetFirstDerivationQueryFile(expr, vs) 

        # -- delete the result file -- 
        if (os.path.isfile(FNAME_FPT_REL)): 
            os.system("rm " + FNAME_FPT_REL) 

        # -- run fptaylor -- 
        tft_utils.checkFPTaylorInstallation("master") 
        cfg_first = os.environ["HOME_FPTAYLOR"] + "/" + tft_utils.FPT_CFG_FIRST 
        command_fpt = os.environ["FPTAYLOR"] + " -c " + cfg_first + " " + FNAME_FPT_QUERY 
        if (VERBOSE): 
            os.system(command_fpt) 
        else:
            exe_fpt = subp.Popen(command_fpt, shell=True, stdout=subp.PIPE, stderr=subp.PIPE) 

            exe_fpt.communicate() 

            assert(os.path.isfile(FNAME_FPT_REL))

        # -- read result file -- 
        ParseFPTaylorResults(cstr_expr, vs) 

    return CACHE_TEXT_TERMS[cstr_expr] 




