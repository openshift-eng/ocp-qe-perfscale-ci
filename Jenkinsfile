@Library('flexy') _

// rename build
def userId = currentBuild.rawBuild.getCause(hudson.model.Cause$UserIdCause)?.userId
if (userId) {
  currentBuild.displayName = userId
}

def CUR_JENKINS_JOB_NUMBER = currentBuild.number.toString()
println "JENKINS_JOB_NUMBER $CUR_JENKINS_JOB_NUMBER"

pipeline {
  agent none

  parameters {
        string(
          name: 'BUILD_NUMBER', 
          defaultValue: '', 
          description: 'Build number of job that has installed the cluster.'
        )
        string(name: 'JOB', defaultValue: '', description: '''Type of job you ran and want to write output for ex <br>
               e.g.<br>
               loaded-upgrade
               upgrade
               cluster-density
               ...
        ''')
        string(
          name: 'JENKINS_JOB_NUMBER', 
          defaultValue: '', 
          description: 'Build number of the scale-ci job that was used to load the cluster.')
        string(
          name: 'JENKINS_JOB_PATH', 
          defaultValue: '', 
          description: 'Build path for the type of job that was used to load the cluster.'
        )
        string(name: 'CI_JOB_URL', defaultValue: '', description: 'Ran job url')
        string(name: 'UPGRADE_JOB_URL', defaultValue: '', description: 'Upgrade job url')
        booleanParam(name: 'ENABLE_FORCE', defaultValue: true, description: 'This variable will force the upgrade or not')
        booleanParam(name: 'SCALE', defaultValue: false, description: 'This variable will scale the cluster up one node at the end up the ugprade')
        string(name: 'LOADED_JOB_URL', defaultValue: '', description: 'Upgrade job url')
        string(name: 'CI_STATUS', defaultValue: 'FAIL', description: 'Scale-ci job ending status')
        string(name: 'JOB_PARAMETERS', defaultValue: '', description:'These are the parameters that were run for the specific scale-ci job')
        string(name: 'RAN_JOBS', defaultValue: '', description:'These are all the tests from the nightly scale-ci regresion runs')
        string(name: 'FAILED_JOBS', defaultValue: '', description:'These are the failed tests from the nightly scale-ci regresion runs')
        string(name: 'PROFILE', defaultValue: '', description:'The profile name that created the cluster')
        string(name: 'PROFILE_SIZE', defaultValue: '', description:'The size of cluster that got created defined in the profile')
        string(name: 'USER', defaultValue: '', description:'The user who ran the job')
        string(name:'JENKINS_AGENT_LABEL',defaultValue:'oc420',description:
        '''
        scale-ci-static: for static agent that is specific to scale-ci, useful when the jenkins dynamic agent isn't stable
        <br>
        4.y: oc4y || mac-installer || rhel8-installer-4y <br/>
            e.g, for 4.20, use oc420 || mac-installer || rhel8-installer-420 <br/>
        3.11: ansible-2.6 <br/>
        3.9~3.10: ansible-2.4 <br/>
        3.4~3.7: ansible-2.4-extra || ansible-2.3 <br/>
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
   }

  stages {
    stage('Run Workload and Mr. Sandman') {
        when {
            expression { (!["nightly-scale","loaded-upgrade","upgrade","nightly-longrun"].contains(params.JOB)) }
        }
        agent { label params['JENKINS_AGENT_LABEL'] }
        steps {
            deleteDir()
            copyArtifacts(
                fingerprintArtifacts: true, 
                projectName: JENKINS_JOB_PATH,
                selector: specific(JENKINS_JOB_NUMBER),
                target: 'workload-artifacts'
            )
            script {
                sh label: '', script: """
                ls $WORKSPACE/workload-artifacts/workloads/*/
                cp $WORKSPACE/workload-artifacts/workloads/*/*.json . 
                ls
                pwd

                """

                workloadInfo = readJSON file: "index_data.json"
                workloadInfo.each { env.setProperty(it.key.toUpperCase(), it.value) }
                // update build description fields

                currentBuild.description = "Write to sheet info: <br/>"
                // UUID of workload that was ran 
                currentBuild.description += "<b>UUID:</b> ${env.UUID}<br/>"

                currentBuild.description += "<b>BENCHMARK:</b> ${env.BENCHMARK}<br/>"
                // STARTTIME_STRING is string rep of start time
                currentBuild.description += "<b>STARTDATE:</b> ${env.STARTDATE}<br/>"
                // ENDTIME_STRING is string rep of end time
                currentBuild.description += "<b>ENDATE:</b> ${env.ENDDATE}<br/>"
                // STARTTIME_TIMESTAMP is unix timestamp of start time
            }
        }
    }
    stage('Run Write to Sheets'){
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

          if (!["nightly-scale","loaded-upgrade","upgrade","nightly-longrun"].contains(params.JOB)) {
            copyArtifacts(
                fingerprintArtifacts: true, 
                projectName: JENKINS_JOB_PATH,
                selector: specific(JENKINS_JOB_NUMBER),
                target: 'workload-artifacts'
            )
          }
        }
        script {
          buildinfo = readYaml file: "flexy-artifacts/BUILDINFO.yml"
          currentBuild.displayName = "${currentBuild.displayName}-${params.BUILD_NUMBER}"
          currentBuild.description += "Flexy-install build <a href=\"${buildinfo.buildUrl}\">Flexy-install#${params.BUILD_NUMBER}</a>"
          buildinfo.params.each { env.setProperty(it.key, it.value) }
        }

        script {
          withCredentials([usernamePassword(credentialsId: 'elasticsearch-perfscale-ocp-qe', usernameVariable: 'ES_USERNAME', passwordVariable: 'ES_PASSWORD'),
            file(credentialsId: 'sa-google-sheet', variable: 'GSHEET_KEY_LOCATION')]) {
              sh label: '', script: """
                # Get ENV VARS Supplied by the user to this job and store in .env_override
                echo "$ENV_VARS" > .env_override
                cp $GSHEET_KEY_LOCATION $WORKSPACE/.gsheet.json
                export GSHEET_KEY_LOCATION=$WORKSPACE/.gsheet.json
                # Export those env vars so they could be used by CI Job
                set -a && source .env_override && set +a
                mkdir -p ~/.kube
                cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config
                env
                
                python3 --version
                python3 -m venv venv3
                source venv3/bin/activate
                pip --version
                pip install --upgrade pip
                pip install -r requirements.txt

                cd write_to_sheet
                printf "${params.ENV_VARS}"  >> env_vars.out
                export ES_SERVER="https://$ES_USERNAME:$ES_PASSWORD@search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com"

                export PYTHONIOENCODING=utf8
                if [[ "${params.JOB}" == "loaded-upgrade" ]]; then
                    python -c "import write_loaded_results; write_loaded_results.write_to_sheet('$GSHEET_KEY_LOCATION', ${params.BUILD_NUMBER}, '${params.CI_JOB_URL}', '${params.UPGRADE_JOB_URL}','${params.LOADED_JOB_URL}', '${params.CI_STATUS}', '${params.SCALE}', 'env_vars.out', '${params.USER}', '${params.PROFILE}','${params.PROFILE_SIZE}')"
                elif [[ "${params.JOB}" == "upgrade" ]]; then
                  python -c "import write_to_sheet; write_to_sheet.write_to_sheet('$GSHEET_KEY_LOCATION', ${params.BUILD_NUMBER}, '${params.UPGRADE_JOB_URL}', '${params.CI_STATUS}', '${params.SCALE}', '${params.ENABLE_FORCE}', 'env_vars.out', '${params.USER}')"
                elif [[ "${params.JOB}" == "nightly-scale" || "${params.JOB}" == "nightly-longrun" ]]; then
                    python -c "import write_nightly_results; write_nightly_results.write_to_sheet('$GSHEET_KEY_LOCATION', ${params.BUILD_NUMBER}, '${params.CI_JOB_URL}', '${params.RAN_JOBS}', '${params.FAILED_JOBS}', '${params.CI_STATUS}', 'env_vars.out', '${params.JOB}', '${params.PROFILE}','${params.PROFILE_SIZE}', '${params.USER}')"
                else
                    echo "else job"
                    python -c "import write_scale_results_sheet; write_scale_results_sheet.write_to_sheet('$GSHEET_KEY_LOCATION', ${params.BUILD_NUMBER},  '${params.JENKINS_JOB_NUMBER}', '${params.JOB}', '${params.CI_JOB_URL}', '${params.CI_STATUS}', '${params.JOB_PARAMETERS}', '$WORKSPACE/workload-artifacts/workloads/*/*.out', 'env_vars.out', '${params.USER}', '$ES_USERNAME', '$ES_PASSWORD')"
                fi
                rm -rf ~/.kube
              """
          }
        }
      }
    }
  }
}
