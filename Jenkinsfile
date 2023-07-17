@Library('flexy') _

// rename build
def userId = currentBuild.rawBuild.getCause(hudson.model.Cause$UserIdCause)?.userId
if (userId) {
  currentBuild.displayName = userId
}

pipeline {
  agent none

  parameters {
        string(name: 'BUILD_NUMBER', defaultValue: '', description: 'Build number of job that has installed the cluster.')
        string(name:'JENKINS_AGENT_LABEL',defaultValue:'oc48',description:
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
        booleanParam(name:'INFRA_NODES', defaultValue:true, description:'If set to true, infra nodes machineset will be created, and options listed below will be used')
        text(name: 'ENV_VARS', defaultValue: '''PLEASE FILL ME''', description:'''<p>
               Enter list of additional Env Vars you need to pass to the script, one pair on each line. <br>
               For OPENSHIFT_PROMETHEUS_STORAGE_CLASS and OPENSHIFT_ALERTMANAGER_STORAGE_CLASS, use `oc get storageclass` to get them on your cluster.<br>
               e.g.<b>for AWS:</b><br>
               <b>AMD/Standard Architecture:</b> <br>
                OPENSHIFT_INFRA_NODE_INSTANCE_TYPE=m5.12xlarge<br>
                OPENSHIFT_WORKLOAD_NODE_INSTANCE_TYPE=m5.8xlarge<br>
               <b>ARM64 Architecture:</b> <br>
                OPENSHIFT_INFRA_NODE_INSTANCE_TYPE=m6g.12xlarge <br>
                OPENSHIFT_WORKLOAD_NODE_INSTANCE_TYPE=m6g.8xlarge<br>
               <b>Both Architectures also need:</b> <br>
               OPENSHIFT_INFRA_NODE_VOLUME_IOPS=0            <br>
               OPENSHIFT_INFRA_NODE_VOLUME_TYPE=gp2          <br>
               OPENSHIFT_INFRA_NODE_VOLUME_SIZE=100          <br>
               OPENSHIFT_WORKLOAD_NODE_VOLUME_IOPS=0         <br>
               OPENSHIFT_WORKLOAD_NODE_VOLUME_TYPE=gp2       <br>
               OPENSHIFT_WORKLOAD_NODE_VOLUME_SIZE=500       <br>
               OPENSHIFT_PROMETHEUS_STORAGE_CLASS=gp2        <br>
               OPENSHIFT_ALERTMANAGER_STORAGE_CLASS=gp2      <br>
               e.g. <b>for Azure:</b><br>
               OPENSHIFT_INFRA_NODE_VOLUME_SIZE=128                <br>
               OPENSHIFT_INFRA_NODE_VOLUME_TYPE=Premium_LRS        <br>
               OPENSHIFT_INFRA_NODE_VM_SIZE=Standard_D48s_v3       <br>
               OPENSHIFT_WORKLOAD_NODE_VOLUME_SIZE=500             <br>
               OPENSHIFT_WORKLOAD_NODE_VOLUME_TYPE=Premium_LRS     <br>
               OPENSHIFT_WORKLOAD_NODE_VM_SIZE=Standard_D32s_v3    <br>
               OPENSHIFT_PROMETHEUS_STORAGE_CLASS=managed-csi  <br>
               OPENSHIFT_ALERTMANAGER_STORAGE_CLASS=managed-csi<br>
               e.g.<b>for GCP:</b><br>
               OPENSHIFT_INFRA_NODE_VOLUME_SIZE=100    <br>
               OPENSHIFT_INFRA_NODE_VOLUME_TYPE=pd-ssd <br>
               OPENSHIFT_INFRA_NODE_INSTANCE_TYPE=n1-standard-64 <br>
               OPENSHIFT_WORKLOAD_NODE_VOLUME_SIZE=500 <br>
               OPENSHIFT_WORKLOAD_NODE_VOLUME_TYPE=pd-ssd <br>
               OPENSHIFT_WORKLOAD_NODE_INSTANCE_TYPE=n1-standard-32 <br>
               GCP_PROJECT=openshift-qe <br>
               GCP_SERVICE_ACCOUNT_EMAIL=openshift-qe.iam.gserviceaccount.com <br>
               e.g. <b>for vSphere:</b><br>
               OPENSHIFT_INFRA_NODE_VOLUME_SIZE=120<br>
               OPENSHIFT_INFRA_NODE_CPU_COUNT=48<br>
               OPENSHIFT_INFRA_NODE_MEMORY_SIZE=196608<br>
               OPENSHIFT_INFRA_NODE_CPU_CORE_PER_SOCKET_COUNT=2<br>
               OPENSHIFT_INFRA_NODE_NETWORK_NAME=qe-segment<br>
               OPENSHIFT_WORKLOAD_NODE_VOLUME_SIZE=500<br>
               OPENSHIFT_WORKLOAD_NODE_CPU_COUNT=32<br>
               OPENSHIFT_WORKLOAD_NODE_MEMORY_SIZE=131072<br>
               OPENSHIFT_WORKLOAD_NODE_CPU_CORE_PER_SOCKET_COUNT=2<br>
               OPENSHIFT_WORKLOAD_NODE_NETWORK_NAME=qe-segment<br>
               e.g. <b>for Alicloud:</b><br>
               OPENSHIFT_INFRA_NODE_VOLUME_SIZE=100 <br>
               OPENSHIFT_INFRA_NODE_INSTANCE_TYPE=ecs.g6.13xlarge <br>
               OPENSHIFT_WORKLOAD_NODE_VOLUME_SIZE=500 <br>
               OPENSHIFT_WORKLOAD_NODE_INSTANCE_TYPE=ecs.g6.8xlarge <br>
               OPENSHIFT_PROMETHEUS_STORAGE_CLASS=alicloud-disk <br>
               OPENSHIFT_ALERTMANAGER_STORAGE_CLASS=alicloud-disk <br>
               e.g. <b>for Ibmcloud:</b><br>
               OPENSHIFT_INFRA_NODE_INSTANCE_TYPE=bx2d-48x192<br>
               OPENSHIFT_WORKLOAD_NODE_INSTANCE_TYPE=bx2-32x128<br>
               OPENSHIFT_PROMETHEUS_STORAGE_CLASS=ibmc-vpc-block-5iops-tier<br>
               OPENSHIFT_ALERTMANAGER_STORAGE_CLASS=ibmc-vpc-block-5iops-tier<br>
               e.g. <b>for OSP:</b><br>
               OPENSHIFT_INFRA_NODE_INSTANCE_TYPE=ci.cpu.xxxl<br>
               OPENSHIFT_WORKLOAD_NODE_INSTANCE_TYPE=ci.cpu.xxl<br>
               e.g. <b>for Nutanix:</b><br>
               OPENSHIFT_INFRA_NODE_INSTANCE_VCPU=16<br>
               OPENSHIFT_INFRA_NODE_INSTANCE_MEMORYSIZE=64Gi<br>
               OPENSHIFT_WORKLOAD_NODE_INSTANCE_VCPU=16<br>
               OPENSHIFT_WORKLOAD_NODE_INSTANCE_MEMORYSIZE=64Gi<br>
               <b>And ALWAYS INCLUDE(except for vSphere provider or Nutanix install without storageclass) this part, for Prometheus AlertManager, it may look like</b>:<br>
               OPENSHIFT_PROMETHEUS_RETENTION_PERIOD=15d<br>
               OPENSHIFT_PROMETHEUS_STORAGE_SIZE=50Gi  <br>
               OPENSHIFT_ALERTMANAGER_STORAGE_SIZE=1Gi <br></p>'''
            )
        booleanParam(name: 'INSTALL_DITTYBOPPER', defaultValue: true, description: 'Value to install dittybopper dashboards to cluster')
        string(name: 'DITTYBOPPER_REPO', defaultValue:'https://github.com/cloud-bulldozer/performance-dashboards.git', description:'You can change this to point to your fork if needed')
        string(name: 'DITTYBOPPER_REPO_BRANCH', defaultValue:'master', description:'You can change this to point to a branch on your fork if needed')
        string(name: 'DITTYBOPPER_PARAMS', defaultValue:'', description:'Arguments that are added when deploying dittybopper')
  }

  stages {
    stage('Create infra/workload machinesets and transfer infrastructure pods'){
      agent { label params['JENKINS_AGENT_LABEL'] }
      when {
          expression { params.INFRA_NODES == true }
      }
      steps{
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
        withCredentials([file(credentialsId: 'b73d6ed3-99ff-4e06-b2d8-64eaaf69d1db', variable: 'OCP_AWS'),
                         file(credentialsId: 'eb22dcaa-555c-4ebe-bb39-5b25628cc6bb', variable: 'OCP_GCP'),
                         file(credentialsId: 'ocp-azure', variable: 'OCP_AZURE')]) {
            def RETURNSTATUS = sh(returnStatus: true, script: '''
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
              set -x

              SECONDS=0
              ./openshift-qe-workers-infra-workload-commands.sh
              ./openshift-qe-move-pods-infra-commands.sh
              status=$?
              echo "final status $status"
              duration=$SECONDS
              echo "$(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed."
              exit $status
              rm -rf ~/.kube ~/.aws
            ''')
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
    stage('Install Dittybopper') {
      agent { label params['JENKINS_AGENT_LABEL'] }
      when {
          expression { params.INSTALL_DITTYBOPPER == true}
      }
      steps {
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
          sh label: '', script: '''
            # Get ENV VARS Supplied by the user to this job and store in .env_override
            echo "$ENV_VARS" > .env_override
            # Export those env vars so they could be used by CI Job
            set -a && source .env_override && set +a
            mkdir -p ~/.kube
            cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config

            oc config view
            oc projects
            ls -ls ~/.kube/
            # Remove the folder to resolve OCPQE-12185
            rm -rf performance-dashboards
            git clone --single-branch --branch $DITTYBOPPER_REPO_BRANCH --depth 1 $DITTYBOPPER_REPO

            pushd performance-dashboards/dittybopper
            ./deploy.sh $DITTYBOPPER_PARAMS
            popd
            '''
        }
      }
    }
        
  }
}

