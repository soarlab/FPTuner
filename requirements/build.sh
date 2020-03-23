#!/bin/bash

set -e


SUCCESS=1

SCRIPT_LOCATION="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
LOG="${SCRIPT_LOCATION}/log.txt"
rm -f "${LOG}"

pushd () {
    command pushd "$@" > /dev/null
}

popd () {
    command popd "$@" > /dev/null
}

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
pushd "$SCRIPT_LOCATION"
rm -rf FPTaylor
git clone https://github.com/soarlab/FPTaylor.git &>> "${LOG}"
pushd FPTaylor
git checkout my_sine &>> "${LOG}"
make &>> "${LOG}"
popd
popd

# gelpia
echo "Installing Gelpia"
pushd "$SCRIPT_LOCATION"
rm -rf gelpia
git clone https://github.com/soarlab/gelpia.git &>> "${LOG}"
ln -s FPTuner/gelpia gelpia &>> "${LOG}"
pushd gelpia
SUCCESS=-1
pushd requirements
./build.sh | sed "s|^|    |g"
popd
SUCCESS=1
make &>> "${LOG}"
popd
popd

# Debug enviroment source file
pushd "$SCRIPT_LOCATION"
rm -f debug_eniroment.sh
echo "export PATH=${SCRIPT_LOCATION}/fptaylor:${SCRIPT_LOCATION}/gelpia/bin:\$PATH" >> debug_eniroment.sh
echo "export PYTHONPATH=${SCRIPT_LOCATION}/gelpia/bin:\$PYTHON_PATH" >> debug_eniroment.sh
popd

SUCCESS=0
