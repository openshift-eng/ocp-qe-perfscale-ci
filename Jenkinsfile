
@Library('flexy') _

def RETURNSTATUS=0
pipeline {
  agent { label params['JENKINS_AGENT_LABEL'] }
  parameters {
        string(name: 'BUILD_NUMBER', defaultValue: '', description: 'Build number of job that has installed the cluster.')
        string(name: 'IMAGE_STREAM', defaultValue: 'openshift/must-gather', description: 'Base image stream of data to gather for the must-gather.')
        string(name: 'IMAGE', defaultValue: '', description: 'Optional image to help get must-gather information on non default areas. See <a href="https://docs.openshift.com/container-platform/4.12/support/gathering-cluster-data.html">docs</a> for more information and options.')
        string(name:'JENKINS_AGENT_LABEL',defaultValue:'oc412',description:
        '''
        scale-ci-static: for static agent that is specific to scale-ci, useful when the jenkins dynamic agent isn't stable
        <br>
        4.y: oc4y || mac-installer || rhel8-installer-4y <br/>
            e.g, for 4.8, use oc48 || mac-installer || rhel8-installer-48 <br/>
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
    stage('Run Must Gather'){
      agent {
          kubernetes {
            cloud 'openshift qe jenkins agents'
            yaml """\
              apiVersion: v1
              kind: Pod
              metadata:
                labels:
                  label: ${JENKINS_AGENT_LABEL}
              spec:
                containers:
                - name: "jnlp"
                  image: "images.paas.redhat.com/aos-qe-ci/jenkins-agent-rhel8:cucushift-${JENKINS_AGENT_LABEL}"
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
            echo -e "upgrade post check find err, collect must-gather....\n"
            schedulable_masters=(`oc get node | grep master |egrep -v 'Ready,SchedulingDisabled|NotReady'|awk '{print $1}'`)
            if [ -z "$schedulable_masters" ]; then
                echo "Skipping must-gather as there are no schedulable masters...\n"
                exit 120 # upgrade itself succ and post-check fail
            else
              image_param=""
              if [[ -n "$IMAGE" ]]; then
                echo "set image"
                image_param=" --image=$IMAGE"
              fi
              echo "image param $image_param"
              oc adm must-gather --image-stream=$IMAGE_STREAM $image_param
              ls must-gather.local*
              if [ $? -eq 0 ]; then
                filename=`ls |grep must-gather.local*`
                tar -czvf must-gather.tar.gz $filename >/dev/null 2>&1
                exit 0
              else
                echo -e "must-gather file creation fails!!!"
                exit 127 # upgrade itself succ and post-check fail
              fi
              fi

            ''')
          }
          script {
            archiveArtifacts artifacts: 'must-gather.tar.gz', allowEmptyArchive: true, fingerprint: false
          }
      }
    }
  }
}

