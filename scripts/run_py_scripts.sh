#!/usr/bin/env bash

function enable_venv() {
    python3.9 --version
    python3.9 -m pip install virtualenv
    python3.9 -m virtualenv venv3
    source venv3/bin/activate
    python --version
}

function install_requirements(){
    python -m pip install -r "$1"
}

function run_nope_tool(){
    enable_venv
    install_requirements "${WORKSPACE}"/ocp-qe-perfscale-ci/scripts/requirements.txt
    python "${WORKSPACE}"/ocp-qe-perfscale-ci/scripts/nope.py $1
}

function create_csv(){
    enable_venv
    cd "${WORKSPACE}"/e2e-benchmarking/utils || exit
    source compare.sh
    run_benchmark_comparison > "${BENCHMARK_CSV_LOG}"
}


function run_comparison(){
    enable_venv
    cd "${WORKSPACE}"/e2e-benchmarking/utils || exit
    source compare.sh
    rm -rf /tmp/**/*.csv
    rm -rf ./*.csv
    run_benchmark_comparison > "${BENCHMARK_COMP_LOG}"
}

function gen_json_comparison(){
    enable_venv
    cd "${WORKSPACE}"/e2e-benchmarking/utils || exit
    source compare.sh
    run_benchmark_comparison
}

function update_gsheet(){
    SHEET_ID=$(grep Google "${BENCHMARK_COMP_LOG}" | awk -F'/' '{print $NF}' | awk '{print $1}')
    enable_venv
    install_requirements "${WORKSPACE}/ocp-qe-perfscale-ci/scripts/sheets/requirements.txt"
    python "$WORKSPACE"/ocp-qe-perfscale-ci/scripts/sheets/noo_perfsheets_update.py --sheet-id "$SHEET_ID" $1
}
