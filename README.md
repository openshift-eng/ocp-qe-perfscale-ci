# E2E Benchmarking CI Repo - Benchmark Cleaner

## Purpose

Want to cleanup namespaces created by e2e-benchmarking after test is finished, mostly used for kube-burner workloads

NOTE: Network-perf and router-perf cleanup both the namespaces and benchmark-operator at the end of their runs

### Parameters

BUILD_NUMBER: flexy id of cluster to cleanup on

CI_TYPE: type of workload that was run to create namespaces (Ex. node-density, pod-density)

UNINSTALL_BENCHMARK_OP: uninstall the benchmark-operator namespace and all of it's sub objects

### Author

Paige Rubendall <@paigerube14 on Github>
