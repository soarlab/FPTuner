
import os 
import sys 
from fractions import Fraction 


# ========
# routines 
# ========
def checkGelpiaInstallation(branch): 
    if ("HOME_GELPIA" in os.environ): 
        if ("GELPIA" in os.environ): 
            return os.path.isfile(os.environ["GELPIA"]) 
        return False 
    return False 


def checkFPTaylorInstallation(branch): 
    if ("HOME_FPTAYLOR" in os.environ): 
        if ("FPTAYLOR" in os.environ): 
            assert(os.path.isfile(os.environ["FPTAYLOR"]))
            
            cfg_default = os.environ["HOME_FPTAYLOR"] + "/default.cfg"
            assert(cfg_default) 

            cfg_first  = os.environ["HOME_FPTAYLOR"] + "/__first.cfg" 
            cfg_verify = os.environ["HOME_FPTAYLOR"] + "/__verify.cfg" 
            
            os.system("cp " + cfg_default + " " + cfg_first) 
            os.system("cp " + cfg_default + " " + cfg_verify) 

            # modify for cfg_first 
            f_cfg_first = open(cfg_first, "a") 
            
            f_cfg_first.write("abs-error=false\n") 
            f_cfg_first.write("rel-error=false\n") 
            
            f_cfg_first.close() 

            # modify for cfg_verify 
            f_cfg_verify = open(cfg_first, "a") 
            
            f_cfg_verify.write("abs-error=true\n") 
            f_cfg_verify.write("rel-error=false\n") 
            
            f_cfg_verify.close() 

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
    for k,v in map1.iteritems(): 
        if (k not in map2.keys()): 
            return False 
        if (not (v == map2[k])): 
            return False 
    for k,v in map2.iteritems(): 
        if (k not in map1.keys()): 
            return False 
        if (not (v == map1[k])): 
            return False 
    return True 



