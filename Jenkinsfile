@Library('flexy') _

// rename build
def userId = currentBuild.rawBuild.getCause(hudson.model.Cause$UserIdCause)?.userId
if (userId) {
  currentBuild.displayName = userId
}

def RETURNSTATUS = "default"

pipeline {
  agent none

  parameters {
        string(
          name: 'BUILD_NUMBER', 
          defaultValue: '', 
          description: 'Build number of job that has installed the cluster.'
        )
        choice(
          choices: ["cluster-density","node-density","node-density-heavy","pod-density","pod-density-heavy","max-namespaces","max-services", "concurrent-builds","network-perf","router-perf","etcd-perf"],
          name: 'WORKLOAD', 
          description: '''Type of kube-burner job to run'''
        )
        string(
          name: "UUID", 
          defaultValue: "", 
          description: 'UUID of current run to do comparison on'
        )
        string(
          name: "BASELINE_UUID", 
          defaultValue: "", 
          description: 'Set a baseline uuid to use for comparison, if blank will find baseline uuid for profile, workload and worker node count to then compare'
        )
        booleanParam(
            name: 'COMPARE_PREVIOUS', 
            defaultValue: false, 
            description: "Compare value with previous version"
        )
        string(
          name: "COMPARE_WITH_PROFILE",
          defaultValue: "",
          description: 'Specify a profile you want to compare your job results to'
        )
        string(
          name: "COMPARISON_CONFIG_PARAM",
          defaultValue: "podLatency.json nodeMasters-max.json nodeWorkers.json etcd.json crio.json kubelet.json",
          description: 'JSON config files of what data to output into a Google Sheet'
        )
        string(
          name: "TOLERANCY_RULES_PARAM",
          defaultValue: "pod-latency-tolerancy-rules.yaml master-tolerancy.yaml worker-tolerancy.yaml etcd-tolerancy.yaml crio-tolerancy1.yaml kubelet-tolerancy.yaml",
          description: 'JSON config files of what data to output into a Google Sheet'
        )
        booleanParam(
            name: 'GEN_CSV',
            defaultValue: true,
            description: 'Boolean to create a google sheet with comparison data'
        )
        string(
          name: 'EMAIL_ID_OVERRIDE',
          defaultValue: '',
          description: '''
            Email to share Google Sheet results with<br/>
            By default shares with email of person who ran the job
          '''
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
        string(
          name: "CI_PROFILES_URL",
          defaultValue: "https://gitlab.cee.redhat.com/aosqe/ci-profiles.git/",
          description:"Owner of ci-profiles repo to checkout, will look at folder 'scale-ci/\${major_v}.\${minor_v}'"
        )
        string(
          name: "CI_PROFILES_REPO_BRANCH", 
          defaultValue: "master", 
          description: "Branch of ci-profiles repo to checkout"
        )
    }

  stages {

    stage('Run Benchmark Comparison'){
      agent { label params['JENKINS_AGENT_LABEL'] }
      environment{
          EMAIL_ID_FOR_RESULTS_SHEET = "${userId}@redhat.com"
      }
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
            branches: [[name: params.E2E_BENCHMARKING_REPO_BRANCH ]],
            doGenerateSubmoduleConfigurations: false,
            extensions: [
                [$class: 'CloneOption', noTags: true, reference: '', shallow: true],
                [$class: 'PruneStaleBranch'],
                [$class: 'CleanCheckout'],
                [$class: 'IgnoreNotifyCommit'],
                [$class: 'RelativeTargetDirectory', relativeTargetDir: 'e2e-benchmark']
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
        // checkout CI profile repo from GitLab
        checkout changelog: false,
            poll: false,
            scm: [
                $class: 'GitSCM',
                branches: [[name: "${params.CI_PROFILES_REPO_BRANCH}"]],
                doGenerateSubmoduleConfigurations: false,
                extensions: [
                    [$class: 'CloneOption', noTags: true, reference: '', shallow: true],
                    [$class: 'PruneStaleBranch'],
                    [$class: 'CleanCheckout'],
                    [$class: 'IgnoreNotifyCommit'],
                    [$class: 'RelativeTargetDirectory', relativeTargetDir: 'ci-profiles']
                ],
                submoduleCfg: [],
                userRemoteConfigs: [[
                    name: 'origin',
                    refspec: "+refs/heads/${params.CI_PROFILES_REPO_BRANCH}:refs/remotes/origin/${params.CI_PROFILES_REPO_BRANCH}",
                    url: "${params.CI_PROFILES_URL}"
                ]]
            ]
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

        script{
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

                    export ES_SERVER_BASELINE="https://$ES_USERNAME:$ES_PASSWORD@search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com"
  
                    mkdir -p ~/.kube
                    cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config


                    python3.9 --version
                    python3.9 -m pip install virtualenv
                    python3.9 -m virtualenv venv3

                    source venv3/bin/activate
                    python --version
                    pip install -r requirements.txt
                    pip install -qq git+https://github.com/cloud-bulldozer/benchmark-comparison.git

                    if [[ -z "$BASELINE_UUID" ]]; then
                      export BASELINE_UUID=$(python find_baseline_uuid.py --workload $WORKLOAD)
                    fi

                    ./loop_rules.sh

                ''')

                if (RETURNSTATUS.toInteger() != 0) {
                    currentBuild.result = "FAILURE"
                }
                archiveArtifacts(
                    artifacts: 'e2e-benchmark/utils/results/*',
                    allowEmptyArchive: true,
                    fingerprint: true
                )
          }
        }
      }

    }
 }
}
