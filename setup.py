#! /usr/bin/env python3

import os 
import sys 
import imp 

tft_utils = imp.load_source("tft_utils", "./src/tft_utils.py") 

vars_file = "fptuner_vars"


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
            os.environ["GELPIA_PATH"] = os.path.abspath(d) 
            os.environ["GELPIA"]      = os.environ["GELPIA_PATH"] + "/bin/gelpia"

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

    CleanDir("./bin", ["rm __fptaylor_m2_check_query.txt", 
                       "rm __fpt_query", 
                       "rm gurobi.log",
                       "rm -rf saved-gelpia-queries"])

    CleanDir("./examples", ["rm *.cpp"]) 

    CleanDir("./examples/primitives", ["rm *.cpp"]) 



# ========
# main 
# ========
if len(sys.argv) != 2:
    print("Usage: python3 {} <install|clean|uninstall>".format(sys.argv[0]))
    sys.exit(-1)
OPT_SETUP = sys.argv[1] 


if   (OPT_SETUP == "install"): 
    # ---- 
    # install the required tools
    # ----
    InstallFPTaylor("develop")
    # InstallGelpia("RustAD") 
    InstallGelpia("ArtifactEvaluation") 


    # ----
    # message 
    # ----
    exports = []
    print ("========")
    print ("Please set the environment variables: ")
    print ("")
    exports.append ("export HOME_FPTUNER=" + os.path.abspath("./")) 
    exports.append ("export GELPIA_PATH=" + os.environ["GELPIA_PATH"]) 
    exports.append ("export GELPIA=" + os.environ["GELPIA"]) 
    exports.append ("export FPTAYLOR_BASE=" + os.environ["FPTAYLOR_BASE"]) 
    exports.append ("export FPTAYLOR=" + os.environ["FPTAYLOR"])
    print("\n".join(exports))
    print ("") 
    print ("Please append the environment variables: ") 
    print ("") 
    ppath = "export PYTHONPATH=" + os.path.abspath("./") + "/src:$PYTHONPATH"
    exports.append(ppath)
    print(ppath)
    print ("")
    print ("Note: You must manually setup PYTHONPATH for Gurobi's python interface. Please refer to READMD.md and www.gurobi.com for more details.")
    print("")
    print ("The file {} has been written which includes these variables. You may type\n\t source {}\nto set them."
           .format(vars_file, vars_file))
    print ("")
    print ("========")

    with open(vars_file, 'w') as f:
        f.write('\n'.join(exports))


elif (OPT_SETUP == "clean"): 
    MakeClean() 


elif (OPT_SETUP == "uninstall"): 
    MakeClean()
    os.system("rm -f " + vars_file)
    os.system("rm -rf gelpia") 
    os.system("rm -rf FPTaylor") 


else: 
    sys.exit("ERROR: invalid option : " + OPT_SETUP) 
