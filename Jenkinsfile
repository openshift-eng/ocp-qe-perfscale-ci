@Library('flexy') _

// rename build
def userCause = currentBuild.rawBuild.getCause(Cause.UserIdCause)
def upstreamCause = currentBuild.rawBuild.getCause(Cause.UpstreamCause)

userId = "prubenda"
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

def baseline_returnCode = null

pipeline {
    agent { label params.JENKINS_AGENT_LABEL }

    options {
        timeout(time: 1, unit: 'HOURS')
        ansiColor('xterm')
    }

    parameters {
        string(
            name: 'BUILD_NUMBER',
            defaultValue: '',
            description: '''
                Build number of Flexy job that installed the cluster.<br/>
                <b>Note that only AWS clusters are supported at the moment.</b>
            '''
        )
        separator(
            name: 'WORKLOAD_CONFIG_OPTIONS',
            sectionHeader: 'Workload Configuration Options',
            sectionHeaderStyle: '''
                font-size: 14px;
                font-weight: bold;
                font-family: 'Orienta', sans-serif;
            '''
        )
        booleanParam(
            name: 'UPLOAD_BASELINE',
            defaultValue: true,
            description: 'Upload baseline data if one is not found'
        )
        choice(
          choices: ["cluster-density-v2","cluster-density","node-density","node-density-heavy","pod-density","pod-density-heavy","max-namespaces","max-services",
            "node-density-cni","cluster-density-ms","pods-service-route","networkpolicy-case1","networkpolicy-case2","networkpolicy-case3",
            "concurrent-builds","network-perf","network-perf-v2","router-perf","ingress-perf","nightly-regression","loaded-upgrade","upgrade",
            "nightly-regression-longrun"], 
          name: 'WORKLOAD', 
          description: '''Type of kube-burner job to run'''
        )
        string(
          name: 'JENKINS_JOB_NUMBER', 
          defaultValue: '', 
          description: 'Build number of the scale-ci job that was used to load the cluster.')
        string(
          name: 'JENKINS_JOB_PATH', 
          defaultValue: '', 
          description: 'Build path for the type of job that was used to load the cluster.'
        )
        string(
            name: 'CI_STATUS', 
            defaultValue: 'FAIL', 
            description: 'Scale-ci job ending status'
        )
        string(
            name: 'FAILED_JOBS', 
            defaultValue: '', 
        description:'These are the failed tests from the nightly scale-ci regresion runs'
        )
        string(
            name: 'CI_PROFILE', 
            defaultValue: '', 
            description: """Name of ci profile to build for the cluster you want to build <br>
            You'll give the name of the file (under the specific version) without `.install.yaml`
            """
        )
        choice(
            choices: ['extra-small','small','medium','large',''], 
            name: 'PROFILE_SCALE_SIZE', 
            description: """Set scale size to set number of workers to add and define size of masters and workers. <br>
            For information about size definitions see <a href="https://gitlab.cee.redhat.com/aosqe/ci-profiles/-/blob/master/scale-ci/4.11/02_IPI-on-AWS.install.yaml#L10"> here </a> (will need ot look at your specific profile) <br>
            set Size of cluster to scale to; will be ignored if SCALE_UP is set"""
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
        stage('Validate job parameters') {
            steps {
                script {
                    if (params.BUILD_NUMBER == '') {
                        error 'A Flexy build number must be specified'
                    }
                }
            }
        }
        stage('Run Workload and Mr. Sandman') {
            when {
                expression { (!["nightly-regression","loaded-upgrade","upgrade","nightly-regression-longrun"].contains(params.WORKLOAD)) }
            }
            steps {
                deleteDir()
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: 'main' ]],
                    userRemoteConfigs: [[url: "https://github.com/openshift-eng/ocp-qe-perfscale-ci" ]],
                    extensions: [[$class: 'RelativeTargetDirectory', relativeTargetDir: 'helpful_scripts']]
                ])
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
        stage('Run Post Baseline UUID to Elastic tool') {
            environment{
                EMAIL_ID_FOR_RESULTS_SHEET = "${userId}@redhat.com"
                GLOBAL_USER_ID = "${userId}"
            }
            when {
                expression { params.UPLOAD_BASELINE == true && (params.CI_STATUS == "PASS" || params.CI_STATUS == "SUCCESS" ) }
            }
            steps {
                deleteDir()
                checkout([
                  $class: 'GitSCM',
                  branches: [[name: GIT_BRANCH ]],
                  doGenerateSubmoduleConfigurations: false,
                  userRemoteConfigs: [[url: GIT_URL ]]
                ])
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
                  checkout([
                        $class: 'GitSCM',
                        branches: [[name: "main_scripts" ]],
                        doGenerateSubmoduleConfigurations: false,
                        extensions: [
                            [$class: 'CloneOption', noTags: true, reference: '', shallow: true],
                            [$class: 'PruneStaleBranch'],
                            [$class: 'CleanCheckout'],
                            [$class: 'IgnoreNotifyCommit'],
                            [$class: 'RelativeTargetDirectory', relativeTargetDir: 'helpful_scripts']
                        ],
                        userRemoteConfigs: [[url: "https://github.com/paigerube14/ocp-qe-perfscale-ci.git" ]]
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
                    currentBuild.displayName = "${currentBuild.displayName}-${params.BUILD_NUMBER}-${params.WORKLOAD}"
                    currentBuild.description += "Copying Artifact from Flexy-install build <a href=\"${buildinfo.buildUrl}\">Flexy-install#${params.BUILD_NUMBER}</a>"
                    buildinfo.params.each { env.setProperty(it.key, it.value) }
                }
                withCredentials([usernamePassword(credentialsId: 'elasticsearch-perfscale-ocp-qe', usernameVariable: 'ES_USERNAME', passwordVariable: 'ES_PASSWORD')]) {
                    script {
                        
                        result_returnCode = sh(returnStatus: true, script: """
                            # Get ENV VARS Supplied by the user to this job and store in .env_override
                            echo "$ENV_VARS" > .env_override
                            # Export those env vars so they could be used by CI Job
                            set -a && source .env_override && set +a
                            mkdir -p ~/.kube
                            cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config
                            python3.9 --version
                            python3.9 -m pip install virtualenv
                            python3.9 -m virtualenv venv3
                            source venv3/bin/activate
                            python --version
                            pip install -r requirements.txt
                            python post_uuid_to_es.py --user $GLOBAL_USER_ID --baseline true
                            """)
                        
                        // fail pipeline if upload to ES run failed
                        if ( result_returnCode.toInteger() != 0 || (baseline_returnCode != null && baseline_returnCode.toInteger() != 0)) {
                            error('Post to ES tool failed :(')
                        }
                        else {
                            println 'Successfully ran Es tool :)'
                        }
                        }
                    }
            }
        }
    }
}

