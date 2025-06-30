@Library('flexy') _

// rename build
def userCause = currentBuild.rawBuild.getCause(Cause.UserIdCause)
def upstreamCause = currentBuild.rawBuild.getCause(Cause.UpstreamCause)

userId = "prubenda"
if (userCause) {
  userId = userCause.getUserId()
} else if (upstreamCause) {
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
def status = "FAIL"

pipeline {
  agent none

  parameters {
    string(
      name: 'BUILD_NUMBER', 
      defaultValue: '', 
      description: 'Build number of job that has installed the cluster.'
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
    choice(
      choices: ['smoke', 'pod2pod', 'hostnet', 'pod2svc'], 
      name: 'WORKLOAD_TYPE', 
      description: 'Workload type'
    )
    booleanParam(
      name: "NETWORK_POLICY", 
      defaultValue: false, 
      description: "If enabled, benchmark-operator will create a network policy to allow ingress trafic in uperf server pods"
    )
    string(
        name: "COMPARISON_CONFIG",
        defaultValue: "uperf-touchstone-stream.json uperf-touchstone-rr.json uperf-touchstone-norm-ltcy.json uperf-touchstone-norm-ops.json",
        description: 'JSON files of what data to output into a google sheet'
    )
    booleanParam(
      name: 'GEN_CSV', 
      defaultValue: true, 
      description: 'Boolean to create a google sheet with comparison data'
    )        
    booleanParam(
      name: 'WRITE_TO_FILE', 
      defaultValue: false, 
      description: 'Value to write to google sheet (will run https://mastern-jenkins-csb-openshift-qe.apps.ocp-c1.prod.psi.redhat.com/job/scale-ci/job/e2e-benchmarking-multibranch-pipeline/job/write-scale-ci-results)'
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
    string(
      name:'JENKINS_AGENT_LABEL',
      defaultValue:'oc420',
      description:
        '''
        scale-ci-static: for static agent that is specific to scale-ci, useful when the jenkins dynamic agen
        isn't stable<br>
        4.y: oc4y || mac-installer || rhel8-installer-4y <br/>
            e.g, for 4.20, use oc420 || mac-installer || rhel8-installer-420 <br/>
        3.11: ansible-2.6 <br/>
        3.9~3.10: ansible-2.4 <br/>
        3.4~3.7: ansible-2.4-extra || ansible-2.3 <br/>
        '''
    )
    text(
      name: 'ENV_VARS', 
      defaultValue: '', 
      description:'''<p>
        Enter list of additional (optional) Env Vars you'd want to pass to the script, one pair on each line. <br>
        e.g.<br>
        SOMEVAR1='env-test'<br>
        SOMEVAR2='env2-test'<br>
        ...<br>
        SOMEVARn='envn-test'<br>
        </p>'''
    )
    string(
      name: 'E2E_BENCHMARKING_REPO', 
      defaultValue:'https://github.com/cloud-bulldozer/e2e-benchmarking', 
      description:'You can change this to point to your fork if needed.'
    )
    string(
      name: 'E2E_BENCHMARKING_REPO_BRANCH', 
      defaultValue:'master', 
      description:'You can change this to point to a branch on your fork if needed.'
    )
  }

  stages {
    stage('Run Network Pod Perf Tests'){
      agent { label params['JENKINS_AGENT_LABEL'] }
      environment{
          EMAIL_ID_FOR_RESULTS_SHEET = "${userId}@redhat.com"
      }
      steps{
        script{
          if(params.SCALE_UP.toInteger() > 0) {
            build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cluster-workers-scaling/', parameters: [string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), text(name: "ENV_VARS", value: ENV_VARS), string(name: 'WORKER_COUNT', value: SCALE_UP), string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL)]
          }
        }
        deleteDir()
        checkout([
          $class: 'GitSCM',
          branches: [[name: params.E2E_BENCHMARKING_REPO_BRANCH ]],
          doGenerateSubmoduleConfigurations: false,
          userRemoteConfigs: [[url: params.E2E_BENCHMARKING_REPO ]
          ]])

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
          withCredentials([usernamePassword(credentialsId: 'elasticsearch-perfscale-ocp-qe', usernameVariable: 'ES_USERNAME', passwordVariable: 'ES_PASSWORD'),
            file(credentialsId: 'sa-google-sheet', variable: 'GSHEET_KEY_LOCATION')]) {
            RETURNSTATUS = sh(returnStatus: true, script: '''
            # Get ENV VARS Supplied by the user to this job and store in .env_override
            echo "$ENV_VARS" > .env_override
            cp $GSHEET_KEY_LOCATION $WORKSPACE/.gsheet.json
            export GSHEET_KEY_LOCATION=$WORKSPACE/.gsheet.json
            export EMAIL_ID_FOR_RESULTS_SHEET=$EMAIL_ID_FOR_RESULTS_SHEET
            export ES_SERVER="https://$ES_USERNAME:$ES_PASSWORD@search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com"
            # Export those env vars so they could be used by CI Job
            set -a && source .env_override && set +a
            mkdir -p ~/.kube
            cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config
            oc config view
            oc projects
            ls -ls ~/.kube/
            env
            cd workloads/network-perf
            
            python3.9 -m pip install virtualenv
            python3.9 -m virtualenv venv3
            source venv3/bin/activate
            python --version

            export WORKLOAD=$WORKLOAD_TYPE
            set -o pipefail
            ./run.sh |& tee "network-perf.out"
            ''')
            output = sh(returnStdout: true, script: 'cat workloads/network-perf/network-perf.out')
            if (RETURNSTATUS.toInteger() == 0) {
                  status = "PASS"
              } else { 
                  currentBuild.result = "FAILURE"
              }
          }
        }

        script{
            if(params.CERBERUS_CHECK == true) {
                cerberus_job = build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cerberus',
                    parameters: [
                        string(name: 'BUILD_NUMBER', value: BUILD_NUMBER),text(name: "ENV_VARS", value: ENV_VARS),
                        string(name: "CERBERUS_ITERATIONS", value: "1"), string(name: "CERBERUS_WATCH_NAMESPACES", value: "[^.*\$]"),
                        string(name: 'CERBERUS_IGNORE_PODS', value: "[^installer*, ^kube-burner*, ^redhat-operators*, ^certified-operators*]"),
                        string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL),booleanParam(name: "INSPECT_COMPONENTS", value: true),
                        booleanParam(name: "MUST_GATHER", value: MUST_GATHER)
                    ],
                    propagate: false
                if( status == "PASS") {
                    if (cerberus_job == null && cerberus_job == "" && cerberus_job.result.toString() != "SUCCESS") {
                        status = "Cerberus check failed"
                    }
                } else {
                    if (cerberus_job == null && cerberus_job == "" && cerberus_job.result.toString() != "SUCCESS") {
                        status += "Cerberus check failed"
                        currentBuild.result = "FAILURE"
                    }
                }
            }
         }
        script{
            def parameter_to_pass = NETWORK_POLICY + "," + WORKLOAD_TYPE
           if(params.WRITE_TO_FILE == true) {
            build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/write-scale-ci-results',
                parameters: [
                    string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), string(name: 'CI_JOB_ID', value: BUILD_ID),
                    string(name: 'CI_JOB_URL', value: BUILD_URL), text(name: "ENV_VARS", value: ENV_VARS),
                    string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL),
                    string(name: "CI_STATUS", value: "${status}"), string(name: "JOB", value: "network-perf"),
                     string(name: "JOB_PARAMETERS", value: "${parameter_to_pass}" ),
                     text(name: "JOB_OUTPUT", value: "${output}")
                ],
                propagate: false
           }
        }
        script{
          // if the build fails, scale down will not happen, letting user review and decide if cluster is ready for scale down or re-run the job on same cluster
          if(params.SCALE_DOWN.toInteger() > 0) {
            build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cluster-workers-scaling', parameters: [string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), string(name: 'WORKER_COUNT', value: SCALE_DOWN), text(name: "ENV_VARS", value: ENV_VARS), string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL)]
          }

        }
      }
    }
  }
  post {
      always {
          script {
              if (params.SEND_SLACK == true ) {
                      build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/post-to-slack',
                      parameters: [
                          string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), string(name: 'WORKLOAD', value: "network-perf"),
                          text(name: "BUILD_URL", value: env.BUILD_URL), string(name: 'BUILD_ID', value: currentBuild.number.toString()),string(name: 'RESULT', value:currentBuild.currentResult)
                      ], propagate: false
              }
          }
      }
  }
}
