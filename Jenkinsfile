@Library('flexy') _

// rename build
def userId = currentBuild.rawBuild.getCause(hudson.model.Cause$UserIdCause)?.userId
if (userId) {
  currentBuild.displayName = userId
}

def RETURNSTATUS = "default"
def output = ""
def status = "FAIL"
pipeline {
    agent { label params['JENKINS_AGENT_LABEL'] }
    parameters {
        string(
            name: 'BUILD_NUMBER', 
            defaultValue: '', 
            description: 'Build number of job that has installed the cluster.'
        )
        string(
            name: 'CERBERUS_ITERATIONS', 
            defaultValue: '', 
            description: 'Number of iterations to run of cerberus.'
        )
        booleanParam(
            name: 'CERBERUS_DAEMON_MODE', 
            defaultValue: false, 
            description: 'This variable will set cerberus to run forever (only way to stop is abort job)'
        )
        booleanParam(
            name: 'INSPECT_COMPONENTS', 
            defaultValue: false, 
            description: 'This variable will set cerberus to inspect failing components'
        )
        string(
            name: "CERBERUS_WATCH_NAMESPACES", 
            defaultValue: "[openshift-etcd, openshift-apiserver, openshift-kube-apiserver, openshift-monitoring, openshift-kube-controller-manager, openshift-machine-api, openshift-kube-scheduler, openshift-ingress, openshift-sdn]",
            description: "Which specific namespaces you want to watch any failing components, use [^.*\$] if you want to watch all namespaces"
        )
        string(
            name: "WORKLOAD",
            defaultValue: "", 
            description: "Specify the workload if you created more than 5000 pods in a namespace, will ignore the namespaces in cerberus check"
        )
        string(
            name: "CERBERUS_IGNORE_PODS",
            defaultValue: "[^installer*]", 
            description: "Which specific pod names regex patterns you want to ignore in the namespaces you defined above"
        )
        booleanParam(
            name: 'MUST_GATHER', 
            defaultValue: true, 
            description: 'This variable will set cerberus to inspect failing components'
        )
        string(
          name: 'IMAGE_STREAM', 
          defaultValue: 'openshift/must-gather', 
          description: 'Base image stream of data to gather for the must-gather.'
        )
        string(
          name: 'IMAGE', 
          defaultValue: '', 
          description: 'Optional image to help get must-gather information on non defualt areas. See <a href="https://docs.openshift.com/container-platform/4.12/support/gathering-cluster-data.html">docs</a> for more information and options.'
        )
        string(
            name: 'JENKINS_AGENT_LABEL',
            defaultValue: 'oc420',
            description:
            '''
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
            description:'''<p>
              Enter list of additional (optional) Env Vars you'd want to pass to the script, one pair on each line. <br>
              See https://github.com/cloud-bulldozer/kraken-hub/blob/main/docs/cerberus.md for list of variables to pass <br>
              e.g.<br>
              SOMEVAR1='env-test'<br>
              SOMEVAR2='env2-test'<br>
              ...<br>
              SOMEVARn='envn-test'<br>
              </p>
            '''
        )
        string(
            name: 'CERBERUS_REPO',
            defaultValue: 'https://github.com/krkn-chaos/cerberus',
            description: 'You can change this to point to your fork if needed.'
        )
        string(
            name: 'CERBERUS_REPO_BRANCH',
            defaultValue: 'main', 
            description: 'You can change this to point to a branch on your fork if needed.'
        )
        string(
          name: 'KRAKEN_HUB_REPO',
          defaultValue:'https://github.com/krkn-chaos/krkn-hub',
          description:'You can change this to point to your fork if needed.'
        )
        string(
          name: 'KRAKN_HUB_REPO_BRANCH', 
          defaultValue:'main', 
          description:'You can change this to point to a branch on your fork if needed.'
        )
     }

  stages {
    stage('Cerberus Run'){
      agent { label params['JENKINS_AGENT_LABEL'] }
      steps{
        deleteDir()
        checkout([
          $class: 'GitSCM',
          branches: [[name: params.CERBERUS_REPO_BRANCH ]],
          doGenerateSubmoduleConfigurations: false,
          userRemoteConfigs: [[url: params.CERBERUS_REPO ]
         ]])
        checkout([
            $class: 'GitSCM',
            branches: [[name: params.KRAKN_HUB_REPO_BRANCH ]],
            doGenerateSubmoduleConfigurations: false,
            extensions: [
                [$class: 'CloneOption', noTags: true, reference: '', shallow: true],
                [$class: 'PruneStaleBranch'],
                [$class: 'CleanCheckout'],
                [$class: 'IgnoreNotifyCommit'],
                [$class: 'RelativeTargetDirectory', relativeTargetDir: 'kraken-hub']
            ],
            userRemoteConfigs: [[url: params.KRAKEN_HUB_REPO ]]
        ])
        checkout([
            $class: 'GitSCM',
            branches: [[name: GIT_BRANCH ]],
            doGenerateSubmoduleConfigurations: false,
            extensions: [
                [$class: 'CloneOption', noTags: true, reference: '', shallow: true],
                [$class: 'PruneStaleBranch'],
                [$class: 'CleanCheckout'],
                [$class: 'IgnoreNotifyCommit'],
                [$class: 'RelativeTargetDirectory', relativeTargetDir: 'cerberus_jenkins']
            ],
            userRemoteConfigs: [[url: GIT_URL ]]
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
          RETURNSTATUS = sh(returnStatus: true, script: '''
          ls
          cd kraken-hub/cerberus
          source env.sh
          # Get ENV VARS Supplied by the user to this job and store in .env_override
          echo "$ENV_VARS" > .env_override
          # Export those env vars so they could be used by CI Job
          set -a && source .env_override && set +a
          cd ../..
          mkdir -p ~/.kube
          cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config
          export CERBERUS_KUBECONFIG=~/.kube/config
        
          export CERBERUS_CORES=.05
          export CERBERUS_TIMEOUT=10
          cd cerberus_jenkins
          python3.9 --version
          python3.9 -m venv venv3
          source venv3/bin/activate
          if [[ $CERBERUS_WATCH_NAMESPACES == '[^.*$]' ]]; then
            if [[ $WORKLOAD != "" ]]; then
              export CERBERUS_WATCH_NAMESPACES=$(python set_namespace_list.py -w $WORKLOAD)
            fi
          fi
          cd ..
          env
          cp kraken-hub/cerberus/cerberus.yaml.template cerberus.yaml.template
          envsubst <cerberus.yaml.template > cerberus.yaml
          
          pip --version
          pip install --upgrade pip
          pip install -U -r requirements.txt
          export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES
          python start_cerberus.py --config cerberus.yaml
          replaced_json=$(less -XF final_cerberus_info.json | sed "s/True/0/g" | sed "s/False/1/g" )
          value=${replaced_json#*:*:}   # remove prefix ending at second ":"
          final_health=${value%,*}  # remove suffix starting with ","
          echo "health $final_health"
          cd cerberus_jenkins
          
          python -c "import check_kube_burner_ns; check_kube_burner_ns.check_namespaces( '$WORKLOAD' )"
          cd ..
          ls
          exit $final_health
          ''')
            
            sh "echo $RETURNSTATUS"
            if( RETURNSTATUS.toString() == "0") {
                status = "PASS"
            }else {
                currentBuild.result = "FAILURE"
           }
      }
      }
    }
  }
  post {
      always {
          script {
            if (status != "PASS" ) { 
              if (fileExists("inspect_data")) {
                archiveArtifacts artifacts: 'inspect_data/*,inspect_data/**', fingerprint: false
              }
              if (params.MUST_GATHER == true) {
                build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/must-gather',
                parameters: [
                    string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL),
                    text(name: "ENV_VARS", value: ENV_VARS), string(name: 'IMAGE', value: IMAGE),
                    string(name: 'IMAGE_STREAM', value: IMAGE_STREAM)
                ], propagate: false
              }
            }
            if (fileExists("cerberus_jenkins/failed_pods/*")) {
              archiveArtifacts artifacts: 'cerberus_jenkins/failed_pods/*,cerberus_jenkins/failed_pods/**', fingerprint: false
            }
            if (fileExists("cerberus_jenkins/cerberus.report")) {
              archiveArtifacts artifacts: 'cerberus_jenkins/cerberus.report', fingerprint: false
            }
        }

     }
   }
}
