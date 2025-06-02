@Library('flexy') _

// rename build
def userCause = currentBuild.rawBuild.getCause(Cause.UserIdCause)
def upstreamCause = currentBuild.rawBuild.getCause(Cause.UpstreamCause)

userId = "prubenda"
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

def overall_status = "PASS"
def output = ""
def scale_up_job = null

pipeline {
  agent none

  parameters {
    string(
        name: 'BUILD_NUMBER', 
        defaultValue: '', 
        description: 'Build number of job that has installed the cluster.'
    )
    choice(
        choices: ["conc_jobs","large_network_policy"], 
        name: 'TEST_CASE',
        description:'''<p>
            Select the test case you want to run.<br>
            This job will search the TEST_CASE.sh file under svt repo <a href="https://github.com/openshift/svt/blob/master/perfscale_regression_ci/scripts">perfscale_regression_ci/scripts</a> folder and sub folders<br>
            If SCRIPT is specified TEST_CASE will be overwritten.
            </p>'''
    )
    string(
        name: 'SCRIPT', 
        defaultValue: '', 
        description: '''<p>
            Relative path to the script of the TEST_CASE under <a href="https://github.com/openshift/svt">svt repo</a>.<br>
            e.g.<br>
            For large_network_policy test case: perfscale_regression_ci/scripts/network/large_network_policy.sh<br>
            If TEST_CASE is specified, SCRIPT will overwrite the TEST_CASE.
            </p>'''
    )
    string(
        name: 'PARAMETERS', 
        defaultValue: '', 
        description: '''<p>
                  Parameter or an array of parameters to pass to the TEST_CASE script<p>
                  e.g.<br>
                  For conc_jobs: 100 500 1000 2000<br>
                  For large_network_policy: 5000<br>
                  </p>'''
    )
    string(
        name: 'KUBE_BURNER_VERSION',
        defaultValue: '1.7.6',
        description: 'You can change this to point to an older kube-burner version if needed.'
    )
    string(
        name: 'SVT_REPO', 
        defaultValue:'https://github.com/openshift/svt', 
        description:'''<p>
                  Repository to get regression test scripts and artifacts.<br>
                  You can change this to point to your fork if needed.
                  </p>'''
    )
    string(
        name: 'SVT_REPO_BRANCH', 
        defaultValue:'master', 
        description:'You can change this to point to a branch on your fork if needed.'
    )
    string(
        name: 'SCALE_UP', 
        defaultValue: '0', 
        description: 'If value is set to anything greater than 0, cluster will be scaled up before executing the workload.'
    )
    string(
        name: 'SCALE_DOWN', 
        defaultValue: '0', 
        description:
        '''If value is set to anything greater than 0, cluster will be scaled down after the execution of the workload is complete,<br>
        if the build fails, scale down may not happen, user should review and decide if cluster is ready for scale down or re-run the job on same cluster.'''
    )
    booleanParam(
        name: 'INFRA_WORKLOAD_INSTALL',
        defaultValue: false,
        description: '''
        Install workload and infrastructure nodes even if less than 50 nodes.<br>
        Checking this parameter box is valid only when SCALE_UP is greater than 0.
        '''
    )
    string(
        name:'JENKINS_AGENT_LABEL',
        defaultValue:'oc412',
        description:''
    )
    text(
        name: 'ENV_VARS', 
        defaultValue: '', 
        description:'''<p>
            Enter list of additional (optional) Env vars you'd want to pass to the script, one pair on each line. <br>
            e.g.<br>
            SOMEVAR1='env-test'<br>
            SOMEVAR2='env2-test'<br>
            ...<br>
            SOMEVARn='envn-test'<br>
            </p>'''
    )
    booleanParam(
      name: 'CLEANUP',
      defaultValue: false,
      description: 'Cleanup namespaces (and all sub-objects) created from workload (will run <a href=https://mastern-jenkins-csb-openshift-qe.apps.ocp-c1.prod.psi.redhat.com/job/scale-ci/job/e2e-benchmarking-multibranch-pipeline/job/benchmark-cleaner/>benchmark-cleaner</a>)'
    )
    booleanParam(
      name: 'CERBERUS_CHECK',
      defaultValue: false,
      description: 'Check cluster health status pass (will run <a href=https://mastern-jenkins-csb-openshift-qe.apps.ocp-c1.prod.psi.redhat.com/job/scale-ci/job/e2e-benchmarking-multibranch-pipeline/job/cerberus/>cerberus</a>)'
    )
    booleanParam(
        name: 'MUST_GATHER', 
        defaultValue: true, 
        description: 'This variable will run must-gather if any cerberus components fail'
    )
    booleanParam(
        name: "SEND_SLACK",
        defaultValue: false,
        description: "Check this box to send a Slack notification to #ocp-qe-scale-ci-results upon the job's completion"
    )
  }
  stages {
    stage("Scale Up Cluster") {
        agent { label params['JENKINS_AGENT_LABEL'] }
        when {
            expression { (SCALE_UP.toInteger() > 0  || INFRA_WORKLOAD_INSTALL == true)}
        }
        steps {
            script{

                scale_up_job = build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cluster-workers-scaling/', parameters: [
                    string(name: 'BUILD_NUMBER', value: "${BUILD_NUMBER}"), text(name: "ENV_VARS", value: ENV_VARS),
                    booleanParam(name: 'INFRA_WORKLOAD_INSTALL', value: INFRA_WORKLOAD_INSTALL),
                    string(name: 'WORKER_COUNT', value: SCALE_UP.toString()), string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL)
                ]
                if( scale_up_job != null && scale_up_job.result.toString() != "SUCCESS") {
                    overall_status = "Scale Up Failed"
                    currentBuild.result = "FAILURE"
                }
            }
        }
    }
    stage('Run Regression Test'){
      agent { label params['JENKINS_AGENT_LABEL'] }
      environment{
        EMAIL_ID_FOR_RESULTS_SHEET = "${userId}@redhat.com"
      }
      steps{
        deleteDir()

        checkout([
          $class: 'GitSCM',
          branches: [[name: params.SVT_REPO_BRANCH ]],
          doGenerateSubmoduleConfigurations: false,
          userRemoteConfigs: [[url: params.SVT_REPO ]
          ]])

        copyArtifacts(
          filter: '',
          fingerprintArtifacts: true,
          projectName: 'ocp-common/Flexy-install',
          selector: specific(params.BUILD_NUMBER),
          target: 'flexy-artifacts'
        )

        script{
          buildinfo = readYaml file: "flexy-artifacts/BUILDINFO.yml"
          currentBuild.displayName = "${currentBuild.displayName}-${params.BUILD_NUMBER}"
          currentBuild.description = "Copying Artifact from Flexy-install build <a href=\"${buildinfo.buildUrl}\">Flexy-install#${params.BUILD_NUMBER}</a><br/>"
          buildinfo.params.each { env.setProperty(it.key, it.value) }
        }

        script{
          withCredentials([file(credentialsId: 'sa-google-sheet', variable: 'GSHEET_KEY_LOCATION')]) {
            RETURNSTATUS = sh(returnStatus: true, script: '''
              # Get ENV VARS Supplied by the user to this job and store in .env_override
              echo "$ENV_VARS" > .env_override
              # Export those env vars so they could be used by CI Job
              set -a && source .env_override && set +a
              cp $GSHEET_KEY_LOCATION $WORKSPACE/.gsheet.json
              export GSHEET_KEY_LOCATION=$WORKSPACE/.gsheet.json
              export EMAIL_ID_FOR_RESULTS_SHEET=$EMAIL_ID_FOR_RESULTS_SHEET
             
              mkdir -p ~/.kube
              cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config
              ls -ls ~/.kube/

              python3.9 --version
              python3.9 -m pip install virtualenv
              python3.9 -m virtualenv venv3
              source venv3/bin/activate
              python --version
                python --version
                # If SCRIPT is not specified, find the script by the TEST_CASE.
                if [[ $SCRIPT == "" ]]
                then
                SCRIPT=$(find perfscale_regression_ci -name $TEST_CASE.sh)
                if [[ $SCRIPT == "" ]]
                then
                    echo "$TEST_CASE.sh is not found under svt repo perfscale_regression_ci/scripts folder. Please check."
                    exit 1
                fi
                fi

                export folder=${SCRIPT%/*}
                export script=${SCRIPT##*/}

                # Validate directory existence before changing to it
                if [[ ! -d "${folder}" ]]; then
                echo "Error: Directory ${folder} does not exist in the workspace."
                echo "Workspace contents:"
                ls -R $WORKSPACE
                exit 1
                fi

                # Change to the directory
                cd ${folder}

              chmod +x ${script}
              set -o pipefail
              ./${script} $PARAMETERS |& tee $WORKSPACE/output.out
            ''')
            output = sh(returnStdout: true, script: 'cat $WORKSPACE/output.out')
            println "return num $RETURNSTATUS"
            if ( params.SCRIPT != "" ){
                currentBuild.description = """
                        <b>Ran regression script: </b> ${params.SCRIPT} <br/>
                    """
            } else {
                currentBuild.description += """
                        <b>Ran regression script: </b> ${params.TEST_CASE} <br/>
                    """
            }

            if ( RETURNSTATUS.toInteger() != 0 ) {
              currentBuild.result = "FAILURE"
              overall_status = "Regression test: FAIL"
            }
          }
        }
        script {
          if (params.CERBERUS_CHECK == true) {
              cerberus_job = build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cerberus',
                  parameters: [
                      string(name: 'BUILD_NUMBER', value: BUILD_NUMBER),text(name: "ENV_VARS", value: ENV_VARS),
                      string(name: "CERBERUS_ITERATIONS", value: "1"), string(name: "CERBERUS_WATCH_NAMESPACES", value: "[^.*\$]"),
                      string(name: 'CERBERUS_IGNORE_PODS', value: "[^installer*, ^kube-burner*, ^redhat-operators*, ^certified-operators*]"),
                      string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL),booleanParam(name: "INSPECT_COMPONENTS", value: true),
                      booleanParam(name: "MUST_GATHER", value: MUST_GATHER)
                  ],
                  propagate: false
              if (overall_status == "PASS") {
                  if ( cerberus_job.result.toString() != "SUCCESS") {
                      overall_status = "Cerberus check failed"
                      currentBuild.result = "FAILURE"
                  }
              }
              else {
                  if (cerberus_job.result.toString() != "SUCCESS") {
                      overall_status += "Cerberus check failed"
                      currentBuild.result = "FAILURE"
                  }
              }
          }
          currentBuild.description += """
                <b>Final Status: </b> ${overall_status} <br/>
            """
        }

        script {
            // if the build fails, cleaning and scale down will not happen, letting user review and decide if cluster is ready for scale down or re-run the job on same cluster
            if (params.CLEANUP == true) {
                build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/benchmark-cleaner',
                    parameters: [
                        string(name: 'BUILD_NUMBER', value: BUILD_NUMBER),text(name: "ENV_VARS", value: ENV_VARS),
                        string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL),booleanParam(name: "UNINSTALL_BENCHMARK_OP", value: false),
                        string(name: "CI_TYPE", value: "")
                    ],
                    propagate: false
            }
        }
      }
    }
    stage("Scale down workers") {
        agent { label params['JENKINS_AGENT_LABEL'] }
        when {
            expression { params.SCALE_DOWN.toInteger() > 0 }
        }
          steps {
            script {
                build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cluster-workers-scaling',
                    parameters: [
                        string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), string(name: 'WORKER_COUNT', value: SCALE_DOWN),
                        text(name: "ENV_VARS", value: ENV_VARS), string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL)
                    ]
            }

        }
    }
  }
  post {
        always {
          script {
            println 'Post Section - Always'
            if (params.SEND_SLACK == true ) {
                build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/post-to-slack',
                parameters: [
                    string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), string(name: 'WORKLOAD', value: "regression-test"),
                    text(name: "BUILD_URL", value: env.BUILD_URL), string(name: 'BUILD_ID', value: currentBuild.number.toString()),
                    string(name: 'RESULT', value:currentBuild.currentResult)
                ], propagate: false
            }
          }
        }

    }
}