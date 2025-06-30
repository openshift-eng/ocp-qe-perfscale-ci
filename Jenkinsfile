@Library('flexy') _

// rename build
def userId = currentBuild.rawBuild.getCause(hudson.model.Cause$UserIdCause)?.userId
if (userId) {
  currentBuild.displayName = userId
}
def scale_num = 3

pipeline {
    agent none

    parameters {
        string(
            name: 'BUILD_NUMBER', 
            defaultValue: '', 
            description: 'Build number of job that has installed the cluster.'
        )
        string(
            name: "JENKINS_AGENT_LABEL",
            defaultValue: 'oc420',
            description:
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
        string(
            name: 'WORKER_COUNT',
            defaultValue: '0',
            description:'Total Worker count desired in the cluster'
        )
        booleanParam(
            name: 'UPDATE_OUTBOUND_PORTS', 
            defaultValue: false, 
            description: 'Updating the outbound port for over 55 nodes, https://issues.redhat.com/browse/OCPBUGS-42983'
        )
        booleanParam(
            name: 'INFRA_WORKLOAD_INSTALL', 
            defaultValue: false, 
            description: 'Install workload and infrastructure nodes even if less than 50 nodes'
        )
        booleanParam(
            name: 'IF_CREATE_WORKLOAD_NODE', 
            defaultValue: false, 
            description: 'If set to true, create workload nodes'
        )
        booleanParam(
            name: 'IF_MOVE_INGRESS',
            defaultValue: true,
            description: '''
                If set to true, move ingress pods to infra nodes.
            '''
        )
        booleanParam(
            name: 'IF_MOVE_MONITORING',
            defaultValue: true,
            description: '''
                If set to true, move monitoring pods to infra nodes.
            '''
        )
        booleanParam(
            name: 'IF_MOVE_REGISTRY',
            defaultValue: true,
            description: '''
                If set to true, move registry pods to infra nodes.
            '''
        )
        booleanParam(
            name: 'INSTALL_DITTYBOPPER',
            defaultValue: true,
            description: 'Value to install dittybopper dashboards to cluster'
        )
        string(
            name: 'DITTYBOPPER_REPO',
            defaultValue:'https://github.com/cloud-bulldozer/performance-dashboards.git',
            description:'You can change this to point to your fork if needed'
        )
        string(
            name: 'DITTYBOPPER_REPO_BRANCH',
            defaultValue:'master',
            description:'You can change this to point to a branch on your fork if needed'
        )
        string(
            name: 'DITTYBOPPER_PARAMS',
            defaultValue:'',
            description:'Arguments that are added when deploying dittybopper'
        )
        text(
            name: 'ENV_VARS',
            defaultValue: '',
            description:'''<p>
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
        stage('Scale Workers in OCP Cluster'){
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
                buildinfo = readYaml file: "$WORKSPACE/flexy-artifacts/BUILDINFO.yml"
                currentBuild.displayName = "${currentBuild.displayName}-${params.BUILD_NUMBER}"
                currentBuild.description = "Copying Artifact from Flexy-install build <a href=\"${buildinfo.buildUrl}\">Flexy-install#${params.BUILD_NUMBER}</a>"
                buildinfo.params.each { env.setProperty(it.key, it.value) }
            }
            script{
                withCredentials([file(credentialsId: 'ocp-azure', variable: 'OCP_AZURE')]) {
                            
                            if(env.VARIABLES_LOCATION.indexOf("azure") != -1){
                                if (params.WORKER_COUNT.toInteger() > 50 || params.UPDATE_OUTBOUND_PORTS == true ) {
                                 RETURNSTATUS = sh(returnStatus: true, script: '''
                                    mkdir -p ~/.kube
                                    # Get ENV VARS Supplied by the user to this job and store in .env_override
                                    echo "$ENV_VARS" > .env_override
                                    # Export those env vars so they could be used by CI Job
                                    set -a && source .env_override && set +a
                                    cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config

                                    ls
                                    SECONDS=0
                                    ./az_outbound_ports.sh
                                    status=$?
                                    echo "final status $status"
                                    duration=$SECONDS
                                    echo "$(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed."
                                    exit $status
                                ''')
                                }
                            }
                         }
            }

        script{
            if (params.WORKER_COUNT.toInteger() > 0 ) {
                RETURNSTATUS = sh(returnStatus: true, script: '''
                    mkdir -p ~/.kube
                    # Get ENV VARS Supplied by the user to this job and store in .env_override
                    echo "$ENV_VARS" > .env_override
                    # Export those env vars so they could be used by CI Job
                    set -a && source .env_override && set +a
                    cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config
                    oc config view
                    oc projects
                    ls -ls ~/.kube/
                    env
                    SECONDS=0
                    ./scaling.sh
                    status=$?
                    echo "final status $status"
                    duration=$SECONDS
                    echo "$(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed."
                    exit $status
                '''
                )
            
                if (RETURNSTATUS.toInteger() == 0) {
                    status = "PASS"
                }
                else { 
                    currentBuild.result = "FAILURE"
                }
            }
        }
        
        script{
          if (params.WORKER_COUNT.toInteger() > 50 || params.INFRA_WORKLOAD_INSTALL == true ) {

              sh(script: '''
                mkdir -p ~/.kube
                # Get ENV VARS Supplied by the user to this job and store in .env_override
                echo "$ENV_VARS" > .env_override
                # Export those env vars so they could be used by CI Job
                set -a && source .env_override && set +a
                cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config
                oc cluster-info
  
                oc whoami''')
              def architecture_type = sh(returnStdout: true, script: '''
                # Export those env vars so they could be used by CI Job
                set -a && source .env_override && set +a
                node_name=$(oc get node --no-headers | grep master| head -1| awk '{print $1}')
                oc get node $node_name -ojsonpath='{.status.nodeInfo.architecture}'
              ''')
              ENV_VARS += '''
OPENSHIFT_PROMETHEUS_RETENTION_PERIOD=15d
OPENSHIFT_PROMETHEUS_STORAGE_SIZE=500Gi
OPENSHIFT_ALERTMANAGER_STORAGE_SIZE=20Gi'''
              println "architecture_type $architecture_type"
              if(env.VARIABLES_LOCATION.indexOf("aws") != -1){
                if (architecture_type.contains("arm64")) {
                      ENV_VARS += '''
OPENSHIFT_INFRA_NODE_INSTANCE_TYPE=m6g.4xlarge
OPENSHIFT_WORKLOAD_NODE_INSTANCE_TYPE=m6g.xlarge'''
              } else {
                  ENV_VARS += '''
OPENSHIFT_INFRA_NODE_INSTANCE_TYPE=r5.4xlarge
OPENSHIFT_WORKLOAD_NODE_INSTANCE_TYPE=m5.xlarge'''
              }
                build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cluster-post-config', parameters: [
                string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), booleanParam(name: 'HOST_NETWORK_CONFIGS', value:false),
                string(name: 'PROVISION_OR_TEARDOWN', value: 'PROVISION'),
                string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL),
                booleanParam(name: 'INFRA_NODES', value: true),
                booleanParam(name: 'IF_MOVE_INGRESS', value: IF_MOVE_INGRESS),
                booleanParam(name: 'IF_MOVE_MONITORING', value: IF_MOVE_MONITORING),
                booleanParam(name: 'IF_MOVE_REGISTRY', value: IF_MOVE_REGISTRY),
                booleanParam(name: 'INSTALL_DITTYBOPPER', value: INSTALL_DITTYBOPPER),
                string(name: 'DITTYBOPPER_REPO', value: DITTYBOPPER_REPO),
                string(name: 'DITTYBOPPER_REPO_BRANCH', value: DITTYBOPPER_REPO_BRANCH),
                string(name: 'DITTYBOPPER_PARAMS', value: DITTYBOPPER_PARAMS),
                text(name: 'ENV_VARS', value: ENV_VARS + '''
OPENSHIFT_INFRA_NODE_VOLUME_IOPS=0
OPENSHIFT_INFRA_NODE_VOLUME_TYPE=gp2
OPENSHIFT_INFRA_NODE_VOLUME_SIZE=100
OPENSHIFT_PROMETHEUS_STORAGE_CLASS=gp2
OPENSHIFT_ALERTMANAGER_STORAGE_CLASS=gp2
OPENSHIFT_WORKLOAD_NODE_VOLUME_IOPS=0
OPENSHIFT_WORKLOAD_NODE_VOLUME_TYPE=gp2
OPENSHIFT_WORKLOAD_NODE_VOLUME_SIZE=500
                  ''')]
            }else if(env.VARIABLES_LOCATION.indexOf("azure") != -1){
                if (architecture_type.contains("arm64")) {
                      ENV_VARS += '''
OPENSHIFT_INFRA_NODE_VM_SIZE=Standard_D16ps_v5
OPENSHIFT_WORKLOAD_NODE_VM_SIZE=Standard_D4ps_v5'''
              } else {
                  ENV_VARS += '''
OPENSHIFT_INFRA_NODE_VM_SIZE=Standard_D16s_v3
OPENSHIFT_WORKLOAD_NODE_VM_SIZE=Standard_D4s_v3'''
              }
              build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cluster-post-config', parameters: [
              string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), booleanParam(name: 'HOST_NETWORK_CONFIGS', value:false),
              string(name: 'PROVISION_OR_TEARDOWN', value: 'PROVISION'),
              string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL),
              booleanParam(name: 'INFRA_NODES', value: true),
              booleanParam(name: 'IF_MOVE_INGRESS', value: IF_MOVE_INGRESS),
              booleanParam(name: 'IF_MOVE_MONITORING', value: IF_MOVE_MONITORING),
              booleanParam(name: 'IF_MOVE_REGISTRY', value: IF_MOVE_REGISTRY),
              booleanParam(name: 'INSTALL_DITTYBOPPER', value: INSTALL_DITTYBOPPER),
              string(name: 'DITTYBOPPER_REPO', value: DITTYBOPPER_REPO),
              string(name: 'DITTYBOPPER_REPO_BRANCH', value: DITTYBOPPER_REPO_BRANCH),
              string(name: 'DITTYBOPPER_PARAMS', value: DITTYBOPPER_PARAMS),              
              text(name: 'ENV_VARS', value: ENV_VARS + '''
OPENSHIFT_INFRA_NODE_VOLUME_SIZE=128
OPENSHIFT_INFRA_NODE_VOLUME_TYPE=Premium_LRS
OPENSHIFT_PROMETHEUS_STORAGE_CLASS=managed-csi
OPENSHIFT_ALERTMANAGER_STORAGE_CLASS=managed-csi
OPENSHIFT_WORKLOAD_NODE_VOLUME_SIZE=500
              ''')]
            }else if(env.VARIABLES_LOCATION.indexOf("gcp") != -1){
              if (architecture_type.contains("arm64")) {
                      ENV_VARS += '''
OPENSHIFT_INFRA_NODE_VM_SIZE=t2a-standard-16
OPENSHIFT_WORKLOAD_NODE_VM_SIZE=t2a-standard-4'''
              } else {
                  ENV_VARS += '''
OPENSHIFT_INFRA_NODE_VM_SIZE=n1-standard-16
OPENSHIFT_WORKLOAD_NODE_VM_SIZE=n1-standard-4'''
              }              
              build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cluster-post-config', parameters: [
              string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), booleanParam(name: 'HOST_NETWORK_CONFIGS', value:false),
              string(name: 'PROVISION_OR_TEARDOWN', value: 'PROVISION'),
              string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL),
              booleanParam(name: 'INFRA_NODES', value: true),
              booleanParam(name: 'IF_MOVE_INGRESS', value: IF_MOVE_INGRESS),
              booleanParam(name: 'IF_MOVE_MONITORING', value: IF_MOVE_MONITORING),
              booleanParam(name: 'IF_MOVE_REGISTRY', value: IF_MOVE_REGISTRY),
              booleanParam(name: 'INSTALL_DITTYBOPPER', value: INSTALL_DITTYBOPPER),
              string(name: 'DITTYBOPPER_REPO', value: DITTYBOPPER_REPO),
              string(name: 'DITTYBOPPER_REPO_BRANCH', value: DITTYBOPPER_REPO_BRANCH),
              string(name: 'DITTYBOPPER_PARAMS', value: DITTYBOPPER_PARAMS),
              text(name: 'ENV_VARS', value: ENV_VARS + '''
OPENSHIFT_INFRA_NODE_VOLUME_SIZE=100
OPENSHIFT_INFRA_NODE_VOLUME_TYPE=pd-ssd
GCP_PROJECT=openshift-qe
GCP_SERVICE_ACCOUNT_EMAIL=openshift-qe.iam.gserviceaccount.com
OPENSHIFT_WORKLOAD_NODE_VOLUME_SIZE=500
OPENSHIFT_WORKLOAD_NODE_VOLUME_TYPE=pd-ssd
''')
                  ]
                } else if(env.VARIABLES_LOCATION.indexOf("vsphere") != -1){
                  build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cluster-post-config', parameters: [
                      string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), booleanParam(name: 'HOST_NETWORK_CONFIGS', value:false),
                      string(name: 'PROVISION_OR_TEARDOWN', value: 'PROVISION'),
                      string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL),
                      booleanParam(name: 'INFRA_NODES', value: true),
                      booleanParam(name: 'IF_MOVE_INGRESS', value: IF_MOVE_INGRESS),
                      booleanParam(name: 'IF_MOVE_MONITORING', value: IF_MOVE_MONITORING),
                      booleanParam(name: 'IF_MOVE_REGISTRY', value: IF_MOVE_REGISTRY),
                      booleanParam(name: 'INSTALL_DITTYBOPPER', value: INSTALL_DITTYBOPPER),
                      string(name: 'DITTYBOPPER_REPO', value: DITTYBOPPER_REPO),
                      string(name: 'DITTYBOPPER_REPO_BRANCH', value: DITTYBOPPER_REPO_BRANCH),
                      string(name: 'DITTYBOPPER_PARAMS', value: DITTYBOPPER_PARAMS),
                      text(name: 'ENV_VARS', value: ENV_VARS + '''                    
OPENSHIFT_INFRA_NODE_VOLUME_SIZE=120
OPENSHIFT_INFRA_NODE_CPU_COUNT=16
OPENSHIFT_INFRA_NODE_MEMORY_SIZE=65536
OPENSHIFT_INFRA_NODE_CPU_CORE_PER_SOCKET_COUNT=2
OPENSHIFT_INFRA_NODE_NETWORK_NAME=qe-segment
OPENSHIFT_WORKLOAD_NODE_VOLUME_SIZE=500
OPENSHIFT_WORKLOAD_NODE_CPU_COUNT=4
OPENSHIFT_WORKLOAD_NODE_MEMORY_SIZE=16384
OPENSHIFT_WORKLOAD_NODE_CPU_CORE_PER_SOCKET_COUNT=2
OPENSHIFT_WORKLOAD_NODE_NETWORK_NAME=qe-segment''')]
            } else if(env.VARIABLES_LOCATION.indexOf("alicloud") != -1){
              build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cluster-post-config', parameters: [
              string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), booleanParam(name: 'HOST_NETWORK_CONFIGS', value:false),
              string(name: 'PROVISION_OR_TEARDOWN', value: 'PROVISION'),
              string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL),
              booleanParam(name: 'INFRA_NODES', value: true),
              booleanParam(name: 'IF_MOVE_INGRESS', value: IF_MOVE_INGRESS),
              booleanParam(name: 'IF_MOVE_MONITORING', value: IF_MOVE_MONITORING),
              booleanParam(name: 'IF_MOVE_REGISTRY', value: IF_MOVE_REGISTRY),
              booleanParam(name: 'INSTALL_DITTYBOPPER', value: INSTALL_DITTYBOPPER),
              string(name: 'DITTYBOPPER_REPO', value: DITTYBOPPER_REPO),
              string(name: 'DITTYBOPPER_REPO_BRANCH', value: DITTYBOPPER_REPO_BRANCH),
              string(name: 'DITTYBOPPER_PARAMS', value: DITTYBOPPER_PARAMS),
              text(name: 'ENV_VARS', value: ENV_VARS + '''
OPENSHIFT_INFRA_NODE_VOLUME_SIZE=100
OPENSHIFT_INFRA_NODE_INSTANCE_TYPE=ecs.g6.13xlarge
OPENSHIFT_WORKLOAD_NODE_VOLUME_SIZE=500
OPENSHIFT_WORKLOAD_NODE_INSTANCE_TYPE=ecs.g6.xlarge
OPENSHIFT_PROMETHEUS_STORAGE_CLASS=alicloud-disk
OPENSHIFT_ALERTMANAGER_STORAGE_CLASS=alicloud-disk
              ''')]
            } else if(env.VARIABLES_LOCATION.indexOf("ibmcloud") != -1){
              build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cluster-post-config', parameters: [
              string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), booleanParam(name: 'HOST_NETWORK_CONFIGS', value:false),
              string(name: 'PROVISION_OR_TEARDOWN', value: 'PROVISION'),
              string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL),
              booleanParam(name: 'INFRA_NODES', value: true),
              booleanParam(name: 'IF_MOVE_INGRESS', value: IF_MOVE_INGRESS),
              booleanParam(name: 'IF_MOVE_MONITORING', value: IF_MOVE_MONITORING),
              booleanParam(name: 'IF_MOVE_REGISTRY', value: IF_MOVE_REGISTRY),
              booleanParam(name: 'INSTALL_DITTYBOPPER', value: INSTALL_DITTYBOPPER),
              string(name: 'DITTYBOPPER_REPO', value: DITTYBOPPER_REPO),
              string(name: 'DITTYBOPPER_REPO_BRANCH', value: DITTYBOPPER_REPO_BRANCH),
              string(name: 'DITTYBOPPER_PARAMS', value: DITTYBOPPER_PARAMS),
              text(name: 'ENV_VARS', value: ENV_VARS + '''
OPENSHIFT_INFRA_NODE_INSTANCE_TYPE=bx2d-48x192
OPENSHIFT_WORKLOAD_NODE_INSTANCE_TYPE=bx2-4x16
OPENSHIFT_PROMETHEUS_STORAGE_CLASS=ibmc-vpc-block-5iops-tier
OPENSHIFT_ALERTMANAGER_STORAGE_CLASS=ibmc-vpc-block-5iops-tier
              ''')]
            } else if(env.VARIABLES_LOCATION.indexOf("osp") != -1){
              build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cluster-post-config', parameters: [
              string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), string(name: 'HOST_NETWORK_CONFIGS', value:'false'),
              string(name: 'PROVISION_OR_TEARDOWN', value: 'PROVISION'),
              string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL),
              string(name: 'INFRA_NODES', value: 'true'),
              booleanParam(name: 'IF_MOVE_INGRESS', value: IF_MOVE_INGRESS),
              booleanParam(name: 'IF_MOVE_MONITORING', value: IF_MOVE_MONITORING),
              booleanParam(name: 'IF_MOVE_REGISTRY', value: IF_MOVE_REGISTRY),
              text(name: 'ENV_VARS', value: ENV_VARS + '''
OPENSHIFT_INFRA_NODE_INSTANCE_TYPE=ci.m1.xlarge
OPENSHIFT_WORKLOAD_NODE_INSTANCE_TYPE=ci.m1.xlarge
              ''')]
            }else {
            echo "Cloud type is not set up yet"
            }
          }
        }
      }
        
    }
  }
}

