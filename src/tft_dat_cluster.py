
import os
import sys

from Pycluster import * 

import tft_utils 
import tft_alloc 
import tft_dat_def as DEF 


# ====
# global variables 
# ====
VERBOSE = True 


# ====
# cluster 
# ====
def Cluster (): 
    assert((DEF.N_CTT_Samples is None) or ((type(DEF.N_CTT_Samples) is int) and (DEF.N_CTT_Samples > 0))) 

    print ("==== clustering sub-domains ====")     

    # ---- load feature --> allocation ---- 
    Features = [] 
    Allocations = []
    FID_AID = []
    assert(os.path.isfile(DEF.FNAME_Feature_Allocation)) 
    file_fa = open(DEF.FNAME_Feature_Allocation, "r") 

    for aline in file_fa: 
        aline = aline.strip() 

        if (aline == ""): 
            continue 

        if (DEF.N_CTT_Samples is not None): 
            assert(len(Features) <= DEF.N_CTT_Samples) 
            if (len(Features) == DEF.N_CTT_Samples): 
                break 

        feat_alloc = tft_utils.String2Tokens(aline, ":") 
        assert(len(feat_alloc) == 2) 

        assert(feat_alloc[0].startswith("[") and feat_alloc[0].endswith("]")) 
        str_feat = feat_alloc[0][1:len(feat_alloc[0])-1] 
        feats = tft_utils.String2Tokens(str_feat, ",") 
        this_feat = [float(feats[i]) for i in range(0, len(feats))]

        this_alloc = tft_alloc.Alloc() 
        this_alloc.loadFromShortString(feat_alloc[1]) 

        Features.append(this_feat)

        this_fid = len(Features) - 1 
        this_aid = -1 
        for aid in range(0, len(Allocations)): 
            if (this_alloc == Allocations[aid]): 
                this_aid = aid 
                break 
        if (this_aid == -1): 
            Allocations.append(this_alloc) 
            this_aid = len(Allocations) -1 

        FID_AID.append(this_aid) 

    file_fa.close()

    if (DEF.N_CTT_Samples is None): 
        DEF.N_CTT_Samples = len(Features) 

    # check the validity of the parameters 
    assert(0 < len(Features)) 
    assert(len(Features) == len(FID_AID)) 
    assert(len(Features) == DEF.N_CTT_Samples) 
    assert(DEF.N_Clusters <= len(Features)) 

    # build FID -> HDLabel mapping for clustering 
    fid_hdlabel = [] 
    for fid in range(0, len(Features)): 
        assert(fid < len(FID_AID)) 
        aid = FID_AID[fid] 

        assert(aid < len(Allocations)) 
        alloc = Allocations[aid] 

        hdlabel = DEF.Alloc2HDLabel(alloc) 
        assert(DEF.isTypedList(int, hdlabel)) 

        fid_hdlabel.append(hdlabel) 

    assert(len(fid_hdlabel) == len(Features)) 

    # -- export HDLID to GID --
    # NOTE: this mapping is built by function DEF.Alloc2HDLabel 
    assert(DEF.HDLID_GID is not None)
    file_hdlid_gid = open(DEF.FNAME_HDLID_GID, "w")

    for hdlid, gid in DEF.HDLID_GID.items(): 
        assert((type(hdlid) is int) and (type(gid) is int))
        file_hdlid_gid.write(str(hdlid) + " " + str(gid) + "\n") 
    
    file_hdlid_gid.close() 

    # clustering 
    rel_tree = treecluster(fid_hdlabel, None, None, 0, 'm', 'b', None)
    fid_cid = rel_tree.cut(DEF.N_Clusters) 

    FID_CID = {} 
    for fid in range(0, len(fid_cid)): 
        cid = fid_cid[fid] 
        assert(fid not in FID_CID.keys()) 
        FID_CID[fid] = cid 

    # -- merge the allocs classified to the same class --
    print ("==== merging tuning results based on clustering ====") 

    assert(len(Features) == len(FID_AID)) 
    assert(len(Features) == len(FID_CID)) 

    DEF.CID_HDLabel = {} # [None for c in range(0, DEF.N_Clusters)] 
    for fid in range(0, len(FID_CID)): 
        cid = FID_CID[fid] 
        if (cid not in DEF.CID_HDLabel.keys()): 
            DEF.CID_HDLabel[cid] = None 
        DEF.CID_HDLabel[cid] = DEF.MergeHDLsTowardTop( DEF.CID_HDLabel[cid], fid_hdlabel[fid] ) 

    # -- fixing the repeated HDLabels (which are allocations) -- 
    EQ_CID = {} 

    for cid in range(0, DEF.N_Clusters): 
        same_cid = cid 
        for later_cid in range(0, DEF.N_Clusters): 
            if ( DEF.CID_HDLabel[cid] == DEF.CID_HDLabel[later_cid] ): 
                same_cid = later_cid 
        if (same_cid > cid): 
            assert(cid not in EQ_CID.keys()) 
            EQ_CID[cid] = same_cid 

    for fid,cid in FID_CID.items(): 
        if (cid in EQ_CID.keys()): 
            FID_CID[fid] = EQ_CID[cid] 
            if (cid in DEF.CID_HDLabel.keys()): 
                del DEF.CID_HDLabel[cid] 

    for cid1 in DEF.CID_HDLabel.keys(): 
        for cid2 in DEF.CID_HDLabel.keys(): 
            if (cid1 == cid2): 
                continue 
            assert(DEF.CID_HDLabel[cid1] != DEF.CID_HDLabel[cid2]) 

    # -- print out the allocations -- 
    for cid in range(0, DEF.N_Clusters): 
        if (cid in DEF.CID_HDLabel.keys()): 
            print ("---- class alloc (" + str(cid) + ") ----") 
            DEF.PrintHDLabel(DEF.CID_HDLabel[cid])

    # -- export CID_HDLabel -- 
    file_cid_hdlabel = open(DEF.FNAME_CID_HDLabel, "w") 

    for cid in range(0, DEF.N_Clusters): 
        if (cid in DEF.CID_HDLabel.keys()): 
            file_cid_hdlabel.write(str(cid) + " : " + str(DEF.CID_HDLabel[cid]) + "\n") 

    file_cid_hdlabel.close() 
    
    # -- build DEF.CID_Training_Counts -- 
    n_features = len(Features) 
    DEF.CID_Training_Counts = {} # [0 for i in range(0, DEF.N_Clusters)] 
    for fid in range(0, n_features):
        if (not DEF.isTrainingID(fid, n_features)): 
            continue 

        cid = FID_CID[fid] 
        assert((0 <= cid) and (cid < DEF.N_Clusters)) 

        if (cid not in DEF.CID_Training_Counts.keys()): 
            DEF.CID_Training_Counts[cid] = 0 

        DEF.CID_Training_Counts[cid] = DEF.CID_Training_Counts[cid] + 1 

    assert(sum(DEF.CID_Training_Counts.values()) == (int(float(n_features) * float(DEF.RATE_Trains_Samples))))

    if (VERBOSE): 
        print ("---- cid to # of training partitions ----") 
        for cid in range(0, DEF.N_Clusters): 
            if (cid in DEF.CID_Training_Counts.keys()): 
                print ("CID: " + str(cid) + " : " + str(DEF.CID_Training_Counts[cid])) 

    # -- export CID_Training_Counts -- 
    file_ctc = open(DEF.FNAME_CID_Training_Counts, "w") 

    for cid,tcounts in DEF.CID_Training_Counts.items(): 
        file_ctc.write(str(cid) + " " + str(tcounts) + "\n") 

    file_ctc.close() 

    # -- export training and testing data -- 
    # ( export feature -> cluster )
    assert((0 < DEF.RATE_Trains_Samples) and (DEF.RATE_Trains_Samples < 1)) 

    file_train_f2c = open(DEF.FNAME_SVM_TRAIN_FEATURE_CLUSTER, "w") 
    file_test_f2c  = open(DEF.FNAME_SVM_TEST_FEATURE_CLUSTER,  "w") 

    file_train_f2c_csv = open(DEF.FNAME_CSV_TRAIN_FEATURE_CLUSTER, "w") 
    file_test_f2c_csv  = open(DEF.FNAME_CSV_TEST_FEATURE_CLUSTER, "w") 

    assert(n_features > 0) 
    l_feat = len(Features[0]) 

    file_train_f2c_csv.write(",cid")
    file_test_f2c_csv.write(",cid")
    
    for f in range(0, l_feat): 
        file_train_f2c_csv.write(",f" + str(f))
        file_test_f2c_csv.write(",f" + str(f)) 

    file_train_f2c_csv.write("\n") 
    file_test_f2c_csv.write("\n") 

    for fid in range(0, n_features): 
        assert(len(Features[fid]) == l_feat)    

        cid = FID_CID[fid] 

        if (DEF.isTrainingID(fid, n_features)): 
            file_train_f2c.write(str(cid)) 

            file_train_f2c_csv.write(str(fid) + "," + str(cid)) 

            for findex in range(0, l_feat): 
                file_train_f2c.write(" " + str((findex+1)) + ":" + str(Features[fid][findex])) 

                file_train_f2c_csv.write("," + str(Features[fid][findex])) 
 
            file_train_f2c.write("\n") 

            file_train_f2c_csv.write("\n") 
            
        else: 
            file_test_f2c.write(str(cid)) 

            file_test_f2c_csv.write(str(fid) + "," + str(cid)) 
                        
            for findex in range(0, l_feat): 
                file_test_f2c.write(" " + str((findex+1)) + ":" + str(Features[fid][findex])) 

                file_test_f2c_csv.write("," + str(Features[fid][findex])) 
 
            file_test_f2c.write("\n") 

            file_test_f2c_csv.write("\n") 

    file_train_f2c.close() 
    file_test_f2c.close() 
