
import os
import tft_utils
from sklearn import tree

MAX_DT_DEPTH = 3
DT_MODEL = None
FNAME_DT_DOT = "__scikit_decision_tree.dot"



def scikitExportDecisionTree2Dot (fname):
    assert(DT_MODEL is not None)

    fdot = open(fname, "w")

    tree.export_graphviz(DT_MODEL, out_file=fdot)

    fdot.close()



def scikitDecisionTreeTraining (tdata):
    global DT_MODEL

    assert(os.path.isfile(tdata))


    # -- load training data --
    ftrain = open(tdata, "r")

    l_feat = None

    feats = []
    labels = []

    for aline in ftrain:
        aline = aline.strip()

        if (aline == ""):
            continue

        tokens = tft_utils.String2Tokens(aline, " ")
        assert(len(tokens) >= 2)
        if (l_feat is None):
            l_feat = len(tokens) - 1
        else:
            assert(len(tokens) == l_feat + 1)

        this_feat = []

        for i in range(0, len(tokens)):
            if (i == 0): # get the label
                labels.append(int(tokens[0]))

            else: # the a feature
                assert(tokens[i].startswith(str(i)+":"))

                this_feat.append( float(tokens[i][len(str(i)+":") : ]) )

        assert(len(this_feat) == l_feat)
        feats.append(this_feat)

    ftrain.close()
    assert(len(labels) == len(feats))


    # -- train the model --
    DT_MODEL = tree.DecisionTreeClassifier()
    DT_MODEL.max_depth = MAX_DT_DEPTH
    DT_MODEL = DT_MODEL.fit(feats, labels)


    # -- export --
    scikitExportDecisionTree2Dot(FNAME_DT_DOT)



def scikitDecisionTreePredict (this_feat = []):
    assert(DT_MODEL is not None)

    pred_cid = DT_MODEL.predict([this_feat])
    assert(len(pred_cid) == 1)
    assert(int(pred_cid[0]) == pred_cid)

    return int(pred_cid[0])
