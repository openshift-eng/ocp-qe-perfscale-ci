@Library('flexy') _

//Variables
def DITTYBOPPER_URL
def TEST_START
def TEST_END

// rename build
def userId = currentBuild.rawBuild.getCause(hudson.model.Cause$UserIdCause)?.userId
if (userId) {
    currentBuild.displayName = userId
}

pipeline {

    // job runs on specified agent
    agent { label params.JENKINS_AGENT_LABEL }

    // set timeout and enable coloring in console output
    options {
        timeout(time: 1, unit: 'HOURS')
        ansiColor('xterm')
    }

    // job parameters
    parameters {
        // Flexy-install and label
        string(
            name: 'FLEXY_BUILD_NUMBER',
            defaultValue: '',
            description: 'Build number of <a href=https://mastern-jenkins-csb-openshift-qe.apps.ocp-c1.prod.psi.redhat.com/job/ocp-common/job/Flexy-install/>Flexy-install</a> job that installed the cluster'
        )
        string(
            name: 'JENKINS_AGENT_LABEL',
            defaultValue: 'oc420',
            description: 'Label of Jenkins agent to execute job'
        )
        // Pre-workload cluster configuration
        separator(
            name: 'CLUSTER_CONFIG_OPTIONS',
            sectionHeader: 'OpenShift Cluster Configuration Options',
            sectionHeaderStyle: '''
                font-size: 16px;
                font-weight: bold;
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
        string(
            name: 'DITTYBOPPER_PARAMS',
            defaultValue:'',
            description:'Arguments that are added when deploying dittybopper'
        )
        separator(
            name: 'OPENTELEMETRY_OPERATOR_OPTIONS',
            sectionHeader: 'Red Hat OpenShift distributed tracing data collection',
            sectionHeaderStyle: '''
                font-size: 16px;
                font-weight: bold;
            '''
        )
        booleanParam(
            name: 'INSTALL_OPENTELEMETRY_OPERATOR',
            defaultValue: true,
            description: 'Install Red Hat OpenShift distributed tracing data collection'
        )
        string(
            name: 'OPENTELEMETRY_OPERATOR_VERSION',
            defaultValue: '0.81.1-5',
            description: 'Version of Red Hat OpenShift distributed tracing data collection you want to install'
        )
        separator(
            name: 'TEMPO_OPERATOR_OPTIONS',
            sectionHeader: 'Tempo Operator',
            sectionHeaderStyle: '''
                font-size: 16px;
                font-weight: bold;
            '''
        )
        booleanParam(
            name: 'INSTALL_TEMPO_OPERATOR',
            defaultValue: true,
            description: 'Install Grafana Tempo Operator'
        )
        string(
            name: 'TEMPO_OPERATOR_VERSION',
            defaultValue: '0.3.1-3',
            description: 'Version of Grafana Tempo Operator you want to install'
        )
        // Workload
        separator(
            name: 'WORKLOAD_CONFIG_OPTIONS',
            sectionHeader: 'Workload Configuration Options',
            sectionHeaderStyle: '''
                font-size: 16px;
                font-weight: bold;
            '''
        )
        string(
            name: 'DISTRIBUTED_TRACING_QE_REPO',
            defaultValue:'https://github.com/openshift/distributed-tracing-qe',
            description: 'Repository to get distributet tracing test scripts and artifacts<br/>You can change it to point your fork if needed'
        )
        string(
            name: 'DISTRIBUTED_TRACING_QE_BRANCH',
            defaultValue:'main',
            description:'You can change this to point to a branch on your fork if needed.'
        )
        text(
            name: 'ENV_VARS', 
            defaultValue: '', 
            description:'''
                Enter list of additional (optional) Env vars you'd want to pass to the script, one pair on each line. <br>
                e.g.<br>
                VAR1='env-test'<br>
                VAR2='env2-test'<br>
                ...<br>
                VARn='envn-test'<br>
                Check test scenario/script to see if you need add some.
                '''
        )
        string(
            name: 'TEST_SCRIPT', 
            defaultValue: '', 
            description: 'Relative path to the script to run under <a href="https://github.com/openshift/distributed-tracing-qe">Distributed Tracing QE repo</a>'
        )
        separator(
            name: 'CLEANUP_OPTIONS',
            sectionHeader: 'Cleanup Options',
            sectionHeaderStyle: '''
                font-size: 16px;
                font-weight: bold;
            '''
        )
        booleanParam(
            name: 'UNINSTALL_DITTYBOPPER',
            defaultValue: false,
            description: 'Setting this flag will uninstall dittybopper dashboards'
        )
        booleanParam(
            name: 'UNINSTALL_OPENTELEMETRY_OPERATOR',
            defaultValue: false,
            description: 'Setting this flag will uninstall Red Hat OpenShift distributed tracing data collection'
        )
        booleanParam(
            name: 'UNINSTALL_TEMPO_OPERATOR',
            defaultValue: false,
            description: 'Setting this flag will uninstall Grafana Tempo Operator'
        )
    }

    stages {
        stage('Validate job parameters') {
            steps {
                script {
                    if (params.FLEXY_BUILD_NUMBER == '') {
                        error('FLEXY_BUILD_NUMBER must be specified')
                    }
                    if (params.JENKINS_AGENT_LABEL == '') {
                        error('JENKINS_AGENT_LABEL must be specified')
                    }
                    if (params.INSTALL_OPENTELEMETRY_OPERATOR == true && params.OPENTELEMETRY_OPERATOR_VERSION == '') {
                        error('Installing OpenTelemetry Operator, OPENTELEMETRY_OPERATOR_VERSION must be specified')
                    }
                    if (params.INSTALL_TEMPO_OPERATOR == true && params.TEMPO_OPERATOR_VERSION == ''){
                        error('Installing Tempo Operator, TEMPO_OPERATOR_VERSION must be specified')
                    }
                    if (params.TEST_SCRIPT == '') {
                        error('TEST_SCRIPT that you want to run must be specified')
                    }
                    println('Job params are valid - continuing execution...')
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

        stage('Install OpenTelemetry Operator') {
            when {
                expression {params.INSTALL_OPENTELEMETRY_OPERATOR == true}
            }
            steps {
                script {
                    installOpenTelemetryReturnCode = sh(returnStatus: true, script: '''
                        export OPENTELEMETRY_OPERATOR_VERSION=$OPENTELEMETRY_OPERATOR_VERSION
                        pushd scripts
                        ./install-opentelemetry-operator.sh
                        popd
                    ''')
                    // Fail jenkins job if installation failed
                    if (installOpenTelemetryReturnCode.toInteger() != 0) {
                        error("${params.OPENTELEMETRY_OPERATOR_VERSION} version of OpenTelemetry Operator installation failed.")
                    }
                    else {
                        println("${params.OPENTELEMETRY_OPERATOR_VERSION} version of OpenTelemetry Operator successfully installed.")
                    }
                }
            }
        }

        stage('Install Tempo Operator') {
            when {
                expression {params.INSTALL_TEMPO_OPERATOR == true}
            }
            steps {
                script {
                    installTempoOperatorReturnCode = sh(returnStatus: true, script: '''
                        export TEMPO_OPERATOR_VERSION=$TEMPO_OPERATOR_VERSION
                        pushd scripts
                        ./install-tempo-operator.sh
                        popd
                    ''')
                    // Fail jenkins job if installation failed
                    if (installTempoOperatorReturnCode.toInteger() != 0) {
                        error("${params.TEMPO_OPERATOR_VERSION} version of Tempo Operator installation failed.")
                    }
                    else {
                        println("${params.TEMPO_OPERATOR_VERSION} version of Tempo Operator successfully installed.")
                    }
                }
            }
        }

        stage('Install Dittybopper') {
            when {
                expression { params.INSTALL_DITTYBOPPER == true}
            }
            steps {
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: params.DITTYBOPPER_REPO_BRANCH ]],
                    doGenerateSubmoduleConfigurations: false,
                    extensions: [
                        [$class: 'CloneOption', noTags: true, reference: '', shallow: true],
                        [$class: 'PruneStaleBranch'],
                        [$class: 'CleanCheckout'],
                        [$class: 'IgnoreNotifyCommit'],
                        [$class: 'RelativeTargetDirectory', relativeTargetDir: 'performance-dashboards']
                    ],
                    userRemoteConfigs: [[url: params.DITTYBOPPER_REPO ]]
                ])
                script{ 
                    sh label: '', script: '''
                        pushd performance-dashboards/dittybopper
                        ./deploy.sh $DITTYBOPPER_PARAMS
                        popd
                        dittybopper_url=$(oc get routes -n dittybopper -o jsonpath={.items[0].spec.host})
                        echo -e "Dittybopper url: http://${dittybopper_url}/"
                        '''
                }
            }
        }

        stage("Workload") {
            steps{
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: params.DISTRIBUTED_TRACING_QE_BRANCH ]],
                    doGenerateSubmoduleConfigurations: false,
                    extensions: [
                        [$class: 'CloneOption', noTags: true, reference: '', shallow: true],
                        [$class: 'PruneStaleBranch'],
                        [$class: 'CleanCheckout'],
                        [$class: 'IgnoreNotifyCommit'],
                        [$class: 'RelativeTargetDirectory', relativeTargetDir: 'distributed-tracing-qe']
                    ],
                    userRemoteConfigs: [[url: params.DISTRIBUTED_TRACING_QE_REPO ]]
                ])
                script{
                    TEST_START = sh(returnStdout: true, script: 'date +%s%3N').trim()
                    try {
                        sh label: '', script: '''
                            pushd distributed-tracing-qe
                            chmod +x $TEST_SCRIPT
                            ./$TEST_SCRIPT
                            popd
                            '''
                    } catch (err) {
                        println("Test failed: ${err}")
                    }
                    TEST_END = sh(returnStdout: true, script: 'date +%s%3N').trim()
                }
            }
        }

        stage("Post Workload") {
            steps{
                script {
                    //Check if dittybopper is installed
                    dittybopper_installedReturnCode = sh(returnStatus: true, script: '''
                        oc get project dittybopper
                    ''')
                    if (dittybopper_installedReturnCode.toInteger() != 0) {
                        println("Dittybopper not installed. NO URL to provide")
                    }
                    else {
                        DITTYBOPPER_URL = sh(returnStdout: true, script: 'oc get routes -n dittybopper -o jsonpath={.items[0].spec.host}').trim()
                        println("API Performance url:        http://${DITTYBOPPER_URL}/d/xxFgyoDIz/api-performance?orgId=1&from=${TEST_START}&to=${TEST_END}")
                        println("Hypershift Performance url: http://${DITTYBOPPER_URL}/d/SA5gyoDSk/hypershift-performance?orgId=1&from=${TEST_START}&to=${TEST_END}")
                        println("OpenShift Performance url:  http://${DITTYBOPPER_URL}/d/NwFRsoDSk/openshift-performance?orgId=1&from=${TEST_START}&to=${TEST_END}")
                        println("k8s Performance url:        http://${DITTYBOPPER_URL}/d/3y5gsoDSz/k8s-performance?orgId=1&from=${TEST_START}&to=${TEST_END}")
                    }
                }
            }
        }
    }

    post {
        cleanup {
            script {
                if (params.UNINSTALL_OPENTELEMETRY_OPERATOR == true) {
                    sh label: '', script: '''
                        pushd scripts
                        ./uninstall-opentelemetry-operator.sh
                        popd
                    '''
                }
                if (params.UNINSTALL_TEMPO_OPERATOR == true) {
                    sh label: '', script: '''
                        pushd scripts
                        ./uninstall-tempo-operator.sh
                        popd
                    '''
                }
                if (params.UNINSTALL_DITTYBOPPER == true) {
                    sh label: '', script: '''
                        oc delete project dittybopper
                    '''
                }
            }
        }
    }
}
