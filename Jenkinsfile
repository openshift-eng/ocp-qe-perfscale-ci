@Library('flexy') _

// rename build
def userCause = currentBuild.rawBuild.getCause(Cause.UserIdCause)
def upstreamCause = currentBuild.rawBuild.getCause(Cause.UpstreamCause)

userId = "ocp-perfscale-qe"
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

def CUR_JENKINS_JOB_NUMBER = currentBuild.number.toString()
println "JENKINS_JOB_NUMBER $CUR_JENKINS_JOB_NUMBER"

pipeline {
    agent { label params['JENKINS_AGENT_LABEL'] }

    environment {
        def JENKINS_JOB_NUMBER = "${CUR_JENKINS_JOB_NUMBER}"
    }

    triggers {
        cron('0 3 * * 5')
    }

    parameters {
        string(
            name: 'OCM_TOKEN_URL',
            defaultValue: 'https://sso.redhat.com/auth/realms/redhat-external/protocol/openid-connect/token',
            description: 'OCM Token URL'
        )
        string(
            name: 'GATEWAY_URL',
            defaultValue: 'https://api.integration.openshift.com',
            description: 'Gateway URL'
        )
        string(
            name: 'JOB_TIMEOUT',
            defaultValue: '28800',
            description: 'Job Timeout'
        )
        string(
            name: 'COOLDOWN',
            defaultValue: '60',
            description: 'Cooldown'
        )
        string(
            name: 'SLEEP',
            defaultValue: '300',
            description: 'Sleep'
        )
        string(
            name: 'ORCHESTRATION_USER',
            defaultValue: 'perf-ci',
            description: 'Orchestration User'
        )
        string(
            name: 'KUBE_BURNER_RELEASE_URL',
            defaultValue: 'https://github.com/cloud-bulldozer/kube-burner/releases/download/v0.16.1/kube-burner-0.16.1-Linux-x86_64.tar.gz',
            description: 'Kube Burner Release URL'
        )
        booleanParam(
            name: "SEND_SLACK",
            defaultValue: false,
            description: "Check this box to send a Slack notification to #ocp-qe-scale-ci-results upon the job's completion"
        )
        string(
            name: 'QE_OCM_REPO',
            defaultValue: 'https://github.com/chentex/ocp-qe-perfscale-ci',
            description: 'You can change this to point to your fork if needed.'
        )
        string(
            name: 'QE_OCM_REPO_BRANCH',
            defaultValue: 'ocm-api-load',
            description: 'You can change this to point to a branch on your fork if needed.'
        )
        string(
            name: 'AWS_PROFILE',
            defaultValue: 'openshift-perfscale',
            description: 'AWS profile to use.'
        )
        string(
            name: 'AWS_ACCOUNT_ID',
            defaultValue: '415909267177',
            description: 'AWS account ID.'
        )
        string(
            name: 'AWS_DEFAULT_REGION',
            defaultValue: 'us-west-2',
            description: 'AWS default region.'
        )
        string(
            name: 'AWS_SECRET_ACCESS_KEY',
            defaultValue: '',
            description: 'AWS access key.'
        )
        string(
            name: 'AWS_ACCESS_KEY_ID',
            defaultValue: '',
            description: 'AWS access key ID.'
        )
        string(
            name: 'ES_SERVER_USER',
            defaultValue: 'admin',
            description: 'ES Server URL to store results.'
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
                check <a href="https://github.com/cloud-bulldozer/e2e-benchmarking/tree/master/workloads/ingress-perf">ingress perf README</a> for more env vars you can set
            '''
        )
    }

    stages {
        stage('Run OCM API Load tests'){
            steps {
                deleteDir()
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: params.QE_OCM_REPO_BRANCH ]],
                    doGenerateSubmoduleConfigurations: false,
                    userRemoteConfigs: [[url: params.QE_OCM_REPO ]]
                ])
                script {
                    withCredentials([
                            file(credentialsId: 'ocm-al-aws', variable: 'AWS_CREDS' ),
                            file(credentialsId: 'ocm-al-infra', variable: 'INFRA' ),
                            string(credentialsId: 'ocm-al-ocm-token', variable: 'OCM_TOKEN' ),
                            string(credentialsId: 'ocm-al-ocm-client-id', variable: 'OCM_CLIENT_ID' ),
                            string(credentialsId: 'ocm-al-ocm-client-secret', variable: 'OCM_CLIENT_SECRET' ),
                            string(credentialsId: 'ocm-al-prom-token', variable: 'PROM_TOKEN' ),
                            string(credentialsId: 'ocm-al-server-password', variable: 'ES_SERVER_PASS' ),
                            string(credentialsId: 'ocm-al-sshkey-token', variable: 'SSHKEY_TOKEN' ),
                    ]) {
                        env.AWS_ACCESS_KEY_ID = sh(script: "cat \$AWS_CREDS | awk -F' = ' '/^aws_access_key_id/ {print \$2}'", returnStdout: true).trim()
                        env.AWS_SECRET_ACCESS_KEY = sh(script: "cat \$AWS_CREDS | awk -F' = ' '/^aws_secret_access_key/ {print \$2}'", returnStdout: true).trim()
                        env.ORCHESTRATION_HOST = sh(script: "cat \$INFRA | awk -F' = ' '/^ORCHESTRATION_HOST/ {print \$2}'", returnStdout: true).trim()
                        env.PROM_URL = sh(script: "cat \$INFRA | awk -F' = ' '/^PROM_URL/ {print \$2}'", returnStdout: true).trim()
                        env.ES_SERVER_URL = sh(script: "cat \$INFRA | awk -F' = ' '/^ES_SERVER/ {print \$2}'", returnStdout: true).trim()
                        sh '''
                        ./scripts/run_ocm_benchmark.sh -o ocm-api-load
                        sleep 60
                        ./scripts/run_ocm_benchmark.sh -o cleanup
                        '''
                    }
                }
           }
        }
    }
    post {
        always {

            println 'Post Section - Always'

            script {
                if (params.SEND_SLACK == true ) {
                    build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/post-to-slack',
                    parameters: [
                        string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), string(name: 'WORKLOAD', value: "OCM API Load Test"),
                        text(name: "BUILD_URL", value: env.BUILD_URL), string(name: 'BUILD_ID', value: currentBuild.number.toString()),string(name: 'RESULT', value:currentBuild.currentResult)
                    ], propagate: false
                }
            }
        }
    }
}
