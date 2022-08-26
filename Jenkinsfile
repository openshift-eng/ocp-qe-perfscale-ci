@Library('flexy') _

// rename build
def userCause = currentBuild.rawBuild.getCause(Cause.UserIdCause)
def upstreamCause = currentBuild.rawBuild.getCause(Cause.UpstreamCause)

if (userCause) {
    userId = userCause.getUserId()
}
else if (upstreamCause) {
    def upstreamJob = Jenkins.getInstance().getItemByFullName(upstreamCause.getUpstreamProject(), hudson.model.Job.class)
    if (upstreamJob) {
        def upstreamBuild = upstreamJob.getBuildByNumber(upstreamCause.getUpstreamBuild())
        if (upstreamBuild) {
            def realUpstreamCause = upstreamBuild.getCause(Cause.UserIdCause)
            if (realUpstreamCause) {
                userId = realUpstreamCause.getUserId()
            }
        }
    }
}
if (userId) {
    currentBuild.displayName = userId
}
println "user id $userId"
def RETURNSTATUS = "default"
def output = ""
def status = ""
pipeline {
    agent { label params['JENKINS_AGENT_LABEL'] }

    parameters {
        string(
            name: 'BUILD_NUMBER',
            defaultValue: '',
            description: 'Build number of job that has installed the cluster.'
        )
        booleanParam(
            name: 'WRITE_TO_FILE',
            defaultValue: false,
            description: 'Value to write to google sheet (will run <a href=https://mastern-jenkins-csb-openshift-qe.apps.ocp-c1.prod.psi.redhat.com/job/scale-ci/job/e2e-benchmarking-multibranch-pipeline/job/write-scale-ci-results/>write-scale-ci-results</a>)'
        )
        booleanParam(
            name: 'CERBERUS_CHECK',
            defaultValue: false,
            description: 'Check cluster health status pass'
        )
        string(
            name: 'JENKINS_AGENT_LABEL',
            defaultValue: 'oc412',
            description: '''
                scale-ci-static: for static agent that is specific to scale-ci, useful when the jenkins dynamic agen isn't stable<br>
                4.y: oc4y e.g, for 4.12, use oc412
            '''
        )
        string(
            name: 'ES_SERVER',
            defaultValue: '',
            description: 'Make sure to include OCP-QE ES server, talk to Mike Fiedler or Paige Rubendall'
        )
        string(
            name: 'ES_INDEX',
            defaultValue: 'router-test-results',
            description: 'Elasticsearch index name'
        )
        string(
            name: 'RUNTIME',
            defaultValue: '60',
            description: 'Workload duration in seconds'
        )
        string(
            name: 'SAMPLES',
            defaultValue: '2',
            description: 'Number of samples to perform of each test'
        )
        string(
            name: 'TERMINATIONS',
            defaultValue: 'mix',
            description: 'List of HTTP terminations to test. http edge passthrough reencrypt mix'
        )
        string(
            name: 'KEEPALIVE_REQUESTS',
            defaultValue: '0 1 50',
            description: 'List with the number of keep alive requests to perform in the same HTTP session'
        )
        string(
            name: 'HOST_NETWORK',
            defaultValue: 'true',
            description: 'Enable hostNetwork in the mb client'
        )
        string(
            name: 'NODE_SELECTOR',
            defaultValue: '{node-role.kubernetes.io/workload: }',
            description:'Node selector of the mb client'
        )
        string(
            name: 'LARGE_SCALE_THRESHOLD',
            defaultValue: '24',
            description: 'Number of worker nodes required to consider a large scale scenario'
        )
        string(
            name: 'LARGE_SCALE_ROUTES',
            defaultValue: '500',
            description: 'Number of routes of each termination to create in the large scale scenario'
        )
        string(
            name: 'LARGE_SCALE_CLIENTS',
            defaultValue: '1 20',
            description: 'Threads/route to use in the large scale scenario'
        )
        string(
            name: 'LARGE_SCALE_CLIENTS_MIX',
            defaultValue: '1 10',
            description: 'Threads/route to use in the large scale scenario with mix termination'
        )
        string(
            name: 'SMALL_SCALE_ROUTES',
            defaultValue: '100',
            description: 'Number of routes of each termination to create in the small scale scenario'
        )
        string(
            name: 'SMALL_SCALE_CLIENTS',
            defaultValue: '1 100',
            description: 'Threads/route to use in the small scale scenario'
        )
        string(
            name: 'SMALL_SCALE_CLIENTS_MIX',
            defaultValue: '1 50',
            description: 'Threads/route to use in the small scale scenario with mix termination'
        )
        string(
            name: 'BASELINE_UUID',
            defaultValue: '',
            description: 'Baseline UUID used for comparison'
        )
        string(
            name: 'COMPARISON_ALIASES',
            defaultValue: '',
            description: 'Benchmark-comparison aliases, e.g. 4.10.z 4.11.0-0.nightly-xxxx'
        )
        booleanParam(
            name: 'GEN_CSV',
            defaultValue: true,
            description: 'Boolean to create a google sheet with comparison data'
        )
        text(
            name: 'ENV_VARS',
            defaultValue: '',
            description: '''
                Enter list of additional (optional) Env Vars you'd want to pass to the script, one pair on each line.<br/>
                e.g.<br/>
                SOMEVAR1='env-test'<br/>
                SOMEVAR2='env2-test'<br/>
                ...<br/>
                SOMEVARn='envn-test'<br/>
                check <a href="https://github.com/cloud-bulldozer/e2e-benchmarking/tree/master/workloads/router-perf-v2">router perf README</a> for more env vars you can set
            '''
        )
        booleanParam(
            name: 'INFRA_WORKLOAD_INSTALL',
            defaultValue: false,
            description: '''
                Install workload and infrastructure nodes even if less than 50 nodes.<br/>
                Checking this parameter box is valid only when SCALE_UP is greater than 0.
            '''
        )
        string(
            name: 'SCALE_UP',
            defaultValue: '0',
            description: 'If value is set to anything greater than 0, cluster will be scaled up before executing the workload.'
        )
        string(
            name: 'SCALE_DOWN',
            defaultValue: '0',
            description: '''
                If value is set to anything greater than 0, cluster will be scaled down after the execution of the workload is complete,<br/>
                if the build fails, scale down may not happen, user should review and decide if cluster is ready for scale down or re-run the job on same cluster.
            '''
        )
        string(
            name: 'E2E_BENCHMARKING_REPO',
            defaultValue: 'https://github.com/cloud-bulldozer/e2e-benchmarking',
            description:'You can change this to point to your fork if needed.'
        )
        string(
            name: 'E2E_BENCHMARKING_REPO_BRANCH',
            defaultValue: 'master',
            description: 'You can change this to point to a branch on your fork if needed.'
        )
    }

    stages {
        stage('Run Router perf tests'){
            environment{
                EMAIL_ID_FOR_RESULTS_SHEET = "${userId}@redhat.com"
            }
            steps {
                script {
                    if (params.SCALE_UP.toInteger() > 0) {
                        build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cluster-workers-scaling', 
                            parameters: [
                                string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), text(name: "ENV_VARS", value: ENV_VARS), 
                                string(name: 'WORKER_COUNT', value: SCALE_UP), 
                                string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL), 
                                booleanParam(name: 'INFRA_WORKLOAD_INSTALL', value: INFRA_WORKLOAD_INSTALL)
                            ]
                    }
                }
                deleteDir()
                checkout([
                    $class: 'GitSCM', 
                    branches: [[name: params.E2E_BENCHMARKING_REPO_BRANCH ]],
                    doGenerateSubmoduleConfigurations: false, 
                    userRemoteConfigs: [[url: params.E2E_BENCHMARKING_REPO ]]
                ])
                copyArtifacts(
                    filter: '', 
                    fingerprintArtifacts: true, 
                    projectName: 'ocp-common/Flexy-install', 
                    selector: specific(params.BUILD_NUMBER),
                    target: 'flexy-artifacts'
                )
                script {
                    buildinfo = readYaml file: "flexy-artifacts/BUILDINFO.yml"
                    currentBuild.displayName = "${currentBuild.displayName}-${params.BUILD_NUMBER}"
                    currentBuild.description = "Copying Artifact from Flexy-install build <a href=\"${buildinfo.buildUrl}\">Flexy-install#${params.BUILD_NUMBER}</a>"
                    buildinfo.params.each { env.setProperty(it.key, it.value) }
                }
                script {
                    withCredentials([file(credentialsId: 'sa-google-sheet', variable: 'GSHEET_KEY_LOCATION')]) {
                        RETURNSTATUS = sh(returnStatus: true, script: '''
                            # Get ENV VARS Supplied by the user to this job and store in .env_override
                            echo "$ENV_VARS" > .env_override
                            # Export those env vars so they could be used by CI Job
                            set -a && source .env_override && set +a
                            mkdir -p ~/.kube
                            cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config
                            oc config view
                            oc projects
                            ls -ls ~/.kube/
                            env
                            cd workloads/router-perf-v2
                            ./ingress-performance.sh  | tee "ingress_router.out"
                            '''
                        )
                        if (RETURNSTATUS.toInteger() == 0) {
                            status = "PASS"
                        }
                        else { 
                            currentBuild.result = "FAILURE"
                            status = "Router perf FAIL"
                        }
                        output = sh(returnStdout: true, script: 'cat workloads/router-perf-v2/ingress_router.out')
                    }
                }
                script{
                    if (params.CERBERUS_CHECK == true) {
                        cerberus_job = build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cerberus',
                            parameters: [
                                string(name: 'BUILD_NUMBER', value: BUILD_NUMBER),text(name: "ENV_VARS", value: ENV_VARS),
                                string(name: "CERBERUS_ITERATIONS", value: "1"), string(name: "CERBERUS_WATCH_NAMESPACES", value: "[^.*\$]"),
                                string(name: 'CERBERUS_IGNORE_PODS', value: "[^installer*, ^kube-burner*, ^redhat-operators*, ^certified-operators*]"),
                                string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL),booleanParam(name: "INSPECT_COMPONENTS", value: true)
                            ],
                            propagate: false
                        def result = cerberus_job.result.toString()
                        println "cerberus result $result"
                        if (status == "PASS") {
                            println "previous status = pass"
                            if (cerberus_job.result.toString() != "SUCCESS") {
                                status = "Cerberus check failed"
                                currentBuild.result = "FAILURE"
                            }
                        }
                        else {
                            println "previous test had already failed"
                            if (cerberus_job.result.toString() != "SUCCESS") {
                                status += ", Cerberus check failed"
                                currentBuild.result = "FAILURE"
                            }
                        }
                    }
                }
                script{
                    if (params.WRITE_TO_FILE == true) {
                        def parameter_to_pass = ""
                        build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/write-scale-ci-results', 
                            parameters: [
                                string(name: 'BUILD_NUMBER', value: BUILD_NUMBER),text(name: "ENV_VARS", value: ENV_VARS),
                                string(name: 'CI_JOB_ID', value: BUILD_ID), string(name: 'CI_JOB_URL', value: BUILD_URL), 
                                string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL), string(name: "CI_STATUS", value: "${status}"), 
                                string(name: "JOB", value: "router-perf"), string(name: "JOB_PARAMETERS", value: "${parameter_to_pass}" ), 
                                text(name: "JOB_OUTPUT", value: "${output}")
                            ],
                            propagate: false
                    }
                }
                script{
                    // if the build fails, scale down will not happen, letting user review and decide if cluster is ready for scale down or re-run the job on same cluster
                    if (params.SCALE_DOWN.toInteger() > 0) {
                        build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cluster-workers-scaling', 
                            parameters: [
                                string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), string(name: 'WORKER_COUNT', value: SCALE_DOWN), 
                                text(name: "ENV_VARS", value: ENV_VARS), string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL)
                            ]
                    }
                }
            }
        }
    }
    post {
        always {
            println 'Post Section - Always'
            archiveArtifacts(
                artifacts: 'workloads/router-perf-v2/ingress_router.out',
                allowEmptyArchive: true,
                fingerprint: true
            )
        }
        failure {
            println 'Post Section - Failure'
        }
    }
}
