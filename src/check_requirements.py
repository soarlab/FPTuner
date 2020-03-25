

import os
import os.path as path
import subprocess
import sys


SRC_DIR = path.abspath(path.dirname(__file__))
GIT_DIR = path.split(SRC_DIR)[0]

from fpcore_logging import Logger


logger = Logger(color=Logger.yellow)


def append_to_environ(pathname, addition):
    try:
        current = os.environ[pathname]
        os.environ[pathname] = "{}:{}".format(addition, current)
        logger("  {} = {}", pathname, os.environ[pathname])
    except KeyError:
        os.environ[pathname] = addition
        logger("  new {} = {}", pathname, os.environ[pathname])


# External requirements
try:
    import sly
except ModuleNotFoundError:
    logger.error("Unable to find sly")
    logger.error("Usually this can be installed with:")
    logger.error("  pip3 install --user sly")
    sys.exit(1)

try:
    import gurobipy
except ModuleNotFoundError as e:
    logger.error(e)
    logger.error("Unable to find gurobi")
    logger.error("This can be installed from:")
    logger.error("  https://www.gurobi.com/")
    sys.exit(1)


# Self built requirements
try:
    import gelpia
except ModuleNotFoundError:
    mod_directory = path.join(GIT_DIR, "requirements/gelpia/bin")
    sys.path.append(mod_directory)
    try:
        import gelpia
    except ModuleNotFoundError:
        logger.error("Unable to find gelpia")
        logger.error("Have the requirements been built?")
        sys.exit(1)


try:
    subprocess.check_output(["fptaylor", "--help"])
except FileNotFoundError:
    path_addition = path.join(GIT_DIR, "requirements/FPTaylor")
    append_to_environ("PATH", path_addition)
    try:
        subprocess.check_output(["fptaylor", "--help"])
    except FileNotFoundError as e:
        logger.error("Unable to run fptaylor")
        logger.error("Have the requirements been built?")
        logger.error(e)
        sys.exit(1)
