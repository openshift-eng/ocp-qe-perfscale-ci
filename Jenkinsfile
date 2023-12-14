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

pipeline {
  agent none

  parameters {
        string(
          name: "COMPARISON_CONFIG_PARAM",
          defaultValue: "podLatency.json nodeMasters.json nodeWorkers.json etcd.json crio.json kubelet.json",
          description: '''JSON config files of what data to output into a Google Sheet<br/>
          For kube-burner-ocp workloads use "podLatency.json nodeMasters-ocp.json nodeAggWorkers-ocp.json etcd-ocp.json crio-ocp.json kubelet-ocp.json"<br/>
          For k8s-netperf use "k8s-touchstone.json"<br/>
          For ingress-perf use "ingress.json"'''
        )
        string(
          name: "TOLERANCY_RULES_PARAM",
          defaultValue: "pod-latency-tolerancy-rules.yaml master-tolerancy.yaml worker-tolerancy.yaml etcd-tolerancy.yaml crio-tolerancy.yaml kubelet-tolerancy.yaml",
          description: '''JSON config files of what data to output into a Google Sheet<br/>
          For kube-burner-ocp workloads use: "pod-latency-tolerancy-rules.yaml master-tolerancy-ocp.yaml worker-agg-tolerancy-ocp.yaml etcd-tolerancy-ocp.yaml crio-tolerancy-ocp.yaml kubelet-tolerancy-ocp.yaml"<br/>
          For k8s-netperf use "k8s-tolerancy.yaml"<br/>
          For ingress-perf use "ingress-tolerancy.yaml"'''
        )
        text(name: 'ENV_VARS', defaultValue: '', description:'''<p>
               Enter list of additional (optional) Env Vars you'd want to pass to the script, one pair on each line. <br>
               e.g.<br>
               SOMEVAR1='env-test'<br>
               SOMEVAR2='env2-test'<br>
               ...<br>
               SOMEVARn='envn-test'<br>
               </p>'''
            )
        string(name:'JENKINS_AGENT_LABEL',defaultValue:'oc411',description:
        '''
        scale-ci-static: for static agent that is specific to scale-ci, useful when the jenkins dynamic agen
          isn't stable<br>
        4.y: oc4y || mac-installer || rhel8-installer-4y <br/>
            e.g, for 4.8, use oc48 || mac-installer || rhel8-installer-48 <br/>
        3.11: ansible-2.6 <br/>
        3.9~3.10: ansible-2.4 <br/>
        3.4~3.7: ansible-2.4-extra || ansible-2.3 <br/>
        '''
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
        string(
          name: 'BENCHMARKING_COMPARISON_REPO', 
          defaultValue:'https://github.com/paigerube14/benchmark-comparison.git', 
          description:'You can change this to point to your fork if needed.'
        )
        string(
          name: 'BENCHMARKING_COMPARISON_REPO_BRANCH', 
          defaultValue:'master', 
          description:'You can change this to point to a branch on your fork if needed.'
        )
    }

  stages {

    stage('Run Benchmark Comparison'){
      agent { label params['JENKINS_AGENT_LABEL'] }
      steps{

        deleteDir()
        
        checkout([
          $class: 'GitSCM',
          branches: [[name: GIT_BRANCH ]],
          doGenerateSubmoduleConfigurations: false,
          userRemoteConfigs: [[url: GIT_URL ]
          ]])
        checkout([
            $class: 'GitSCM',
            branches: [[name: "main" ]],
            doGenerateSubmoduleConfigurations: false,
            extensions: [
                [$class: 'CloneOption', noTags: true, reference: '', shallow: true],
                [$class: 'PruneStaleBranch'],
                [$class: 'CleanCheckout'],
                [$class: 'IgnoreNotifyCommit'],
                [$class: 'RelativeTargetDirectory', relativeTargetDir: 'helpful_scripts']
            ],
            userRemoteConfigs: [[url: "https://github.com/openshift-qe/ocp-qe-perfscale-ci.git" ]]
        ])
        checkout([
            $class: 'GitSCM',
            branches: [[name: params.E2E_BENCHMARKING_REPO_BRANCH ]],
            doGenerateSubmoduleConfigurations: false,
            extensions: [
                [$class: 'CloneOption', noTags: true, reference: '', shallow: true],
                [$class: 'PruneStaleBranch'],
                [$class: 'CleanCheckout'],
                [$class: 'IgnoreNotifyCommit'],
                [$class: 'RelativeTargetDirectory', relativeTargetDir: 'e2e-benchmarking']
            ],
            userRemoteConfigs: [[url: params.E2E_BENCHMARKING_REPO ]]
        ])
        checkout([
            $class: 'GitSCM',
            branches: [[name: params.BENCHMARKING_COMPARISON_REPO_BRANCH ]],
            doGenerateSubmoduleConfigurations: false,
            extensions: [
                [$class: 'CloneOption', noTags: true, reference: '', shallow: true],
                [$class: 'PruneStaleBranch'],
                [$class: 'CleanCheckout'],
                [$class: 'IgnoreNotifyCommit'],
                [$class: 'RelativeTargetDirectory', relativeTargetDir: 'comparison']
            ],
            userRemoteConfigs: [[url: params.BENCHMARKING_COMPARISON_REPO ]]
        ])
        
        script{
            withCredentials([usernamePassword(credentialsId: 'elasticsearch-perfscale-ocp-qe', usernameVariable: 'ES_USERNAME', passwordVariable: 'ES_PASSWORD')]) {
                RETURNSTATUS = sh(returnStatus: true, script: '''
                    # Get ENV VARS Supplied by the user to this job and store in .env_override
                    echo "$ENV_VARS" > .env_override
                    # Export those env vars so they could be used by CI Job
                    set -a && source .env_override && set +a

                    export ES_SERVER="https://$ES_USERNAME:$ES_PASSWORD@search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com"

                    // mkdir -p ~/.kube
                    // cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config

                    ls 
                    python3.9 --version
                    python3.9 -m pip install virtualenv
                    python3.9 -m virtualenv venv3
                    pip install -r requirements.txt
                    source venv3/bin/activate
                    python --version
                    env
                    cd e2e-benchmarking/utils/compare/
                    pip install -r requirements.txt
                    python3.9 read_files.py

                ''')

                if (RETURNSTATUS.toInteger() != 0) {
                    currentBuild.result = "FAILURE"
                }
                archiveArtifacts(
                    artifacts: 'e2e-benchmarking/utils/results/*',
                    allowEmptyArchive: true,
                    fingerprint: true
                )
          }
        }
      }

    }
 }
}
