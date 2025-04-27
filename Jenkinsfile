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
def cerberus_job = ""
def status = "FAIL"

def JENKINS_JOB_NUMBER = currentBuild.number.toString()
println "JENKINS_JOB_NUMBER $JENKINS_JOB_NUMBER"
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
          choices: ["node-density-cni-networkpolicy","concurrent-builds","pods-service-route","networkpolicy-case1","networkpolicy-case2","networkpolicy-case3"],
          description: 'Type of kube-burner job to run'
      )
      booleanParam(
          name: 'WRITE_TO_FILE',
          defaultValue: false,
          description: 'Value to write to google sheet (will run <a href=https://mastern-jenkins-csb-openshift-qe.apps.ocp-c1.prod.psi.redhat.com/job/scale-ci/job/e2e-benchmarking-multibranch-pipeline/job/write-scale-ci-results>write-scale-ci-results</a>)'
      )
      booleanParam(
          name: 'WRITE_TO_ES',
          defaultValue: false,
          description: 'Value to write to elastic seach under metricName: jenkinsEnv'
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
          name: 'IMAGE_STREAM', 
          defaultValue: 'openshift/must-gather', 
          description: 'Base image stream of data to gather for the must-gather.'
        )
        string(
          name: 'IMAGE', 
          defaultValue: '', 
          description: 'Optional image to help get must-gather information on non default areas. See <a href="https://docs.openshift.com/container-platform/4.12/support/gathering-cluster-data.html">docs</a> for more information and options.'
        )
        string(
            name: "KUBE_BURNER_URL",
            defaultValue: "https://github.com/cloud-bulldozer/kube-burner/releases/download/v0.17.3/kube-burner-0.17.3-Linux-x86_64.tar.gz",
            description: "Url of the kube-burner tar file to use to load the cluster"
        )
        string(
          name: 'VARIABLE',
          defaultValue: '1000', 
          description: '''
          This variable configures parameter needed for each type of workload. By default 1000.<br>
          pod-density: This will export PODS env variable; set to 200 * num_workers, work up to 250 * num_workers. Creates as many "sleep" pods as configured in this environment variable.<br>
          pod-density-heavy: This will export PODS_PER_NODE env variable; set to 200, work up to 250. Creates as many hello-openshift application as configured in this variable*NODE_COUNT - existing number of pods on node - 1.<br>
          cluster-density: This will export JOB_ITERATIONS env variable; set to 9 * num_workers. This variable sets the number of iterations to perform (1 namespace per iteration).<br>
          cluster-density-ms: This will export JOB_ITERATIONS env variable; set to 9 * num_workers. This variable sets the number of iterations to perform (1 namespace per iteration).<br>
          max-namespaces: This will export NAMESPACE_COUNT env variable; set to ~30 * num_workers. The number of namespaces created by Kube-burner.<br>
          pods-service-route: This will export NAMESPACE_COUNT env variable; set to ~30 * num_workers. The number of namespaces created by Kube-burner.<br>
          max-services: This will export SERVICE_COUNT env variable; set to 200 * num_workers, work up to 250 * num_workers. Creates n-replicas of an application deployment (hello-openshift) and a service in a single namespace.<br>
          node-density: This will export PODS_PER_NODE env variable; set to 200, work up to 250. Creates as many "sleep" pods as configured in this variable*NODE_COUNT - existing number of pods on node - 1.<br>
          node-density-heavy: This will export PODS_PER_NODE env variable; set to 200, work up to 250. Creates this number of applications proportional to the calculated number of pods / 2<br>
          node-density-cni: This will export PODS_PER_NODE env variable; set to 200, work up to 250. Creates this number of applications proportional to the calculated number of pods / 2<br>
          node-density-cni-networkpolicy: This will export PODS_PER_NODE env variable; set to 200, work up to 250. Creates this number of applications proportional to the calculated number of pods / 2<br>
          networkpolicy-case1: This will export JOB_ITERATIONS env variable; set to 5 * num_workers. This variable sets the number of iterations to perform (1 namespace per iteration)<br>
          networkpolicy-case2: This will export JOB_ITERATIONS env variable; set to 1 * num_workers. This variable sets the number of iterations to perform (1 namespace per iteration)<br>
          networkpolicy-case3: This will export JOB_ITERATIONS env variable; set to 4 * num_workers. This variable sets the number of iterations to perform (1 namespace per iteration)<br>
          Read <a href=https://github.com/openshift-qe/ocp-qe-perfscale-ci/tree/kube-burner/README.md>here</a> for details about each variable
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
          defaultValue: "clusterVersion.json podLatency.json containerMetrics.json kubelet.json etcd.json crio.json nodeMasters-max.json nodeWorkers.json",
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
          description: '''Run churn at end of original iterations. <a href=https://github.com/cloud-bulldozer/e2e-benchmarking/tree/master/workloads/kube-burner#churn>Churning</a> allows you to scale down and then up a percentage of JOB_ITERATIONS after the objects have been created <br>
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
          defaultValue: 'oc412',
          description: '''
            scale-ci-static: for static agent that is specific to scale-ci, useful when the jenkins dynamic agent isn't stable<br>
            4.y: oc4y || mac-installer || rhel8-installer-4y <br/>
                e.g, for 4.8, use oc48 || mac-installer || rhel8-installer-48 <br/>
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
          defaultValue: 'https://github.com/cloud-bulldozer/e2e-benchmarking',
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
    stage('Run Kube-Burner Test'){    
        agent {
          kubernetes {
            cloud 'openshift qe jenkins agents'
            yaml """\
              apiVersion: v1
              kind: Pod
              metadata:
                labels:
                  label: ${JENKINS_AGENT_LABEL}
              spec:
                containers:
                - name: "jnlp"
                  image: "images.paas.redhat.com/aos-qe-ci/jenkins-agent-rhel8-cucushift-${JENKINS_AGENT_LABEL}:latest"
                  resources:
                    requests:
                      memory: "8Gi"
                      cpu: "2"
                    limits:
                      memory: "8Gi"
                      cpu: "2"
                  imagePullPolicy: Always
                  workingDir: "/home/jenkins/ws"
                  tty: true
              """.stripIndent()
          }
        }
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
                        cd workloads/kube-burner
                        python3.9 --version
                        python3.9 -m pip install virtualenv
                        python3.9 -m virtualenv venv3
                        source venv3/bin/activate
                        python --version
                        pip install pytimeparse futures
                        if [[ $WORKLOAD == *"cluster-density"* ]] || [[ $WORKLOAD == *"networkpolicy-case"* ]]; then
                            export JOB_ITERATIONS=$VARIABLE
                        elif [[ $WORKLOAD == "pod-density" ]]; then
                            export PODS=$VARIABLE
                        elif [[ $WORKLOAD == "max-namespaces" ]] || [[ $WORKLOAD == "pods-service-route" ]]; then
                            export NAMESPACE_COUNT=$VARIABLE
                        elif [[ $WORKLOAD == "max-services" ]]; then
                            export SERVICE_COUNT=$VARIABLE
                        elif [[ $WORKLOAD == *"node-density"* ]] || [[ $WORKLOAD == "pod-density-heavy" ]]; then
                            export PODS_PER_NODE=$VARIABLE
                        fi

                        if [[ $WORKLOAD == "max-services" ]] || [[ $WORKLOAD == "max-namespaces" ]] || [[ $WORKLOAD == "cluster-density" ]] || [[ $WORKLOAD == "concurrent-builds" ]]; then 
                            export COMPARISON_CONFIG=$(echo ${COMPARISON_CONFIG/nodeWorkers/nodeAggWorkers})
                            ## kubelet and crio metrics aren't in aggregated metrics files
                            export COMPARISON_CONFIG=$(echo ${COMPARISON_CONFIG/kubelet.json/})
                            export COMPARISON_CONFIG=$(echo ${COMPARISON_CONFIG/crio.json/})
                            export COMPARISON_CONFIG=$(echo ${COMPARISON_CONFIG/containerMetrics.json/})
                            
                        fi

                        set -o pipefail
                        pwd
                        echo "workspace $WORKSPACE"
                        ./run.sh |& tee "kube-burner.out"
                        ls /tmp
                        folder_name=$(ls -t -d /tmp/*/ | head -1)
                        file_loc=$folder_name"*"
                        cp $file_loc .
                        ls
                    ''')
                    archiveArtifacts(
                        artifacts: 'workloads/kube-burner/kube-burner.out',
                        allowEmptyArchive: true,
                        fingerprint: true
                    )

                    archiveArtifacts(
                        artifacts: 'workloads/kube-burner/index_data.json',
                        allowEmptyArchive: true,
                        fingerprint: true
                    )
                    workloadInfo = readJSON file: "workloads/kube-burner/index_data.json"
                    workloadInfo.each { env.setProperty(it.key.toUpperCase(), it.value) }
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
                        string(name: 'CERBERUS_IGNORE_PODS', value: "[^installer*, ^kube-burner*, ^redhat-operators*, ^certified-operators*]"),
                        string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL),booleanParam(name: "INSPECT_COMPONENTS", value: true),
                        string(name: "WORKLOAD", value: WORKLOAD),booleanParam(name: "MUST_GATHER", value: MUST_GATHER),
                        string(name: 'IMAGE', value: IMAGE),string(name: 'IMAGE_STREAM', value: IMAGE_STREAM)
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
              if (params.WORKLOAD == "node-density" || params.WORKLOAD == "node-density-heavy") {
                  parameter_to_pass += "," + NODE_COUNT
              }
              else if (params.WORKLOAD == "concurrent-builds") {
                  parameter_to_pass = APP_LIST + "," + BUILD_LIST
              }
              build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/write-scale-ci-results',
                  parameters: [
                      string(name: 'BUILD_NUMBER', value: BUILD_NUMBER),text(name: "ENV_VARS", value: ENV_VARS),
                      string(name: 'CI_JOB_URL', value: BUILD_URL),
                      string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL), string(name: "CI_STATUS", value: "${status}"),
                      string(name: "JOB", value: WORKLOAD), string(name: "JOB_PARAMETERS", value: "${parameter_to_pass}" ),
                      string(name: "JENKINS_JOB_NUMBER", value: JENKINS_JOB_NUMBER), 
                      string(name: "JENKINS_JOB_PATH", value: JOB_NAME)
                  ],
                  propagate: false
            }
        }
    }
    stage("Write es results") {
      agent { label params['JENKINS_AGENT_LABEL'] }
      when {
          expression { params.WRITE_TO_ES == true }
      }
        steps {
          script {
                build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/post-results-to-es',
                  parameters: [
                      string(name: 'BUILD_NUMBER', value: BUILD_NUMBER),text(name: "ENV_VARS", value: ENV_VARS),
                      string(name: "JENKINS_JOB_NUMBER", value: JENKINS_JOB_NUMBER), string(name: "JENKINS_JOB_PATH", value: JOB_NAME),
                      string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL), string(name: "CI_STATUS", value: "${status}"),
                      string(name: "WORKLOAD", value: WORKLOAD)
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

