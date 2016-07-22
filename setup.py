
import os 
import sys 



# ========
# subroutines 
# ======== 
def checkGelpiaInstallation (): 
    return False



def checkFPTaylorInstallation (branch): 
    return False 



def DownloadGelpia (): 
    assert(not os.path.isdir("gelpia")) 
    os.system("git clone https://github.com/soarlab/gelpia.git")
    assert(os.path.isdir("gelpia")) 

    os.chdir("gelpia") 
    os.system("make requirements") 
    os.system("make") 
    assert(os.path.isfile("./bin/gelpia")) 
    os.chdir("../") 



def DownloadFPTaylor (branch): 
    d = "FPTaylor-" + branch 

    assert(not os.path.isdir(d)) 
    os.system("git clone -b " + branch + " https://github.com/soarlab/FPTaylor.git " + d) 
    assert(os.path.isdir(d))  

    os.chdir(d)
    os.system("make") 
    assert(os.path.isfile("fptaylor")) 
    os.chdir("../") 
    


def InstallGelpia (): 
    if (not checkGelpiaInstallation()): 
        DownloadGelpia() 

        # set environment variables 

    assert(checkGelpiaInstallation()) 



def InstallFPTaylor (branch): 
    assert(type(branch) is str) 

    if (not checkFPTaylorInstallation(branch)):
        DownloadFPTaylor(branch) 

        # set environment variables 

    assert(checkFPTaylorInstallation(branch)) 



# ========
# main 
# ========
# ---- 
# install the required tools
# ----
InstallGelpia() 
InstallFPTaylor("master")
InstallFPTaylor("fptuner") 

