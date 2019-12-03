
import os
import sys
import random
import subprocess as subp
import datetime
import imp

import tft_expr
import tft_error_form
import tft_sol_exprs
import tft_utils
import tft_tuning
import tft_solver

import tft_dat_def as DEF
import tft_dat_sampling
import tft_dat_scikit


# ====
# global variables
# ====
VERBOSE = True

CV_TESTER = "/home/weifan/numerical_precision/taylor-fptuning/svm_scripts/cv-testing.py"
# CV_TESTER = "/home/wfchiang/tools/libsvm-3.20/tools/cv-testing.py"



# ====
# functions for calling the svm predictor
# ====
def ArbitraryPredict (this_feature = []):
    assert(DEF.SVM_MODEL is not None)

    this_cid, p_acc, p_vals = svm_predict([0], [this_feature], DEF.SVM_MODEL)
    assert(len(this_cid) == 1)
    this_cid = int(this_cid[0])
    assert(this_cid in DEF.CID_HDLabel.keys())

    return this_cid

def CVPredict (this_feature = []):
    assert(len(this_feature) > 0)

#    if (VERBOSE):
#        print ("- predict feature -")
#        print (str(this_feature))

    tfile = open(DEF.FNAME_SVM_TEST, "w")

    tfile.write("1")
    for iid in range(0, len(this_feature)):
        tfile.write(" " + str((iid+1)) + ":" + str(this_feature[iid]))
    tfile.write("\n")

    tfile.close()

    fname_predict = DEF.FNAME_SVM_TEST + ".predict"

    assert(os.path.isfile(CV_TESTER))
    assert(os.path.isfile(DEF.FNAME_SVM_MODEL))
    if (os.path.isfile(fname_predict)):
        os.system("rm " + fname_predict)

    # os.system(CV_TESTER + " " + DEF.FNAME_SVM_MODEL + " " + DEF.FNAME_SVM_TEST)
    exe_cv_tester = subp.Popen(CV_TESTER+" "+DEF.FNAME_SVM_MODEL+" "+DEF.FNAME_SVM_TEST, shell=True, stdout=subp.PIPE, stderr=subp.PIPE)
    exe_cv_tester.communicate()

    assert(os.path.isfile(fname_predict))
    file_predict = open(fname_predict, "r")

    this_cid = None
    for aline in file_predict:
        aline = aline.strip()
        if (aline == ""):
            continue
        assert(this_cid is None)
        this_cid = int(aline)

    file_predict.close()

    return this_cid


def DecisionTreePredict (this_feature = []):
    assert(DEF.DT_MODEL is not None)
    assert(DEF.DT_ROOT is not None)
    assert(DEF.DT_FLABELS is not None)
    assert(len(this_feature) == len(DEF.DT_FLABELS))
    assert(len(DEF.DT_FLABELS) > 0)

    dt_test = []

    for f in range(0, len(DEF.DT_FLABELS)):
        fv = DEF.DT_FLABELS[f] + "=" + str(this_feature[f])
        dt_test.append(fv)

    prob_cid = DEF.DT_MODEL.classify(DEF.DT_ROOT, dt_test)

    pred_cid = None
    pred_prob = None

    for k,v in prob_cid.items():
        if (k.startswith("cid=")):
            cid = int(k[4:])

            if (pred_cid is None):
                assert(pred_prob is None)
                pred_cid = cid
                pred_prob = float(v)

            else:
                assert(pred_prob is not None)
                if (pred_prob < float(v)):
                    pred_cid = cid
                    pred_prob = float(v)
        else:
            assert(k == "solution_path")

    assert((pred_cid is not None) and (pred_prob is not None))

    return pred_cid


def UniformRandomPredict ():
    assert(DEF.CID_HDLabel is not None)
    cids = DEF.CID_HDLabel.keys()
    return cids[random.randint(0, len(cids)-1)]


def BiasRandomPredict ():
    assert(DEF.CID_Training_Counts is not None)
    n_counts = sum(DEF.CID_Training_Counts.values())
    sel = random.randint(1, n_counts)

    cids = DEF.CID_Training_Counts.keys()
    cids.sort()

    acc = 0
    for cid in cids:
        acc = acc + DEF.CID_Training_Counts[cid]
        if (acc >= sel):
            return cid


def CIDPredict (this_feature = []):
    assert(type(DEF.TEST_MODE) is str)
    assert(DEF.TEST_MODE in DEF.AVAILABLE_MODES)

    if (DEF.TEST_MODE == "arbitrary"):
        if (DEF.SVM_MODEL is None):
            DEF.SVM_MODEL = svm_load_model(DEF.FNAME_SVM_MODEL)
        return ArbitraryPredict(this_feature)

    elif (DEF.TEST_MODE == "cv"):
        return CVPredict(this_feature)

    elif (DEF.TEST_MODE == "decision-tree"):
        # cid = DecisionTreePredict(this_feature)
        cid = tft_dat_scikit.scikitDecisionTreePredict(this_feature)
        return cid

    elif (DEF.TEST_MODE == "random-uniform"):
        return UniformRandomPredict()

    elif (DEF.TEST_MODE == "random-bias"):
        return BiasRandomPredict()

    else:
        sys.exit("ERROR: invalid prediction mode: " + DEF.TEST_MODE)


# Return None if the theoretical prediction accuracy cannot be calculated.
def TheoreticalPredictionAccuracy ():
    if (DEF.TEST_MODE in ["random-uniform", "random-bias"]):
        assert(DEF.CID_HDLabel is not None)
        assert(DEF.CID_Training_Counts is not None)

        cid_hdlabel = DEF.CID_HDLabel.copy()

        sorted_tcounts = []
        while (len(cid_hdlabel.keys()) > 0):
            lowest_cid = None
            lowest_hdlabel = None

            for cid,hdlabel in cid_hdlabel.items():
                if ((lowest_cid is None) and (lowest_hdlabel is None)):
                    lowest_cid = cid
                    lowest_hdlabel = hdlabel
                else:
                    assert(len(lowest_hdlabel) == len(hdlabel))
                    assert(lowest_hdlabel != hdlabel)

                    if (all([(lowest_hdlabel[i] <= hdlabel[i]) for i in range(0, len(hdlabel))])):
                        lowest_cid = cid
                        lowest_hdlabel = hdlabel
                    else:
                        if (not all([(lowest_hdlabel[i] >= hdlabel[i]) for i in range(0, len(hdlabel))])):
                            return None

            assert((lowest_cid is not None) and (lowest_hdlabel is not None))
            assert(lowest_cid in DEF.CID_Training_Counts.keys())

            del cid_hdlabel[lowest_cid]

            sorted_tcounts.append(DEF.CID_Training_Counts[lowest_cid])

        assert(len(sorted_tcounts) == len(DEF.CID_HDLabel.keys()))

        total_counts = sum(sorted_tcounts)
        sorted_trates = []
        for i in range(0, len(sorted_tcounts)):
            sorted_trates.append( float(sorted_tcounts[i]) / float(total_counts) )

        if (DEF.TEST_MODE == "random-uniform"):
            tpa = 0.0
            for i in range(0, len(sorted_trates)):
                tpa = tpa + (sorted_trates[i] * (float(len(sorted_trates) - i) / float(len(sorted_trates))))

            return tpa

        elif (DEF.TEST_MODE == "random-bias"):
            tpa = 0.0
            for i in range(0, len(sorted_trates)):
                tpa = tpa + (sorted_trates[i] * float(sum(sorted_trates[i:])))

            return tpa

        else:
            sys.exit("Error: ")

    else:
        sys.exit("Error: invalid mode for TheoreticalPredictionAccuracy : " + DEF.TEST_MODE)



# ====
# testing
# ====
def Testing ():
    print ("==== testing in small-scale ====")

    # turn off tft_solver.LIMIT_N_CASTINGS
    tft_solver.LIMIT_N_CASTINGS = False

    # load CID_Training_Counts
    if (DEF.CID_Training_Counts is None):
        DEF.CID_Training_Counts = {}

        assert(os.path.isfile(DEF.FNAME_CID_Training_Counts))
        file_ctc = open(DEF.FNAME_CID_Training_Counts, "r")

        for aline in file_ctc:
            aline = aline.strip()
            if (aline == ""):
                continue
            tokens = tft_utils.String2Tokens(aline, " ")
            assert(len(tokens) == 2)
            cid = int(tokens[0])
            tcounts = int(tokens[1])

            print ("CID Counts : " + str(cid) + " : " + str(tcounts))

            assert(cid not in DEF.CID_Training_Counts.keys())
            DEF.CID_Training_Counts[cid] = tcounts

#        assert(sum(DEF.CID_Training_Counts.values()) == DEF.N_Samples)

        file_ctc.close()

    # load HDLID_GID
    if (DEF.HDLID_GID is None):
        DEF.HDLID_GID = {}

        assert(os.path.isfile(DEF.FNAME_HDLID_GID))
        fild_hdlid_gid = open(DEF.FNAME_HDLID_GID, "r")

        for aline in fild_hdlid_gid:
            aline = aline.strip()
            if (aline == ""):
                continue
            tokens = tft_utils.String2Tokens(aline, " ")
            assert(len(tokens) == 2)
            hdlid = int(tokens[0])
            gid = int(tokens[1])

            print ("HDLID: " + str(hdlid) + " : GID: " + str(gid))

            assert(hdlid not in DEF.HDLID_GID.keys())
            DEF.HDLID_GID[hdlid] = gid

        fild_hdlid_gid.close()

    # load CID_HDLabel
    if (DEF.CID_HDLabel is None):
        DEF.CID_HDLabel = {}
        assert(DEF.DIM_HDL == 0)
        DEF.DIM_HDL = None

        assert(os.path.isfile(DEF.FNAME_CID_HDLabel))
        file_cid_hdlabel = open(DEF.FNAME_CID_HDLabel, "r")

        for aline in file_cid_hdlabel:
            aline = aline.strip()
            if (aline == ""):
                continue
            tokens = tft_utils.String2Tokens(aline, ":")
            assert(len(tokens) == 2)
            cid = int(tokens[0])
            str_hdlabel = tokens[1]

            assert((0 <= cid) and (cid < DEF.N_Clusters))
            assert(cid not in DEF.CID_HDLabel.keys())
            assert(str_hdlabel.startswith("[") and str_hdlabel.endswith("]"))
            str_hdlabel = str_hdlabel[1:len(str_hdlabel)-1]

            tokens = tft_utils.String2Tokens(str_hdlabel, ",")
            hdlabel = [int(tokens[i]) for i in range(0, len(tokens))]

            print ("CID: " + str(cid) + " : " + str(hdlabel))

            if (DEF.DIM_HDL is None):
                DEF.DIM_HDL = len(hdlabel)
            else:
                assert(DEF.DIM_HDL == len(hdlabel))

            DEF.CID_HDLabel[cid] = hdlabel[:]

        file_cid_hdlabel.close()


    # count DEF.N_CTT_Samples
    if (DEF.N_CTT_Samples is None):
        DEF.N_CTT_Samples = 0

        file_fc = open(DEF.FNAME_SVM_TRAIN_FEATURE_CLUSTER, "r")

        for aline in file_fc:
            aline = aline.strip()

            if (aline == ""):
                continue

            DEF.N_CTT_Samples = DEF.N_CTT_Samples + 1

        file_fc.close()

        file_fc = open(DEF.FNAME_SVM_TEST_FEATURE_CLUSTER, "r")

        for aline in file_fc:
            aline = aline.strip()

            if (aline == ""):
                continue

            DEF.N_CTT_Samples = DEF.N_CTT_Samples + 1

        file_fc.close()

    # load testing partitions
    assert((type(DEF.N_CTT_Samples) is int) and (DEF.N_CTT_Samples > 0))

    file_parts = open(DEF.FNAME_Partitions, "r")

    String_Partitions = []

    for aline in file_parts:
        aline = aline.strip()

        if (aline == ""):
            continue

        assert(len(String_Partitions) <= DEF.N_CTT_Samples)
        if (len(String_Partitions) == DEF.N_CTT_Samples):
            break

        String_Partitions.append(aline)

    file_parts.close()

    assert(len(String_Partitions) == DEF.N_CTT_Samples)

    Testing_Partitions = []
    pid = -1

    for i in range(0, DEF.N_CTT_Samples):
        aline = String_Partitions[i]

        pid = pid + 1

        if (DEF.isTrainingID(pid, DEF.N_CTT_Samples)):
            continue

        tokens = tft_utils.String2Tokens(aline, " ")
        this_part = []

        for i in range(0, len(tokens)):
            bs = tft_utils.String2Tokens(tokens[i], "~")
            assert(len(bs) == 2)

            lb = float(bs[0])
            ub = float(bs[1])

            this_part.append((lb, ub))

        Testing_Partitions.append(this_part)

    String_Partitions = [] # release the space .

    # load testing feature -> CID
    Testing_Features = []
    Testing_CIDs = []
    assert(os.path.isfile(DEF.FNAME_SVM_TEST_FEATURE_CLUSTER))
    file_fc = open(DEF.FNAME_SVM_TEST_FEATURE_CLUSTER, "r")

    for aline in file_fc:
        aline = aline.strip()

        if (aline == ""):
            continue

        tokens = tft_utils.String2Tokens(aline, " ")

        cid = int(tokens[0])
        assert(cid in DEF.CID_HDLabel.keys())

        this_feature = []
        for i in range(1, len(tokens)):
            fv = tft_utils.String2Tokens(tokens[i], ":")
            assert(len(fv) == 2)
            assert(i == int(fv[0]))

            this_feature.append(float(fv[1]))

        Testing_CIDs.append(cid)
        Testing_Features.append(this_feature)

    file_fc.close()

    # check the validity of the data
    n_tests = len(Testing_Partitions)
    assert(n_tests == len(Testing_Features))
    assert(n_tests == len(Testing_CIDs))

    # go testing
    n_test_success = 0
    n_exact_allocs = 0
    CID_Testing_Counts = {} # [0 for i in range(0, DEF.N_Clusters)]

    while (len(Testing_Partitions) > 0):
        assert(len(Testing_Partitions) == len(Testing_Features))
        assert(len(Testing_Features) == len(Testing_CIDs))

        # print out the testing progress
        sys.stdout.write("\rTest [" + str(n_tests - len(Testing_Partitions)) + "] : ")

        # get this partition, feature, and the cid
        this_part = Testing_Partitions[0]
        this_dvec = DEF.InverseSampleInputPartitionFromVec(this_part)

        this_feature = Testing_Features[0]

        exact_cid = Testing_CIDs[0]

        # sanitation check
        this_feature_2 = DEF.InputPartition2Feature([DEF.Feature_Option, []], this_dvec)
        assert(len(this_feature) == len(this_feature_2))

        for i in range(0, len(this_feature)):
            f = this_feature[i]
            f2 = this_feature_2[i]
            assert(abs(f - f2) < 0.00000001)

        # predict the alloc
        this_cid = CIDPredict(this_feature)
        assert(this_cid in DEF.CID_HDLabel.keys())

        if (this_cid not in CID_Testing_Counts.keys()):
            CID_Testing_Counts[this_cid] = 0

        sys.stdout.write("predicted/exact CID : [" + str(this_cid) + " / " + str(exact_cid) + "] ")
        sys.stdout.flush()

        CID_Testing_Counts[this_cid] = CID_Testing_Counts[this_cid] + 1

        predicted_alloc = DEF.HDLabel2Alloc(DEF.CID_HDLabel[this_cid])
        assert(predicted_alloc is not None)

        # count exact prediction
        if (this_cid == exact_cid):
            n_exact_allocs = n_exact_allocs + 1

        # solve the alloc
        this_eforms = None
        this_alloc = None

        if (DEF.REUSE_EFORMS):
            assert(DEF.BASE_EFORMS is not None)

            original_gid_epss = None
            new_gid_epss      = {}

            # record and overwrite epsilons
            for ef in DEF.BASE_EFORMS:
                if (original_gid_epss is None):
                    original_gid_epss = ef.gid2epsilons.copy()
                else:
                    assert(original_gid_epss.keys() == ef.gid2epsilons.keys())
                    for gid,epss in original_gid_epss.items():
                        assert(ef.gid2epsilons[gid] == epss)

                for et in ef.terms:

                    et.stored_overapprox_expr = None

                    etgid = et.getGid()
                    assert(etgid >= 0)
                    assert(predicted_alloc.isAssigned(etgid))

                    assert(etgid in original_gid_epss.keys())

                    ow_epss = [tft_expr.ConstantExpr(predicted_alloc[etgid])]

                    if (etgid in new_gid_epss.keys()):
                        assert(new_gid_epss[etgid] == ow_epss)
                    else:
                        new_gid_epss[etgid] = ow_epss

            for gid in original_gid_epss.keys():
                assert(predicted_alloc.isAssigned(gid))
                new_gid_epss[gid] = [tft_expr.ConstantExpr(predicted_alloc[gid])]

            assert(new_gid_epss.keys() == original_gid_epss.keys())

            for ef in DEF.BASE_EFORMS:
                ef.gid2epsilons = new_gid_epss.copy()

            # solve alloc.
            tft_tuning.TFTSystemReset()
            DEF.RewriteVarBounds(this_part)
            this_eforms, this_alloc = tft_sol_exprs.SolveErrorForms(DEF.BASE_EFORMS, tft_tuning.OPTIMIZERS)

            # restore the original epsilons
            for ef in DEF.BASE_EFORMS:
                ef.gid2epsilons = original_gid_epss.copy()

        else:
            # create the exprs file
            fname_part = tft_dat_sampling.FNameExprs(tft_dat_sampling.FNAME_EXPRS, id_feat)

            # solve alloc.
            tft_dat_sampling.WriteExprsFile(fname_part, this_part, predicted_alloc)
            tft_tuning.TFTSystemReset()
            this_eforms, this_alloc = tft_sol_exprs.SolveExprs(fname_part, tft_tuning.OPTIMIZERS)
            os.system("rm " + fname_part)

        # count the correct prediction
        if (this_alloc is not None):
            assert(this_alloc == predicted_alloc)

            n_test_success = n_test_success + 1

            if (VERBOSE):
                sys.stdout.write(" ---- prediction successed!!")
                sys.stdout.flush()

        else:
            if (VERBOSE):
                print (" ---- prediction failed.")

        # finalizing
        del Testing_Partitions[0]
        del Testing_Features[0]
        del Testing_CIDs[0]

    print ("")
    print ("Small-scale Testing Result: " + str(n_test_success) + " / " + str(n_tests) + " (" + str(float(n_test_success)/float(n_tests)) + ")")
    print ("    Exact Result : " + str(n_exact_allocs) + " / " + str(n_tests) + " (" + str(float(n_exact_allocs)/float(n_tests)) + ")")

    # show CID_Testing_Counts
    assert(sum(CID_Testing_Counts.values()) == n_tests)
    if (VERBOSE):
        print ("---- cid to # of training partitions ----")
        for cid in range(0, DEF.N_Clusters):
            if (cid in CID_Testing_Counts.keys()):
                print ("CID: " + str(cid) + " : " + str(CID_Testing_Counts[cid]))
