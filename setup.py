
import os 
import sys 
import imp 

tft_utils = imp.load_source("tft_utils", "./src/tft_utils.py") 



# ========
# subroutines 
# ======== 
def InstallGelpia (branch): 
    assert(type(branch) is str) 

    if (not tft_utils.checkGelpiaInstallation(branch)): 
        # download Gelpia 
        d = "gelpia" 

        assert(not os.path.isdir("gelpia")) 
        os.system("git clone -b " + branch + " https://github.com/soarlab/gelpia.git " + d)
        assert(os.path.isdir(d)) 

        os.chdir(d) 
        os.system("make requirements") 
        os.system("make") 
        os.chdir("../") 

        # set environment variables 
        os.environ["HOME_GELPIA"] = os.path.abspath(d) 
        os.environ["GELPIA"]      = os.environ["HOME_GELPIA"] + "/bin/gelpia"

    assert(tft_utils.checkGelpiaInstallation(branch)) 



def InstallFPTaylor (branch): 
    assert(type(branch) is str) 

    if (not tft_utils.checkFPTaylorInstallation(branch)): 
        # download FPTaylor 
        d = "FPTaylor" 
        # d = "FPTaylor-" + branch 

        assert(not os.path.isdir(d)) 
        os.system("git clone -b " + branch + " https://github.com/soarlab/FPTaylor.git " + d) 
        assert(os.path.isdir(d))  

        os.chdir(d)
        os.system("make") 
        os.chdir("../") 

        # set environment variables 
        os.environ["HOME_FPTAYLOR"] = os.path.abspath(d) 
        os.environ["FPTAYLOR"]      = os.environ["HOME_FPTAYLOR"] + "/fptaylor"

    assert(tft_utils.checkFPTaylorInstallation(branch)) 



# ========
# main 
# ========
assert(len(sys.argv) == 2) 
OPT_SETUP = sys.argv[1] 


if   (OPT_SETUP == "install"): 
    # ---- 
    # install the required tools
    # ----
    InstallGelpia("master") 
    InstallFPTaylor("master")


    # ----
    # message 
    # ----
    print ("========")
    print ("Please set the environment variables: ")
    print ("export HOME_FPTUNER=" + os.path.abspath("./")) 
    print ("export HOME_GELPIA=" + os.environ["HOME_GELPIA"]) 
    print ("export GELPIA=" + os.environ["GELPIA"]) 
    print ("export HOME_FPTAYLOR=" + os.environ["HOME_FPTAYLOR"]) 
    print ("export FPTAYLOR=" + os.environ["FPTAYLOR"]) 
    print ("") 
    print ("Please append the environment variables: ") 
    print ("export PYTHONPATH=" + os.path.abspath("./") + "/src:$PYTHONPATH") 
    print ("========") 


elif (OPT_SETUP == "uninstall"): 
    os.system("rm *~") 
    os.system("rm *.pyc") 
    os.system("rm ./src/*.pyc")
    os.system("rm -rf ./src/__pycache__") 
    os.system("rm -rf gelpia") 
    os.system("rm -rf FPTaylor") 


else: 
    sys.exit("ERROR: invalid option : " + OPT_SETUP) 
