#!/bin/bash

SCRIPT_LOCATION=$(readlink -f $(dirname $0))

#source ../requirements/gurobi_environment.sh

FPTUNER="${SCRIPT_LOCATION}/fptuner -v none"

PASSES=0
FAILS=0
TOTAL=0

check_run ()
{
    # echo "FPTUNER=${FPTUNER}"
    # echo "PASSES=${PASSES}"
    # echo "FAILS=${FAILS}"

    test_name=`echo $(basename ${1}) | sed "s|\.fpcore||g"`
    echo -n "${test_name}: "

    tmp_out=$(mktemp /tmp/check_out.XXXXXX)
    tmp_err=$(mktemp /tmp/check_err.XXXXXX)

    \time -f %e ${FPTUNER} ${1} -e 10.0 5.0 1.0 0.5 0.1 0.05 0.01 0.005 0.001 0.0005 0.0001 0.00005 0.00001 0.000005 0.000001 0.0000005 0.0000001 2>&1
    #> ${tmp_out} 2> ${tmp_err}
    exit_code=$?

    # echo "exit_code=${exit_code}"
    # echo "stdout:"
    # cat ${tmp_out}
    # echo "stdout^"
    # echo "stderr:"
    # cat ${tmp_err}
    # echo "stderr^"


    if [ ${exit_code} == 0 ] ; then
        echo "pass"
        let PASSES+=1
    else
        echo "FAIL"
        let FAILS+=1
    fi
    let TOTAL+=1

    rm ${tmp_out}
    rm ${tmp_err}
}

report_runs ()
{
    echo ""
    echo "Pass: ${PASSES}"
    echo "Fail: ${FAILS}"
    echo "Total: ${TOTAL}"
}

check_run ../benchmarks/has_sin_exp_log/complex_sine_and_cosine_domain.fpcore
check_run ../benchmarks/has_sin_exp_log/i6.fpcore
check_run ../benchmarks/has_sin_exp_log/nmse_example_3_3_domain.fpcore
check_run ../benchmarks/has_sin_exp_log/nmse_problem_3_4_5_domain.fpcore
check_run ../benchmarks/has_sin_exp_log/sphere.fpcore
check_run ../benchmarks/has_sin_exp_log/exp1x_log.fpcore
check_run ../benchmarks/has_sin_exp_log/logexp2.fpcore
check_run ../benchmarks/has_sin_exp_log/logexp.fpcore
check_run ../benchmarks/has_sin_exp_log/nmse_example_3_8_domain.fpcore
check_run ../benchmarks/has_sin_exp_log/nmse_problem_3_3_6_domain.fpcore
check_run ../benchmarks/has_sin_exp_log/exp1x_32.fpcore
check_run ../benchmarks/has_sin_exp_log/exp1x.fpcore
check_run ../benchmarks/has_sin_exp_log/hartman3.fpcore
check_run ../benchmarks/has_sin_exp_log/hartman6.fpcore
check_run ../benchmarks/has_sin_exp_log/nmse_example_3_7_domain.fpcore
check_run ../benchmarks/has_sin_exp_log/nmse_problem_3_3_7_domain.fpcore
check_run ../benchmarks/has_sin_exp_log/nmse_problem_3_4_4_domain.fpcore
check_run ../benchmarks/has_sin_exp_log/nmse_section_3_11_domain.fpcore
check_run ../benchmarks/has_sin_exp_log/nmse_section_3_5_domain.fpcore
