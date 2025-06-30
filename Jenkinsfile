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
def RETURNSTATUS = "default"
def output = ""
def cerberus_job = ""
def status = "FAIL"
pipeline {
  agent none
  parameters {
      string(
          name: 'BUILD_NUMBER',
          defaultValue: '',
          description: 'Build number of job that has installed the cluster.'
      )
      choice(
          name: 'WORKLOAD',
          choices: ["mixed-workload","statefulset","deployment"],
          description: 'Type of storage-csi-perf job to run'
      )
      booleanParam(
          name: 'WRITE_TO_FILE',
          defaultValue: false,
          description: 'Value to write to google sheet (will run <a href=https://mastern-jenkins-csb-openshift-qe.apps.ocp-c1.prod.psi.redhat.com/job/scale-ci/job/e2e-benchmarking-multibranch-pipeline/job/write-scale-ci-results>write-scale-ci-results</a>)'
      )
      string(
            name: 'ES_SERVER',
            defaultValue: '',
            description: 'Make sure to include OCP-QE ES server, talk to Mike Fiedler or Paige Rubendall'
        )
      string(
            name: 'ES_INDEX',
            defaultValue: 'perfscale-storage-csi-index',
            description: 'Elasticsearch index name'
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
      string(
          name: 'VARIABLE',
          defaultValue: '400', 
          description: '''
          This variable configures parameter needed for each type of workload. By default 400.<br>
          storage-csi-perf: This will export TOTAL_WORKLOAD env variable; Due to statefulset and deployment exercise different behavior from attach-detach controllers. For mixed-workload, 1 statefulset with 200 replicas and 200 deployments with 2 replica will be created. For statefulset, each POD(replicas) will mount one pvc and pv. For deployment, two pod of each deployment will mount a shared pvc and pv. set to 20 * num_workers, work up to 25 * num_workers. Creates as 600 "nginx" pods with 400 pvc/pv as configured in this environment variable.<br>
          Read <a href=https://github.com/openshift-qe/ocp-qe-perfscale-ci/tree/storage-csi-perf/README.md>here</a> for details about each variable
          '''
      )
      separator(
          name: "NODE_DENSITY_JOB_INFO",
          sectionHeader: "Node Density Job Options",
          sectionHeaderStyle: """
          font-size: 14px;
          font-weight: bold;
          font-family: 'Orienta', sans-serif;
          """
      )
      string(
          name: 'NODE_COUNT',
          defaultValue: '3',
          description: 'Number of nodes to be used in your cluster for this workload. Should be the number of worker nodes on your cluster'
      )
      separator(
          name: "CONCURRENT_BUILDS_JOB_INFO",
          sectionHeader: "Concurrent Builds Job Options",
          sectionHeaderStyle: """
          font-size: 14px;
          font-weight: bold;
          font-family: 'Orienta', sans-serif;
          """
      )
      string(
          name: 'BUILD_LIST',
          defaultValue: "1 8 15 30 45 60 75",
          description: 'Number of concurrent builds to run at a time; will run 2 iterations of each number in this list'
      )
      string(
          name: 'APP_LIST',
          defaultValue: 'cakephp eap django nodejs',
          description: 'Applications to build, will run each of the concurrent builds against each application. Best to run one application at a time'
      )
      string(
          name: "COMPARISON_CONFIG",
          defaultValue: "csi-touchstone.json",
          description: 'JSON config files of what data to output into a Google Sheet'
      )
      booleanParam(
          name: 'GEN_CSV',
          defaultValue: true,
          description: 'Boolean to create a google sheet with comparison data'
      )
      booleanParam(
          name: 'CHURN',
          defaultValue: true,
          description: '''Run churn at end of original iterations. <a href=https://github.com/cloud-bulldozer/e2e-benchmarking/tree/master/workloads/storage-csi-perf#churn>Churning</a> allows you to scale down and then up a percentage of JOB_ITERATIONS after the objects have been created <br>
          Use the following variables in ENV_VARS to set specifics of churn: <br>
          CHURN_DURATION=60m  <br>
          CHURN_PERCENT=20 <br>
          CHURN_DELAY=30s'''
      )
      string(
          name: 'EMAIL_ID_OVERRIDE',
          defaultValue: '',
          description: '''
            Email to share Google Sheet results with<br/>
            By default shares with email of person who ran the job
          '''
      )
      string(
          name: 'JENKINS_AGENT_LABEL',
          defaultValue: 'oc420',
          description: '''
            scale-ci-static: for static agent that is specific to scale-ci, useful when the jenkins dynamic agent isn't stable<br>
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
          description: '''
          Enter list of additional (optional) Env Vars you'd want to pass to the script, one pair on each line.<br>
          e.g.<br>
          SOMEVAR1='env-test'<br>
          SOMEVAR2='env2-test'<br>
          ...<br>
          SOMEVARn='envn-test'<br>
          '''
      )
      booleanParam(
          name: "SEND_SLACK",
          defaultValue: false,
          description: "Check this box to send a Slack notification to #ocp-qe-scale-ci-results upon the job's completion"
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
          name: 'SCALE_UP',
          defaultValue: '0',
          description: 'If value is set to anything greater than 0, cluster will be scaled up before executing the workload.'
      )
      string(
          name: 'SCALE_DOWN',
          defaultValue: '0',
          description: '''
          If value is set to anything greater than 0, cluster will be scaled down after the execution of the workload is complete,<br>
          if the build fails, scale down may not happen, user should review and decide if cluster is ready for scale down or re-run the job on same cluster.
          '''
      )
      string(
          name: 'E2E_BENCHMARKING_REPO',
          defaultValue: 'https://github.com/openshift/svt.git',
          description: 'You can change this to point to your fork if needed.'
      )
      string(
          name: 'E2E_BENCHMARKING_REPO_BRANCH',
          defaultValue: 'master',
          description: 'You can change this to point to a branch on your fork if needed.'
      )
  }
  stages {  
    stage('Scale up cluster') {
      agent { label params['JENKINS_AGENT_LABEL'] }
        when {
            expression { params.SCALE_UP.toInteger() > 0 || params.INFRA_WORKLOAD_INSTALL == true}
        }
        steps {
            script {
                build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cluster-workers-scaling/',
                    parameters: [
                        string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), text(name: "ENV_VARS", value: ENV_VARS),
                        string(name: 'WORKER_COUNT', value: SCALE_UP), string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL),
                        booleanParam(name: 'INFRA_WORKLOAD_INSTALL', value: INFRA_WORKLOAD_INSTALL)
                    ]
            }
      }
    }
    stage('Run Storage-Perf Test'){    
        agent { label params['JENKINS_AGENT_LABEL'] }
        steps {
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
                currentBuild.displayName = "${currentBuild.displayName}-${params.BUILD_NUMBER}-${params.WORKLOAD}"
                currentBuild.description = "Copying Artifact from Flexy-install build <a href=\"${buildinfo.buildUrl}\">Flexy-install#${params.BUILD_NUMBER}</a>"
                buildinfo.params.each { env.setProperty(it.key, it.value) }
            }
            script {
                if (params.EMAIL_ID_OVERRIDE != '') {
                    env.EMAIL_ID_FOR_RESULTS_SHEET = params.EMAIL_ID_OVERRIDE
                }
                else {
                    env.EMAIL_ID_FOR_RESULTS_SHEET = "${userId}@redhat.com"
                }
                withCredentials([usernamePassword(credentialsId: 'elasticsearch-perfscale-ocp-qe', usernameVariable: 'ES_USERNAME', passwordVariable: 'ES_PASSWORD'),
                    file(credentialsId: 'sa-google-sheet', variable: 'GSHEET_KEY_LOCATION')]) {
                    RETURNSTATUS = sh(returnStatus: true, script: '''
                        # Get ENV VARS Supplied by the user to this job and store in .env_override
                        echo "$ENV_VARS" > .env_override
                        # Export those env vars so they could be used by CI Job
                        set -a && source .env_override && set +a
                        cp $GSHEET_KEY_LOCATION $WORKSPACE/.gsheet.json
                        export GSHEET_KEY_LOCATION=$WORKSPACE/.gsheet.json
                        export EMAIL_ID_FOR_RESULTS_SHEET=$EMAIL_ID_FOR_RESULTS_SHEET
                        export ES_SERVER="https://$ES_USERNAME:$ES_PASSWORD@search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com"
                        mkdir -p ~/.kube
                        cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config
                        ls -ls ~/.kube/
                        cd storage-csi-perf
                        python3.9 --version
                        python3.9 -m pip install virtualenv 
                        python3.9 -m virtualenv venv3
                        source venv3/bin/activate
                        python3.9 -m pip install pytimeparse futures
			            pip3 install elasticsearch==6.8.2
                        pip3 install "numpy<2"
                        pip3 install requests
                        pip3 install urllib3==2.0.2
                        python --version
                        pip3 list
                        export WORKLOAD=${WORKLOAD}
                        export TOTAL_WORKLOAD=${VARIABLE}
                        export WORKLOAD_CHECKING_TIMEOUT=${WORKLOAD_CHECKING_TIMEOUT}

                        set -o pipefail
                        pwd
                        echo "workspace $WORKSPACE"
                        ./run.sh |& tee "storage-csi-perf.out"
                    ''')
                    output = sh(returnStdout: true, script: 'cat storage-csi-perf/storage-csi-perf.out')
                    archiveArtifacts(
                        artifacts: 'workloads/storage-csi-perf/storage-csi-perf.out',
                        allowEmptyArchive: true,
                        fingerprint: true
                    )
                    if (RETURNSTATUS.toInteger() == 0) {
                        status = "PASS"
                    }
                    else { 
                        currentBuild.result = "FAILURE"
                    }
                }
            }
        }
    }
    stage("Check cluster health") {
        agent { label params['JENKINS_AGENT_LABEL'] }
        when {
            expression { params.CERBERUS_CHECK == true }
        }
        steps {
            script {
                cerberus_job = build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cerberus',
                    parameters: [
                        string(name: 'BUILD_NUMBER', value: BUILD_NUMBER),text(name: "ENV_VARS", value: ENV_VARS),
                        string(name: "CERBERUS_ITERATIONS", value: "1"), string(name: "CERBERUS_WATCH_NAMESPACES", value: "[^.*\$]"),
                        string(name: 'CERBERUS_IGNORE_PODS', value: "[^installer*, ^storage-csi-perf*, ^redhat-operators*, ^certified-operators*]"),
                        string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL),booleanParam(name: "INSPECT_COMPONENTS", value: true),
                        string(name: "WORKLOAD", value: WORKLOAD),booleanParam(name: "MUST_GATHER", value: MUST_GATHER)
                    ],
                    propagate: false
                if (status == "PASS") {
                    if (cerberus_job.result.toString() != "SUCCESS") {
                        status = "Cerberus check failed"
                        currentBuild.result = "FAILURE"
                    }
                }
                else {
                    if (cerberus_job.result.toString() != "SUCCESS") {
                        status += "Cerberus check failed"
                        currentBuild.result = "FAILURE"
                    }
                }
            }
        }
    }
    stage("Write out results") {
      agent { label params['JENKINS_AGENT_LABEL'] }
      when {
          expression { params.WRITE_TO_FILE == true }
      }
        steps {
          script {
              if (status != "PASS") {
                  currentBuild.result = "FAILURE"
              }
              def parameter_to_pass = VARIABLE
              build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/write-scale-ci-results',
                  parameters: [
                      string(name: 'BUILD_NUMBER', value: BUILD_NUMBER),text(name: "ENV_VARS", value: ENV_VARS),
                      string(name: 'CI_JOB_ID', value: BUILD_ID), string(name: 'CI_JOB_URL', value: BUILD_URL),
                      string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL), string(name: "CI_STATUS", value: "${status}"),
                      string(name: "JOB", value: WORKLOAD), string(name: "JOB_PARAMETERS", value: "${parameter_to_pass}" ),
                      text(name: "JOB_OUTPUT", value: "${output}")
                  ],
                  propagate: false
            }
        }
    }
    stage("Cleanup cluster of objects created in workload") {
      agent { label params['JENKINS_AGENT_LABEL'] }
      when {
          expression { params.CLEANUP == true}
      }
        steps {
          script {
              // if the build fails, cleaning and scale down will not happen, letting user review and decide if cluster is ready for scale down or re-run the job on same cluster
              build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/benchmark-cleaner',
                  parameters: [
                      string(name: 'BUILD_NUMBER', value: BUILD_NUMBER),text(name: "ENV_VARS", value: ENV_VARS),
                      string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL),
                      string(name: "CI_TYPE", value: WORKLOAD)
                  ],
                  propagate: false
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
                if (params.SEND_SLACK == true ) {
                        build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/post-to-slack',
                        parameters: [
                            string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), string(name: 'WORKLOAD', value: WORKLOAD),
                            text(name: "BUILD_URL", value: env.BUILD_URL), string(name: 'BUILD_ID', value: currentBuild.number.toString()),string(name: 'RESULT', value:currentBuild.currentResult)
                        ], propagate: false
                }
            }
        }
    }
}
