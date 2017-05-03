#! /usr/bin/env python3

import os
import sys
import imp

tft_utils = imp.load_source("tft_utils", "./src/tft_utils.py")

vars_file = "fptuner_vars"


# ========
# subroutines
# ========
def InstallGelpia(branch, commit=None):
    assert(type(branch) is str)

    if tft_utils.checkGelpiaInstallation(branch):
        print("Gelpia seems to already be installed. Skipping instillation.")
        return

    # download Gelpia
    d = "gelpia"

    if os.path.isdir(d):
        print("Removing old Gelpia directory")
        os.system("rm -rf {}".format(d))

    print("Downloading Gelpia git repository at branch {}".format(branch))
    os.system("git clone --quiet -b {} https://github.com/soarlab/gelpia.git {}"
              .format(branch, d))
    assert(os.path.isdir(d))

    os.chdir(d)
    if commit != None:
        print("Checking out Gelpia at commit {}".format(commit))
        os.system("git checkout --quiet {}".format(commit))
    print("Building Gelpia requirements")
    os.system("make requirements")
    print("Building Gelpia")
    os.system("make")
    assert(os.path.isfile("./bin/gelpia"))

    os.chdir("../")

    # set environment variables
    os.environ["GELPIA_PATH"] = os.path.abspath(d)
    os.environ["GELPIA"]      = os.environ["GELPIA_PATH"] + "/bin/gelpia"
    assert(tft_utils.checkGelpiaInstallation(branch))


def InstallFPTaylor(branch, commit=None):
    assert(type(branch) is str)

    if tft_utils.checkFPTaylorInstallation(branch):
        print("FPTaylor seems to already be installed. Skipping instillation.")
        return

    # download FPTaylor
    d = "FPTaylor"

    if os.path.isdir(d):
        print("Removing old FPTaylor")
        os.system("rm -rf {}".format(d))

    print("Downloading FPTaylor git repository at branch {}".format(branch))
    os.system("git clone --quiet -b {} https://github.com/soarlab/FPTaylor.git {}"
              .format(branch, d))
    assert(os.path.isdir(d))

    os.chdir(d)
    if commit != None:
        print("Checking out FPTaylor at commit {}".format(commit))
        os.system("git checkout --quiet {}".format(commit))
    print("Building FPTaylor")
    os.system("make --quiet")
    assert(os.path.isfile("./fptaylor"))

    cfg_orig = "default.cfg"
    cfg_default = "fptuner_default.cfg"
    os.system("cp {} {}".format(cfg_orig, cfg_default))
    os.system('sed -i "s|fp-power2-model = true|fp-power2-model = false|g" {}'
              .format(cfg_default))
    os.system('sed -i "s|\[short:|#[short:|g" {}'.format(cfg_default))
    assert(os.path.isfile(cfg_default))

    # write FPT_CFG_FIRST
    cfg_first  = tft_utils.FPT_CFG_FIRST
    os.system("cp {} {}".format(cfg_default, cfg_first))

    with open(cfg_first, "a") as f_cfg_first:
        f_cfg_first.write("\n")
        f_cfg_first.write("abs-error = false\n")
        f_cfg_first.write("rel-error = false\n")
        f_cfg_first.write("fail-on-exception = false\n")
        f_cfg_first.write("find-bounds = false\n")

    # write FPT_CFG_VERIFY
    cfg_verify = tft_utils.FPT_CFG_VERIFY
    os.system("cp {} {}".format(cfg_default, cfg_verify))

    with open(cfg_verify, "a") as f_cfg_verify:
        f_cfg_verify.write("\n")
        f_cfg_verify.write("abs-error=true\n")
        f_cfg_verify.write("rel-error=false\n")
        f_cfg_verify.write("opt = gelpia\n")

    # write FPT_CFG_VERIFY_DETAIL_GELPIA
    cfg_verify_dg = tft_utils.FPT_CFG_VERIFY_DETAIL_GELPIA
    os.system("cp {} {}".format(cfg_default, cfg_verify_dg))

    with open(cfg_verify_dg, "a") as f_cfg_verify_dg:
        f_cfg_verify_dg.write("\n")
        f_cfg_verify_dg.write("abs-error=true\n")
        f_cfg_verify_dg.write("rel-error=false\n")
        f_cfg_verify_dg.write("intermediate-opt = true\n")
        f_cfg_verify_dg.write("opt = gelpia\n")

    # write FPT_CFG_VERIFY_DETAIL_BB
    cfg_verify_bb = tft_utils.FPT_CFG_VERIFY_DETAIL_BB
    os.system("cp {} {}".format(cfg_default, cfg_verify_bb))

    with open(cfg_verify_bb, "a") as f_cfg_verify_bb:
        f_cfg_verify_bb.write("\n")
        f_cfg_verify_bb.write("abs-error=true\n")
        f_cfg_verify_bb.write("rel-error=false\n")
        f_cfg_verify_bb.write("fp-power2-model=true\n")
        f_cfg_verify_bb.write("intermediate-opt = true\n")
        f_cfg_verify_bb.write("opt = bb\n")

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
    os.system("rm -f *~")
    os.system("rm -f *.exprs")
    os.system("rm -f *.pyc")
    os.system("rm -rf log")
    os.system("rm -rf tmp")
    os.system("rm -rf __pycache__")

    for c in more_commands:
        os.system(c)

    os.chdir(d_curr)


def MakeClean ():
    CleanDir("./")
    CleanDir("./src", ["rm -f __fptaylor_m2_check_query.txt",
                       "rm -f __fpt_query",
                       "rm -f gurobi.log",
                       "rm -f -rf saved-gelpia-queries"])
    CleanDir("./bin", ["rm -f __fptaylor_m2_check_query.txt",
                       "rm -f __fpt_query",
                       "rm -f gurobi.log",
                       "rm -rf saved-gelpia-queries"])
    CleanDir("./examples", ["rm -f *.cpp"])
    CleanDir("./examples/primitives", ["rm -f *.cpp"])


def usage(argv):
    print("Usage: python3 {} <install|clean|uninstall>".format(argv[0]))
    sys.exit(-1)




# ========
# main
# ========
def main(argv):
    if len(argv) != 2:
        usage(argv)

    OPT_SETUP = sys.argv[1]
    if OPT_SETUP == "install":
        # ----
        # install the required tools
        # ----
        InstallFPTaylor("develop", "bb773cb0e9e1b13db8845623e80186e1a343bb11")
        InstallGelpia("ArtifactEvaluation")

        # ----
        # message
        # ----
        exports = []
        print("="*80)
        print("Please set the environment variables: ")
        print("")
        exports.append("export HOME_FPTUNER={}".format(os.path.abspath("./")))
        exports.append("export GELPIA_PATH={}".format(os.environ["GELPIA_PATH"]))
        exports.append("export GELPIA={}".format(os.environ["GELPIA"]))
        exports.append("export FPTAYLOR_BASE={}"
                       .format(os.environ["FPTAYLOR_BASE"]))
        exports.append("export FPTAYLOR={}".format(os.environ["FPTAYLOR"]))
        print("\n".join(exports))
        print("")
        print("Please append the environment variables: ")
        print("")
        ppath = ("export PYTHONPATH={0}/src:{0}/src/parser:$PYTHONPATH"
                 .format(os.path.abspath("./")))
        exports.append(ppath)
        print(ppath)
        print("")
        print("Note: You must manually setup PYTHONPATH for Gurobi's python " +
              "interface.")
        print("      Please refer to READMD.md and www.gurobi.com for " +
              "more details.")
        print("")
        print("The file {0} has been written which includes these variables. "
              "You may type\n\t source {0}\nto set them."
               .format(vars_file))
        print("")
        print("="*80)

        with open(vars_file, 'w') as f:
            f.write('\n'.join(exports))


    elif (OPT_SETUP == "clean"):
        MakeClean()


    elif (OPT_SETUP == "uninstall"):
        MakeClean()
        os.system("rm -f {}".format(vars_file))
        os.system("rm -rf gelpia")
        os.system("rm -rf FPTaylor")


    else:
        print("ERROR: invalid option: {}".format(OPT_SETUP))
        usage(argv)




if __name__ == "__main__":
    main(sys.argv)
