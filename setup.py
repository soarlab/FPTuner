
import os 
import sys 
import imp 

tft_utils = imp.load_source("tft_utils", "./src/tft_utils.py") 

USE_DUAL_GELPIAS = False



# ========
# subroutines 
# ======== 
def InstallGelpia (branch, silent=False): 
    assert(type(branch) is str) 

    if (silent or 
        not tft_utils.checkGelpiaInstallation(branch)): 
        # download Gelpia 
        d = "gelpia" 

        assert(not os.path.isdir("gelpia")) 
        os.system("git clone -b " + branch + " https://github.com/soarlab/gelpia.git " + d)
        assert(os.path.isdir(d)) 

        os.chdir(d) 
        os.system("make requirements") 
        os.system("make")
        assert(os.path.isfile("./bin/gelpia"))
        
        os.chdir("../") 

        # set environment variables 
        if (not silent): 
            os.environ["HOME_GELPIA"] = os.path.abspath(d) 
            os.environ["GELPIA"]      = os.environ["HOME_GELPIA"] + "/bin/gelpia"

    if (not silent): 
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

        if (USE_DUAL_GELPIAS): 
            InstallGelpia("FPTaylorCompat", True)

        os.system("make")
        assert(os.path.isfile("./fptaylor"))

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

        f_cfg_verify = open(cfg_verify, "a") 
                
        f_cfg_verify.write("\n") 
        f_cfg_verify.write("abs-error=true\n") 
        f_cfg_verify.write("rel-error=false\n")
        f_cfg_verify.write("opt = gelpia\n") 
            
        f_cfg_verify.close() 

        # write FPT_CFG_VERIFY_DETAIL_GELPIA
        cfg_verify_dg = tft_utils.FPT_CFG_VERIFY_DETAIL_GELPIA
        os.system("cp " + cfg_default + " " + cfg_verify_dg) 

        f_cfg_verify_dg = open(cfg_verify_dg, "a") 

        f_cfg_verify_dg.write("\n")
        f_cfg_verify_dg.write("abs-error=true\n")
        f_cfg_verify_dg.write("rel-error=false\n")
        f_cfg_verify_dg.write("intermediate-opt = true\n") 
        f_cfg_verify_dg.write("opt = gelpia\n") 

        f_cfg_verify_dg.close()

        # write FPT_CFG_VERIFY_DETAIL_BB 
        cfg_verify_bb = tft_utils.FPT_CFG_VERIFY_DETAIL_BB 
        os.system("cp " + cfg_default + " " + cfg_verify_bb)

        f_cfg_verify_bb = open(cfg_verify_bb, "a")

        f_cfg_verify_bb.write("\n") 
        f_cfg_verify_bb.write("abs-error=true\n")
        f_cfg_verify_bb.write("rel-error=false\n")
        f_cfg_verify_bb.write("fp-power2-model=true\n") 
        f_cfg_verify_bb.write("intermediate-opt = true\n")
        f_cfg_verify_bb.write("opt = bb\n") 
        
        f_cfg_verify_bb.close()

        # end of the installation 
        os.chdir("../") 

        # set environment variables 
        os.environ["FPTAYLOR_BASE"] = os.path.abspath(d) 
        os.environ["FPTAYLOR"]      = os.environ["FPTAYLOR_BASE"] + "/fptaylor"

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
    InstallFPTaylor("develop")
    if (USE_DUAL_GELPIAS):
        InstallGelpia("master") # For the setting of the environment variables, must install Gelpia after FPTaylor
    else:
        InstallGelpia("RustAD") 


    # ----
    # message 
    # ----
    print ("========")
    print ("Please set the environment variables: ")
    print ("")
    print ("export HOME_FPTUNER=" + os.path.abspath("./")) 
    print ("export HOME_GELPIA=" + os.environ["HOME_GELPIA"]) 
    print ("export GELPIA=" + os.environ["GELPIA"]) 
    print ("export FPTAYLOR_BASE=" + os.environ["FPTAYLOR_BASE"]) 
    print ("export FPTAYLOR=" + os.environ["FPTAYLOR"]) 
    if (USE_DUAL_GELPIAS):
        print ("export GELPIA_PATH=" + os.environ["FPTAYLOR_BASE"] + "/gelpia")
    else: 
        print ("export GELPIA_PATH=" + os.environ["HOME_GELPIA"])
    print ("") 
    print ("Please append the environment variables: ") 
    print ("") 
    print ("export PYTHONPATH=" + os.path.abspath("./") + "/src:$PYTHONPATH") 
    print ("") 
    if (USE_DUAL_GELPIAS):
        print ("Note that the two environment variables, HOME_GELPIA and GELPIA_PATH, point to different Gelpia branches. We will integrate them in the near future.")
        print ("")
    print ("========") 


elif (OPT_SETUP == "clean"): 
    MakeClean() 


elif (OPT_SETUP == "uninstall"): 
    MakeClean() 
    os.system("rm -rf gelpia") 
    os.system("rm -rf FPTaylor") 


else: 
    sys.exit("ERROR: invalid option : " + OPT_SETUP) 
