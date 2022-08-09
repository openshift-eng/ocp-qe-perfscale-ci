@Library('flexy') _

// rename build
def userId = currentBuild.rawBuild.getCause(hudson.model.Cause$UserIdCause)?.userId
if (userId) {
  currentBuild.displayName = userId
}

pipeline {

    agent { label params.JENKINS_AGENT_LABEL }

    options {
        timeout(time: 1, unit: 'HOURS')
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
            description: 'Build number of Flexy job that installed the cluster'
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
            choices: ['OperatorHub', 'Source', 'None'],
            description: '''
                Network Observability can be installed either from OperatorHub or directly from the main branch of the Source code<br/>
                If None is selected the installation will be skipped<br/>
            '''
        )
        booleanParam(
            name: 'USER_WORKLOADS',
            defaultValue: true,
            description: 'Check this box to setup FLP service and create service-monitor'
        )
        choice(
            name: 'COLLECTOR_AGENT',
            choices: ['ipfix', 'ebpf'],
            description: 'Collector agent Network Observability will use'
        )
        string(
            name: 'FLOW_SAMPLING_RATE',
            defaultValue: '100',
            description: 'Rate at which to sample flows'
        )
        string(
            name: 'CPU_LIMIT',
            defaultValue: '1000m',
            description: 'Note that 1000m = 1000 millicores, i.e. 1 core'
        )
        string(
            name: 'MEMORY_LIMIT',
            defaultValue: '500Mi',
            description: 'Note that 500Mi = 500 megabytes, i.e. 0.5 GB'
        )
        string(
            name: 'REPLICAS',
            defaultValue: '1',
            description: 'Number of FLP replica pods'
        )
    }

    stages {
        stage('Validate job parameters') {
            steps {
                script {
                    if (params.FLEXY_BUILD_NUMBER == '') {
                        error "A Flexy build number must be specified"
                    }
                    println("Job params are valid - continuing execution...")
                }
            }
        }
        stage('Get Flexy config and Netobserv scripts') {
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
                script {
                    buildinfo = readYaml file: "flexy-artifacts/BUILDINFO.yml"
                    currentBuild.displayName = "${currentBuild.displayName}-${params.FLEXY_BUILD_NUMBER}"
                    currentBuild.description = "Copied artifacts from Flexy-install build <a href=\"${buildinfo.buildUrl}\">${params.FLEXY_BUILD_NUMBER}</a>"
                    buildinfo.params.each { env.setProperty(it.key, it.value) }
                    sh(returnStatus: true, script: '''
                        mkdir -p ~/.kube
                        cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config
                    ''')
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
                    if (params.INSTALLATION_SOURCE == 'OperatorHub') {
                        println "Installing Network Observability from OperatorHub..."
                        returnCode = sh(returnStatus: true, script: '''
                            source $WORKSPACE/ocp-qe-perfscale-ci/scripts/netobserv.sh
                            deploy_operatorhub_noo
                        ''')
                    }
                    else {
                        println "Installing Network Observability from Source..."
                        returnCode = sh(returnStatus: true, script: '''
                            source $WORKSPACE/ocp-qe-perfscale-ci/scripts/netobserv.sh
                            deploy_main_noo
                        ''')
                    }
                    // fail pipeline if installation failed, continue otherwise
                    if (returnCode.toInteger() != 0) {
                        error("Network Observability installation from ${params.INSTALLATION_SOURCE} failed :(")
                    }
                    else {
                        println "Successfully installed Network Observability from ${params.INSTALLATION_SOURCE} :)"
                    }
                }
            }
        }
        stage('Setup FLP and service-monitor') {
            when {
                expression { params.USER_WORKLOADS == true }
            }
            steps {
                script {
                    // attempt setup of FLP service and creation of service-monitor
                    println "Setting up FLP service and creating service-monitor..."
                    returnCode = sh(returnStatus: true, script:  '''
                        source $WORKSPACE/ocp-qe-perfscale-ci/scripts/common.sh
                        source $WORKSPACE/ocp-qe-perfscale-ci/scripts/netobserv.sh
                        populate_netobserv_metrics
                    ''')
                    // fail pipeline if setup failed, continue otherwise
                    if (returnCode.toInteger() != 0) {
                        error("Setting up FLP service and creating service-monitor failed :(")
                    }
                    else {
                        println "Successfully set up FLP service and created service-monitor :)"
                    }
                }
            }
        }
        stage('Update flowcollector params') {
            environment {
                COLLECTOR_AGENT = "${params.COLLECTOR_AGENT}"
                FLOW_SAMPLING_RATE = "${params.FLOW_SAMPLING_RATE}"
                CPU_LIMIT = "${params.CPU_LIMIT}"
                MEMORY_LIMIT = "${params.MEMORY_LIMIT}"
                REPLICAS = "${params.REPLICAS}"
            }
            steps {
                script {
                    // attempt updating common parameters of flowcollector
                    println "Updating common parameters of flowcollector..."
                    returnCode = sh(returnStatus: true, script: '''
                        oc patch flowcollector cluster --type=json -p "[{"op": "replace", "path": "/spec/agent", "value": $COLLECTOR_AGENT}] -n network-observability"
                        oc patch flowcollector cluster --type=json -p "[{"op": "replace", "path": "/spec/ipfix/sampling", "value": $FLOW_SAMPLING_RATE}] -n network-observability"
                        oc patch flowcollector cluster --type=json -p "[{"op": "replace", "path": "/spec/flowlogsPipeline/resources/limits/cpu", "value": "$CPU_LIMIT"}] -n network-observability"
                        oc patch flowcollector cluster --type=json -p "[{"op": "replace", "path": "/spec/flowlogsPipeline/resources/limits/memory", "value": "$MEMORY_LIMIT"}] -n network-observability"
                        oc patch flowcollector cluster --type=json -p "[{"op": "replace", "path": "/spec/flowlogsPipeline/replicas", "value": $REPLICAS}] -n network-observability"
                    ''')
                    // fail pipeline if setup failed, continue otherwise
                    if (returnCode.toInteger() != 0) {
                        error("Updating common parameters of flowcollector failed :(")
                    }
                    else {
                        println "Successfully updated common parameters of flowcollector :)"
                    }
                }
            }
        }
    }

    post {
        always {
            println "Post Section - Always"
            archiveArtifacts(
                artifacts: 'ocp-qe-perfscale-ci/data',
                allowEmptyArchive: true,
                fingerprint: true
            )
        }
        failure {
            println "Post Section - Failure"
        }
    }
}
