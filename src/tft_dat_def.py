
import os
import sys
import math
import random
from fractions import Fraction

import tft_expr
import tft_utils
import tft_alloc

# ========
# global variables
# ========
# -- for performance improvement --
REUSE_EFORMS        = True
BASE_EFORMS         = None

# -- some constants: decided by the config file --
N_Samples           = -1
N_CTT_Samples       = None
N_Clusters          = -1
N_Partitions        = -1
RATE_Trains_Samples = 0.8

VarExprs            = []
VNames              = []
VRanges             = []

N_Var_Intervals     = None

# -- book keeping for mappings of domain to various things
FNAME_Partitions    = "__tft_partitions"
FNAME_Feature_Allocation = "__tft_feature_allocation"

# -- for converting alloc to feature --
GID_HDLID         = None # mapping of GID to the label id in a high-dimension (HD) label
HDLID_GID         = None
DIM_HDL           = 0 # counter for the dimension of a HD label

FNAME_HDLID_GID   = "__tft_hdlid_gid"

# -- for mergeing cluster allocations --
FNAME_CID_HDLabel = "__tft_cid_hdlabel"
CID_HDLabel       = None
FNAME_CID_Training_Counts = "__tft_cid_training_counts"
CID_Training_Counts       = None

# -- verbose --
VERBOSE = False

# -- switches of the DAT steps --
STEP_SAMPLE       = True
STEP_CLUSTER      = True
STEP_TRAIN        = True
STEP_TEST         = True

# -- sampling options --
Available_Sampling_Methods = ["random", "1d", "2d", "3d"]
Sampling_Method   = "random"
Sampling_Shuffle  = True

# -- feature option --
Available_Feature_Options = ["part-ids", "mids", "pid-1d", "pid-2d", "richardson", "horner-low", "horner-high", "horner-both", "jp", "dot-product", "dot-product-1", "bal-reduction", "jacobi-2d", "fdtd-2d"]
Feature_Option            = None

# -- for svm --
AVAILABLE_MODES = ["arbitrary", "cv", "decision-tree", "random-uniform", "random-bias"]
# TRAIN_MODE = "cv"
# TEST_MODE = "cv"
TRAIN_MODE      = "decision-tree"
TEST_MODE       = "decision-tree"

SVM_MODEL                       = None
FNAME_SVM_MODEL                 = "tft_svm_model"
FNAME_SVM_TRAIN_FEATURE_CLUSTER = "tft_train_feature2cluster"
FNAME_SVM_TEST_FEATURE_CLUSTER  = "tft_test_feature2cluster"

# -- for decision tree --
DT_MODEL                        = None
DT_ROOT                         = None
DT_FLABELS                      = None
FNAME_CSV_TRAIN_FEATURE_CLUSTER = FNAME_SVM_TRAIN_FEATURE_CLUSTER + ".csv"
FNAME_CSV_TEST_FEATURE_CLUSTER  = FNAME_SVM_TEST_FEATURE_CLUSTER + ".csv"
FNAME_SVM_TEST                  = "tft_svm_test"


# ========
# misc routines
# ========
def isTrainingID (i, size_all):
    assert(type(i) is int)
    assert(type(size_all) is int)
    assert(0 <= i)
    assert(i < size_all)
    assert((0 < RATE_Trains_Samples) and (RATE_Trains_Samples < 1))
    if (i < (float(RATE_Trains_Samples) * float(size_all))):
        return True

def isTypedList (t, l=[]):
    assert((t is int) or (t is float) or (t is str))
    assert(len(l) > 0)
    return all([(type(i) is t) for i in l])

def checkValidPartitions (n_vs, parts = []):
    assert(0 < n_vs)
    assert(len(parts) == n_vs)
    assert(all([((len(parts[i]) == 2) and (parts[i][0] <= parts[i][1])) for i in range(0, n_vs)]))

def getMidsFromPartitions (n_vs, parts = []):
    checkValidPartitions(n_vs, parts)
    return [((parts[i][0] + parts[i][1]) / 2.0) for i in range(0, n_vs)]

def assert_VNames ():
    assert(isTypedList(str, VNames))
    assert(len(VNames) > 0)

def assert_N_Var_Intervals ():
    assert_VNames()
    assert(len(VNames) == len(N_Var_Intervals))
    assert(isTypedList(int, N_Var_Intervals))
    assert(all([(0 < e) for e in N_Var_Intervals]))

def assert_VRanges ():
    assert_VNames()
    assert(len(VNames) == len(VRanges))
    for bds in VRanges:
        assert(len(bds) == 2)
        vlb = bds[0]
        vub = bds[1]
        assert((type(vlb) is float) and (type(vub) is float))
        assert(vlb <= vub)

def MatrixRead (D, x, y, m = []):
    assert((type(D) is int) and (type(x) is int) and (type(y) is int))
    assert(len(m) == D * D)
    assert((0 <= x) and (x < D))
    assert((0 <= y) and (y < D))

    return m[x*D + y]



# ========
# converting an epsilon to a label in a HD label
# ========
def EPS2HDLValue (eps):
    assert(isinstance(eps, Fraction))
    try:
        i = tft_alloc.EpsValues().index(eps)
        return i

    except ValueError:
        sys.exit("ERROR: not supporting argument for EPS2FID: " + str(eps))

def HDLValue2EPSString (f):
    assert(type(f) is int)
    assert(f in range(0, len(tft_alloc.EPSILONS)))

    return tft_alloc.EPSILONS[f].label_string

def HDLValue2EPS (i):
    assert(type(i) is int)
    assert(i in range(0, len(tft_alloc.EPSILONS)))

    return tft_alloc.EPSILONS[i].value

def MergeHDLValueTowardTop(f0, f1):
    assert(type(f0) is int)
    assert(type(f1) is int)
    assert((0 <= f0) and (0 <= f1))
    return min(f0, f1)


# ========
# converting an alloc. to a HD label
# converting a HD label to an alloc.
# ========
def Alloc2HDLabel (alloc):
    global GID_HDLID
    global HDLID_GID
    global DIM_HDL

    assert(isinstance(alloc, tft_alloc.Alloc))

    gid2eps = alloc.gid2eps
    assert(gid2eps is not None)
    assert(len(gid2eps) > 0)

    first_alloc = (GID_HDLID is None)
    hd_label = []

    if (first_alloc):
        DIM_HDL = 0
        GID_HDLID = {}
        HDLID_GID = {}
    else:
        assert(DIM_HDL > 0)
        hd_label = [None for i in range(0, DIM_HDL)]


    for gid, eps in gid2eps.items():
        if (first_alloc):
            assert(gid not in GID_HDLID.keys())
            assert(len(hd_label) == DIM_HDL)

            GID_HDLID[gid] = DIM_HDL
            HDLID_GID[DIM_HDL] = gid
            hd_label.append(EPS2HDLValue(eps))
            DIM_HDL = DIM_HDL + 1

        else:
            assert(gid in GID_HDLID.keys())
            lid = GID_HDLID[gid]
            assert((0 <= lid) and (lid < DIM_HDL))

            hd_label[lid] = EPS2HDLValue(eps)

    assert(all([(hd_label[i] is not None) for i in range(0, DIM_HDL)]))
    return hd_label


def HDLabel2Alloc (hdl):
    assert(len(hdl) == DIM_HDL)
    assert(isTypedList(int, hdl))
    assert(HDLID_GID is not None)

    ret_alloc = tft_alloc.Alloc()

    for i in range(0, len(hdl)):
        assert(HDLID_GID[i] not in ret_alloc.gid2eps.keys())
        ret_alloc.gid2eps[HDLID_GID[i]] = HDLValue2EPS(hdl[i])

    return ret_alloc


# ========
# print-out utils
# ========
def PrintHDLabel (hdl):
    assert(len(hdl) == DIM_HDL)

    gids = GID_HDLID.keys()
    gids.sort()
    for gid in gids:
        id_hdlv = GID_HDLID[gid]
        assert((0 <= id_hdlv) and (id_hdlv < DIM_HDL))
        print ("group: " + str(gid) + " => " + HDLValue2EPSString(hdl[id_hdlv]))


# =======
# merge allocations toward TOP
# ========
def MergeHDLsTowardTop (hdl0, hdl1):
    if ((hdl0 is None) and (hdl1 is None)):
        return None
    elif (hdl0 is None):
        return hdl1[:]
    elif (hdl1 is None):
        return hdl0[:]
    else:
        assert(len(hdl0) == len(hdl1))
        len_hdl = len(hdl0)
        ret_hdl = [(MergeHDLValueTowardTop(hdl0[i], hdl1[i])) for i in range(0, len_hdl)]
        return ret_hdl


# ========
# Load DAT confs
# ========
def LoadDATConfig (fname_config):
    global N_Samples
    global N_CTT_Samples
    global N_Clusters
    global N_Partitions
    global VERBOSE
    global Feature_Option
    global TRAIN_MODE
    global TEST_MODE
    global STEP_SAMPLE
    global STEP_CLUSTER
    global STEP_TRAIN
    global STEP_TEST
    global Sampling_Method

    fconf = open(fname_config, "r")

    for aline in fconf:
        aline = aline.strip()
        if (aline == ""):
            continue

        if (aline.startswith("#")):
            continue

        tokens = tft_utils.String2Tokens(aline, "=")
        assert(len(tokens) == 2)

        opt = tokens[0]
        val = tokens[1]

        if (opt.startswith("DAT_")):
            if (opt == "DAT_VERBOSE"):
                VERBOSE = tft_utils.String2Bool(val)
            elif (opt == "DAT_N_SAMPLES"):
                N_Samples = tft_utils.String2Int(val)
            elif (opt == "DAT_N_CTT_SAMPLES"):
                N_CTT_Samples = tft_utils.String2Int(val)
            elif (opt == "DAT_N_CLUSTERS"):
                N_Clusters = tft_utils.String2Int(val)
            elif (opt == "DAT_N_PARTITIONS"):
                N_Partitions = tft_utils.String2Int(val)
            elif (opt == "DAT_FEATURE_OPT"):
                Feature_Option = val

            elif (opt == "DAT_SAMPLING_METHOD"):
                Sampling_Method = val

            elif (opt == "DAT_STEP_SAMPLE"):
                STEP_SAMPLE  = tft_utils.String2Bool(val)
            elif (opt == "DAT_STEP_CLUSTER"):
                STEP_CLUSTER = tft_utils.String2Bool(val)
            elif (opt == "DAT_STEP_TRAIN"):
                STEP_TRAIN   = tft_utils.String2Bool(val)
            elif (opt == "DAT_STEP_TEST"):
                STEP_TEST    = tft_utils.String2Bool(val)

            elif (opt == "DAT_TRAIN_MODE"):
                TRAIN_MODE = val
            elif (opt == "DAT_TEST_MODE"):
                TEST_MODE = val

            else:
                sys.exit("ERROR: invalid DAT option: " + opt)
        else:
            pass

    fconf.close()

    # checking the correct of the settings
    assert(0 < N_Samples)
    assert(0 < N_Partitions)
    assert(Feature_Option in Available_Feature_Options)
    assert(Sampling_Method in Available_Sampling_Methods)


# ========
# routines of sampling input partitions
# ========
# ==== Sample Input Domain from the scratch ====
def SampleInputPartitionVec (sid=None):
    assert_N_Var_Intervals()
    assert(type(Feature_Option) is str)

    dvec = None

    if (Sampling_Method == "1d"):
        assert(len(VNames) == 1)
        assert(sid < N_Samples)
        assert(N_Samples <= N_Partitions)

        pid = int(round(float(sid) / float(N_Samples) * float(N_Partitions)))

        dvec = [ pid ]

    elif (Sampling_Method == "2d"):
        assert(len(VNames) == 2)
        assert(sid < N_Samples)
        assert(N_Samples <= (N_Partitions*N_Partitions))

        pid = int(round(float(sid) / float(N_Samples) * float(N_Partitions*N_Partitions)))

        pid_x = pid / N_Partitions
        pid_y = pid % N_Partitions

        dvec = [ pid_x, pid_y ]

    elif (Sampling_Method == "3d"):
        assert(len(VNames) == 3)
        assert(sid < N_Samples)
        assert(N_Samples <= (N_Partitions * N_Partitions * N_Partitions))

        pid = int(round(float(sid) / float(N_Samples) * float(N_Partitions*N_Partitions*N_Partitions)))

        pid_x = pid / (N_Partitions * N_Partitions)
        pid_y = (pid % (N_Partitions * N_Partitions)) / N_Partitions
        pid_z = (pid % (N_Partitions * N_Partitions)) % N_Partitions

        dvec = [pid_x, pid_y, pid_z]

    elif (Sampling_Method == "random"):
        dvec = [random.randint(0, N_Var_Intervals[i]-1) for i in range(0, len(VNames))]

    else:
        sys.exit("ERROR: unknown Sampling_Method")

    return dvec

# ==== Sample Input Domain from an id vector ====
def SampleInputPartitionFromVec (interval_ids = []):
    assert_VNames()
    assert_N_Var_Intervals()
    assert_VRanges()

    n_vs = len(VNames)
    assert(n_vs == len(interval_ids))
    assert(all([((0<= interval_ids[i]) and (interval_ids[i] < N_Var_Intervals[i])) for i in range(0, n_vs)]))

    ipart = []

    for i in range(0, n_vs):
        r = VRanges[i]
        gap = (r[1] - r[0]) / float(N_Var_Intervals[i]);
        assert(gap >= 0);

        lb = r[0] + gap * float(interval_ids[i])
        ub = lb + gap

        if (lb < r[0]):
            lb = r[0]
        if (ub > r[1]):
            ub = r[1]

        ipart.append([lb, ub])

    return ipart

def InverseSampleInputPartitionFromVec (ipart = []):
    assert_VNames()
    assert_N_Var_Intervals()
    assert_VRanges()

    n_vs = len(VNames)
    assert(n_vs == len(ipart))
    assert(all([((len(ipart[i]) == 2) and (VRanges[i][0] <= ipart[i][0]) and (ipart[i][0] <= ipart[i][1]) and (ipart[i][1] <= VRanges[i][1])) for i in range(0, n_vs)]))

    interval_ids = []

    for i in range(0, n_vs):
        r = VRanges[i]
        gap = (r[1] - r[0]) / float(N_Var_Intervals[i]);
        assert(gap >= 0)

        for iid in range(0, N_Var_Intervals[i]):
            if (abs((ipart[i][0] - (r[0] + (gap * iid)))) < (float(gap) / 10.0)):
                interval_ids.append(iid)
                break

    assert(n_vs == len(interval_ids))

    return interval_ids


# ==== Sample Input Domain ====
def SampleInputPartition (s=None):
    interval_ids = SampleInputPartitionVec(s)
    return SampleInputPartitionFromVec(interval_ids)

# ==== Rewrite var. bounds ====
def RewriteVarBounds (this_part = []):
    checkValidPartitions(len(VarExprs), this_part)

    for vi in range(0, len(VarExprs)):
        ve = VarExprs[vi]

        assert(len(this_part[vi]) == 2)
        assert(this_part[vi][0] <= this_part[vi][1])

        ve.lower_bound = None
        ve.upper_bound = None
        ve.setBounds(this_part[vi][0], this_part[vi][1])

        for v in tft_expr.ALL_VariableExprs:
            if (v == ve):
                v.lower_bound = ve.lb()
                v.upper_bound = ve.ub()



# ========
# input partition --> feature
# ========
def InputPartition2Feature (fopt, interval_ids = []):
    assert_VNames()
    assert_N_Var_Intervals()
    assert_VRanges()

    n_vs = len(VNames)
    assert(n_vs > 0)
    assert(all([((0<= interval_ids[i]) and (interval_ids[i] < N_Var_Intervals[i])) for i in range(0, n_vs)]))

    assert(len(fopt) == 2)
    assert(type(fopt[0]) is str)

    if (fopt[0] == "part-ids"):
        return interval_ids

    elif (fopt[0] == "mids"):
        this_part = SampleInputPartitionFromVec(interval_ids)

        mids = getMidsFromPartitions(n_vs, this_part)

        return mids

    elif (fopt[0] == "pid-1d"):
        assert(len(interval_ids) == 1)
        return interval_ids

    elif (fopt[0] == "pid-2d"):
        assert(len(interval_ids) == 2)
        return interval_ids

    elif (fopt[0] == "jp"):
        return interval_ids

    elif (fopt[0] in ["horner-low", "horner-high", "horner-both"]):
        this_part = SampleInputPartitionFromVec(interval_ids)

        mids = getMidsFromPartitions(n_vs, this_part)

        assert(n_vs >= 7)

        if (fopt[0] == "horner-low"):
            # return [mids[n_vs-2], mids[n_vs-3], mids[n_vs-4], mids[n_vs-5], mids[n_vs-6], mids[n_vs-1]]
            return [mids[n_vs-2], mids[n_vs-3], mids[n_vs-4], mids[n_vs-1]]
        if (fopt[0] == "horner-high"):
            return [mids[0], mids[1], mids[2], mids[3], mids[4], mids[n_vs-1]]
        if (fopt[0] == "horner-both"):
            return [mids[0], mids[1], mids[2], mids[n_vs-2], mids[n_vs-3], mids[n_vs-4], mids[n_vs-1]]

        assert(False)

    elif (fopt[0] == "richardson"):
        this_part = SampleInputPartitionFromVec(interval_ids)
        assert(len(this_part) == n_vs)

        vlen = 0
        while (True):
            ilen = (((vlen+1) * vlen) / 2) + (2 * vlen)
            assert(ilen <= n_vs)
            if (ilen == n_vs):
                break
            vlen = vlen + 1
        vlen2 = ((vlen+1) * vlen) / 2

        o_vecA = this_part[0:vlen2]
        o_vecb = this_part[vlen2:(vlen2+vlen)]
        o_vecx = this_part[(vlen2+vlen):(vlen2+2*vlen)]

        sum_A = 0
        sum_b = 0
        sum_x = 0

        vec_A = []
        vec_b = []
        vec_x = []
        vec_A_2 = []
        vec_b_2 = []
        vec_x_2 = []

        for i in range(0, vlen2):
            assert(len(o_vecA[i]) == 2)
            v = sum(o_vecA[i]) / 2.0
            sum_A = sum_A + v
            vec_A.append(abs(v))
            vec_A_2.append(v*v)
        ave_A = sum(vec_A) / float(len(vec_A))
        var_A = (sum(vec_A_2) / float(len(vec_A_2))) - (ave_A * ave_A)

        for i in range(0, vlen):
            assert(len(o_vecb[i]) == 2)
            v = sum(o_vecb[i]) / 2.0
            sum_b = sum_b + v
            vec_b.append(abs(v))
            vec_b_2.append(v*v)
        ave_b = sum(vec_b) / float(len(vec_b))
        var_b = (sum(vec_b_2) / float(len(vec_b_2))) - (ave_b * ave_b)

        for i in range(0, vlen):
            assert(len(o_vecx[i]) == 2)
            v = sum(o_vecx[i]) / 2.0
            sum_x = sum_x + v
            vec_x.append(abs(v))
            vec_x_2.append(v*v)
        ave_x = sum(vec_x) / float(len(vec_x))
        var_x = (sum(vec_x_2) / float(len(vec_x_2))) - (ave_x * ave_x)

        sum_A = sum_A / float(vlen2)
        sum_b = sum_b / float(vlen)
        sum_x = sum_x / float(vlen)
        return [sum_A, ave_A, var_A, sum_b, ave_b, var_b, sum_x, ave_x, var_x]

    elif (fopt[0] == "richardson-prev"):
        this_part = SampleInputPartitionFromVec(interval_ids)
        assert(len(this_part) == n_vs)

        vlen = 0
        while (True):
            ilen = (((vlen+1) * vlen) / 2) + (2 * vlen)
            assert(ilen <= n_vs)
            if (ilen == n_vs):
                break
            vlen = vlen + 1
        vlen2 = ((vlen+1) * vlen) / 2

        o_vecA = this_part[0:vlen2]
        o_vecb = this_part[vlen2:(vlen2+vlen)]
        o_vecx = this_part[(vlen2+vlen):(vlen2+2*vlen)]
        vec_A = []
        vec_b = []
        vec_x = []

        for e in o_vecA:
            assert(len(e) == 2)
            assert(e[0] <= e[1])
            if (0 <= e[0]):
                vec_A.append(e[0])
                vec_A.append(e[1])
            elif ((e[0] < 0) and (0 < e[1])):
                vec_A.append(0.0)
                vec_A.append(e[1])
            else:
                vec_A.append(abs(e[0]))
                vec_A.append(abs(e[1]))
        for e in o_vecb:
            assert(len(e) == 2)
            assert(e[0] <= e[1])
            if (0 <= e[0]):
                vec_b.append(e[0])
                vec_b.append(e[1])
            elif ((e[0] < 0) and (0 < e[1])):
                vec_b.append(0.0)
                vec_b.append(e[1])
            else:
                vec_b.append(abs(e[0]))
                vec_b.append(abs(e[1]))
        for e in o_vecx:
            assert(len(e) == 2)
            assert(e[0] <= e[1])
            if (0 <= e[0]):
                vec_x.append(e[0])
                vec_x.append(e[1])
            elif ((e[0] < 0) and (0 < e[1])):
                vec_x.append(0.0)
                vec_x.append(e[1])
            else:
                vec_x.append(abs(e[0]))
                vec_x.append(abs(e[1]))

        min_A = min(vec_A)
        ave_A = float(sum(vec_A)) / float(len(vec_A))
        max_A = max(vec_A)

        min_b = min(vec_b)
        ave_b = float(sum(vec_b)) / float(len(vec_b))
        max_b = max(vec_b)

        min_x = min(vec_x)
        ave_x = float(sum(vec_x)) / float(len(vec_x))
        max_x = max(vec_x)

        return [min_A, ave_A, max_A, min_b, ave_b, max_b, min_x, ave_x, max_x]

    elif (fopt[0] == "dot-product"):
        this_part = SampleInputPartitionFromVec(interval_ids)
        assert(int(n_vs) % 2 == 0)

        mids = getMidsFromPartitions(n_vs, this_part)

        assert(int(n_vs) % 16 == 0)
        gap = int(n_vs) / 16

        feats = []

        for i in range(0, 16):
            ave_mid = float(sum( mids[(i*gap) : (i*gap+gap)] )) / float(gap)
            feats.append(ave_mid)

        assert(len(feats) == 16)
        return feats

    elif (fopt[0] == "dot-product-1"):
        this_part = SampleInputPartitionFromVec(interval_ids)
        assert(len(this_part) == n_vs)
        assert(int(n_vs) % 2 == 0)
        assert(all([((len(this_part[i]) == 2) and (this_part[i][0] <= this_part[i][1])) for i in range(0, n_vs)]))

        mids = [abs((this_part[i][0] + this_part[i][1]) / 2.0) for i in range(0, n_vs)]

        return [(float(sum(mids)) / float(len(mids)))]

    elif (fopt[0] == "bal-reduction"):
        this_part = SampleInputPartitionFromVec(interval_ids)
        assert(len(this_part) == n_vs)
        assert(int(n_vs) % 2 == 0)
        assert(all([((len(this_part[i]) == 2) and (this_part[i][0] <= this_part[i][1])) for i in range(0, n_vs)]))

        mids = [((this_part[i][0] + this_part[i][1]) / 2.0) for i in range(0, n_vs)]

        assert(n_vs == 16)

        return mids

    elif (fopt[0] == "jacobi-2d"):
        this_part = SampleInputPartitionFromVec(interval_ids)

        mids = getMidsFromPartitions(n_vs, this_part)

        assert(int(math.sqrt(n_vs)) == math.sqrt(n_vs))
        dim = int(math.sqrt(n_vs))
        assert(dim % 4 == 0)
        dim_gap = int(dim / 4)

        feat = []

        for xx in range(0, 4):
            for yy in range(0, 4):
                ave = 0
                for x in range(0, dim_gap):
                    for y in range(0, dim_gap):
                        ave = ave + MatrixRead(dim, (xx*dim_gap+x), (yy*dim_gap+y), mids)
                ave = float(ave) / float(dim_gap * dim_gap)

                feat.append(ave)

        assert(len(feat) == 16)
        return feat

    elif (fopt[0] == "fdtd-2d"):
        this_part = SampleInputPartitionFromVec(interval_ids)

        mids = getMidsFromPartitions(n_vs, this_part)

        assert(n_vs % 3 == 0)
        size_matrix = int(n_vs / 3)
        assert(int(math.sqrt(size_matrix)) == math.sqrt(size_matrix))
        dim = int(math.sqrt(size_matrix))
        assert(dim % 4 == 0)
        dim_gap = int(dim / 4)

        mids_ex = mids[0 : size_matrix]
        mids_ey = mids[size_matrix : size_matrix*2]
        mids_hz = mids[size_matrix*2 : ]

        feat = []

        for xx in range(0, 4):
            for yy in range(0, 4):
                ave = 0
                for x in range(0, dim_gap):
                    for y in range(0, dim_gap):
                        ave = ave + MatrixRead(dim, (xx*dim_gap+x), (yy*dim_gap+y), mids_ex)
                ave = float(ave) / float(dim_gap * dim_gap)

                feat.append(ave)

        for xx in range(0, 4):
            for yy in range(0, 4):
                ave = 0
                for x in range(0, dim_gap):
                    for y in range(0, dim_gap):
                        ave = ave + MatrixRead(dim, (xx*dim_gap+x), (yy*dim_gap+y), mids_ey)
                ave = float(ave) / float(dim_gap * dim_gap)

                feat.append(ave)

        for xx in range(0, 4):
            for yy in range(0, 4):
                ave = 0
                for x in range(0, dim_gap):
                    for y in range(0, dim_gap):
                        ave = ave + MatrixRead(dim, (xx*dim_gap+x), (yy*dim_gap+y), mids_hz)
                ave = float(ave) / float(dim_gap * dim_gap)

                feat.append(ave)

        return feat

    elif (fopt[0] == "fdtd-2d-hz"):
        this_part = SampleInputPartitionFromVec(interval_ids)

        mids = getMidsFromPartitions(n_vs, this_part)

        assert(n_vs % 3 == 0)
        size_matrix = int(n_vs / 3)
        assert(int(math.sqrt(size_matrix)) == math.sqrt(size_matrix))
        dim = int(math.sqrt(size_matrix))
        assert(dim % 4 == 0)
        dim_gap = int(dim / 4)

        mids_ex = mids[0 : size_matrix]
        mids_ey = mids[size_matrix : size_matrix*2]
        mids_hz = mids[size_matrix*2 : ]

        feat = []

        for xx in range(0, 4):
            for yy in range(0, 4):
                ave = 0
                for x in range(0, dim_gap):
                    for y in range(0, dim_gap):
                        ave = ave + MatrixRead(dim, (xx*dim_gap+x), (yy*dim_gap+y), mids_hz)
                ave = float(ave) / float(dim_gap * dim_gap)

                feat.append(ave)

        return feat

    elif (fopt[0] == "jacobi-2d"):
        this_part = SampleInputPartitionFromVec(interval_ids)
        assert(len(this_part) == n_vs)
        assert(int(n_vs) % 2 == 0)
        assert(all([((len(this_part[i]) == 2) and (this_part[i][0] <= this_part[i][1])) for i in range(0, n_vs)]))

        mids = [((this_part[i][0] + this_part[i][1]) / 2.0) for i in range(0, n_vs)]

        assert(n_vs == 36)

        feat = []
        for xx in range(1, 5):
            for yy in range(1, 5):
                feat.append(mids[xx*6+yy])

        return feat

    else :
        sys.exit("ERROR: invalid feature option: " + fopt[0])
