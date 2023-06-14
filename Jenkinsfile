@Library('flexy') _

// global variables for pipeline
NETOBSERV_MUST_GATHER_IMAGE = 'quay.io/netobserv/must-gather'

// rename build
def userId = currentBuild.rawBuild.getCause(hudson.model.Cause$UserIdCause)?.userId
if (userId) {
    currentBuild.displayName = userId
}

pipeline {
    agent { label params.JENKINS_AGENT_LABEL }

    options {
        timeout(time: 6, unit: 'HOURS')
        ansiColor('xterm')
    }

    parameters {
        string(
            name: 'JENKINS_AGENT_LABEL',
            defaultValue:'oc413',
            description: 'Label of Jenkins agent to execute job'
        )
        string(
            name: 'FLEXY_BUILD_NUMBER',
            defaultValue: '',
            description: '''
                Build number of Flexy job that installed the cluster.<br/>
                <b>Note that only AWS clusters are supported at the moment.</b>
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
            defaultValue: false,
            description: 'Install workload and infrastructure nodes even if less than 50 nodes'
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
                If <b>None</b> is selected the installation will be skipped
            '''
        )
        choice(
            name: 'LOKISTACK_SIZE',
            choices: ['1x.extra-small', '1x.small', '1x.medium'],
            description: '''
                Depending on size of cluster nodes, use following guidance to choose LokiStack size:<br/>
                1x.extra-small - Nodes size < m5.4xlarge<br/>
                1x.small - Nodes size >= m5.4xlarge<br/>
                1x.medium - Nodes size >= m5.8xlarge<br/>
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
            choices: ['None', 'Official', 'Internal', 'OperatorHub', 'Source'],
            description: '''
                Network Observability can be installed from the following sources:<br/>
                <b>Official</b> installs the <b>latest released downstream</b> version of the operator, i.e. what is available to customers<br/>
                <b>Internal</b> installs the <b>latest unreleased downstream</b> version of the operator, i.e. the most recent internal bundle<br/>
                <b>OperatorHub</b> installs the <b>latest released upstream</b> version of the operator, i.e. what is currently available on OperatorHub<br/>
                <b>Source</b> installs the <b>latest unreleased upstream</b> version of the operator, i.e. directly from the main branch of the upstream source code<br/>
                If <b>None</b> is selected the installation will be skipped
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
            name: 'CONTROLLER_MEMORY_LIMIT',
            defaultValue: '',
            description: 'Note that 800Mi = 800 mebibytes, i.e. 0.8 Gi'
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
            defaultValue: '',
            description: 'Rate at which to sample flows'
        )
        string(
            name: 'EBPF_MEMORY_LIMIT',
            defaultValue: '',
            description: 'Note that 800Mi = 800 mebibytes, i.e. 0.8 Gi'
        )
        string(
            name: 'FLP_CPU_LIMIT',
            defaultValue: '',
            description: 'Note that 1000m = 1000 millicores, i.e. 1 core'
        )
        string(
            name: 'FLP_MEMORY_LIMIT',
            defaultValue: '',
            description: 'Note that 800Mi = 800 mebibytes, i.e. 0.8 Gi'
        )
        booleanParam(
            name: 'ENABLE_KAFKA',
            defaultValue: false,
            description: 'Check this box to setup Kafka for NetObserv or to update Kafka configs even if it is already installed'
        )
        choice(
            name: 'TOPIC_PARTITIONS',
            choices: [6, 10, 24, 48],
            description: '''
                Number of Kafka Topic Partitions. Below are recommended values for partitions:<br/>
                6 - default for non-perf testing environments<br/>
                10 - Perf testing with worker nodes <= 20<br/>
                24 - Perf testing with worker nodes <= 50<br/>
                48 - Perf testing with worker nodes <= 100<br/>
            '''
        )
        string(
            name: 'FLP_KAFKA_REPLICAS',
            defaultValue: '3',
            description: '''
                Replicas should be at least half the number of Kafka TOPIC_PARTITIONS and should not exceed number of TOPIC_PARTITIONS or number of nodes:<br/>
                3 - default for non-perf testing environments<br/>
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
            choices: ['None', 'cluster-density', 'node-density', 'node-density-heavy', 'pod-density', 'pod-density-heavy', 'max-namespaces', 'max-services', 'concurrent-builds', 'router-perf'],
            description: '''
                Workload to run on Netobserv-enabled cluster<br/>
                Note that all options excluding "router-perf" and "None" will trigger "kube-burner" job<br/>
                "router-perf" will trigger "router-perf" job and "None" will run no workload<br/>
                For additional guidance on configuring workloads, see <a href=https://docs.google.com/spreadsheets/d/1DdFiJkCMA4c35WQT2SWXbdiHeCCcAZYjnv6wNpsEhIA/edit?usp=sharing#gid=1506806462>here</a>
            '''
        )
        string(
            name: 'VARIABLE',
            defaultValue: '1000',
            description: '''
                This variable configures parameter needed for each type of workload. <b>Not used by <a href=https://github.com/cloud-bulldozer/e2e-benchmarking/blob/master/workloads/router-perf-v2/README.md>router-perf</a> workload</b>.<br/>
                <a href=https://github.com/cloud-bulldozer/e2e-benchmarking/blob/master/workloads/kube-burner/README.md>cluster-density</a>: This will export JOB_ITERATIONS env variable; set to 4 * num_workers. This variable sets the number of iterations to perform (1 namespace per iteration).<br/>
                <a href=https://github.com/cloud-bulldozer/e2e-benchmarking/blob/master/workloads/kube-burner/README.md>node-density-heavy</a>: This will export PODS_PER_NODE env variable; set to 200, work up to 250. Creates this number of applications proportional to the calculated number of pods / 2<br/>
                Read <a href=https://github.com/openshift-qe/ocp-qe-perfscale-ci/tree/kube-burner/README.md>here</a> for details about each variable
            '''
        )
        string(
            name: 'NODE_COUNT',
            defaultValue: '3',
            description: '''
                Only for <b>node-density</b> and <b>node-density-heavy</b><br/>
                Should be the number of worker nodes on your cluster (after scaling)
            '''
        )
        string(
            name: 'LARGE_SCALE_CLIENTS',
            defaultValue: '1 80',
            description: '''
                Only for <b>router-perf</b><br/>
                Threads/route to use in the large scale scenario
            '''
        )
        string(
            name: 'LARGE_SCALE_CLIENTS_MIX',
            defaultValue: '1 25',
            description: '''
                Only for <b>router-perf</b><br/>
                Threads/route to use in the large scale scenario with mix termination
            '''
        )
        booleanParam(
            name: 'CERBERUS_CHECK',
            defaultValue: false,
            description: 'Check cluster health status after workload runs'
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
            name: 'NOPE_DUMP',
            defaultValue: false,
            description: '''
                Check this box to dump data collected by the NOPE tool to a file instead of uploading to Elasticsearch<br/>
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
                Adds a Jira ticket to be tied to the NOPE run<br/>
                Format should in the form of <b>NETOBSERV-123</b>
            '''
        )
        string(
            name: 'BASELINE_UUID',
            defaultValue: '',
            description: '''
                Baseline UUID to compare this run to<br/>
                If the workload completes successfully and is uploaded to Elasticsearch, adding a UUID here will configure Touchstone to run a comparison between the job run and the given baseline UUID<br/>
                If no UUID is specified, no comparison will be made
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
                    if (params.FLEXY_BUILD_NUMBER == '') {
                        error 'A Flexy build number must be specified'
                    }
                    if (params.WORKLOAD == 'None' && params.NOPE == true) {
                        error 'NOPE tool cannot be run if a workload is not run first'
                    }
                    if (params.NOPE == false && params.NOPE_DUMP == true) {
                        error 'NOPE must be run to dump data to a file'
                    }
                    if (params.NOPE == false && params.NOPE_DEBUG == true) {
                        error 'NOPE must be run to enable debug mode'
                    }
                    if (params.NOPE == false && params.NOPE_JIRA != '') {
                        error 'NOPE must be run to tie in a Jira'
                    }
                    if (params.GEN_CSV == true && params.NOPE_DUMP == true) {
                        error 'Spreadsheet cannot be generated if data is not uploaded to Elasticsearch'
                    }
                    println('Job params are valid - continuing execution...')
                }
            }
        }
        stage('Setup testing environment') {
            steps {
                copyArtifacts(
                    fingerprintArtifacts: true,
                    projectName: 'ocp-common/Flexy-install',
                    selector: specific(params.FLEXY_BUILD_NUMBER),
                    target: 'flexy-artifacts'
                )
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: GIT_BRANCH ]],
                    userRemoteConfigs: [[url: GIT_URL ]],
                    extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'ocp-qe-perfscale-ci']]
                ])
                withCredentials([file(credentialsId: 'b73d6ed3-99ff-4e06-b2d8-64eaaf69d1db', variable: 'OCP_AWS')]) {
                    script {
                        buildinfo = readYaml file: 'flexy-artifacts/BUILDINFO.yml'
                        buildinfo.params.each { env.setProperty(it.key, it.value) }
                        currentBuild.displayName = "${currentBuild.displayName}-${params.FLEXY_BUILD_NUMBER}"
                        currentBuild.description = "Flexy-install Job: <a href=\"${buildinfo.buildUrl}\">${params.FLEXY_BUILD_NUMBER}</a><br/>"
                        installData = readYaml(file: 'flexy-artifacts/workdir/install-dir/cluster_info.yaml')
                        env.MAJOR_VERSION = installData.INSTALLER.VER_X
                        env.MINOR_VERSION = installData.INSTALLER.VER_Y
                        returnCode = sh(returnStatus: true, script: """
                            mkdir -p ~/.kube
                            cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config
                            oc get route console -n openshift-console
                            mkdir -p ~/.aws
                            cp -f $OCP_AWS ~/.aws/credentials
                            echo "[profile default]
                            region = `cat $WORKSPACE/flexy-artifacts/workdir/install-dir/terraform.platform.auto.tfvars.json | jq -r ".aws_region"`
                            output = text" > ~/.aws/config
                        """)
                        if (returnCode.toInteger() != 0) {
                            error("Failed to setup testing environment :(")
                        }
                        else {
                            println "Successfully setup testing environment :)"
                        }
                    }
                }
            }
        }
        stage('Scale workers and install infra nodes') {
            when {
                expression { params.WORKER_COUNT != '0' }
            }
            steps {
                script {
                    scaleJob = build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cluster-workers-scaling/', parameters: [
                        string(name: 'BUILD_NUMBER', value: params.FLEXY_BUILD_NUMBER),
                        string(name: 'JENKINS_AGENT_LABEL', value: params.JENKINS_AGENT_LABEL),
                        string(name: 'WORKER_COUNT', value: params.WORKER_COUNT),
                        booleanParam(name: 'INFRA_WORKLOAD_INSTALL', value: params.INFRA_WORKLOAD_INSTALL),
                        booleanParam(name: 'INSTALL_DITTYBOPPER', value: false),
                    ]
                    currentBuild.description += "Scale Job: <b><a href=${scaleJob.absoluteUrl}>${scaleJob.getNumber()}</a></b><br/>"
                    if (scaleJob.result != 'SUCCESS') {
                        error 'Scale job failed :('
                    }
                    else {
                        println "Successfully scaled cluster to ${params.WORKER_COUNT} worker nodes :)"
                        if (params.INFRA_WORKLOAD_INSTALL) {
                            println 'Successfully installed infrastructure and workload nodes :)'
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
                        env.IMAGE = "quay.io/openshift-qe-optional-operators/aosqe-index:v${MAJOR_VERSION}.${MINOR_VERSION}"
                    }
                    // set USER variable to be included in AWS bucket name
                    if (userId) {
                        env.USER = userId
                    }
                    else {
                        env.USER = 'auto'
                    }
                    // attempt installation of Loki Operator from selected source
                    println "Installing ${params.LOKI_OPERATOR} version of Loki Operator..."
                    returnCode = sh(returnStatus: true, script: """
                        source $WORKSPACE/ocp-qe-perfscale-ci/scripts/netobserv.sh
                        deploy_lokistack
                    """)
                    // fail pipeline if installation failed, continue otherwise
                    if (returnCode.toInteger() != 0) {
                        error("${params.LOKI_OPERATOR} version of Loki Operator installation failed :(")
                    }
                    else {
                        println "Successfully installed ${LOKI_OPERATOR} version of Loki Operator :)"
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
                    if (params.INSTALLATION_SOURCE == 'Internal' && params.IIB_OVERRIDE != '') {
                        env.IMAGE = "brew.registry.redhat.io/rh-osbs/iib:${params.IIB_OVERRIDE}"
                    }
                    else {
                        env.IMAGE = "quay.io/openshift-qe-optional-operators/aosqe-index:v${MAJOR_VERSION}.${MINOR_VERSION}"
                    }
                    // attempt installation of Network Observability from selected source
                    println "Installing Network Observability from ${params.INSTALLATION_SOURCE}..."
                    returnCode = sh(returnStatus: true, script: """
                        source $WORKSPACE/ocp-qe-perfscale-ci/scripts/netobserv.sh
                        deploy_netobserv
                    """)
                    // fail pipeline if installation failed, continue otherwise
                    if (returnCode.toInteger() != 0) {
                        error("Network Observability installation from ${params.INSTALLATION_SOURCE} failed :(")
                    }
                    else {
                        println "Successfully installed Network Observability from ${params.INSTALLATION_SOURCE} :)"
                        sh(returnStatus: true, script: '''
                            oc get pods -n openshift-netobserv-operator
                            oc get pods -n openshift-operators-redhat
                            oc get pods -n netobserv
                            oc get pods -n netobserv-privileged
                        ''')
                    }
                }
            }
        }
        stage('Configure NetObserv, flowcollector, and Kafka') {
            steps {
                script {
                    // capture NetObserv release and add it to build description
                    env.RELEASE = sh(returnStdout: true, script: "oc get pods -l app=netobserv-operator -o jsonpath='{.items[*].spec.containers[1].env[0].value}' -A").trim()
                    env.IS_DOWNSTREAM = sh(returnStdout: true, script: "oc get pods -l app=netobserv-operator -o jsonpath='{.items[*].spec.containers[0].env[-2].value}' -A").trim()
                    if (env.RELEASE != '') {
                        currentBuild.description += "NetObserv Release: <b>${env.RELEASE}</b> (downstream: <b>${env.IS_DOWNSTREAM}</b>)<br/>"
                    }

                    // attempt updating common parameters of NetObserv and flowcollector where specified
                    println 'Updating common parameters of NetObserv and flowcollector where specified...'
                    if (params.CONTROLLER_MEMORY_LIMIT != '') {
                        returnCode = sh(returnStatus: true, script: """
                            oc -n openshift-netobserv-operator patch csv $RELEASE --type=json -p "[{"op": "replace", "path": "/spec/install/spec/deployments/0/spec/template/spec/containers/0/resources/limits/memory", "value": ${params.CONTROLLER_MEMORY_LIMIT}}]"
                            sleep 60
                        """)
                        if (returnCode.toInteger() != 0) {
                            error('Updating controller memory limit failed :(')
                        }
                    }
                    if (params.EBPF_SAMPLING_RATE != '') {
                        returnCode = sh(returnStatus: true, script: """
                            oc patch flowcollector cluster --type=json -p "[{"op": "replace", "path": "/spec/agent/ebpf/sampling", "value": ${params.EBPF_SAMPLING_RATE}}] -n netobserv"
                        """)
                        if (returnCode.toInteger() != 0) {
                            error('Updating eBPF sampling rate failed :(')
                        }
                    }
                    if (params.EBPF_MEMORY_LIMIT != '') {
                        returnCode = sh(returnStatus: true, script: """
                            oc patch flowcollector cluster --type=json -p "[{"op": "replace", "path": "/spec/agent/ebpf/resources/limits/memory", "value": "${params.EBPF_MEMORY_LIMIT}"}] -n netobserv"
                        """)
                        if (returnCode.toInteger() != 0) {
                            error('Updating eBPF memory limit failed :(')
                        }
                    }
                    if (params.FLP_CPU_LIMIT != '') {
                        returnCode = sh(returnStatus: true, script: """
                            oc patch flowcollector cluster --type=json -p "[{"op": "replace", "path": "/spec/processor/resources/limits/cpu", "value": "${params.FLP_CPU_LIMIT}"}] -n netobserv"
                        """)
                        if (returnCode.toInteger() != 0) {
                            error('Updating FLP CPU limit failed :(')
                        }
                    }
                    if (params.FLP_MEMORY_LIMIT != '') {
                        returnCode = sh(returnStatus: true, script: """
                            oc patch flowcollector cluster --type=json -p "[{"op": "replace", "path": "/spec/processor/resources/limits/memory", "value": "${params.FLP_MEMORY_LIMIT}"}] -n netobserv"
                        """)
                        if (returnCode.toInteger() != 0) {
                            error('Updating FLP memory limit failed :(')
                        }
                    }
                    println 'Successfully updated common parameters of NetObserv and flowcollector :)'

                    // attempt to enable or update Kafka if applicable
                    println "Checking if Kafka needs to be enabled or updated..."
                    if (params.ENABLE_KAFKA == true) {
                        println "Configuring Kafka in flowcollector..."
                        returnCode = sh(returnStatus: true, script: """
                            source $WORKSPACE/ocp-qe-perfscale-ci/scripts/netobserv.sh
                            deploy_kafka
                        """)
                        if (returnCode.toInteger() != 0) {
                            error('Failed to enable Kafka in flowcollector :(')
                        }
                        else {
                            println 'Successfully enabled Kafka with flowcollector :)'
                            sh(returnStatus: true, script: '''
                                oc get pods -n openshift-netobserv-operator
                                oc get pods -n openshift-operators-redhat
                                oc get pods -n openshift-operators
                                oc get pods -n netobserv
                                oc get pods -n netobserv-privileged
                            ''')
                        }
                    }
                    else {
                        println "Skipping Kafka configuration..."
                    }
                }
            }
        }
        stage('Setup FLP service and service-monitor') {
            when {
                expression { env.IS_DOWNSTREAM == 'false' }
            }
            steps {
                script {
                    // attempt setup of FLP service and creation of service-monitor
                    println 'Setting up FLP service and creating service-monitor...'
                    returnCode = sh(returnStatus: true, script:  """
                        source $WORKSPACE/ocp-qe-perfscale-ci/scripts/netobserv.sh
                        populate_netobserv_metrics
                    """)
                    // fail pipeline if setup failed, continue otherwise
                    if (returnCode.toInteger() != 0) {
                        error('Setting up FLP service and creating service-monitor failed :(')
                    }
                    else {
                        println 'Successfully set up FLP service and created service-monitor :)'
                    }
                }
            }
        }
        stage('Install Dittybopper') {
            when {
                expression { params.INSTALL_DITTYBOPPER == true }
            }
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: params.DITTYBOPPER_REPO_BRANCH ]],
                    userRemoteConfigs: [[url: params.DITTYBOPPER_REPO ]],
                    extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'performance-dashboards']]
                ])
                script {
                    // if an upstream installation, use custom Dittybopper template
                    if (env.IS_DOWNSTREAM == 'false') {
                        DITTYBOPPER_PARAMS = "-t $WORKSPACE/ocp-qe-perfscale-ci/scripts/netobserv/netobserv-dittybopper.yaml -i $WORKSPACE/ocp-qe-perfscale-ci/scripts/queries/netobserv_dittybopper_upstream.json"
                    }
                    else {
                        DITTYBOPPER_PARAMS = "-i $WORKSPACE/ocp-qe-perfscale-ci/scripts/queries/netobserv_dittybopper_downstream.json"
                    }
                    // attempt installation of dittybopper
                    returnCode = sh(returnStatus: true, script: """
                        source $WORKSPACE/ocp-qe-perfscale-ci/scripts/netobserv.sh
                        setup_dittybopper_template
                        . $WORKSPACE/performance-dashboards/dittybopper/deploy.sh $DITTYBOPPER_PARAMS
                    """)
                    // fail pipeline if installation failed, continue otherwise
                    if (returnCode.toInteger() != 0) {
                        error('Installation of Dittybopper failed :(')
                    }
                    else {
                        println 'Successfully installed Dittybopper :)'
                    }
                }
            }
        }
        stage('Run Workload and Mr. Sandman') {
            when {
                expression { params.WORKLOAD != 'None' }
            }
            steps {
                script {
                    // set build name and remove previous artifacts
                    currentBuild.displayName = "${currentBuild.displayName}-${params.WORKLOAD}"
                    sh(script: "rm -rf $WORKSPACE/workload-artifacts/workloads/**/*.out")
                    // build workload job based off selected workload
                    if (params.WORKLOAD == 'router-perf') {
                        env.JENKINS_JOB = 'scale-ci/e2e-benchmarking-multibranch-pipeline/router-perf'
                        workloadJob = build job: env.JENKINS_JOB, parameters: [
                            string(name: 'BUILD_NUMBER', value: params.FLEXY_BUILD_NUMBER),
                            booleanParam(name: 'CERBERUS_CHECK', value: params.CERBERUS_CHECK),
                            booleanParam(name: 'MUST_GATHER', value: true),
                            string(name: 'IMAGE', value: NETOBSERV_MUST_GATHER_IMAGE),
                            string(name: 'JENKINS_AGENT_LABEL', value: params.JENKINS_AGENT_LABEL),
                            booleanParam(name: 'GEN_CSV', value: false),
                            string(name: 'LARGE_SCALE_CLIENTS', value: params.LARGE_SCALE_CLIENTS),
                            string(name: 'LARGE_SCALE_CLIENTS_MIX', value: params.LARGE_SCALE_CLIENTS_MIX)
                        ]
                    }
                    else {
                        env.JENKINS_JOB = 'scale-ci/e2e-benchmarking-multibranch-pipeline/kube-burner'
                        workloadJob = build job: env.JENKINS_JOB, parameters: [
                            string(name: 'BUILD_NUMBER', value: params.FLEXY_BUILD_NUMBER),
                            string(name: 'WORKLOAD', value: params.WORKLOAD),
                            booleanParam(name: 'CLEANUP', value: true),
                            booleanParam(name: 'CERBERUS_CHECK', value: params.CERBERUS_CHECK),
                            booleanParam(name: 'MUST_GATHER', value: true),
                            string(name: 'IMAGE', value: NETOBSERV_MUST_GATHER_IMAGE),
                            string(name: 'VARIABLE', value: params.VARIABLE), 
                            string(name: 'NODE_COUNT', value: params.NODE_COUNT),
                            booleanParam(name: 'GEN_CSV', value: false),
                            string(name: 'JENKINS_AGENT_LABEL', value: params.JENKINS_AGENT_LABEL)
                        ]
                    }
                    if (workloadJob.result != 'SUCCESS') {
                        error 'Workload job failed :('
                    }
                    else {
                        println "Successfully ran workload job :)"
                        // update build description with workload job link
                        env.JENKINS_BUILD = "${workloadJob.getNumber()}"
                        currentBuild.description += "Workload Job: <b><a href=${workloadJob.absoluteUrl}>${env.JENKINS_BUILD}</a></b> (workload <b>${params.WORKLOAD}</b> was run)<br/>"
                    }
                }
                copyArtifacts(
                    fingerprintArtifacts: true, 
                    projectName: env.JENKINS_JOB,
                    selector: specific(env.JENKINS_BUILD),
                    target: 'workload-artifacts'
                )
                script {
                    // run Mr. Sandman
                    returnCode = sh(returnStatus: true, script: """
                        python3.9 --version
                        python3.9 -m pip install virtualenv
                        python3.9 -m virtualenv venv3
                        source venv3/bin/activate
                        python --version
                        python -m pip install -r $WORKSPACE/ocp-qe-perfscale-ci/scripts/requirements.txt
                        python $WORKSPACE/ocp-qe-perfscale-ci/scripts/sandman.py --file $WORKSPACE/workload-artifacts/workloads/**/*.out
                    """)
                    // fail pipeline if Mr. Sandman run failed, continue otherwise
                    if (returnCode.toInteger() != 0) {
                        error('Mr. Sandman tool failed :(')
                    }
                    else {
                        println 'Successfully ran Mr. Sandman tool :)'
                    }
                    // update build description fields
                    // UUID
                    env.UUID = sh(returnStdout: true, script: "jq -r '.uuid' $WORKSPACE/ocp-qe-perfscale-ci/data/workload.json").trim()
                    currentBuild.description += "<b>UUID:</b> ${env.UUID}<br/>"
                    // STARTTIME_STRING is string rep of start time
                    env.STARTTIME_STRING = sh(returnStdout: true, script: "jq -r '.starttime_string' $WORKSPACE/ocp-qe-perfscale-ci/data/workload.json").trim()
                    currentBuild.description += "<b>STARTTIME_STRING:</b> ${env.STARTTIME_STRING}<br/>"
                    // ENDTIME_STRING is string rep of end time
                    env.ENDTIME_STRING = sh(returnStdout: true, script: "jq -r '.endtime_string' $WORKSPACE/ocp-qe-perfscale-ci/data/workload.json").trim()
                    currentBuild.description += "<b>ENDTIME_STRING:</b> ${env.ENDTIME_STRING}<br/>"
                    // STARTTIME_TIMESTAMP is unix timestamp of start time
                    env.STARTTIME_TIMESTAMP = sh(returnStdout: true, script: "jq -r '.starttime_timestamp' $WORKSPACE/ocp-qe-perfscale-ci/data/workload.json").trim()
                    currentBuild.description += "<b>STARTTIME_TIMESTAMP:</b> ${env.STARTTIME_TIMESTAMP}<br/>"
                    // ENDTIME_TIMESTAMP is unix timestamp of end time
                    env.ENDTIME_TIMESTAMP = sh(returnStdout: true, script: "jq -r '.endtime_timestamp' $WORKSPACE/ocp-qe-perfscale-ci/data/workload.json").trim()
                    currentBuild.description += "<b>ENDTIME_TIMESTAMP:</b> ${env.ENDTIME_TIMESTAMP}<br/>"
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
                        NOPE_ARGS = '--starttime $STARTTIME_TIMESTAMP --endtime $ENDTIME_TIMESTAMP --jenkins-job $JENKINS_JOB --jenkins-build $JENKINS_BUILD --uuid $UUID'
                        if (params.NOPE_DUMP == true) {
                            NOPE_ARGS += " --dump"
                        }
                        if (params.NOPE_DEBUG == true) {
                            NOPE_ARGS += " --debug"
                        }
                        if (params.NOPE_JIRA != '') {
                            NOPE_ARGS += " --jira ${params.NOPE_JIRA}"
                        }
                        returnCode = sh(returnStatus: true, script: """
                            python3.9 --version
                            python3.9 -m pip install virtualenv
                            python3.9 -m virtualenv venv3
                            source venv3/bin/activate
                            python --version
                            python -m pip install -r $WORKSPACE/ocp-qe-perfscale-ci/scripts/requirements.txt
                            python $WORKSPACE/ocp-qe-perfscale-ci/scripts/nope.py $NOPE_ARGS
                        """)
                        // fail pipeline if NOPE run failed, continue otherwise
                        if (returnCode.toInteger() == 2) {
                            unstable('NOPE tool ran, but Elasticsearch upload failed - check build artifacts for data and try uploading it locally :/')
                        }
                        else if (returnCode.toInteger() != 0) {
                            error('NOPE tool failed :(')
                        }
                        else {
                            println 'Successfully ran NOPE tool :)'
                        }
                    }
                }
            }
        }
        stage('Run Touchstone tool') {
            when {
                expression { params.WORKLOAD != 'None' && params.NOPE == true && params.NOPE_DUMP == false && currentBuild.currentResult != "UNSTABLE" }
            }
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: 'master' ]],
                    userRemoteConfigs: [[url: 'https://github.com/cloud-bulldozer/e2e-benchmarking.git' ]],
                    extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'e2e-benchmarking']]
                ])
                withCredentials([usernamePassword(credentialsId: 'elasticsearch-perfscale-ocp-qe', usernameVariable: 'ES_USERNAME', passwordVariable: 'ES_PASSWORD'), file(credentialsId: 'sa-google-sheet', variable: 'GSHEET_KEY_LOCATION')]) {
                    script {
                        println 'Running Touchstone to get statistics for workload run...'
                        // set env variables needed for touchstone (note UUID and GSHEET_KEY_LOCATION are needed but already set above)
                        env.CONFIG_LOC = "$WORKSPACE/ocp-qe-perfscale-ci/scripts/queries"
                        env.COMPARISON_CONFIG = 'netobserv_touchstone_statistics_config.json'
                        env.ES_SERVER = "https://$ES_USERNAME:$ES_PASSWORD@search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com"
                        env.EMAIL_ID_FOR_RESULTS_SHEET = "${userId}@redhat.com"
                        env.GEN_CSV = params.GEN_CSV
                        env.NETWORK_TYPE = sh(returnStdout: true, script: "oc get network.config/cluster -o jsonpath='{.spec.networkType}'").trim()
                        env.WORKLOAD = params.WORKLOAD
                        returnCode = sh(returnStatus: true, script: """
                            python3.9 --version
                            python3.9 -m pip install virtualenv
                            python3.9 -m virtualenv venv3
                            source venv3/bin/activate
                            python --version
                            cd $WORKSPACE/e2e-benchmarking/utils
                            source compare.sh
                            run_benchmark_comparison
                        """)
                        // mark pipeline as unstable if Touchstone failed, continue otherwise
                        if (returnCode.toInteger() != 0) {
                            unstable('Touchstone tool failed - run locally with the given UUID to get workload run statistics :(')
                        }
                        else {
                            println 'Successfully ran Touchstone tool :)'
                            // do tolerancy rules check if a baseline UUID is provided
                            if (params.BASELINE_UUID != '') {
                                println "Running automatic comparison between new UUID ${env.UUID} with provided baseline UUID ${params.BASELINE_UUID}..."
                                // set additional vars for tolerancy rules check
                                // note COMPARISON_CONFIG is changed here to only focus on specific statistics
                                //      ES_SERVER and ES_SERVER_BASELINE are the same since we store all of our results on the same ES server
                                env.BASELINE_UUID = params.BASELINE_UUID
                                env.COMPARISON_CONFIG = 'netobserv_touchstone_tolerancy_config.json'
                                env.ES_SERVER_BASELINE = "https://$ES_USERNAME:$ES_PASSWORD@search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com"
                                env.TOLERANCY_RULES = "$WORKSPACE/ocp-qe-perfscale-ci/scripts/queries/netobserv_touchstone_tolerancy_rules.yaml"
                                returnCode = sh(returnStatus: true, script: """
                                    cd $WORKSPACE/e2e-benchmarking/utils
                                    rm -rf /tmp/**/*.csv
                                    rm -rf *.csv
                                    source compare.sh
                                    run_benchmark_comparison
                                """)
                                // mark pipeline as unstable if Touchstone failed, continue otherwise
                                if (returnCode.toInteger() != 0) {
                                    unstable('One or more new statistics was not in a tolerable range of baseline statistics :(')
                                }
                                else {
                                    println 'New statistics were within tolerable range of baseline statistics :)'
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
            println 'Post Section - Always'
            archiveArtifacts(
                artifacts: 'ocp-qe-perfscale-ci/data/**, ocp-qe-perfscale-ci/scripts/netobserv/netobserv-dittybopper.yaml',
                allowEmptyArchive: true,
                fingerprint: true
            )
        }
        failure {
            println 'Post Section - Failure'
        }
        cleanup {
            script {
                // uninstall NetObserv operator and related resources if desired
                if (params.NUKEOBSERV == true) {
                    println "Deleting Network Observability operator..."
                    returnCode = sh(returnStatus: true, script: """
                        source $WORKSPACE/ocp-qe-perfscale-ci/scripts/netobserv.sh
                        nukeobserv
                    """)
                    if (returnCode.toInteger() != 0) {
                        error('Operator deletion unsuccessful - please delete manually :(')
                    }
                    else {
                        println 'Operator deleted successfully :)'
                    }
                }
                if (params.DESTROY_CLUSTER ==  true) {
                    println "Destroying Flexy cluster..."
                    build job: 'ocp-common/Flexy-destroy', parameters: [
                        string(name: 'BUILD_NUMBER', value: params.FLEXY_BUILD_NUMBER)
                    ]
                }
            }
        }
    }
}
