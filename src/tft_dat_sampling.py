
import os
import sys 
import time 
import random 

from fractions import Fraction

import tft_utils 
import tft_tuning 
import tft_alloc 
import tft_expr 
import tft_parser 
import tft_sol_exprs 

import tft_dat_def as DEF 


# ========
# global variables 
# ========
# -- variables for expr file generation -- 
FNAME_EXPRS = None 
FILE_PREFIX = []
FILE_GID2EPSS = {} 
FILE_POSTFIX = [] 

# -- verbose -- 
VERBOSE = True 


# ========
# misc routines 
# ========
# ==== decide if printing domain sampling progress or not ==== 
def domainSampleProgress (s, N_Samples): 
    assert(type(s) is int) 
    assert(type(N_Samples) is int) 
    assert((0 <= s) and (s < N_Samples)) 

    this_prog = int (float(s)/float(N_Samples) * 100.0)
    next_prog = int (float(s+1)/float(N_Samples) * 100.0) 

    if ((this_prog == 0) or (this_prog < next_prog)): 
        return True 
    else:
        return False 

# ==== generate exprs file name which works for a certain input (sub-)domain ====
def FNameExprs (fname, index): 
    assert(os.path.isfile(fname)) 
    assert(type(index) is int) 
    assert(index >= 0) 
    assert(fname.endswith(".exprs")) 

    return fname[0:len(fname)-6] + "." + str(index) + ".exprs"


# ======== 
# load exprs 
# ======== 
def LoadExprsFile (fname): 
    global FNAME_EXPRS
    global FILE_PREFIX
    global FILE_GID2EPSS 
    global FILE_POSTFIX 

    assert(fname.endswith(".exprs")) 
    FNAME_EXPRS = fname 

    f_stage = "prefix" 
    efile = open(fname, "r") 
    for aline in efile: 
        # decide loading stage 
        if (aline.strip() == "var-ranges:"): 
            assert(f_stage == "prefix") 
            f_stage = "var-ranges" 
            continue 

        elif (aline.strip() == "group-epsilons:"): 
            assert(f_stage == "var-ranges") 
            f_stage = "group-epsilons" 
            continue 

        elif (aline.strip() == "eq-gids:"): 
            assert(f_stage == "group-epsilons") 
            f_stage = "postfix" 
            FILE_POSTFIX.append("\n")

        else: 
            pass 

        # handle based on stage 
        if (f_stage == "prefix"):
            FILE_PREFIX.append(aline) 

        elif (f_stage == "var-ranges"):
            if (aline.strip() != ""): 

                ve = tft_parser.String2BoundedVariableExpr(aline.strip()) 
                assert(ve.label() not in DEF.VNames) 
            
                if (not tft_expr.isConstVar(ve)): 
                    DEF.VarExprs.append(ve) 
                    DEF.VNames.append(ve.label()) 
                    DEF.VRanges.append((float(ve.lb().value()), float(ve.ub().value()))) 

        elif (f_stage == "group-epsilons"): 
            if (aline.strip() != ""): 
                tokens = tft_utils.String2Tokens(aline.strip(), ":") 
                assert(len(tokens) == 2) 

                gid = int(tokens[0]) 
                epss = tokens[1] 

                assert(gid not in FILE_GID2EPSS.keys()) 
                FILE_GID2EPSS[gid] = epss

        elif (f_stage == "postfix"): 
            FILE_POSTFIX.append(aline) 

        else:
            assert(False) 

    efile.close()

    # generate N_Var_Intervals 
    DEF.assert_VNames() 
    DEF.assert_VRanges() 
    DEF.N_Var_Intervals = [DEF.N_Partitions for i in range(0, len(DEF.VNames))] 


# ======== 
# write exprs 
# ======== 
def WriteExprsFile (fname, ipart, alloc = None): 
    assert(len(ipart) == len(DEF.VNames))
    assert((alloc is None) or isinstance(alloc, tft_alloc.Alloc)) 

    for i in range(0, len(DEF.VNames)): 
        assert(len(ipart[i]) == 2) 
        assert((DEF.VRanges[i][0] <= ipart[i][0]) and (ipart[i][0] <= ipart[i][1]) and (ipart[i][1] <= DEF.VRanges[i][1]))
    if (os.path.isfile(fname)): 
        os.system("rm " + fname) 

    efile = open(fname, "w")
    
    # write prefix 
    for i in range(0, len(FILE_PREFIX)): 
        efile.write(FILE_PREFIX[i]) 

    # write var-ranges 
    efile.write("var-ranges:\n") 
    for i in range(0, len(DEF.VNames)): 
        efile.write(DEF.VNames[i] + " in [" + str(ipart[i][0]) + ", " + str(ipart[i][1]) + "]\n") 
    efile.write("\n")

    # write group epsilons 
    efile.write("group-epsilons:\n") 
    for gid,epss in FILE_GID2EPSS.items(): 
        if ((alloc is not None) and (gid in alloc.gid2eps.keys())): 
            epss = "[" + DEF.HDLValue2EPSString(DEF.EPS2HDLValue(alloc.gid2eps[gid])) + "]" 
        efile.write(str(gid) + " : " + epss + "\n") 
    
    # write postfix 
    for i in range(0, len(FILE_POSTFIX)): 
        efile.write(FILE_POSTFIX[i]) 
    
    efile.close() 


# ========
# generate training data 
# ========
def SamplePartitions(): 
    assert(FNAME_EXPRS is not None)
    assert(DEF.N_Samples > 0) 
    assert((0 < DEF.RATE_Trains_Samples) and (DEF.RATE_Trains_Samples < 1)) 

    last_prog = -1 

    print ("==== tuning for input sub-domains ====") 

    file_parts = open(DEF.FNAME_Partitions, "w") 
    file_fa = open(DEF.FNAME_Feature_Allocation, "w") 

    assert(not file_parts.closed)
    assert(not file_fa.closed) 

    s = 0 
    max_n_retries = 10 
    n_retries = 0 

    tstamp = time.time() 
    
    while (True): 
        # prevent failing 
        if (n_retries >= max_n_retries): 
            sys.exit("WARNING: Failed to sample a valid partition within " + str(max_n_retries) + " trials...")

        # print out sampling progress 
        this_prog = int(float(s)/float(DEF.N_Samples)*100.0) 
        if (VERBOSE and (last_prog < this_prog)): 
            sys.stdout.write("\rDomain Sampling Progress: {}% ".format(float(this_prog)))
            sys.stdout.flush() 
            last_prog = this_prog 

        # sample a sub-domain 
#        print ("-- dat_sampling.py: go sampling a sub-domain") 
        this_dvec = DEF.SampleInputPartitionVec(s)
        this_part = DEF.SampleInputPartitionFromVec(this_dvec)

        # make the corresponding feature of the input partition 
        this_feature = DEF.InputPartition2Feature([DEF.Feature_Option, []], this_dvec)

        # check redundency 
        # NOTE: we currently don't check redundency... 

        # ==== solve alloc. ====
        this_eforms = None 
        this_alloc  = None 
#        print ("-- dat_sampling.py: go solve the alloc") 

        # -- reuse eforms -- 
        if (DEF.REUSE_EFORMS): 
            assert(DEF.BASE_EFORMS is not None) 

            # solve alloc. 
            tft_tuning.TFTSystemReset() 
            DEF.RewriteVarBounds(this_part) 
            this_eforms, this_alloc = tft_sol_exprs.SolveErrorForms(DEF.BASE_EFORMS, tft_tuning.OPTIMIZERS) 

        # -- not reusing eforms -- 
        else: 
            fname_part = FNameExprs(FNAME_EXPRS, s) 
            WriteExprsFile(fname_part, this_part) 

            # solve alloc. 
            tft_tuning.TFTSystemReset() 
            this_eforms, this_alloc = tft_sol_exprs.SolveExprs(fname_part, tft_tuning.OPTIMIZERS) 
            os.system("rm " + fname_part) 

        if (this_alloc is None): 
            print ("WARNING: failed to solve a certain partition (no alloc. found)") 
            n_retries = n_retries + 1 
            continue

        assert(this_eforms is not None) 

        # record the mapping of feature -> allocation 
        file_fa.write(str(this_feature) + " : " + this_alloc.shortString() + "\n") 

        # write partitions 
        for i in range(0, len(this_part)): 
            assert(len(this_part[i]) == 2) 
            assert(this_part[i][0] <= this_part[i][1]) 
            file_parts.write(str(this_part[i][0]) + "~" + str(this_part[i][1]) + " ") 
        file_parts.write("\n") 
    
        # -- some finalizing work for this sample --
        s = s + 1 
        n_retries = 0 

        if (int(s) % 100 == 0): 
            print ("Time spent for 100 trains: " + str(time.time() - tstamp)) 
            tstamp = time.time() 
        
        assert(s <= DEF.N_Samples) 
        if (s == DEF.N_Samples): 
            break 

    if (VERBOSE): 
        print ("")    

    file_parts.close() 
    file_fa.close() 

    # -- possibly shuffles the samples -- 
    # if (DEF.Sampling_Shuffle): 
    if (DEF.Sampling_Method in ["1d", "2d", "3d"]): 
        parts = [] 
        fas = [] 

        file_parts = open(DEF.FNAME_Partitions, "r") 
        file_fa = open(DEF.FNAME_Feature_Allocation, "r")

        # read partitions 
        for aline in file_parts: 
            aline = aline.strip() 

            if (aline == ""): 
                continue 

            parts.append(aline) 

        file_parts.close() 

        # read feature-allocation 
        for aline in file_fa: 
            aline = aline.strip() 

            if (aline == ""): 
                continue 

            fas.append(aline) 

        file_fa.close() 

        assert(len(parts) == len(fas)) 

        # shuffle the partiions and the feature-allocation pairs 
        for i in range(0, len(parts)): 
            t = random.randint(0, len(parts)-1) 
            
            pt_temp = parts[0]
            fa_temp = fas[0]

            parts[0] = parts[t]
            fas[0]   = fas[t] 

            parts[t] = pt_temp
            fas[t]   = fa_temp 

        assert(len(parts) == len(fas)) 

        # write back the results 
        file_parts = open(DEF.FNAME_Partitions, "w") 
        file_fa = open(DEF.FNAME_Feature_Allocation, "w") 

        for i in range(0, len(parts)): 
            file_parts.write(parts[i] + "\n") 
            file_fa.write(fas[i] + "\n") 

        file_parts.close() 
        file_fa.close() 


        
        




