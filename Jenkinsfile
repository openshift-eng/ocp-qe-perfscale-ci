// global variables for pipeline
NETOBSERV_MUST_GATHER_IMAGE = 'quay.io/netobserv/must-gather'
BASELINE_UPDATE_USERS = ['auto', 'aramesha', 'memodi']

// rename build
def userId = currentBuild.rawBuild.getCause(hudson.model.Cause$UserIdCause)?.userId
if (userId) {
    currentBuild.displayName = userId
} else {
    currentBuild.displayName = 'auto'
}

pipeline {
    environment {
        // environment variable declared here will retain its values  
        // through all stages when accessesed as ${env.VAR} 
        // If the env var values are updated during the stages it should be accessed as ${VAR}
        NOO_BUNDLE_VERSION = null
        def BENCHMARK_CSV_LOG = "$WORKSPACE/e2e-benchmarking/benchmark_csv.log"
        def BENCHMARK_COMP_LOG = "$WORKSPACE/e2e-benchmarking/benchmark_comp.log"
        def templateParams = ''
        def ingressWorkloadJob = ''
        def kubeburnerWorkloadJob = ''
    }

    // job runs on specified agent
    agent { label params.JENKINS_AGENT_LABEL }

    // set timeout and enable coloring in console output
    options {
        timeout(time: 6, unit: 'HOURS')
        ansiColor('xterm')
        parallelsAlwaysFailFast()
    }

    // job parameters
    parameters {
        string(
            name: 'JENKINS_AGENT_LABEL',
            defaultValue: 'oc416',
            description: 'Label of Jenkins agent to execute job'
        )
        string(
            name: 'FLEXY_BUILD_NUMBER',
            defaultValue: '',
            description: '''
                Build number of Flexy job that installed the cluster<br/>
                <b>Note that only AWS clusters are supported at the moment</b>
            '''
        )
        separator(
            name: 'CLUSTER_CONFIG_OPTIONS',
            sectionHeader: 'OpenShift Cluster Configuration Options',
            sectionHeaderStyle: '''
                font-size: 14px;
                font-weight: bold;
                font-family: 'Orienta', sans-serif;
            '''
        )
        string(
            name: 'WORKER_COUNT',
            defaultValue: '0',
            description: '''
                Total Worker count desired to scale the cluster to<br/>
                If set to '0' no scaling will occur<br/>
                You can also directly scale the cluster up (or down) yourself with <a href=https://mastern-jenkins-csb-openshift-qe.apps.ocp-c1.prod.psi.redhat.com/job/scale-ci/job/e2e-benchmarking-multibranch-pipeline/job/cluster-workers-scaling/>this job</a>
            '''
        )
        booleanParam(
            name: 'INFRA_WORKLOAD_INSTALL',
            defaultValue: true,
            description: 'Install workload and infrastructure nodes; required for ingress-perf. Uncheck if you already have infra nodes in your cluster'
        )
        booleanParam(
            name: 'INSTALL_DITTYBOPPER',
            defaultValue: false,
            description: 'Value to install dittybopper dashboards to cluster'
        )
        string(
            name: 'DITTYBOPPER_REPO',
            defaultValue: 'https://github.com/cloud-bulldozer/performance-dashboards.git',
            description: 'You can change this to point to your fork if needed'
        )
        string(
            name: 'DITTYBOPPER_REPO_BRANCH',
            defaultValue: 'master',
            description: 'You can change this to point to a branch on your fork if needed'
        )
        separator(
            name: 'LOKI_CONFIG_OPTIONS',
            sectionHeader: 'Loki Operator Configuration Options',
            sectionHeaderStyle: '''
                font-size: 14px;
                font-weight: bold;
                font-family: 'Orienta', sans-serif;
            '''
        )
        choice(
            name: 'LOKI_OPERATOR',
            choices: ['None', 'Released', 'Unreleased'],
            description: '''
                You can use either the latest released or unreleased version of Loki Operator:<br/>
                <b>Released</b> installs the <b>latest released downstream</b> version of the operator, i.e. what is available to customers<br/>
                <b>Unreleased</b> installs the <b>latest unreleased downstream</b> version of the operator, i.e. the most recent internal bundle<br/>
                If <b>None</b> is selected the installation will be skipped and Loki will disabled in Flowcollector
            '''
        )
        choice(
            name: 'LOKISTACK_SIZE',
            choices: ['1x.demo', '1x.extra-small', '1x.small', '1x.medium'],
            description: '''
                Depending on size of cluster, use following guidance to choose LokiStack size:<br/>
                1x.demo - 3 nodes<br/>
                1x.extra-small - 10 nodes<br/>
                1x.small - 25 or 65 nodes<br/>
                1x.medium - 120 nodes<br/>
            '''
        )
        separator(
            name: 'NETOBSERV_CONFIG_OPTIONS',
            sectionHeader: 'Network Observability Configuration Options',
            sectionHeaderStyle: '''
                font-size: 14px;
                font-weight: bold;
                font-family: 'Orienta', sans-serif;
            '''
        )
        choice(
            name: 'INSTALLATION_SOURCE',
            choices: ['None', 'Official', 'Internal', 'Source'],
            description: '''
                Network Observability can be installed from the following sources:<br/>
                <b>Official</b> installs the <b>latest released downstream</b> version of the operator, i.e. what is available to customers<br/>
                <b>Internal</b> installs the <b>latest unreleased downstream</b> version of the operator, i.e. the most recent internal bundle<br/>
                <b>Source</b> installs the <b>latest unreleased upstream</b> version of the operator, i.e. directly from the main branch of the upstream source code<br/>
                If <b>None</b> is selected the Operator installation and flowcollector configuration will be skipped
            '''
        )
        string(
            name: 'IIB_OVERRIDE',
            defaultValue: '',
            description: '''
                If using Internal installation, you can specify here a specific internal index image to use in the CatalogSource rathar than using the most recent bundle<br/>
                These IDs can be found in CVP emails under 'Index Image Location' section<br/>
                e.g. <b>450360</b>
            '''
        )
        string(
            name: 'OPERATOR_PREMERGE_OVERRIDE',
            defaultValue: '',
            description: '''
                If using Source installation, you can specify here a specific premerge Operator bundle image to use in the CatalogSource rather than using the main branch<br/>
                These SHA hashes can be found in PR's after adding the label '/ok-to-test'<br/>
                e.g. <b>e2bdef6</b>
            '''
        )
        string(
            name: 'FLP_PREMERGE_OVERRIDE',
            defaultValue: '',
            description: '''
                You can specify here a specific FLP premerge image to use rather than using the operator defined image<br/>
                These SHA hashes can be found in FLP PR's after adding the label '/ok-to-test'<br/>
                e.g. <b>e2bdef6</b>
            '''
        )
        string(
            name: 'EBPF_PREMERGE_OVERRIDE',
            defaultValue: '',
            description: '''
                You can specify here a specific eBPF premerge image to use rather than using the operator defined image<br/>
                These SHA hashes can be found in eBPF PR's after adding the label '/ok-to-test'<br/>
                e.g. <b>e2bdef6</b>
            '''
        )
        separator(
            name: 'FLOWCOLLECTOR_CONFIG_OPTIONS',
            sectionHeader: 'Flowcollector Configuration Options',
            sectionHeaderStyle: '''
                font-size: 14px;
                font-weight: bold;
                font-family: 'Orienta', sans-serif;
            '''
        )
        string(
            name: 'EBPF_SAMPLING_RATE',
            defaultValue: '1',
            description: 'Rate at which to sample flows'
        )
        string(
            name: 'EBPF_CACHE_MAXFLOWS',
            defaultValue: '100000',
            description: 'eBPF max flows that can be cached before evicting'
        )
        booleanParam(
            name: 'EBPF_PRIVILEGED',
            defaultValue: true,
            description: 'Uncheck this box to run ebpf-agent in unprivileged mode'
        )
        booleanParam(
            name: 'ENABLE_KAFKA',
            defaultValue: true,
            description: 'Check this box to setup Kafka for NetObserv or to update Kafka configs even if it is already installed'
        )
        choice(
            name: 'TOPIC_PARTITIONS',
            choices: [6, 10, 24, 48],
            description: '''
                Number of Kafka Topic Partitions. 48 Partitions are used for all Perf testing scenarios<br/>
            '''
        )
        string(
            name: 'FLP_KAFKA_REPLICAS',
            defaultValue: '',
            description: '''
                Replicas should be at least half the number of Kafka TOPIC_PARTITIONS and should not exceed number of TOPIC_PARTITIONS or number of nodes:<br/>
                <b>Leave this empty if you're triggering standard perf-workloads, default of 6 and 18 FLP_KAFKA_REPLICAS will be used for node-density-heavy and cluster-density-v2 workloads respectively</b><br/>
                3 - for non-perf testing environments<br/>
                <b>Use this field to overwrite default FLP_KAFKA_REPLICAS, for e.g. when triggering for ingress-perf workload</b><br/>
            '''
        )
        separator(
            name: 'WORKLOAD_CONFIG_OPTIONS',
            sectionHeader: 'Workload Configuration Options',
            sectionHeaderStyle: '''
                font-size: 14px;
                font-weight: bold;
                font-family: 'Orienta', sans-serif;
            '''
        )
        choice(
            name: 'WORKLOAD',
            choices: ['None', 'cluster-density-v2', 'node-density-heavy', 'ingress-perf'],
            description: '''
                Workload to run on Netobserv-enabled cluster<br/>
                "cluster-density-v2" and "node-density-heavy" options will trigger "kube-burner-ocp" job<br/>
                "ingress-perf" will always run with node-density-heavy and cluster-density-v2 workloads. If only ingress-perf workload needs to be run, select that option.<br/>
                "None" will run no workload<br/>
                For additional guidance on configuring workloads, see <a href=https://docs.google.com/spreadsheets/d/1DdFiJkCMA4c35WQT2SWXbdiHeCCcAZYjnv6wNpsEhIA/edit?usp=sharing#gid=1506806462>here</a>
            '''
        )
        booleanParam(
            name: 'RUN_INGRESS_PERF_IN_PARALLEL',
            defaultValue: true,
            description: 'Uncheck this box if you want to disable running ingress-perf workload in parallel to node-density-heavy or cluster-density-v2 workload'
        )
        string(
            name: 'VARIABLE',
            defaultValue: '1000',
            description: '''
                This variable configures parameter needed for each type of workload. <b>Not used by <b><a href=https://github.com/cloud-bulldozer/e2e-benchmarking/blob/master/workloads/ingress-perf/README.md>ingress-perf</a> workload</b>.<br/>
                <a href=https://github.com/cloud-bulldozer/e2e-benchmarking/blob/master/workloads/kube-burner/README.md>cluster-density-v2</a>: This will export JOB_ITERATIONS env variable; set to 4 * num_workers. This variable sets the number of iterations to perform (1 namespace per iteration).<br/>
                <a href=https://github.com/cloud-bulldozer/e2e-benchmarking/blob/master/workloads/kube-burner/README.md>node-density-heavy</a>: This will export PODS_PER_NODE env variable; set to 200, work up to 250. Creates this number of applications proportional to the calculated number of pods / 2<br/>
                Read <a href=https://github.com/openshift-qe/ocp-qe-perfscale-ci/tree/kube-burner/README.md>here</a> for details about each variable
            '''
        )
        string(
            name: 'NODE_COUNT',
            defaultValue: '3',
            description: '''
                Only for <b>node-density-heavy</b><br/>
                Should be the number of worker nodes on your cluster (after scaling)
            '''
        )
        booleanParam(
            name: 'CERBERUS_CHECK',
            defaultValue: false,
            description: 'Check cluster health status after workload runs'
        )
        string(
            name: 'E2E_BENCHMARKING_REPO',
            defaultValue: 'https://github.com/cloud-bulldozer/e2e-benchmarking',
            description: 'You can change this to point to your fork if needed'
        )
        string(
            name: 'E2E_BENCHMARKING_REPO_BRANCH',
            defaultValue: 'master',
            description: 'You can change this to point to a branch on your fork if needed.'
        )
        separator(
            name: 'NOPE_TOUCHSTONE_CONFIG_OPTIONS',
            sectionHeader: 'NOPE and Touchstone Configuration Options',
            sectionHeaderStyle: '''
                font-size: 14px;
                font-weight: bold;
                font-family: 'Orienta', sans-serif;
            '''
        )
        booleanParam(
            name: 'NOPE',
            defaultValue: false,
            description: '''
                Check this box to run the NOPE tool after the workload completes<br/>
                If the tool successfully uploads results to Elasticsearch, Touchstone will be run afterword
            '''
        )
        booleanParam(
            name: 'GEN_CSV',
            defaultValue: false,
            description: '''
                Boolean to create Google Sheets with statistical and comparison data where applicable<br/>
                Note this will only run if the NOPE tool successfully uploads to Elasticsearch
            '''
        )
        booleanParam(
            name: 'NOPE_DUMP_ONLY',
            defaultValue: false,
            description: '''
                Check this box to dump data collected by the NOPE tool to a file without uploading to Elasticsearch<br/>
                Touchstone will <b>not</b> be run if this box is checked
            '''
        )
        booleanParam(
            name: 'NOPE_DEBUG',
            defaultValue: false,
            description: 'Check this box to run the NOPE tool in debug mode for additional logging'
        )
        string(
            name: 'NOPE_JIRA',
            defaultValue: '',
            description: '''
                Add a NETOBSERV Jira ticket or any context to be associated with this Perf run, <b>must set when INSTALLATION_SOURCE = None</b><br/>
            '''
        )
        booleanParam(
            name: 'RUN_BASELINE_COMPARISON',
            defaultValue: false,
            description: '''
                If the workload completes successfully and is uploaded to Elasticsearch, checking this box will configure Touchstone to run a comparison between the job run and a baseline UUID<br/>
                By default, the NOPE tool will be used to fetch the most recent baseline for the given workload from Elasticsearch<br/>
                Alternatively, you can specify a specific baseline UUID to run the comparison with using the text box below
            '''
        )
        string(
            name: 'BASELINE_UUID_OVERRIDE',
            defaultValue: '',
            description: '''
                Override baseline UUID to compare this run to<br/>
                Note you will still need to check the box above to run the comparison<br/>
                Using this override will casue the job to not automatically update the Elasticsearch baseline even is the comparsion is a success
            '''
        )
        separator(
            name: 'CLEANUP_OPTIONS',
            sectionHeader: 'Cleanup Options',
            sectionHeaderStyle: '''
                font-size: 14px;
                font-weight: bold;
                font-family: 'Orienta', sans-serif;
            '''
        )
        booleanParam(
            name: 'NUKEOBSERV',
            defaultValue: false,
            description: '''
                Check this box to completely remove NetObserv and all related resources at the end of the pipeline run<br/>
                This includes the AWS S3 bucket, Kafka (if applicable), LokiStack, and flowcollector
            '''
        )
        booleanParam(
            name: 'DESTROY_CLUSTER',
            defaultValue: false,
            description: '''
                Check this box to destroy the cluster at the end of the pipeline run<br/>
                Ensure external resources such as AWS S3 buckets are destroyed as well
            '''
        )
    }

    stages {
        stage('Validate job parameters') {
            steps {
                script {
                    validateParams()
                }
            }
        }
        stage('Setup testing environment') {
            steps {
                // copy artifacts from Flexy install
                copyArtifacts(
                    fingerprintArtifacts: true,
                    projectName: 'ocp-common/Flexy-install',
                    selector: specific(params.FLEXY_BUILD_NUMBER),
                    target: 'flexy-artifacts'
                )
                // checkout ocp-qe-perfscale-ci repo
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: GIT_BRANCH ]],
                    userRemoteConfigs: [[url: GIT_URL ]],
                    extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'ocp-qe-perfscale-ci']]
                ])
                // login to Flexy cluster and set AWS credentials in Shell env for pipeline execution
                withCredentials([file(credentialsId: 'b73d6ed3-99ff-4e06-b2d8-64eaaf69d1db', variable: 'OCP_AWS')]) {
                    script {
                        // set USER variable to be included in AWS bucket name and determine baseline upload permissions
                        if (userId) {
                            env.USER = userId
                        }
                        else {
                            env.USER = 'auto'
                        }
                        println("USER identified as ${env.USER}")
                        buildInfo = readYaml(file: 'flexy-artifacts/BUILDINFO.yml')
                        buildInfo.params.each { env.setProperty(it.key, it.value) }
                        installData = readYaml(file: 'flexy-artifacts/workdir/install-dir/cluster_info.yaml')
                        OCP_BUILD = installData.INSTALLER.VERSION
                        env.MAJOR_VERSION = installData.INSTALLER.VER_X
                        env.MINOR_VERSION = installData.INSTALLER.VER_Y
                        currentBuild.displayName = "${currentBuild.displayName}-${params.FLEXY_BUILD_NUMBER}"
                        currentBuild.description = "Flexy-install Job: <a href=\"${buildInfo.buildUrl}\">${params.FLEXY_BUILD_NUMBER}</a> using OCP build <b>${OCP_BUILD}</b><br/>"
                        setupReturnCode = sh(returnStatus: true, script: """
                            mkdir -p ~/.kube
                            cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config
                            oc get route console -n openshift-console
                            mkdir -p ~/.aws
                            cp -f $OCP_AWS ~/.aws/credentials
                            echo "[profile default]
                            region = `cat $WORKSPACE/flexy-artifacts/workdir/install-dir/terraform.platform.auto.tfvars.json | jq -r ".aws_region"`
                            output = text" > ~/.aws/config
                        """)
                        if (setupReturnCode.toInteger() != 0) {
                            error("Failed to setup testing environment :(")
                        }
                        else {
                            println("Successfully setup testing environment :)")
                        }
                    }
                }
            }
        }
        stage('Scale workers and install infra nodes') {
            when {
                expression { params.WORKER_COUNT != '0' && params.WORKER_COUNT != '' }
            }
            steps {
                script {
                    // call E2E Benchmarking scale job to scale cluster
                    scaleJob = build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cluster-workers-scaling/', parameters: [
                        string(name: 'BUILD_NUMBER', value: params.FLEXY_BUILD_NUMBER),
                        string(name: 'JENKINS_AGENT_LABEL', value: params.JENKINS_AGENT_LABEL),
                        string(name: 'WORKER_COUNT', value: params.WORKER_COUNT),
                        booleanParam(name: 'INFRA_WORKLOAD_INSTALL', value: params.INFRA_WORKLOAD_INSTALL),
                        booleanParam(name: 'INSTALL_DITTYBOPPER', value: false),
                    ]
                    currentBuild.description += "Scale Job: <b><a href=${scaleJob.absoluteUrl}>${scaleJob.getNumber()}</a></b><br/>"
                    // fail pipeline if scaling failed
                    if (scaleJob.result != 'SUCCESS') {
                        error('Scale job failed :(')
                    }
                    // otherwise continue and display newly scaled nodes and count of totals based on role
                    else {
                        println("Successfully scaled cluster to ${params.WORKER_COUNT} worker nodes :)")
                        if (params.INFRA_WORKLOAD_INSTALL) {
                            println('Successfully installed infrastructure and workload nodes :)')
                        }
                        sh(returnStatus: true, script: '''
                            oc get nodes
                            echo "Total Worker Nodes: `oc get nodes | grep worker | wc -l`"
                            echo "Total Infra Nodes: `oc get nodes | grep infra | wc -l`"
                            echo "Total Workload Nodes: `oc get nodes | grep workload | wc -l`"
                        ''')
                    }
                }
            }
        }
        stage('Install Loki Operator') {
            when {
                expression { params.LOKI_OPERATOR != 'None' }
            }
            steps {
                script {
                    // if an 'Unreleased' installation, use aosqe-index image for unreleased CatalogSource image
                    if (params.LOKI_OPERATOR == 'Unreleased') {
                        env.DOWNSTREAM_IMAGE = "quay.io/openshift-qe-optional-operators/aosqe-index:v${env.MAJOR_VERSION}.${env.MINOR_VERSION}"
                    }
                    // attempt installation of Loki Operator from selected source
                    println("Installing ${params.LOKI_OPERATOR} version of Loki Operator...")
                    lokiReturnCode = sh(returnStatus: true, script: """
                        source $WORKSPACE/ocp-qe-perfscale-ci/scripts/netobserv.sh
                        deploy_lokistack
                    """)
                    // fail pipeline if installation failed
                    if (lokiReturnCode.toInteger() != 0) {
                        error("${params.LOKI_OPERATOR} version of Loki Operator installation failed :(")
                    }
                    // otherwise continue and display controller and lokistack pods running in cluster
                    else {
                        println("Successfully installed ${params.LOKI_OPERATOR} version of Loki Operator :)")
                        sh(returnStatus: true, script: '''
                            oc get pods -n openshift-operators-redhat
                            oc get pods -n netobserv
                        ''')
                    }
                }
            }
        }
        stage('Install NetObserv Operator') {
            when {
                expression { params.INSTALLATION_SOURCE != 'None' }
            }
            steps {
                script {
                    // if an 'Internal' installation, determine whether to use aosqe-index image or specific IIB image
                    if (params.INSTALLATION_SOURCE == 'Internal') {
                        if (params.IIB_OVERRIDE != '') {
                            env.DOWNSTREAM_IMAGE = "brew.registry.redhat.io/rh-osbs/iib:${params.IIB_OVERRIDE}"
                            env.CATALOG_IMAGE=env.DOWNSTREAM_IMAGE
                        }
                        else {
                            env.DOWNSTREAM_IMAGE = "quay.io/openshift-qe-optional-operators/aosqe-index:v${env.MAJOR_VERSION}.${env.MINOR_VERSION}"
                            env.CATALOG_IMAGE=env.DOWNSTREAM_IMAGE
                        }
                    }

                    if (params.INSTALLATION_SOURCE == 'Official') {
                        env.CATALOG_IMAGE= sh(returnStdout: true, script: "oc get catalogsource/redhat-operators -n openshift-marketplace -o jsonpath='{.spec.image}'").trim()
                    }

                    // if a 'Source' installation, determine whether to use main image or specific premerge image
                    if (params.INSTALLATION_SOURCE == 'Source') {
                        if (params.OPERATOR_PREMERGE_OVERRIDE != '') {
                            env.UPSTREAM_IMAGE = "quay.io/netobserv/network-observability-operator-catalog:v0.0.0-${OPERATOR_PREMERGE_OVERRIDE}"
                            env.CATALOG_IMAGE=env.UPSTREAM_IMAGE
                            NOO_BUNDLE_VERSION="v0.0.0-${OPERATOR_PREMERGE_OVERRIDE}"
                        }
                        else {
                            env.UPSTREAM_IMAGE = "quay.io/netobserv/network-observability-operator-catalog:v0.0.0-main"
                            env.CATALOG_IMAGE=env.UPSTREAM_IMAGE
                            NOO_BUNDLE_VERSION="v0.0.0-main"
                        }
                        println("Using NOO Bundle version: ${NOO_BUNDLE_VERSION}")
                        currentBuild.description += "NetObserv Bundle Version: <b>${NOO_BUNDLE_VERSION}</b><br/>"
                    }
                    // attempt installation of Network Observability from selected source
                    println("Installing Network Observability from ${params.INSTALLATION_SOURCE}...")
                    netobservReturnCode = sh(returnStatus: true, script: """
                        source $WORKSPACE/ocp-qe-perfscale-ci/scripts/netobserv.sh
                        deploy_netobserv
                    """)
                    // fail pipeline if installation failed
                    if (netobservReturnCode.toInteger() != 0) {
                        error("Network Observability installation from ${params.INSTALLATION_SOURCE} failed :(")
                    }
                    // patch in premerge images if specified, fail pipeline if patching fails on any component
                    if (params.EBPF_PREMERGE_OVERRIDE != '') {
                        env.EBPF_PREMERGE_IMAGE = "quay.io/netobserv/netobserv-ebpf-agent:${EBPF_PREMERGE_OVERRIDE}"
                        netobservEBPFPatchReturnCode = sh(returnStatus: true, script: """
                            source $WORKSPACE/ocp-qe-perfscale-ci/scripts/netobserv.sh
                            patch_netobserv "ebpf" $EBPF_PREMERGE_IMAGE
                        """)
                        if (netobservEBPFPatchReturnCode.toInteger() != 0) {
                            error("Network Observability eBPF image patch ${params.EBPF_PREMERGE_OVERRIDE} failed :(")
                        }
                    }
                    if (params.FLP_PREMERGE_OVERRIDE != '') {
                        env.FLP_PREMERGE_IMAGE = "quay.io/netobserv/flowlogs-pipeline:${FLP_PREMERGE_OVERRIDE}"
                        netobservFLPPatchReturnCode = sh(returnStatus: true, script: """
                            source $WORKSPACE/ocp-qe-perfscale-ci/scripts/netobserv.sh
                            patch_netobserv "flp" $FLP_PREMERGE_IMAGE
                        """)
                        if (netobservFLPPatchReturnCode.toInteger() != 0) {
                            error("Network Observability FLP image patch ${params.FLP_PREMERGE_OVERRIDE} failed :(")
                        }
                    }
                    // if installation and patching succeeds, continue and display controller, FLP, and eBPF pods running in cluster
                    else {
                        println("Successfully installed Network Observability from ${params.INSTALLATION_SOURCE} :)")
                        sh(returnStatus: true, script: '''
                            oc get pods -n openshift-netobserv-operator
                        ''')
                    }
                }
            }
        }
        stage('Capture NetObserv Operator Bundle version'){
            when {
                beforeAgent true
                expression { params.INSTALLATION_SOURCE == "Official" || params.INSTALLATION_SOURCE == "Internal" }
            }
            agent { 
                // run on upshift_docker agent because
                // opm needs registry login
                label "upshift_docker"
            }
            steps {
                // checkout ocp-qe-perfscale-ci repo
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: GIT_BRANCH ]],
                    userRemoteConfigs: [[url: GIT_URL ]],
                    extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'ocp-qe-perfscale-ci']]
                ])
                // copy artifacts from Flexy install
                copyArtifacts(
                    fingerprintArtifacts: true,
                    projectName: 'ocp-common/Flexy-install',
                    selector: specific(params.FLEXY_BUILD_NUMBER),
                    target: 'flexy-artifacts'
                )
                withCredentials(
                    [usernamePassword(credentialsId: 'c1802784-0f74-4b35-99fb-32dfa9a207ad', usernameVariable: 'QUAY_USER', passwordVariable: 'QUAY_PASSWORD')]){
                    sh 'podman login -u $QUAY_USER -p $QUAY_PASSWORD quay.io'
                }
                withCredentials([usernamePassword(credentialsId: 'db799772-7708-4ed0-bfe7-0fddfc8088eb', usernameVariable: 'REG_REDHAT_USER', passwordVariable: 'REG_REDHAT_PASSWORD')]){
                    sh 'podman login -u $REG_REDHAT_USER -p ${REG_REDHAT_PASSWORD} registry.redhat.io'
                }
                withCredentials([usernamePassword(credentialsId: 'brew-registry-osbs-mirror', usernameVariable: 'BREW_USER', passwordVariable: 'BREW_PASSWORD')]){ 
                    sh 'podman login -u $BREW_USER -p $BREW_PASSWORD brew.registry.redhat.io'
                }
                withCredentials([usernamePassword(credentialsId: '41c2dd39-aad7-4f07-afec-efc052b450f5', usernameVariable: 'REG_STAGE_USER', passwordVariable: 'REG_STAGE_PASSWORD')]){
                    sh 'podman login -u $REG_STAGE_USER -p $REG_STAGE_PASSWORD registry.stage.redhat.io'
                }
                script {
                    BUNDLE_VERSION=sh(returnStdout: true, script: """
                        $WORKSPACE/ocp-qe-perfscale-ci/scripts/build_info.sh
                        """).trim()
                    if (BUNDLE_VERSION != '') {
                        println("Found NOO Bundle version: ${BUNDLE_VERSION}")
                        NOO_BUNDLE_VERSION = "${BUNDLE_VERSION}"
        
                        currentBuild.description += "NetObserv Bundle Version: <b>${NOO_BUNDLE_VERSION}</b><br/>"
                    }
                    else {
                        println("Failed to find NOO_BUNDLE_VERSION :(, comparison may not have context and may use UUID")
                    }
                }
            }
        }
        stage('Configure NetObserv, flowcollector, and Kafka') {
            when {
                expression { params.INSTALLATION_SOURCE != "None"}
            }
            steps {
                script {
                    // attempt to enable or update Kafka if applicable
                    println('Checking if Kafka needs to be enabled or updated...')
                    if (params.ENABLE_KAFKA == true) {
                        println("Configuring Kafka...")
                        kafkaReturnCode = sh(returnStatus: true, script: """
                            source $WORKSPACE/ocp-qe-perfscale-ci/scripts/netobserv.sh
                            deploy_kafka
                        """)
                        // fail pipeline if installation and/or configuration failed
                        if (kafkaReturnCode.toInteger() != 0) {
                            error('Failed to deploy Kafka :(')
                        }
                        // otherwise continue and display controller and pods in netobserv NS
                        else {
                            println('Successfully enabled Kafka :)')
                            sh(returnStatus: true, script: '''
                                oc get pods -n openshift-operators
                                oc get pods -n netobserv
                            ''')
                        }
                    }
                    else {
                        println('Skipping Kafka configuration...')
                    }
                    setKafkaReplicas()
                    templateParams = setTemplateParams()
                    fcReturnCode = sh(returnStatus: true, script: """
                          source $WORKSPACE/ocp-qe-perfscale-ci/scripts/netobserv.sh
                          createFlowCollector $templateParams
                        """)
                    if (fcReturnCode.toInteger() != 0) {
                        error('Failed to deploy flowcollector :(')
                    }
                    else {
                        println('Successfully deployed Flowcollector :)')
                    }
                }
            }
        }
        stage('Install Dittybopper') {
            when {
                expression { params.INSTALL_DITTYBOPPER == true }
            }
            steps {
                // checkout performance dashboards repo
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: params.DITTYBOPPER_REPO_BRANCH ]],
                    userRemoteConfigs: [[url: params.DITTYBOPPER_REPO ]],
                    extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'performance-dashboards']]
                ])
                script {
                    DITTYBOPPER_PARAMS = "-i $WORKSPACE/ocp-qe-perfscale-ci/scripts/queries/netobserv_dittybopper.json"
                    // attempt installation of dittybopper
                    dittybopperReturnCode = sh(returnStatus: true, script: """
                        source $WORKSPACE/ocp-qe-perfscale-ci/scripts/netobserv.sh
                        . $WORKSPACE/performance-dashboards/dittybopper/deploy.sh $DITTYBOPPER_PARAMS
                    """)
                    // fail pipeline if installation failed, continue otherwise
                    if (dittybopperReturnCode.toInteger() != 0) {
                        error('Installation of Dittybopper failed :(')
                    }
                    else {
                        println('Successfully installed Dittybopper :)')
                    }
                }
            }
        }
        stage('Run kube-burner and ingress-perf workload parallel') {
            when {
                expression { params.WORKLOAD != 'None' }
            }
            parallel {
                stage('kube-burner workload'){
                    when {
                        expression { params.WORKLOAD != 'ingress-perf' }
                    }
                    steps {
                        script {
                            // set build name and remove previous artifacts
                            currentBuild.displayName = "${currentBuild.displayName}-${params.WORKLOAD}"
                            sh(script: "rm -rf $WORKSPACE/workload-artifacts/*.json")
                            env.WORKLOAD_JENKINS_JOB = 'scale-ci/e2e-benchmarking-multibranch-pipeline/kube-burner-ocp'
                            // remove this and have it true by default once 
                            // CHURN is supported for node-density-heavy
                            if (params.WORKLOAD == "cluster-density-v2") {
                                env.CHURN = true
                            }
                            else {
                                env.CHURN = false
                            }
                            kubeburnerWorkloadJob = build job: env.WORKLOAD_JENKINS_JOB, parameters: [
                                string(name: 'BUILD_NUMBER', value: params.FLEXY_BUILD_NUMBER),
                                string(name: 'WORKLOAD', value: params.WORKLOAD),
                                booleanParam(name: 'CLEANUP', value: true),
                                booleanParam(name: 'CERBERUS_CHECK', value: params.CERBERUS_CHECK),
                                booleanParam(name: 'MUST_GATHER', value: true),
                                string(name: 'IMAGE', value: NETOBSERV_MUST_GATHER_IMAGE),
                                booleanParam(name: 'CHURN', value: env.CHURN),
                                string(name: 'VARIABLE', value: params.VARIABLE), 
                                string(name: 'NODE_COUNT', value: params.NODE_COUNT),
                                booleanParam(name: 'GEN_CSV', value: false),
                                string(name: 'JENKINS_AGENT_LABEL', value: params.JENKINS_AGENT_LABEL),
                                string(name: 'E2E_BENCHMARKING_REPO', value: params.E2E_BENCHMARKING_REPO),
                                string(name: 'E2E_BENCHMARKING_REPO_BRANCH', value: params.E2E_BENCHMARKING_REPO_BRANCH)
                            ]
                        }
                    }
                }
                stage('Ingress-perf workload'){
                    when {
                        expression { params.RUN_INGRESS_PERF_IN_PARALLEL == true || params.WORKLOAD == 'ingress-perf'}
                    }
                    steps {
                        script {
                            env.INGRESSPERF_JENKINS_JOB = 'scale-ci/e2e-benchmarking-multibranch-pipeline/ingress-perf'
                            // sleep 10 minutes after triggering kube-burner workload.
                            if (params.WORKLOAD != 'ingress-perf') {
                                sleep 600
                            }
                            else {
                                // for nope tool
                                env.WORKLOAD_JENKINS_JOB = env.INGRESSPERF_JENKINS_JOB
                                currentBuild.displayName = "${currentBuild.displayName}-${params.WORKLOAD}"
                            }
                            env.INGRESSPERF_JENKINS_JOB = 'scale-ci/e2e-benchmarking-multibranch-pipeline/ingress-perf'
                            ingressWorkloadJob = build job: env.INGRESSPERF_JENKINS_JOB, parameters: [
                                string(name: 'BUILD_NUMBER', value: params.FLEXY_BUILD_NUMBER),
                                booleanParam(name: 'CERBERUS_CHECK', value: params.CERBERUS_CHECK),
                                booleanParam(name: 'MUST_GATHER', value: true),
                                string(name: 'IMAGE', value: NETOBSERV_MUST_GATHER_IMAGE),
                                string(name: 'JENKINS_AGENT_LABEL', value: params.JENKINS_AGENT_LABEL),
                                booleanParam(name: 'GEN_CSV', value: false),
                                string(name: 'E2E_BENCHMARKING_REPO', value: params.E2E_BENCHMARKING_REPO),
                                string(name: 'E2E_BENCHMARKING_REPO_BRANCH', value: params.E2E_BENCHMARKING_REPO_BRANCH)
                            ]
                        }
                    }
                    
                }
            }
        }
        stage('Capture workload results'){
            when {
                expression { params.WORKLOAD != 'None'}
            }
            steps {
                script {
                    captureWorkloadResults()
                }
            }
        }
        stage('Run NOPE tool') {
            when {
                expression { params.WORKLOAD != 'None' && params.NOPE == true }
            }
            steps {
                withCredentials([usernamePassword(credentialsId: 'elasticsearch-perfscale-ocp-qe', usernameVariable: 'ES_USERNAME', passwordVariable: 'ES_PASSWORD')]) {
                    script {
                        // construct arguments for NOPE tool and execute
                        NOPE_ARGS = "--starttime $STARTDATEUNIXTIMESTAMP --endtime $ENDDATEUNIXTIMESTAMP --jenkins-job $WORKLOAD_JENKINS_JOB --jenkins-build $JENKINS_BUILD --uuid ${env.UUID}"
                        if ("${NOO_BUNDLE_VERSION}" != 'null'){
                            echo "NOO_BUNDLE_VERSION: ${NOO_BUNDLE_VERSION}"
                            NOPE_ARGS += " --noo-bundle-version ${NOO_BUNDLE_VERSION}"
                        }
                        if (params.NOPE_DUMP_ONLY == true) {
                            NOPE_ARGS += " --dump-only"
                        }
                        if (params.NOPE_DEBUG == true) {
                            NOPE_ARGS += " --debug"
                        }
                        if (params.NOPE_JIRA != '') {
                            NOPE_ARGS += " --jira ${params.NOPE_JIRA}"
                        }
                        env.NOPE_ARGS = NOPE_ARGS
                        nopeReturnCode = sh(returnStatus: true, script: """
                            source $WORKSPACE/ocp-qe-perfscale-ci/scripts/run_py_scripts.sh
                            run_nope_tool "$NOPE_ARGS"
                        """)
                        // fail pipeline if NOPE run failed, continue otherwise
                        if (nopeReturnCode.toInteger() == 2) {
                            unstable('NOPE tool ran, but Elasticsearch upload failed - check build artifacts for data and try uploading it locally :/')
                        }
                        else if (nopeReturnCode.toInteger() != 0) {
                            error('NOPE tool failed :(')
                        }
                        else {
                            println('Successfully ran NOPE tool :)')
                        }
                    }
                }
            }
        }
        stage('Run Touchstone tool') {
            when {
                expression { params.WORKLOAD != 'None' && params.NOPE == true && params.NOPE_DUMP_ONLY == false && currentBuild.currentResult != "UNSTABLE" }
            }
            steps {
                // checkout e2e-benchmarking repo
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: params.E2E_BENCHMARKING_REPO_BRANCH ]],
                    userRemoteConfigs: [[url: params.E2E_BENCHMARKING_REPO ]],
                    extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'e2e-benchmarking']]
                ])
                withCredentials([usernamePassword(credentialsId: 'elasticsearch-perfscale-ocp-qe', usernameVariable: 'ES_USERNAME', passwordVariable: 'ES_PASSWORD'), file(credentialsId: 'sa-google-sheet', variable: 'GSHEET_KEY_LOCATION')]) {
                    script {
                        println('Running Touchstone to get statistics for workload run...')
                        // set env variables needed for touchstone (note UUID and GSHEET_KEY_LOCATION are needed but already set above) and execute
                        env.CONFIG_LOC = "$WORKSPACE/ocp-qe-perfscale-ci/scripts/queries"
                        env.COMPARISON_CONFIG = 'netobserv_touchstone_statistics_config.json'
                        env.ES_SERVER = "https://$ES_USERNAME:$ES_PASSWORD@search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com"
                        env.EMAIL_ID_FOR_RESULTS_SHEET = "openshift-netobserv-team@redhat.com"
                        env.GEN_CSV = params.GEN_CSV
                        env.GEN_JSON = false
                        env.NETWORK_TYPE = sh(returnStdout: true, script: "oc get network.config/cluster -o jsonpath='{.spec.networkType}'").trim()
                        env.WORKLOAD = params.WORKLOAD
                        statisticsReturnCode = sh(returnStatus: true, script: """
                            source $WORKSPACE/ocp-qe-perfscale-ci/scripts/run_py_scripts.sh
                            create_csv
                        """)
                        
                        if(fileExists("${BENCHMARK_CSV_LOG}")){
                            try {
                                METRICS_SHEET = sh(script: "grep Google ${BENCHMARK_CSV_LOG} | awk '{print \$6}'", returnStdout: true).trim()
                                currentBuild.description += """Metrics sheet: <a href="${METRICS_SHEET}">${env.UUID}</a><br/>"""
                            } catch (err) {
                                    println("Failed to capture metrics google sheet  :(")
                            }
                        }
                        // mark pipeline as unstable if Touchstone failed, continue otherwise
                        if (statisticsReturnCode.toInteger() != 0) {
                            unstable('Touchstone tool failed - run locally with the given UUID to get workload run statistics :(')
                        }
                        else {
                            println('Successfully ran Touchstone tool :)')
                            // do tolerancy rules check if specified
                            if (params.RUN_BASELINE_COMPARISON) {
                                env.BASELINE_UUID = ''
                                // use baseline override if specified
                                if (params.BASELINE_UUID_OVERRIDE != '') {
                                    env.BASELINE_UUID = params.BASELINE_UUID_OVERRIDE
                                }
                                // otherwise call the NOPE tool to fetch the most recent baseline for the given workload
                                else {
                                    NOPE_ARGS = ''
                                    if (params.NOPE_DEBUG == true) {
                                        NOPE_ARGS += ' --debug'
                                    }
                                    NOPE_ARGS += " baseline --fetch $WORKLOAD"
                                    fetchReturnCode = sh(returnStatus: true, script: """
                                        source $WORKSPACE/ocp-qe-perfscale-ci/scripts/run_py_scripts.sh
                                        run_nope_tool "$NOPE_ARGS"
                                    """)
                                    if (fetchReturnCode.toInteger() != 0) {
                                        unstable('NOPE baseline fetching failed - run locally with UUIDs to get baseline comparison statistics :(')
                                    }
                                    else {
                                        baselineInfo = readJSON(file: "$WORKSPACE/ocp-qe-perfscale-ci/data/baseline.json")
                                        baselineInfo.each { env.setProperty(it.key.toUpperCase(), it.value) }
                                    }
                                }
                                currentBuild.description += "<b>BASELINE_UUID:</b> ${env.BASELINE_UUID}<br/>"
                                if (env.BASELINE_UUID != '') {
                                    println("Running automatic comparison between new UUID ${env.UUID} with provided baseline UUID ${env.BASELINE_UUID}...")
                                    // set additional vars for tolerancy rules check
                                    env.TOLERANCE_LOC = "$WORKSPACE/ocp-qe-perfscale-ci/scripts/queries/"
                                    env.TOLERANCY_RULES = "netobserv_touchstone_tolerancy_rules.yaml"
                                    // COMPARISON_CONFIG is changed here to only focus on specific statistics
                                    env.COMPARISON_CONFIG = 'netobserv_touchstone_tolerancy_config.json'
                                    // ES_SERVER and ES_SERVER_BASELINE are the same since we store all of our results on the same ES server
                                    env.ES_SERVER_BASELINE = "https://$ES_USERNAME:$ES_PASSWORD@search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com"
                                    baselineReturnCode = sh(returnStatus: true, script: """
                                            source $WORKSPACE/ocp-qe-perfscale-ci/scripts/run_py_scripts.sh
                                            run_comparison
                                    """)

                                    if(fileExists("${BENCHMARK_COMP_LOG}")){
                                        try {
                                            COMP_SHEET = sh(script: "grep Google ${BENCHMARK_COMP_LOG} | awk '{print \$6}'", returnStdout: true).trim()
                                            currentBuild.description += """Baseline Comparison: <a href="${COMP_SHEET}">Comparison Sheet</a><br/>"""
                                        } catch (err) {
                                                println("Failed to capture comparison google sheet  :(")
                                        }
                                    }  
                                    GSHEET_ADD_ARGS = "--uuid1 ${env.UUID} --uuid2 $BASELINE_UUID --service-account $GSHEET_KEY_LOCATION"
                                    updateGSheetCode = sh(returnStatus: true, script: """
                                        source $WORKSPACE/ocp-qe-perfscale-ci/scripts/run_py_scripts.sh
                                        update_gsheet "$GSHEET_ADD_ARGS"
                                    """)

                                    // mark pipeline as unstable if Touchstone failed, continue otherwise
                                    if (baselineReturnCode.toInteger() != 0) {
                                        unstable('One or more new statistics was not in a tolerable range of baseline statistics :(')
                                        currentBuild.description += "Baseline Comparison: <b>FAILED</b><br/>"
                                        // collect must-gather
                                        mustGatherJob = build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/must-gather', parameters: [
                                            string(name: 'BUILD_NUMBER', value: params.FLEXY_BUILD_NUMBER),
                                            string(name: 'IMAGE', value: NETOBSERV_MUST_GATHER_IMAGE),
                                            string(name: 'JENKINS_AGENT_LABEL', value: params.JENKINS_AGENT_LABEL),
                                        ]
                                        if (mustGatherJob.result != 'SUCCESS') {
                                            println('must-gather job failed :(')
                                        }
                                        else {
                                            println("Successfully ran must-gather job :)")
                                            copyArtifacts(
                                                fingerprintArtifacts: true,
                                                projectName: 'scale-ci/e2e-benchmarking-multibranch-pipeline/must-gather',
                                                selector: specific("${mustGatherJob.getNumber()}"),
                                            )
                                        }
                                        // rerun Touchstone to generate a JSON for debugging
                                        env.GEN_JSON = true
                                        env.GEN_CSV = false
                                        jsonReturnCode = sh(returnStatus: true, script: """
                                            source $WORKSPACE/ocp-qe-perfscale-ci/scripts/run_py_scripts.sh
                                            gen_json_comparison
                                        """)
                                        println('Generated debug JSON for tolerancy analysis :)')
                                    }
                                    else {
                                        println('New statistics were within tolerable range of baseline statistics :)')
                                        currentBuild.description += "Baseline Comparison: <b>SUCCESS</b><br/>"
                                        // only update Elasticsearch baseline if user has permissions and override isn't used
                                        if (BASELINE_UPDATE_USERS.contains(env.USER) && (BASELINE_UUID_OVERRIDE == ''))  {
                                            println("User ${env.USER} is member of BASELINE_UPDATE_USERS group: ${BASELINE_UPDATE_USERS} - uploading new baseline...")
                                            NOPE_ARGS = ''
                                            if (params.NOPE_DEBUG == true) {
                                                NOPE_ARGS += ' --debug'
                                            }
                                            NOPE_ARGS += " baseline --upload ${env.UUID}"
                                            uploadReturnCode = sh(returnStatus: true, script: """
                                                source $WORKSPACE/ocp-qe-perfscale-ci/scripts/run_py_scripts.sh
                                                run_nope_tool "$NOPE_ARGS"
                                            """)
                                            if (uploadReturnCode.toInteger() != 0) {
                                                unstable('NOPE baseline uploading failed - run locally with the UUID from this job to set the new baseline :(')
                                                currentBuild.description += "New Baseline Upload: <b>FAILED</b><br/>"
                                            }
                                            else {
                                                println('Successfully uploaded new baseline to Elasticsearch :)')
                                                currentBuild.description += "New Baseline Upload: <b>SUCCESS</b><br/>"
                                            }
                                        }
                                    }
                                    if (updateGSheetCode.toInteger() != 0) {
                                        println("Failed to update comparison sheet with context :(")
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    post {
        always {
            println('Post Section - Always')
            archiveArtifacts(
                artifacts: 'e2e-benchmarking/utils/*.json,e2e-benchmarking/*.log',
                allowEmptyArchive: true,
                fingerprint: true
            )
            dir("/tmp"){
                archiveArtifacts(
                    artifacts: 'flowcollector.yaml',
                    allowEmptyArchive: true,
                    fingerprint: true)
            }
            dir("$workspace/ocp-qe-perfscale-ci/"){
                archiveArtifacts(
                    artifacts: 'data/**, scripts/netobserv/netobserv-dittybopper.yaml',
                    allowEmptyArchive: true,
                    fingerprint: true)
            }
        }
        failure {
            println('Post Section - Failure')
        }
        cleanup {
            script {
                // uninstall NetObserv operator and related resources if desired
                if (params.NUKEOBSERV == true) {
                    println("Deleting Network Observability operator...")
                    nukeReturnCode = sh(returnStatus: true, script: """
                        source $WORKSPACE/ocp-qe-perfscale-ci/scripts/netobserv.sh
                        nukeobserv
                    """)
                    if (nukeReturnCode.toInteger() != 0) {
                        error('Operator deletion unsuccessful - please delete manually :(')
                    }
                    else {
                        println('Operator deleted successfully :)')
                    }
                }
                if (params.DESTROY_CLUSTER == true) {
                    println("Destroying Flexy cluster...")
                    build job: 'ocp-common/Flexy-destroy', parameters: [
                        string(name: 'BUILD_NUMBER', value: params.FLEXY_BUILD_NUMBER)
                    ]
                }
            }
        }
    }
}

def validateParams() {
    if (params.FLEXY_BUILD_NUMBER == '') {
        error('A Flexy build number must be specified')
    }
    if (params.WORKLOAD == 'None' && params.NOPE == true) {
        error('NOPE tool cannot be run if a workload is not run first')
    }
    if (params.NOPE == false && params.NOPE_DUMP_ONLY == true) {
        error('NOPE must be run to dump data to a file')
    }
    if (params.NOPE == false && params.NOPE_DEBUG == true) {
        error('NOPE must be run to enable debug mode')
    }
    if (params.NOPE == false && params.NOPE_JIRA != '') {
        error('NOPE must be run to tie in a Jira')
    }
    if (params.GEN_CSV == true && params.NOPE_DUMP_ONLY == true) {
        error('Spreadsheet cannot be generated if data is not uploaded to Elasticsearch')
    }
    if (params.WORKLOAD == 'None' && params.RUN_BASELINE_COMPARISON == true) {
        error('Baseline comparison cannot be run if a workload is not run first')
    }
    if (params.INSTALLATION_SOURCE == 'None' && params.NOPE_JIRA == ''){
        error('Specify context of this perf run using NOPE_JIRA parameter')
    }
    println('Job params are valid - continuing execution...')
}

def setKafkaReplicas(){
    if (params.FLP_KAFKA_REPLICAS == "") {
        if (params.WORKLOAD == 'node-density-heavy') {
            env.FLP_KAFKA_REPLICAS = '6'
        }
        else if (params.WORKLOAD == 'cluster-density-v2') {
            env.FLP_KAFKA_REPLICAS = '18'
        }
        else {
            env.FLP_KAFKA_REPLICAS = '3'
        }
    }
}

def setTemplateParams(){
    def templateParams = "-p "
    if (params.ENABLE_KAFKA != true) {
        templateParams += "DeploymentModel=Direct "
    }
    templateParams += "KafkaConsumerReplicas=${env.FLP_KAFKA_REPLICAS} "
    if (params.EBPF_PRIVILEGED == false){
        templateParams += "EBPFPrivileged=${params.EBPF_PRIVILEGED} "
    }
    if (params.EBPF_SAMPLING_RATE != ""){
        templateParams += "EBPFSamplingRate=${params.EBPF_SAMPLING_RATE} "
    }
    if (params.EBPF_CACHE_MAXFLOWS != ""){
        templateParams += "EBPFCacheMaxFlows=${params.EBPF_CACHE_MAXFLOWS} "
    }
    if (params.LOKI_OPERATOR == 'None') {
        templateParams += "LokiEnable=false "
    }
    // increase ebpf memory limit to 1.5Gi for CD workload.
    if (params.WORKLOAD == 'cluster-density-v2'){
        templateParams += "EBPFMemoryLimit=1.5Gi "
    }

    return templateParams
}

def captureWorkloadResults(){
    def UUID = ''
    def JENKINS_BUILD = ''

    if (params.WORKLOAD != 'ingress-perf'){
        // fail pipeline if workload failed
        if (kubeburnerWorkloadJob.result != 'SUCCESS') {
            unstable('kube-burner workload job failed :(')
        }
        else {
            println("Successfully ran workload job :)")
            env.KUBEBURNER_BUILD = "${kubeburnerWorkloadJob.getNumber()}"
            currentBuild.description += "Kube-burner workload Job: <b><a href=${kubeburnerWorkloadJob.absoluteUrl}>${env.KUBEBURNER_BUILD}</a></b> (workload <b>${params.WORKLOAD}</b> was run)<br/>"
        }
        // copy artifacts from kube-burner-workload job
        copyArtifacts fingerprintArtifacts: true, projectName: env.WORKLOAD_JENKINS_JOB, selector: specific(env.KUBEBURNER_BUILD), target: 'kube-burner-workload-artifacts', flatten: true

        kubeburnerWorkloadInfo = readJSON(file: "$WORKSPACE/kube-burner-workload-artifacts/index_data.json")
        kubeburnerStarttime = kubeburnerWorkloadInfo.startDateUnixTimestamp
        kubeburnerEndtime = kubeburnerWorkloadInfo.endDateUnixTimestamp
        UUID=kubeburnerWorkloadInfo.uuid
        JENKINS_BUILD = "${kubeburnerWorkloadJob.getNumber()}"
    }

     // if ingress-perf was run at all.
    if (params.RUN_INGRESS_PERF_IN_PARALLEL || params.WORKLOAD == 'ingress-perf'){
            // fail pipeline if ingress-perf workload failed
        if (ingressWorkloadJob.result != 'SUCCESS') {
            unstable('ingress-perf workload job failed :(')
        }
        else {
            // otherwise continue and update build description with workload job link
            println("Successfully ran workload job :)")
            env.INGRESSPERF_BUILD = "${ingressWorkloadJob.getNumber()}"
            currentBuild.description += "Ingress perf workload Job: <b><a href=${ingressWorkloadJob.absoluteUrl}>${env.INGRESSPERF_BUILD}</a></b><br/>"
        }
        // copy artifacts from ingress-perf job
        copyArtifacts fingerprintArtifacts: true, projectName: env.INGRESSPERF_JENKINS_JOB, selector: specific(env.INGRESSPERF_BUILD), target: 'ingressperf-workload-artifacts', flatten: true

        ingressperfWorkloadInfo = readJSON(file: "$WORKSPACE/ingressperf-workload-artifacts/index_data.json")
        ingressperfStarttime = ingressperfWorkloadInfo.startDateUnixTimestamp
        ingressperfEndtime = ingressperfWorkloadInfo.endDateUnixTimestamp
        if (params.WORKLOAD == 'ingress-perf'){
            UUID=ingressperfWorkloadInfo.uuid
            JENKINS_BUILD = "${ingressperfWorkloadInfo.getNumber()}"
        }
    }
    
    // evaluate workload start time and end times
    def START_TIME = ''
    def END_TIME = ''
    if (params.RUN_INGRESS_PERF_IN_PARALLEL) {
        // use earliest start time
        if (ingressperfStarttime < kubeburnerStarttime) {
            START_TIME = ingressperfStarttime
        }
        else {
            START_TIME = kubeburnerStarttime
        }
        // use latest end time
        if (ingressperfEndtime > kubeburnerEndtime){
            END_TIME = ingressperfEndtime
        }
        else {
            END_TIME = kubeburnerEndtime
        }
    }
    else {
        if (params.WORKLOAD == 'ingress-perf') {
            START_TIME = ingressperfStarttime
            END_TIME = ingressperfEndtime
        }
        else {
            START_TIME = kubeburnerStarttime
            END_TIME = kubeburnerEndtime
        }
    }

    env.UUID = UUID
    env.JENKINS_BUILD = JENKINS_BUILD
    env.STARTDATEUNIXTIMESTAMP = START_TIME
    env.ENDDATEUNIXTIMESTAMP = END_TIME
    currentBuild.description += "<b>UUID:</b> ${env.UUID}<br/>"
    currentBuild.description += "<b>STARTDATEUNIXTIMESTAMP:</b> ${env.STARTDATEUNIXTIMESTAMP}<br/>"
    currentBuild.description += "<b>ENDDATEUNIXTIMESTAMP:</b> ${env.ENDDATEUNIXTIMESTAMP}<br/>"
}
