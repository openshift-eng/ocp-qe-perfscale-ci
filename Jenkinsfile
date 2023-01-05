@Library('flexy') _

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
            defaultValue:'oc411',
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
            defaultValue: true,
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
            choices: ['Downstream', 'OperatorHub', 'Source', 'None'],
            description: '''
                Network Observability can be installed from the following sources:<br/>
                <b>Downstream</b> installs the operator via the internal-only qe-app-registry (i.e. latest unreleased downstream bits)<br/>
                <b>OperatorHub</b> installs the operator via the public-facing OperatorHub (i.e. latest released upstream bits)<br/>
                <b>Source</b> installs the operator directly from the main branch of the upstream source code (i.e. latest unreleased upstream bits)<br/>
                If <b>None</b> is selected the installation will be skipped
            '''
        )
        string(
            name: 'CONTROLLER_MEMORY_LIMIT',
            defaultValue: '800Mi',
            description: 'Note that 800Mi = 800 mebibytes, i.e. 0.8 Gi'
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
        booleanParam(
            name: 'USER_WORKLOADS',
            defaultValue: true,
            description: 'Check this box to setup FLP service and create service-monitor or to include user workload metrics in a NOPE run even if they are already set up'
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
            name: 'FLP_SAMPLING_RATE',
            defaultValue: '1',
            description: 'Rate at which to sample flows'
        )
        string(
            name: 'FLP_CPU_LIMIT',
            defaultValue: '8000m',
            description: 'Note that 1000m = 1000 millicores, i.e. 1 core'
        )
        string(
            name: 'FLP_MEMORY_LIMIT',
            defaultValue: '8000Mi',
            description: 'Note that 500Mi = 500 mebibytes, i.e. 0.5 Gi'
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
            choices: ['cluster-density', 'node-density', 'node-density-heavy', 'pod-density', 'pod-density-heavy', 'max-namespaces', 'max-services', 'concurrent-builds', 'router-perf', 'None'],
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
                Only for node-density and node-density-heavy<br/>
                Should be the number of worker nodes on your cluster (after scaling)
            '''
        )
        separator(
            name: 'NOPE_CONFIG_OPTIONS',
            sectionHeader: 'NOPE Configuration Options',
            sectionHeaderStyle: '''
                font-size: 14px;
                font-weight: bold;
                font-family: 'Orienta', sans-serif;
            '''
        )
        booleanParam(
            name: 'NOPE',
            defaultValue: true,
            description: '''
                Check this box to run the NOPE tool after the workload completes<br/>
                If the tool successfully uploads results to Elasticsearch, Touchstone will be run afterword
            '''
        )
        booleanParam(
            name: 'GEN_CSV',
            defaultValue: true,
            description: '''
                Boolean to create a Google Sheet with comparison data<br/>
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
                This includes the AWS S3 Bucket, Kafka (if applicable), LokiStack, and flowcollector
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
                        currentBuild.displayName = "${currentBuild.displayName}-${params.FLEXY_BUILD_NUMBER}"
                        currentBuild.description = "Flexy-install Job: <a href=\"${buildinfo.buildUrl}\">${params.FLEXY_BUILD_NUMBER}</a><br/>"
                        buildinfo.params.each { env.setProperty(it.key, it.value) }
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
                    if (scaleJob.result != 'SUCCESS') {
                        error 'Scale job failed :('
                    }
                    else {
                        println "Successfully scaled cluster to ${params.WORKER_COUNT} worker nodes :)"
                        currentBuild.description += "Scale Job: <b><a href=${scaleJob.absoluteUrl}>${scaleJob.getNumber()}</a></b><br/>"
                        if (params.INFRA_WORKLOAD_INSTALL) {
                            println 'Successfully installed infrastructure nodes :)'
                        }
                        sh(returnStatus: true, script: '''
                            oc get nodes
                            echo "Total Workers: `oc get nodes | grep worker | wc -l`"
                        ''')
                    }
                }
            }
        }
        stage('Install Netobserv Operator') {
            when {
                expression { params.INSTALLATION_SOURCE != 'None' }
            }
            steps {
                script {
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
                            oc get pods -n netobserv
                            oc get pods -n netobserv-privileged
                            oc get pods -n openshift-operators
                            oc get pods -n openshift-operators-redhat
                        ''')
                    }
                }
            }
        }
        stage('Configure NOO, flowcollector, and Kafka') {
            steps {
                script {
                    // attempt updating common parameters of NOO and flowcollector
                    println 'Updating common parameters of NOO and flowcollector...'
                    env.NAMESPACE = sh(returnStdout: true, script: "oc get pods -l app=netobserv-operator -o jsonpath='{.items[*].metadata.namespace}' -A").trim()
                    env.RELEASE = sh(returnStdout: true, script: "oc get pods -l app=netobserv-operator -o jsonpath='{.items[*].spec.containers[1].env[0].value}' -n ${NAMESPACE}").trim()
                    returnCode = sh(returnStatus: true, script: """
                        oc -n $NAMESPACE patch csv $RELEASE --type=json -p "[{"op": "replace", "path": "/spec/install/spec/deployments/0/spec/template/spec/containers/0/resources/limits/memory", "value": ${params.CONTROLLER_MEMORY_LIMIT}}]"
                        oc patch flowcollector cluster --type=json -p "[{"op": "replace", "path": "/spec/agent/type", "value": "EBPF"}] -n netobserv"
                        oc patch flowcollector cluster --type=json -p "[{"op": "replace", "path": "/spec/agent/ebpf/sampling", "value": ${params.FLP_SAMPLING_RATE}}] -n netobserv"
                        oc patch flowcollector cluster --type=json -p "[{"op": "replace", "path": "/spec/processor/resources/limits/cpu", "value": "${params.FLP_CPU_LIMIT}"}] -n netobserv"
                        oc patch flowcollector cluster --type=json -p "[{"op": "replace", "path": "/spec/processor/resources/limits/memory", "value": "${params.FLP_MEMORY_LIMIT}"}] -n netobserv"
                    """)
                    // fail pipeline if setup failed, continue otherwise
                    if (returnCode.toInteger() != 0) {
                        error('Updating common parameters of NOO and flowcollector failed :(')
                    }
                    else {
                        println 'Successfully updated common parameters of NOO and flowcollector :)'
                    }
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
                                oc get pods -n netobserv
                                oc get pods -n netobserv-privileged
                                oc get pods -n openshift-operators
                                oc get pods -n openshift-operators-redhat
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
                expression { params.USER_WORKLOADS == true }
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
                    // attempt installation of dittybopper
                    DITTYBOPPER_PARAMS = "-t $WORKSPACE/ocp-qe-perfscale-ci/scripts/netobserv-dittybopper.yaml -i $WORKSPACE/ocp-qe-perfscale-ci/scripts/netobserv_dittybopper_ebpf.json"
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
                            booleanParam(name: 'CERBERUS_CHECK', value: true),
                            string(name: 'JENKINS_AGENT_LABEL', value: params.JENKINS_AGENT_LABEL),
                            booleanParam(name: 'GEN_CSV', value: false)
                        ]
                    }
                    else {
                        env.JENKINS_JOB = 'scale-ci/e2e-benchmarking-multibranch-pipeline/kube-burner'
                        workloadJob = build job: env.JENKINS_JOB, parameters: [
                            string(name: 'BUILD_NUMBER', value: params.FLEXY_BUILD_NUMBER),
                            string(name: 'WORKLOAD', value: params.WORKLOAD),
                            booleanParam(name: 'CLEANUP', value: true),
                            booleanParam(name: 'CERBERUS_CHECK', value: true),
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
                        if (params.USER_WORKLOADS == true) {
                            NOPE_ARGS += " --user-workloads"
                        }
                        if (params.NOPE_DUMP == true) {
                            NOPE_ARGS += " --dump"
                        }
                        if (params.NOPE_DEBUG == true) {
                            NOPE_ARGS += " --debug"
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
                        env.COMPARISON_CONFIG = 'netobserv_touchstone.json'
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
                            unstable('Touchstone tool failed - run locally with the given UUID to get run statistics :(')
                        }
                        else {
                            println 'Successfully ran Touchstone tool :)'
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
                artifacts: 'ocp-qe-perfscale-ci/data/**, ocp-qe-perfscale-ci/scripts/netobserv-dittybopper.yaml',
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
            }
        }
    }
}
