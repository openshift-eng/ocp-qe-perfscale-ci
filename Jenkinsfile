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
        string(name: 'BUILD_NUMBER', defaultValue: '', description: 'Build number of job that has installed the cluster.')
        string(name: "DAST_IMAGE", defaultValue: "quay.io/redhatproductsecurity/rapidast", description: 'Image to use as the base for running zap.')
        string(name: "DAST_IMAGE_TAG", defaultValue: "latest", description: 'Image tag to use as the base for running zap.')
        string(name: 'DAST_TOOL_URL', defaultValue: 'https://github.com/RedHatProductSecurity/rapidast.git', description: 'Rapidast tool github url .')
        string(name: 'DAST_TOOL_BRANCH', defaultValue: 'development', description: 'Rapdiast tool github barnch to checkout.')
        string(name: 'SE_TOOL_URL', defaultValue: 'https://github.com/openshift-qe/ocpqe-security-tools.git', description: 'OCPQE security tool github url.')
        string(name: 'SEC_TOOL_BRANCH', defaultValue: 'main', description: 'OCPQE security tool github barnch to checkout.')
        string(name: 'API_URL_LIST', defaultValue: 'admissionregistration.k8s.io/v1', description: 
        '''List of api files to scan against.
        Api docs you can find using <b>kubectl api-versions</b>''')
        string(name: 'POLICY_FILE', defaultValue: 'API-scan-minimal', description: 'List of policies to check apis against.')
        string(name:'JENKINS_AGENT_LABEL',defaultValue:'oc415',description:
        '''
        scale-ci-static: for static agent that is specific to scale-ci, useful when the jenkins dynamic agent isn't stable<br>
        4.y: oc4y || mac-installer || rhel8-installer-4y <br/>
            e.g, for 4.8, use oc48 || mac-installer || rhel8-installer-48 <br/>
        3.11: ansible-2.6 <br/>
        3.9~3.10: ansible-2.4 <br/>
        3.4~3.7: ansible-2.4-extra || ansible-2.3 <br/>
        '''
        )
       text(name: 'ENV_VARS', defaultValue: '', description:'''<p>
               Enter list of additional (optional) Env Vars you'd want to pass to the script, one pair on each line. <br>
               See https://github.com/cloud-bulldozer/kraken-hub/blob/main/docs/cerberus.md for list of variables to pass <br>
               e.g.<br>
               SOMEVAR1='env-test'<br>
               SOMEVAR2='env2-test'<br>
               ...<br>
               SOMEVARn='envn-test'<br>
               </p>'''
            )
     }
  stages {
    stage('SSMl Run'){
        agent {
          kubernetes {
            cloud 'PSI OCP-C1 agents'
            yaml """\
              apiVersion: v1
              kind: Pod
              metadata:
                labels:
                  label: ${JENKINS_AGENT_LABEL}
              spec:
                containers:
                - name: "jnlp"
                  image: "image-registry.openshift-image-registry.svc:5000/aosqe/cucushift:${JENKINS_AGENT_LABEL}-rhel8"
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
      steps{
        deleteDir()
        checkout([
          $class: 'GitSCM',
          branches: [[name: params.SEC_TOOL_BRANCH ]],
          doGenerateSubmoduleConfigurations: false,
          userRemoteConfigs: [[url: params.SE_TOOL_URL ]
          ]])
        checkout([
            $class: 'GitSCM',
            branches: [[name: params.DAST_TOOL_BRANCH ]],
            doGenerateSubmoduleConfigurations: false,
            extensions: [
                [$class: 'CloneOption', noTags: true, reference: '', shallow: true],
                [$class: 'PruneStaleBranch'],
                [$class: 'CleanCheckout'],
                [$class: 'IgnoreNotifyCommit'],
                [$class: 'RelativeTargetDirectory', relativeTargetDir: 'dast_tool']
            ],
            userRemoteConfigs: [[url: params.DAST_TOOL_URL ]]
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
           # Get ENV VARS Supplied by the user to this job and store in .env_override
          echo "$ENV_VARS" > .env_override
          # Export those env vars so they could be used by CI Job
          set -a && source .env_override && set +a
          mkdir -p ~/.kube
          cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config
          ls
          oc login -u kubeadmin -p $(cat $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeadmin-password)
          HELM_DIR=$(mktemp -d)
          curl -sS -L https://get.helm.sh/helm-v3.11.2-linux-amd64.tar.gz | tar -xzC ${HELM_DIR}/ linux-amd64/helm
          
          ${HELM_DIR}/linux-amd64/helm version  

          mv ${HELM_DIR}/linux-amd64/helm $WORKSPACE/helm
          PATH=$PATH:$WORKSPACE
          helm version

          cd dast
          ls
          export DAST_PATH=../dast_tool
          set +e
          ./deploy_ssml_api.sh
          api_run_status=$?

          echo "api_run_status $api_run_status"
          exit $api_run_status

          ''')
          sh "echo $RETURNSTATUS"
          archiveArtifacts(
              artifacts: 'dast/results/**',
              allowEmptyArchive: true,
              fingerprint: true
          )
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
     }
   }
  }
  post {
      always {
          script {
                      build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/post-to-slack',
                      parameters: [
                          string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), string(name: 'WORKLOAD', value: "ssml"),
                          text(name: "BUILD_URL", value: env.BUILD_URL), string(name: 'BUILD_ID', value: currentBuild.number.toString()),
                          string(name: 'RESULT', value:currentBuild.currentResult)
                      ], propagate: false
          }
      }
  }
}