
# This can be used if:
#   * gurobi version is 901
#   * gurobi was untarred in requirements
#   * the liscence key is in HOME
#   * the python version used is 3.6


SCRIPT_LOCATION=$(readlink -f $(dirname $0))
GUROBI_HOME="${SCRIPT_LOCATION}/gurobi901/linux64"
export GRB_LICENSE_FILE="${HOME}/gurobi.lic"
export PATH="${GUROBI_HOME}/bin:${PATH}"
export LD_LIBRARY_PATH="${GUROBI_HOME}/lib:${LD_LIBRARY_PATH}"
export PYTHONPATH="${GUROBI_HOME}/lib/python3.6_utf32:${PYTHONPATH}"
