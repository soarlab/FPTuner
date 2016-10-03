
import os 
import sys 
import math 
from fractions import Fraction 
import tft_utils 
import tft_expr 

EPSILON_16  = Fraction(1, int(math.pow(2, 10))) 
AVX_RE_23   = Fraction(1, int(math.pow(2, 23))) 
EPSILON_32  = Fraction(1, int(math.pow(2, 24))) 
AVX_RE_28   = Fraction(1, int(math.pow(2, 28))) 
EPSILON_64  = Fraction(1, int(math.pow(2, 53))) 
EPSILON_128 = Fraction(1, int(math.pow(2, 113)))
ZERO = Fraction(0, 1) 


# ========
# class declaration 
# ========
class Epsilon: 
    value = None 
    label_alloc = None 
    label_string = None 

    def __init__ (self, v, la, ls): 
        assert(isinstance(v, Fraction)) 
        assert(type(la) is str) 
        assert(type(ls) is str) 

        self.value = v 
        self.label_alloc = la
        self.label_string = ls 

EPSILONS = [] 
# EPSILONS.append(Epsilon(ZERO,        "ZERO",        "0.0")) 
EPSILONS.append(Epsilon(EPSILON_128, "EPSILON_128", "e128"))
EPSILONS.append(Epsilon(EPSILON_64,  "EPSILON_64",  "e64")) 
# EPSILONS.append(Epsilon(AVX_RE_28,   "AVX_RE_28",   "avx-re-28"))
EPSILONS.append(Epsilon(EPSILON_32,  "EPSILON_32",  "e32")) 
# EPSILONS.append(Epsilon(AVX_RE_23,   "AVX_RE_23",   "avx-re-23"))
EPSILONS.append(Epsilon(EPSILON_16,  "EPSILON_16",  "e16")) 

assert(all([(EPSILONS[e-1].value <= EPSILONS[e].value) for e in range(1, len(EPSILONS))]))



# ========
# sub-routines 
# ========
def EpsValues (): 
    return [ EPSILONS[ii].value for ii in range(0, len(EPSILONS)) ]

def EpsLabels_Alloc (): 
    return [ EPSILONS[ii].label_alloc for ii in range(0, len(EPSILONS)) ]

def EpsLabels_String (): 
    return [ EPSILONS[ii].label_string for ii in range(0, len(EPSILONS)) ]

def ReaderString2Eps (rs): 
    assert(type(rs) is str) 
    try: 
        i = EpsLabels_Alloc().index(rs) 
        return EPSILONS[i].value

    except ValueError: 
        return Fraction(rs) 
    
def Eps2ReaderString (eps): 
    assert(isinstance(eps, Fraction)) 
    try: 
        i = EpsValues().index(eps) 
        return EPSILONS[i].label_alloc 
    
    except ValueError: 
        return str(float(eps)) 

def ConstantExprs2Fractions (ces): 
    assert(all([isinstance(ces[i], tft_expr.ConstantExpr) for i in range(0, len(ces))])) 
    return [Fraction(ces[i].value()) for i in range(0, len(ces))]



# ========
# class 
# ======== 
class Alloc:    
    # Note that this is a mapping of GID/ErrorTerms to Fractions... I know that it should be GID/ErrorTerms to ConstantExprs... But let's leave it as this for now... 
    gid2eps = None # GID to eps

    score = None 

    def __init__ (self): 
        self.gid2eps = {} 
        self.score = None 

    def copy (self): 
        ret = Alloc() 
        ret.gid2eps = self.gid2eps.copy()

        return ret 

    def __eq__ (self, rhs): 
        assert(isinstance(rhs, Alloc)) 

        if (len(self.gid2eps) != len(rhs.gid2eps)): 
            return False 

        for gid,eps in self.gid2eps.items(): 
            if (gid not in rhs.gid2eps.keys()): 
                return False 
            if (rhs.gid2eps[gid] != eps): 
                return False 

        return True 
        
    def __setitem__ (self, gid, eps): 
        assert((type(gid) is int) and (gid >= 0)) 
        assert(type(eps) is Fraction) 

        if (gid in self.gid2eps.keys()): 
            assert(eps == self.gid2eps[gid]) 
        else:
            self.gid2eps[gid] = eps 

    def __getitem__ (self, gid): 
        assert(type(gid) is int) 

        assert(0 <= gid) 
        
        assert(gid in self.gid2eps.keys())
        return self.gid2eps[gid] 

    def isAssigned (self, gid): 
        assert(type(gid) is int) 

        assert(0 <= gid) 

        return (gid in self.gid2eps.keys()) 

    def __str__ (self): 
        str_ret = "---- alloc. ----\n" 

        if (tft_utils.FPTUNER_VERBOSE): 
            str_ret = str_ret + "Score: " 
            if (self.score is None): 
                str_ret = str_ret + "not set...\n" 
            else:
                str_ret = str_ret + str(self.score) + "\n" 

#        str_ret = str_ret + "-- GIDs --\n"
        gids = sorted(self.gid2eps.keys(), key = lambda g : g) 
        for gid in gids: 
            assert(0 <= gid) 

            eps = self.gid2eps[gid] 

            etname = "Group " + str(gid)
            str_eps = Eps2ReaderString(eps)
            if   (str_eps == "EPSILON_32"): 
                str_ret = str_ret + etname + " : 32-bit\n"
            elif (str_eps == "EPSILON_64"): 
                str_ret = str_ret + etname + " : 64-bit\n"
            elif (str_eps == "EPSILON_128"):
                str_ret = str_ret + etname + " : 128-bit\n"
            else:
                sys.exit("Error: unknown bit-width candidate " + str_eps)

        str_ret = str_ret + "----------------\n"
        return str_ret 

    def loadFromStringFile (self, sname): 
        sfile = open(sname, "r") 

        for aline in sfile: 
            aline = aline.strip()

            et_prefix = "ErrorTerm(gid: " 

            if (aline.startswith(et_prefix)): 
                id_gid_end = aline.find(")") 
                assert(id_gid_end > len(et_prefix)) 
                
                gid = int(aline[len(et_prefix):id_gid_end]) 

                assert(gid not in self.gid2eps.keys()) 

                id_eps_start = aline.find("=>") 
                assert(id_gid_end < id_eps_start) 

                eps = ReaderString2Eps(aline[id_eps_start+2:].strip()) 

                self.gid2eps[gid] = eps 

        sfile.close() 

    def shortString (self): 
        str_ret = "" 
        
        for gid,eps in self.gid2eps.items(): 
            str_ret = str_ret + str(gid) + ">" + str(eps) + " " 

        return str_ret.strip() 

    def loadFromShortString (self, ss): 
        tokens = tft_utils.String2Tokens(ss, " ") 
        
        for gid_eps in tokens: 
            ts = tft_utils.String2Tokens(gid_eps, ">") 
            assert(len(ts) == 2) 

            gid = int(ts[0]) 
            eps = Fraction(ts[1]) 
            
            assert(gid not in self.gid2eps.keys())
            self.gid2eps[gid] = eps         

    def queryByExpr (self, expr): 
        assert(isinstance(expr, tft_expr.Expr)) 

        gid = expr.getGid() 
        assert(type(gid) is int) 
        assert(0 <= gid) 

        assert(gid in self.gid2eps.keys()) 
        ret_eps = self.gid2eps[gid] 

        assert(ret_eps is not None) 
        assert(isinstance(ret_eps, Fraction)) 
        return ret_eps 




        


        
        
        
        
            



