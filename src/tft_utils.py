
import os 
import sys 
from fractions import Fraction 


# ======== 
# global variables 
# ========
FPT_CFG_FIRST   = "__first.cfg" 
FPT_CFG_VERIFY  = "__verify.cfg" 
FPT_CFG_VERIFY_DETAIL_GELPIA = "__verify.detail.gelpia.cfg" 
FPT_CFG_VERIFY_DETAIL_BB     = "__verify.detail.bb.cfg"

N_MAX_CASTINGS  = None

FPTUNER_VERBOSE = False
FPTUNER_DEBUG   = False

FIX_CONST_TYPE  = False

GOPT_TIMEOUT    = 120 
GOPT_TOLERANCE  = 5e-02 


if sys.stdout.isatty():
    USE_COLOR_TEXT  = True
else:
    USE_COLOR_TEXT  = False

NO_M2_CHECK     = False


OPT_METHODS = ["max-benefit", "min-penalty"]
OPT_METHOD  = "max-benefit"

TIME_PARSING           = None
TIME_FIRST_DERIVATIVES = None
TIME_GLOBAL_OPT        = None
TIME_ALLOCATION        = None
TIME_CHECK_M2          = None 



# ========
# The following color printing code is provided by Ian Briggs.
# Thanks to his support!
# ========
def color_text(color_code, text):
    assert(type(color_code) is str and
           type(text) is str)
    
    if (USE_COLOR_TEXT): 
        return "{}{}{}".format(color_code, text, "\x1b[0m")
    else:
        return text

def txblack(text):
    return color_text("\x1b[30m", text)

def txred(text):
    return color_text("\x1b[31m", text)

def txgreen(text):
    return color_text("\x1b[32m", text)

def txyellow(text):
    return color_text("\x1b[33m", text)

def txblue(text):
    return color_text("\x1b[34m", text)

def txmagenta(text):
    return color_text("\x1b[35m", text)

def txcyan(text):
    return color_text("\x1b[36m", text)

def txwhite(text):
    return color_text("\x1b[37m", text)

def tx32bit(text):
    return txgreen(text)

def tx64bit(text):
    return txblue(text)

def tx128bit(text):
    return txred(text) 



# ========
# routines 
# ========
def VerboseMessage (mess): 
    assert(type(mess) is str) 
    if (FPTUNER_VERBOSE): 
        print ("[FPTuner]: " + mess) 

def DebugMessage (mess): 
    assert(type(mess) is str) 
    if (FPTUNER_DEBUG): 
        print ("[FPTuner-debug]: " + mess)


def checkGelpiaInstallation(branch): 
    if ("GELPIA_PATH" in os.environ): 
        if ("GELPIA" in os.environ): 
            return os.path.isfile(os.environ["GELPIA"]) 
        return False 
    return False 


def checkFPTaylorInstallation(branch): 
    if ("FPTAYLOR_BASE" in os.environ): 
        if ("FPTAYLOR" in os.environ): 
            if (not os.path.isfile(os.environ["FPTAYLOR"])): 
                return False 
            if (not os.path.isfile(os.environ["FPTAYLOR_BASE"] + "/" + FPT_CFG_FIRST)): 
                return False 
            if (not os.path.isfile(os.environ["FPTAYLOR_BASE"] + "/" + FPT_CFG_VERIFY)):
                return False 
            if (not os.path.isfile(os.environ["FPTAYLOR_BASE"] + "/" + FPT_CFG_VERIFY_DETAIL_GELPIA)):
                return False 
            if (not os.path.isfile(os.environ["FPTAYLOR_BASE"] + "/" + FPT_CFG_VERIFY_DETAIL_BB)):
                return False 
            return True 
        return False 
    return False 



# ==== 
def absFracBounds (fbs): 
    assert(len(fbs) == 2) 
    assert(isinstance(fbs[0], Fraction)) 
    assert(isinstance(fbs[1], Fraction)) 
    assert(fbs[0] <= fbs[1]) 

    if (fbs[1] <= Fraction(0, 1)): 
        return (fbs[1], (fbs[0] * Fraction(-1, 1))) 
    elif (fbs[0] >= Fraction(0, 1)): 
        return fbs 
    else: 
        return (Fraction(0, 1), max((fbs[0] * Fraction(-1, 1)), fbs[1])) 

# ====
def joinBounds (fbs0, fbs1): 
    assert(len(fbs0) == 2) 
    assert(len(fbs1) == 2) 
    assert(isinstance(fbs0[0], Fraction) and isinstance(fbs0[1], Fraction)) 
    assert(fbs0[0] <= fbs0[1]) 
    assert(isinstance(fbs1[0], Fraction) and isinstance(fbs1[1], Fraction)) 
    assert(fbs1[0] <= fbs1[1]) 

    new_fbs = (max(fbs0[0], fbs1[0]), min(fbs0[1], fbs1[1])) 
    if (new_fbs[0] > new_fbs[1]): 
        sys.exit("ERROR: invalid joinBounds from " + str(fbs0) + " and " + str(fbs1) + " ==>> " + str(new_fbs)) 
    return new_fbs 

# ====
def unionSets (s0, s1): 
    ret = s0[:] 
    for e in s1: 
        if (e not in ret): 
            ret.append(e)
    return ret 
def intersectSets (s0, s1): 
    ret = [] 
    for e in s0: 
        if (e in s1): 
            ret.append(e) 
    return ret 
def setMinus (s0, s1): 
    ret = s0[:]
    for e in s1: 
        if (e in ret): 
            ret.remove(e) 
    return ret 


# ==== stirng to tokens ==== 
# i.e. "jenny   wfchiang   family" -> ["jenny", "wfchiang", "family"] 
def String2Tokens (data, seperator = " "): 
    # generate tokens 
    raw_tokens = data.split(seperator) 
    tokens = [] 
    for ti in range(0, len(raw_tokens)): 
        this_token = raw_tokens[ti].strip()
        if (this_token != ""): 
            tokens.append(this_token) 
    return tokens 

def String2VLabelVRange (data): 
    tokens = String2Tokens(data, "in")
    assert(len(tokens) == 2)
    vlabel = tokens[0] 
    assert(tokens[1].startswith("[") and tokens[1].endswith("]")) 
    tokens = String2Tokens(tokens[1][1:len(tokens[1])-1], ",")
    assert(len(tokens) == 2) 
    vlb = float(tokens[0]) 
    vub = float(tokens[1]) 
    assert(vlb <= vub) 

    return [vlabel, [vlb, vub]] 


# ==== string convertions ==== 
def String2Bool (s): 
    assert(isinstance(s, str)) 
    if (s in ["True", "true", "T", "t", "y"]):
        return True 
    elif (s in ["False", "false", "F", "f", "n"]): 
        return False 
    else: 
        print ("ERROR: invalid argument for String2Bool : " + s)
        assert(False) 

def String2Float (s): 
    assert(isinstance(s, str)) 
    try: 
        ret = float(s) 
    except: 
        print ("ERROR: invalid argument for String2Float : " + s)
        assert(False) 
    return ret 

def String2Int (s): 
    assert(isinstance(s, str)) 
    try: 
        ret = int(s) 
    except: 
        print ("ERROR: invalid argument for String2Int : " + s)
        assert(False) 
    return ret     

def Bytes2String (bs, encode_mode = "utf-8"): 
    assert(type(bs) is bytes) 
    
    return bs.decode(encode_mode).strip() 


# ==== extract file ==== 
def File2Strings (fname, remove_empty=False): 
    assert(os.path.isfile(fname))

    istrings = [] 

    ifile = open(fname, "r") 

    for aline in ifile: 
        aline = aline.strip() 

        if (remove_empty): 
            if (aline == ""): 
                continue 

        istrings.append(aline) 

    ifile.close() 

    return istrings 



# ==== check the equivalent of two mappings 
def isSameMap (map1 = {}, map2 = {}): 
    for k,v in map1.items(): 
        if (k not in map2.keys()): 
            return False 
        if (not (v == map2[k])): 
            return False 
    for k,v in map2.items(): 
        if (k not in map1.keys()): 
            return False 
        if (not (v == map1[k])): 
            return False 
    return True



# ==== inf value exception (class)
class InfValueException (Exception):
    pass



