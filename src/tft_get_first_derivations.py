
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

# please set this flag carefully... 
# by setting this flag as true, function "ResetGetFirstDerivations" must be called somewhere 
# in order to query FPTaylor at the first time. 
# Therefore, the reused results are the desired results... 
REUSE_FPT_REL    = False 
CACHE_TEXT_TERMS = {} 
VERBOSE          = False 


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
    qfile.write("\n") 

    # write expression 
    qfile.write("Expressions\n") 
    qfile.write(vname_rel + ";\n") 

    # finalize 
    qfile.close() 


def ParseFPTaylorResults (cstr_expr, vs=[], fpt_outputs=[]): 
    global CACHE_TEXT_TERMS
    if (REUSE_FPT_REL): 
        assert(cstr_expr not in CACHE_TEXT_TERMS.keys()) 

    # -- read FPTaylor output -- 
    raw_expr_2_comment = {}
    reading_phase = None 
    
    for aline in fpt_outputs: 
        if   (reading_phase is None): 
            if   (aline.startswith("Simplified rounding")): 
                reading_phase = "raw_expr" 
                continue 

        elif (reading_phase == "raw_expr"): 
            if (aline.startswith("Corresponding original subexpressions")): 
                reading_phase = "comment" 
                continue 

            ii          = aline.find(" ") 
            if (ii <= 0): 
                continue 
            
            id_raw_expr = None 
            try: 
                id_raw_expr = int(aline[0:ii]) 
            except: 
                continue 

            str_raw_expr_prefix = "exp = -53:"
            ii          = aline.find(str_raw_expr_prefix) 
            assert(ii > 0) 

            raw_expr    = aline[ii+len(str_raw_expr_prefix):].strip() 
            
            if (id_raw_expr > 0): 
                assert(id_raw_expr not in raw_expr_2_comment.keys()) 
                raw_expr_2_comment[id_raw_expr] =  [raw_expr, None]

        elif (reading_phase == "comment"): 
            if (aline.startswith("bounds")): 
                reading_phase = None 
                continue 

            ii         = aline.find(":") 
            if (ii <= 0): 
                continue 

            id_comment = int(aline[0:ii]) 

            comment    = aline[ii+1:].strip() 
            assert(len(comment) > 0) 

            assert(id_comment in raw_expr_2_comment.keys()) 
            assert(len(raw_expr_2_comment[id_comment]) == 2) 
            assert(raw_expr_2_comment[id_comment][1] is None) 
            
            raw_expr_2_comment[id_comment][1] = comment 

        else: 
            assert(False) 


    TEXT_TERMS = [] 
    for index,raw_expr_2_comment in raw_expr_2_comment.items(): 
        assert(len(raw_expr_2_comment) == 2) 

        str_raw_expr = raw_expr_2_comment[0] 
        str_comment  = raw_expr_2_comment[1] 

        assert(type(str_raw_expr) is str) 
        assert(type(str_comment)  is str) 
        
        TEXT_TERMS.append(TextTerm(str_raw_expr, str_comment)) 

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

        # -- run fptaylor -- 
        tft_utils.checkFPTaylorInstallation("master") 
        cfg_first = os.environ["HOME_FPTAYLOR"] + "/" + tft_utils.FPT_CFG_FIRST 
        assert(os.path.isfile(cfg_first)) 

        command_fpt = os.environ["FPTAYLOR"] + " -c " + cfg_first + " " + FNAME_FPT_QUERY 

        exe_fpt = subp.Popen(command_fpt, shell=True, stdout=subp.PIPE, stderr=subp.PIPE) 

        fpt_outputs = [] 
        for aline in exe_fpt.stdout: 
            aline = tft_utils.Bytes2String(aline) 
            if (VERBOSE): 
                print (aline) 
            fpt_outputs.append(aline) 

        exe_fpt.communicate() 

        # -- read result file -- 
        ParseFPTaylorResults(cstr_expr, vs, fpt_outputs) 

    return CACHE_TEXT_TERMS[cstr_expr] 




