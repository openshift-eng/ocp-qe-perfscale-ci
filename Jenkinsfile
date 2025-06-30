@Library('flexy') _

// rename build
def userId = currentBuild.rawBuild.getCause(hudson.model.Cause$UserIdCause)?.userId
if (userId) {
  currentBuild.displayName = userId
}

def overall_status = "FAIL"
def RETURNSTATUS = "default"

def JENKINS_JOB_NUMBER = currentBuild.number.toString()
println "JENKINS_JOB_NUMBER $JENKINS_JOB_NUMBER"

pipeline {
  agent none

  parameters {
        string(name: 'BUILD_NUMBER', defaultValue: '', description: 'Build number of job that has installed the cluster.')
        string(name:'JENKINS_AGENT_LABEL',defaultValue:'oc420',description:
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
        string(name: 'UPGRADE_VERSION', description: 'This variable sets the version number you want to upgrade your OpenShift cluster to.')
        booleanParam(name: 'ENABLE_FORCE', defaultValue: true, description: 'This variable will force the upgrade or not')
        booleanParam(name: 'SCALE', defaultValue: false, description: 'This variable will scale the cluster up one node at the end up the ugprade')
        booleanParam(name: 'EUS_UPGRADE', defaultValue: false, description: '''This variable will perform an EUS type upgrade <br>
        See "https://docs.google.com/document/d/1396VAUFLmhj8ePt9NfJl0mfHD7pUT7ii30AO7jhDp0g/edit#heading=h.bv3v69eaalsw" for how to run
        ''')
        choice(choices: ['fast', 'eus', 'candidate', 'stable'], name: 'EUS_CHANNEL', description: 'EUS Channel type, will be ignored if EUS_UPGRADE is not set to true')
        string(name: 'MAX_UNAVAILABLE', defaultValue: "1", description: 'This variable will set the max number of unavailable nodes during the upgrade')
        booleanParam(name: 'WRITE_TO_FILE', defaultValue: true, description: 'Value to write to google sheet ')
        booleanParam(
          name: "SEND_SLACK",
          defaultValue: false,
          description: "Check this box to send a Slack notification to #ocp-qe-scale-ci-results upon the job's completion"
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
    }

  stages {
    stage('Run Upgrade'){
      agent { label params['JENKINS_AGENT_LABEL'] }
      steps{
        deleteDir()
        checkout([
          $class: 'GitSCM',
          branches: [[name: GIT_BRANCH ]],
          doGenerateSubmoduleConfigurations: false,
          userRemoteConfigs: [[url: GIT_URL ]
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
            cd upgrade_scripts
            ls
            python3 --version
            python3 -m venv venv3
            source venv3/bin/activate
            pip --version
            pip install --upgrade pip
            pip install -U datetime pyyaml
            ./upgrade.sh $UPGRADE_VERSION -f $ENABLE_FORCE -s $SCALE -u $MAX_UNAVAILABLE -e $EUS_UPGRADE -c $EUS_CHANNEL
          ''' )
           }
           script {
            if( RETURNSTATUS.toString() == "0") {
                overall_status = "PASS"
            } else {
                currentBuild.result = "FAILURE"

                must_gather_url = build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/must-gather',
                parameters: [
                    string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL),
                    text(name: "ENV_VARS", value: ENV_VARS)
                ], propagate: false
                currentBuild.description += """
                <b>Must Gather: </b> <a href="${must_gather_url.absoluteUrl}"> ${must_gather_url.getNumber()} </a> <br/>
                """
            }
           }
           script {
                if(params.WRITE_TO_FILE == true) {
                   build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/write-scale-ci-results', 
                   parameters: [
                   string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), text(name: "ENV_VARS", value: ENV_VARS),
                   string(name: 'CI_STATUS', value: "${overall_status}"),
                   booleanParam(name: 'ENABLE_FORCE', value: ENABLE_FORCE), booleanParam(name: 'SCALE', value: SCALE), 
                   string(name: 'UPGRADE_JOB_URL', value: BUILD_URL), string(name: 'JOB', value: "upgrade"),
                   string(name: "JENKINS_JOB_NUMBER", value: JENKINS_JOB_NUMBER), string(name: "JENKINS_JOB_PATH", value: JOB_NAME)
                  ], propagate: false
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
                  string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), string(name: 'WORKLOAD', value: "upgrade"),
                  text(name: "BUILD_URL", value: env.BUILD_URL), string(name: 'BUILD_ID', value: currentBuild.number.toString()),string(name: 'RESULT', value:currentBuild.currentResult)
              ], propagate: false
            }
        }
    }
  }
}

