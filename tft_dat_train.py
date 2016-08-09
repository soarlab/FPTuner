
import os
import sys 
import imp 

import tft_utils 
import tft_dat_def as DEF 
# import DecisionTree as DT 
import tft_dat_scikit 


# ==== 
# global variables 
# ====
VERBOSE = True 

AVAILABLE_MODES = ["arbitrary", "cv", "decision-tree"] 

CV = "/home/weifan/numerical_precision/taylor-fptuning/svm_scripts/cv.py" 
# CV = "/home/wfchiang/tools/libsvm-3.20/tools/cv.py" 


# ====
# arbitrary training
# ==== 
def ArbitraryTraining (tdata): 
    print ("==== train SVM model ====") 

    svm_prob = svm_problem(DEF.FID_CID, DEF.Features) 
    svm_para = svm_parameter('-c 4') 
    svm_model = svm_train(svm_prob, svm_para) 
    svm_save_model(DEF.FNAME_SVM_MODEL, svm_model) 


# ====
# cross validation training by training data file 
# ==== 
def CVTraining (tdata): 
    assert(os.path.isfile(tdata)) 

    print ("==== CV training SVM model ====") 

    os.system(CV + " " + tdata) 
    
    fname_model = tdata + ".model" 
    assert(os.path.isfile(fname_model))

    os.system("mv " + fname_model + " " + DEF.FNAME_SVM_MODEL) 


# ====
# using decision tree to train the data file 
# ====
def DecisionTreeTraining (tdata): 
    assert(type(tdata) is str) 
    assert(os.path.isfile(tdata)) 
    assert(tdata.endswith(".csv")) 

    # calculate the # of features 
    tfile = open(tdata, "r") 

    n_feats = None 

    for aline in tfile: 
        aline = aline.strip() 
        
        if (aline == ""): 
            continue 

        tokens = tft_utils.String2Tokens(aline, ",") 
        
        if (n_feats is None): 
            assert(DEF.DT_FLABELS is None) 
            assert(len(tokens) > 1) 
            assert(tokens[0] == "cid") 
            
            n_feats = len(tokens) - 1 
            DEF.DT_FLABELS = tokens[1:] 

        else:
            assert((n_feats + 2) == len(tokens)) 

    tfile.close() 
    
    assert((n_feats is not None) and (n_feats > 0)) 
        
    # go training 
    print ("==== DecisionTree training model ====") 

    DEF.DT_MODEL = DT.DecisionTree(training_datafile = tdata, 
                                   csv_class_column_index = 1, 
                                   csv_columns_for_features = range(2, (2+n_feats)), 
                                   entropy_threshold = 0.01, 
                                   max_depth_desired = 3, 
                                   symbolic_to_numeric_cardinality_threshold = 0.00001,)
    
#    etd = DT.EvalTrainingData(training_datafile = tdata, 
#                              csv_class_column_index = 1, 
#                              csv_columns_for_features = range(2, (2+n_feats)), 
#                              entropy_threshold = 0.01, 
#                              max_depth_desired = 3, 
#                              symbolic_to_numeric_cardinality_threshold = 0.00001,)

#    etd.get_training_data()
#    score_train = etd.evaluate_training_data() 
#    print ("ETD training score: " + str(score_train)) 

    DEF.DT_MODEL.get_training_data() 
    DEF.DT_MODEL.calculate_first_order_probabilities() 
    DEF.DT_MODEL.calculate_class_priors() 
    DEF.DT_MODEL.show_training_data() 

    DEF.DT_ROOT = DEF.DT_MODEL.construct_decision_tree_classifier() 

    if (VERBOSE): 
        print ("-- dump the trained decision tree --") 
        DEF.DT_ROOT.display_decision_tree("    ") 


# ====
# the interface 
# ==== 
def DATTrain (tdata): 
    assert(type(DEF.TRAIN_MODE) is str) 
    assert(DEF.TRAIN_MODE in DEF.AVAILABLE_MODES) 
    
    if (DEF.TRAIN_MODE == "arbitrary"): 
        ArbitraryTraining(tdata) 

    elif (DEF.TRAIN_MODE == "decision-tree"): 
        # DecisionTreeTraining(tdata+".csv") 
        tft_dat_scikit.scikitDecisionTreeTraining(tdata) 
    
    elif (DEF.TRAIN_MODE == "cv"):
        CVTraining(tdata) 

    else:
        sys.exit("ERROR: invalid training mode: " + DEF.TRAIN_MODE) 
