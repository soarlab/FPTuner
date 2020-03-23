#!/bin/bash

set -e


SUCCESS=1

SCRIPT_LOCATION="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG="${SCRIPT_LOCATION}/log.txt"
rm -f "${LOG}"

function finish {
    if [ "$SUCCESS" == 1 ]
    then
	echo "FPTuner requirements failed to build."
	echo "See ${LOG} for details."
    else
	echo "Success"
    fi
}
trap finish EXIT


# FPTaylor with my_sin
echo "Installing FPTaylor"
cd "$SCRIPT_LOCATION"
rm -rf FPTaylor
git clone https://github.com/soarlab/FPTaylor.git &>> "${LOG}"
cd FPTaylor
git checkout my_sine &>> "${LOG}"
make &>> "${LOG}"

# gelpia
echo "Installing Gelpia"
cd "$SCRIPT_LOCATION"
rm -rf gelpia
git clone https://github.com/soarlab/gelpia.git &>> "${LOG}"
ln -s FPTuner/gelpia gelpia &>> "${LOG}"
cd gelpia
make requirements &>> "${LOG}"
make &>> "${LOG}"

# Debug enviroment source file
cd "$SCRIPT_LOCATION"
rm -f debug_eniroment.sh
echo "export PATH=${SCRIPT_LOCATION}/fptaylor:${SCRIPT_LOCATION}/gelpia/bin:\$PATH" >> debug_eniroment.sh
echo "export PYTHONPATH=${SCRIPT_LOCATION}/gelpia/bin:\$PYTHON_PATH" >> debug_eniroment.sh

SUCCESS=0
