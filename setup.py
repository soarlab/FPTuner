
import os 
import sys 
import imp 

tft_utils = imp.load_source("tft_utils", "./src/tft_utils.py") 



# ========
# subroutines 
# ======== 
def InstallGelpia (branch, set_path=True): 
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
        if (set_path):
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

        InstallGelpia("FPTaylorCompat", False) 

        os.system("make") 

        cfg_default = "default.cfg" 
        assert(os.path.isfile(cfg_default)) 

        # write FPT_CFG_FIRST  
        cfg_first  = tft_utils.FPT_CFG_FIRST 
        os.system("cp " + cfg_default + " " + cfg_first) 

        f_cfg_first = open(cfg_first, "a") 
            
        f_cfg_first.write("\n") 
        f_cfg_first.write("abs-error=false\n") 
        f_cfg_first.write("rel-error=false\n")
        f_cfg_first.write("fail-on-exception=false\n") 
        f_cfg_first.write("find-bounds=false\n")
            
        f_cfg_first.close() 
        
        # write FPT_CFG_VERIFY 
        cfg_verify = tft_utils.FPT_CFG_VERIFY 
        os.system("cp " + cfg_default + " " + cfg_verify) 

        f_cfg_verify = open(cfg_first, "a") 
                
        f_cfg_verify.write("\n") 
        f_cfg_verify.write("abs-error=true\n") 
        f_cfg_verify.write("rel-error=false\n")
        f_cfg_verify.write("opt = gelpia\n") 
            
        f_cfg_verify.close() 

        # end of the installation 
        os.chdir("../") 

        # set environment variables 
        os.environ["HOME_FPTAYLOR"] = os.path.abspath(d) 
        os.environ["FPTAYLOR"]      = os.environ["HOME_FPTAYLOR"] + "/fptaylor"

    assert(tft_utils.checkFPTaylorInstallation(branch)) 



def CleanDir (d, more_commands = []): 
    assert(os.path.isdir(d)) 

    d_curr = os.getcwd()

    os.chdir(d) 

    os.system("rm *~")
    os.system("rm *.exprs") 
    os.system("rm *.pyc")

    os.system("rm -rf log") 
    os.system("rm -rf tmp")     
    os.system("rm -rf __pycache__")
    
    for c in more_commands: 
        os.system(c) 

    os.chdir(d_curr)



def MakeClean (): 
    CleanDir("./") 

    CleanDir("./src", ["rm __fptaylor_m2_check_query.txt", 
                       "rm __fpt_query", 
                       "rm gurobi.log",
                       "rm -rf saved-gelpia-queries"])

    CleanDir("./examples", ["rm *.cpp"]) 

    CleanDir("./examples/primitives", ["rm *.cpp"]) 



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
    # InstallGelpia("FPTaylorCompat") 
    InstallFPTaylor("develop")


    # ----
    # message 
    # ----
    print ("========")
    print ("Please set the environment variables: ")
    print ("export HOME_FPTUNER=" + os.path.abspath("./")) 
    print ("export HOME_GELPIA=" + os.environ["HOME_GELPIA"]) 
    print ("export GELPIA=" + os.environ["GELPIA"]) 
#    print ("export HOME_FPTAYLOR=" + os.environ["HOME_FPTAYLOR"]) 
    print ("export FPTAYLOR_BASE=" + os.environ["HOME_FPTAYLOR"]) 
    print ("export FPTAYLOR=" + os.environ["FPTAYLOR"]) 
    print ("") 
    print ("Please append the environment variables: ") 
    print ("export PYTHONPATH=" + os.path.abspath("./") + "/src:$PYTHONPATH") 
    print ("========") 


elif (OPT_SETUP == "clean"): 
    MakeClean() 


elif (OPT_SETUP == "uninstall"): 
    MakeClean() 
    os.system("rm -rf gelpia") 
    os.system("rm -rf FPTaylor") 


else: 
    sys.exit("ERROR: invalid option : " + OPT_SETUP) 
