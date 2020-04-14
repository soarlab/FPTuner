#!/bin/bash

SCRIPT_LOCATION=$(readlink -f $(dirname $0))

source ../requirements/gurobi_environment.sh

ERROR_BOUND=0.1

FPTUNER="${SCRIPT_LOCATION}/fptuner -e ${ERROR_BOUND}"

PASSES=0
FAILS=0
TOTAL=0

check_run ()
{
    # echo "FPTUNER=${FPTUNER}"
    # echo "PASSES=${PASSES}"
    # echo "FAILS=${FAILS}"

    tmp_out=$(mktemp /tmp/check_out.XXXXXX)
    tmp_err=$(mktemp /tmp/check_err.XXXXXX)

    ${FPTUNER} ${1} > ${tmp_out} 2> ${tmp_err}
    exit_code=$?

    # echo "exit_code=${exit_code}"
    # echo "stdout:"
    # cat ${tmp_out}
    # echo "stdout^"
    # echo "stderr:"
    # cat ${tmp_err}
    # echo "stderr^"

    test_name=`echo $(basename ${1}) | sed "s|\.fpcore||g"`
    echo -n "${test_name}: "

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


check_run ../benchmarks/supported_fpcores/nmse_problem_3_3_1_domain.fpcore
check_run ../benchmarks/supported_fpcores/nmse_problem_3_3_1_domain.fpcore
check_run ../benchmarks/supported_fpcores/sum.fpcore
check_run ../benchmarks/supported_fpcores/turbine3.fpcore
check_run ../benchmarks/supported_fpcores/kepler2.fpcore
check_run ../benchmarks/supported_fpcores/test02_sum8.fpcore
check_run ../benchmarks/supported_fpcores/rigidBody1.fpcore
check_run ../benchmarks/supported_fpcores/rigidBody2.fpcore
check_run ../benchmarks/supported_fpcores/nmse_problem_3_4_1_domain.fpcore
check_run ../benchmarks/supported_fpcores/nonlin1.fpcore
check_run ../benchmarks/supported_fpcores/nmse_problem_3_3_7_domain.fpcore
check_run ../benchmarks/supported_fpcores/doppler1.fpcore
check_run ../benchmarks/supported_fpcores/logexp.fpcore
check_run ../benchmarks/supported_fpcores/nmse_p42_positive_domain.fpcore
check_run ../benchmarks/supported_fpcores/doppler2.fpcore
check_run ../benchmarks/supported_fpcores/test05_nonlin1_test2.fpcore
check_run ../benchmarks/supported_fpcores/nmse_example_3_7_domain.fpcore
check_run ../benchmarks/supported_fpcores/nmse_section_3_11_domain.fpcore
check_run ../benchmarks/supported_fpcores/nmse_problem_3_3_3_domain.fpcore
check_run ../benchmarks/supported_fpcores/jetEngine.fpcore
check_run ../benchmarks/supported_fpcores/test06_sums4_sum2.fpcore
check_run ../benchmarks/supported_fpcores/i6.fpcore
check_run ../benchmarks/supported_fpcores/delta.fpcore
check_run ../benchmarks/supported_fpcores/nmse_example_3_3_domain.fpcore
check_run ../benchmarks/supported_fpcores/i4.fpcore
check_run ../benchmarks/supported_fpcores/hypot_32.fpcore
check_run ../benchmarks/supported_fpcores/floudas3.fpcore
check_run ../benchmarks/supported_fpcores/test05_nonlin1_r4.fpcore
check_run ../benchmarks/supported_fpcores/nmse_problem_3_3_2_domain.fpcore
check_run ../benchmarks/supported_fpcores/verhulst.fpcore
check_run ../benchmarks/supported_fpcores/bspline3.fpcore
check_run ../benchmarks/supported_fpcores/sqroot.fpcore
check_run ../benchmarks/supported_fpcores/nmse_problem_3_3_6_domain.fpcore
check_run ../benchmarks/supported_fpcores/kepler1.fpcore
check_run ../benchmarks/supported_fpcores/turbine2.fpcore
check_run ../benchmarks/supported_fpcores/test04_dqmom9.fpcore
check_run ../benchmarks/supported_fpcores/doppler3.fpcore
check_run ../benchmarks/supported_fpcores/turbine1.fpcore
check_run ../benchmarks/supported_fpcores/sphere.fpcore
check_run ../benchmarks/supported_fpcores/nmse_example_3_1_domain.fpcore
check_run ../benchmarks/supported_fpcores/test03_nonlin2.fpcore
check_run ../benchmarks/supported_fpcores/carbonGas.fpcore
check_run ../benchmarks/supported_fpcores/complex_sine_and_cosine_domain.fpcore
check_run ../benchmarks/supported_fpcores/predatorPrey.fpcore
check_run ../benchmarks/supported_fpcores/floudas1.fpcore
check_run ../benchmarks/supported_fpcores/nmse_section_3_5_domain.fpcore
check_run ../benchmarks/supported_fpcores/sine.fpcore
check_run ../benchmarks/supported_fpcores/nmse_problem_3_2_1_positive_domain.fpcore
check_run ../benchmarks/supported_fpcores/nmse_problem_3_3_5_domain.fpcore
check_run ../benchmarks/supported_fpcores/nmse_problem_3_4_4_domain.fpcore
check_run ../benchmarks/supported_fpcores/hypot.fpcore
check_run ../benchmarks/supported_fpcores/exp1x.fpcore
check_run ../benchmarks/supported_fpcores/x_by_xy.fpcore
check_run ../benchmarks/supported_fpcores/intro_example.fpcore
check_run ../benchmarks/supported_fpcores/hartman6.fpcore
check_run ../benchmarks/supported_fpcores/kepler0.fpcore
check_run ../benchmarks/supported_fpcores/nonlin2.fpcore
check_run ../benchmarks/supported_fpcores/floudas.fpcore
check_run ../benchmarks/supported_fpcores/sec4_example.fpcore
check_run ../benchmarks/supported_fpcores/nmse_p42_negative_domain.fpcore
check_run ../benchmarks/supported_fpcores/test06_sums4_sum1.fpcore
check_run ../benchmarks/supported_fpcores/complex_square_root_domain.fpcore
check_run ../benchmarks/supported_fpcores/exp1x_32.fpcore
check_run ../benchmarks/supported_fpcores/exp1x_log.fpcore
check_run ../benchmarks/supported_fpcores/logexp2.fpcore
check_run ../benchmarks/supported_fpcores/nmse_example_3_8_domain.fpcore
check_run ../benchmarks/supported_fpcores/hartman3.fpcore
check_run ../benchmarks/supported_fpcores/floudas2.fpcore
check_run ../benchmarks/supported_fpcores/test01_sum3.fpcore
check_run ../benchmarks/supported_fpcores/himmilbeau.fpcore
check_run ../benchmarks/supported_fpcores/nmse_problem_3_4_5_domain.fpcore
check_run ../benchmarks/supported_fpcores/nmse_problem_3_2_1_negative_domain.fpcore
check_run ../benchmarks/supported_fpcores/nmse_example_3_6_domain.fpcore
check_run ../benchmarks/supported_fpcores/sqrt_add.fpcore
check_run ../benchmarks/supported_fpcores/nmse_example_3_9_domain.fpcore
check_run ../benchmarks/supported_fpcores/delta4.fpcore
check_run ../benchmarks/supported_fpcores/triangle.fpcore
check_run ../benchmarks/supported_fpcores/nmse_example_3_5_domain.fpcore
check_run ../benchmarks/supported_fpcores/sineOrder3.fpcore

report_runs
