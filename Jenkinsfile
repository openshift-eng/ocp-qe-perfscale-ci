@Library('flexy') _

// rename build
def userId = currentBuild.rawBuild.getCause(hudson.model.Cause$UserIdCause)?.userId
if (userId) {
  currentBuild.displayName = userId
}

def RETURNSTATUS = "default"
def output = ""
pipeline {
  agent none
  parameters {
    string(
      name: 'BUILD_NUMBER', 
      defaultValue: '', 
      description: 'Build number of job that has installed the cluster.'
    )
    string(
      name: 'PAUSE_TIME', 
      defaultValue: '4', 
      description: 'Number of minutes to pause.'
    )
    string(
      name: 'ITERATIONS', 
      defaultValue: '1', 
      description: 'Number of iterations to run of the chaos scenario.'
    )
    choice(
      choices: ["application-outages","container-scenarios","namespace-scenarios","network-chaos","node-scenarios","pod-scenarios","node-cpu-hog","node-io-hog", "node-memory-hog", "power-outages","pvc-scenario","time-scenarios","zone-outages"], 
      name: 'KRAKEN_SCENARIO', 
      description: '''Type of kraken scenario to run'''
    )
    string(
      name: 'NODE_CPU_PERCENTAGE', 
      defaultValue: "", 
      description: 'int the CPU load by percentage'
    )
    string(
      name: 'TOTAL_CHAOS_DURATION', 
      defaultValue: '', 
      description: 'string stop stress test after N seconds.'
    )
    string(
      name: 'NODE_CPU_CORE', 
      defaultValue: '', 
      description: 'nt the number of CPU cores to be used.'
    )
    string(
      name: 'MEMORY_CONSUMPTION_PERCENTAGE', 
      defaultValue: '', 
      description: 'string N bytes per vm process or percentage of memory used (using the % symbol)'
    )
    string(
      name: 'NUMBER_OF_WORKERS', 
      defaultValue: '', 
      description: 'int Number of VM stressors to be run'
    )
    string(
      name:'JENKINS_AGENT_LABEL',
      defaultValue:'oc420',
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
        See https://github.com/krkn-chaos/krkn-hub/blob/main/docs/cerberus.md for list of variables to pass <br>
        e.g.<br>
        SOMEVAR1='env-test'<br>
        SOMEVAR2='env2-test'<br>
        ...<br>
        SOMEVARn='envn-test'<br>
        </p>'''
    )
    string(
      name: 'KRAKEN_REPO', 
      defaultValue:'https://github.com/krkn-chaos/krkn', 
      description:'You can change this to point to your fork if needed.'
    )
    string(
      name: 'KRAKN_REPO_BRANCH', 
      defaultValue:'main', 
      description:'You can change this to point to a branch on your fork if needed.'
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
    stage('Kraken Run'){
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
            branches: [[name: params.KRAKN_REPO_BRANCH ]],
            doGenerateSubmoduleConfigurations: false,
            extensions: [
                [$class: 'CloneOption', noTags: true, reference: '', shallow: true],
                [$class: 'PruneStaleBranch'],
                [$class: 'CleanCheckout'],
                [$class: 'IgnoreNotifyCommit'],
                [$class: 'RelativeTargetDirectory', relativeTargetDir: 'kraken']
            ],
            userRemoteConfigs: [[url: params.KRAKEN_REPO ]]
        ])
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
        withCredentials([file(credentialsId: 'b73d6ed3-99ff-4e06-b2d8-64eaaf69d1db', variable: 'OCP_AWS'),
                         file(credentialsId: 'eb22dcaa-555c-4ebe-bb39-5b25628cc6bb', variable: 'OCP_GCP'),
                         file(credentialsId: 'ocp-azure', variable: 'OCP_AZURE')]) {
          script {
            println "Will keep the cluster long run for ${params.LONG_RUN_HOURS} hours."
            sleep time: PAUSE_TIME, unit:"MINUTES"

            RETURNSTATUS = sh(returnStatus: true, script: '''

            # Get ENV VARS Supplied by the user to this job and store in .env_override
            echo "$ENV_VARS" > .env_override
            # Export those env vars so they could be used by CI Job
            set -a && source .env_override && set +a
            
            #   if [[ $(echo $VARIABLES_LOCATION | grep azure -c) > 0 ]]; then
            #      # create azure profile
            #      az login --service-principal -u 
            #      az account set --subscription 
                

            #      client_id=$(cat $OCP_AZURE | jq -r '.clientId')
            #      client_secret=$(cat $OCP_AZURE | jq -r '.clientSecret')
            #      tenant_id=$(cat $OCP_AZURE | jq -r '.tenantId')
            #      export AZURE_TENANT_ID=$tenant_id
            #      export AZURE_CLIENT_SECRET=$client_secret
            #      export AZURE_CLIENT_ID=$client_id
            #      export AZURE_SUBSCIPTION_ID=$(cat $OCP_AZURE | jq -r '.subscriptionId')
            # else if [[ $(echo $VARIABLES_LOCATION | grep gcp -c) > 0 ]]; then
            #      # login to service account
            #      gcloud auth activate-service-account
            #      cat $OCP_GCP | jq -r '.client_email'
            #      cat $OCP_GCP | jq -r '.project_id'
            #      gcloud auth list
            #      gcloud config set account
            #      ls
            #      cp -f $OCP_GCP $WORKSPACE/.gcp/credentials

            #      export GOOGLE_APPLICATION_CREDENTIALS=$WORKSPACE/.gcp/credentials
            #  else if [[ $(echo $VARIABLES_LOCATION | grep aws -c) > 0 ]]; then
            #      mkdir -p ~/.aws
            #      cp -f $OCP_AWS ~/.aws/credentials
            #      region=$(cat $WORKSPACE/flexy-artifacts/workdir/install-dir/terraform.aws.auto.tfvars.json | jq -r ".aws_region")

            #      cp ~/.aws/config $WORKSPACE/aws_config
            # fi
            
            mkdir -p ~/.kube
            cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config
            kube_config_loc=$(echo ~/.kube/config)
            oc cluster-info
            export KRKN_KUBE_CONFIG=$kube_config_loc
            ./set_kraken_files.sh

            python3.9 --version
            python3.9 -m pip install virtualenv
            python3.9 -m virtualenv venv3
            source venv3/bin/activate
            python --version
            pip install -r kraken/requirements.txt yq
            ./kraken.sh
            exit $?

            ''')
            sh "echo $RETURNSTATUS"
          }
        }
      script{
            def status = "FAIL"
            sh "echo $RETURNSTATUS"
            if( RETURNSTATUS.toString() == "0") {
                status = "PASS"
            }else {
                currentBuild.result = "FAILURE"
           }
      }
      script {
          if (fileExists("kraken/config.yaml")) {
             archiveArtifacts artifacts: 'kraken/config.yaml', fingerprint: false
          }
          if (fileExists("kraken/logs.out")) {
             archiveArtifacts artifacts: 'kraken/logs.out', fingerprint: false
          }
       }
     }
   }
  }
}
