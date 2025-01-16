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
          name: "PREVIOUS_VERSION", 
          defaultValue: false,
          description: "If you want to compare the current UUID's data to any <ocp-version>-1  release data"
        )
        string(
          name: "TIME_RANGE", 
          defaultValue: "4 m", 
          description: 'Set of time to look back at to find any comparable results'
        )
        booleanParam(
          name: "INTERNAL_ES", 
          defaultValue: false,
          description: 'Find matching data in the internal instance'
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
        string(name:'JENKINS_AGENT_LABEL',defaultValue:'oc418',description:
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
          defaultValue:'https://github.com/paigerube14/e2e-benchmarking', 
          description:'You can change this to point to your fork if needed.'
        )
        string(
          name: 'E2E_BENCHMARKING_REPO_BRANCH', 
          defaultValue:'new_compare', 
          description:'You can change this to point to a branch on your fork if needed.'
        )
    }

  stages {

    stage('Run Benchmark Comparison'){
      when {
            expression { params.UUID != "" }
        }
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
        
        script{
            env.EMAIL_ID_FOR_RESULTS_SHEET = "${userId}@redhat.com"
            withCredentials([usernamePassword(credentialsId: 'elasticsearch-perfscale-ocp-qe', usernameVariable: 'ES_USERNAME', passwordVariable: 'ES_PASSWORD'),
            file(credentialsId: 'sa-google-sheet', variable: 'GSHEET_KEY_LOCATION')]) {
                RETURNSTATUS = sh(returnStatus: true, script: '''
                    # Get ENV VARS Supplied by the user to this job and store in .env_override
                    echo "$ENV_VARS" > .env_override
                    # Export those env vars so they could be used by CI Job
                    set -a && source .env_override && set +a

                    if [[ $INTERNAL_ES == "true" ]]; then
                      n=${#ES_PASSWORD_INTERNAL}
                      export ES_SERVER="https://$ES_USERNAME_INTERNAL:$ES_PASSWORD_INTERNAL@opensearch.app.intlab.redhat.com"
                      export ES_URL="https://opensearch.app.intlab.redhat.com"
                      export ES_PASSWORD=$ES_PASSWORD_INTERNAL
                      export ES_USERNAME=$ES_USERNAME_INTERNAL
                      n=${#ES_SERVER}
                      echo "internal $n"
                      export es_metadata_index="ospst-perf-scale-ci*"
                      export es_benchmark_index="ospst-ripsaw-kube-burner*"


                    else
                      echo "qe"
                      export es_metadata_index="perf_scale_ci*"
                      export es_benchmark_index="ripsaw-kube-burner*"
                      export ES_SERVER="https://$ES_USERNAME:$ES_PASSWORD@search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com"
                      export ES_URL="https://search-ocp-qe-perf-scale-test-elk-hcm7wtsqpxy7xogbu72bor4uve.us-east-1.es.amazonaws.com"
                    fi 
                    
                    python3.9 --version
                    python3.9 -m pip install virtualenv
                    python3.9 -m virtualenv venv3
                    source venv3/bin/activate
                    python --version

                    pip install -r helpful_scripts/es_scripts/requirements.txt
                    python helpful_scripts/get_graphana_link.py
                    
                    cd e2e-benchmarking/utils/compare
                    pip install -r requirements.txt
                    python3.9 read_files.py

                  ''')
                  sh(returnStatus: true, script: '''
                    # Get ENV VARS Supplied by the user to this job and store in .env_override
                    echo "$ENV_VARS" > .env_override
                    # Export those env vars so they could be used by CI Job
                    set -a && source .env_override && set +a
                    cp $GSHEET_KEY_LOCATION $WORKSPACE/.gsheet.json
                    export GSHEET_KEY_LOCATION=$WORKSPACE/.gsheet.json
                    env
                    export EMAIL_ID_FOR_RESULTS_SHEET=$EMAIL_ID_FOR_RESULTS_SHEET
                    cd e2e-benchmarking/utils/compare
                   
                    folder_name=$(ls -t -d /tmp/*/ | head -1)
                    
                    file_loc=$(ls $folder_name)
                    echo "file loc $file_loc"
                     # see if csv is in file loc
                     if [[ $file_loc == *".csv" ]]; then
                      echo "found csv"

                      cp $folder_name/$file_loc .
                      ls
                      cd ..
                      
                      python3.9 -m pip install virtualenv
                      python3.9 -m virtualenv venv3
                      source venv3/bin/activate
                      python --version
                      source common.sh
                      gen_spreadsheet_helper comparison ${file_loc} prubenda@redhat.com ${GSHEET_KEY_LOCATION}
                    fi
                ''')

                if (RETURNSTATUS.toInteger() != 0) {
                    currentBuild.result = "FAILURE"
                }
                archiveArtifacts(
                        artifacts: 'e2e-benchmarking/utils/compare/comparison.csv',
                        allowEmptyArchive: true,
                        fingerprint: true
                )
          }
        }
      }

    }
 }
}
