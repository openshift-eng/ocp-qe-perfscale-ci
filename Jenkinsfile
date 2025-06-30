@Library('flexy') _

// rename build
def userId = currentBuild.rawBuild.getCause(hudson.model.Cause$UserIdCause)?.userId
if (userId) {
  currentBuild.displayName = userId
}

def RETURNSTATUS = "default"
def output = ""

def kraken_job = ""
def cerberus_job = ""
def scale_upgrade_ci = ""

pipeline {
  agent none
  parameters {
        string(
          name: 'BUILD_NUMBER', 
          defaultValue: '', 
          description: 'Build number of job that has installed the cluster.'
        )
        booleanParam(
            name: 'INFRA_WORKLOAD_INSTALL', 
            defaultValue: false, 
            description: 'Install workload and infrastructure nodes even if less than 50 nodes. <br> Checking this parameter box is valid only when SCALE_UP is greater than 0.'
        )
        string(
            name: 'SCALE_UP', 
            defaultValue: '0', 
            description: 'If value is set to anything greater than 0, cluster will be scaled up before executing the workload.'
        )
        string(
            name: 'SCALE_DOWN', 
            defaultValue: '0', 
            description:
            '''If value is set to anything greater than 0, cluster will be scaled down after the execution of the workload is complete,<br>
            if the build fails, scale down may not happen, user should review and decide if cluster is ready for scale down or re-run the job on same cluster.'''
        )
        separator(
            name: "SCALE_CI_JOB_INFO", 
            sectionHeader: "Scale-CI Job Options", 
            sectionHeaderStyle: """
				font-size: 18px;
				font-weight: bold;
				font-family: 'Orienta', sans-serif;
			"""
        )
        choice(
            choices: ["","cluster-density", "cluster-density-ms","node-density", "node-density-heavy","node-density-cni","node-density-cni-networkpolicy","pod-density", "pod-density-heavy", "max-namespaces", "max-services", "concurrent-builds","pods-service-route","networkpolicy-case1","networkpolicy-case2","networkpolicy-case3"],
            name: 'CI_TYPE', 
            description: '''Type of scale-ci job to run. Can be left blank to not run ci job <br>
            Router-perf tests will use all defaults if selected, all parameters in this section below will be ignored '''
        )
        string(
            name: 'VARIABLE', 
            defaultValue: '1000', 
            description: '''
                This variable configures parameter needed for each type of workload. By default 1000. <br>
                pod-density: This will export PODS env variable; set to 200 * num_workers, work up to 250 * num_workers. Creates as many "sleep" pods as configured in this environment variable. <br>
                cluster-density: This will export JOB_ITERATIONS env variable; set to 4 * num_workers. This variable sets the number of iterations to perform (1 namespace per iteration). <br>
                max-namespaces: This will export NAMESPACE_COUNT env variable; set to ~30 * num_workers. The number of namespaces created by Kube-burner. <br>
                max-services: This will export SERVICE_COUNT env variable; set to 200 * num_workers, work up to 250 * num_workers. Creates n-replicas of an application deployment (hello-openshift) and a service in a single namespace. <br>
                node-density: This will export PODS_PER_NODE env variable; set to 200, work up to 250. Creates as many "sleep" pods as configured in this variable - existing number of pods on node. <br>
                node-density-heavy: This will export PODS_PER_NODE env variable; set to 200, work up to 250. Creates this number of applications proportional to the calculated number of pods / 2 <br>
                Read here for detail of each variable: <br>
                https://github.com/cloud-bulldozer/e2e-benchmarking/blob/master/workloads/kube-burner/README.md <br>
                ''' 
        )

        separator(
            name: "NODE_DENSITY_JOB_INFO", 
            sectionHeader: "Node Density Job Options", 
            sectionHeaderStyle: """
				font-size: 14px;
				font-weight: bold;
				font-family: 'Orienta', sans-serif;
			"""
        )
        string(
            name: 'NODE_COUNT', 
            defaultValue: '3',
            description: 'Number of worker nodes to be used in your cluster for this workload.'
        )
        separator(
            name: "CONCURRENT_BUILDS_JOB_INFO", sectionHeader: "Concurrent Builds Job Options", sectionHeaderStyle: """
				font-size: 14px;
				font-weight: bold;
				font-family: 'Orienta', sans-serif;
			""")
        string(
            name: 'BUILD_LIST', 
            defaultValue: "1 8 15 30 45 60 75", 
            description: 'Number of concurrent builds to run at a time; will run 2 iterations of each number in this list'
        )
        string(
            name: 'APP_LIST', 
            defaultValue: 'cakephp eap django nodejs', 
            description: 'Applications to build, will run each of the concurrent builds against each application. Best to run one application at a time'
        )
        separator(
            name: "NETWORK_PERF_INFO", 
            sectionHeader: "Network-Perf Job Options", 
            sectionHeaderStyle: """
				font-size: 14px;
				font-weight: bold;
				font-family: 'Orienta', sans-serif;
			"""
        )
        choice(
            choices: ['smoke', 'pod2pod', 'hostnet', 'pod2svc'], 
            name: 'WORKLOAD_TYPE', 
            description: 'Workload type'
        )
        booleanParam(
            name: "NETWORK_POLICY", 
            defaultValue: false, 
            description: "If enabled, benchmark-operator will create a network policy to allow ingress trafic in uperf server pods"
        )
        separator(
        name: "REGRESSION_TEST_JOB_INFO", 
        sectionHeader: "Regression Test Job Options", 
        sectionHeaderStyle: """
          font-size: 14px;
          font-weight: bold;
          font-family: 'Orienta', sans-serif;"""
      )
      choice(
        choices: ["conc_jobs","large_network_policy"], 
        name: 'TEST_CASE',
        description:'''<p>
        Select the test case you want to run.<br>
        This job will search the TEST_CASE.sh file under svt repo <a href="https://github.com/openshift/svt/blob/master/perfscale_regression_ci/scripts">perfscale_regression_ci/scripts</a> folder and sub folders<br>
        If SCRIPT is specified TEST_CASE will be overwritten.
        </p>'''
      )
      string(
        name: 'SCRIPT',
        defaultValue: '',
        description: '''<p>
        Relative path to the script of the TEST_CASE under <a href="https://github.com/openshift/svt">svt repo</a>.<br>
        If you want to use script from your own repo you need to change also SVT_REPO variable. <br>
        e.g.<br>
        For large_network_policy test case: perfscale_regression_ci/scripts/network/large_network_policy.sh<br>
        If TEST_CASE is specified, SCRIPT will overwrite the TEST_CASE.
        </p>'''
      )
        separator(
            name: "UPGRADE_INFO", 
            sectionHeader: "Upgrade Options", 
            sectionHeaderStyle: """
				font-size: 18px;
				font-weight: bold;
				font-family: 'Orienta', sans-serif;
			"""
        )
        string(
            name: 'UPGRADE_VERSION', 
            description: 'This variable sets the version number you want to upgrade your OpenShift cluster to (can list multiple by separating with comma, no spaces).'
        )
        booleanParam(
            name: 'EUS_UPGRADE', 
            defaultValue: false, 
            description: '''This variable will perform an EUS type upgrade <br>
            See "https://docs.google.com/document/d/1396VAUFLmhj8ePt9NfJl0mfHD7pUT7ii30AO7jhDp0g/edit#heading=h.bv3v69eaalsw" for how to run
            '''
        )
        choice(
            choices: ['fast', 'eus', 'candidate', 'stable'], 
            name: 'EUS_CHANNEL', 
            description: 'EUS Channel type, will be ignored if EUS_UPGRADE is not set to true'
        )
        booleanParam(
            name: 'ENABLE_FORCE', 
            defaultValue: true,
            description: 'This variable will force the upgrade or not'
        )
        booleanParam(
            name: 'SCALE', 
            defaultValue: false, 
            description: 'This variable will scale the cluster up one node at the end up the upgrade'
        )
        string(
            name: 'MAX_UNAVAILABLE', 
            defaultValue: "1", 
            description: 'This variable will set the max number of unavailable nodes during the upgrade'
        )

        booleanParam(
            name: 'WRITE_TO_FILE',
            defaultValue: false,
            description: 'Value to write to google sheet (will run <a href=https://mastern-jenkins-csb-openshift-qe.apps.ocp-c1.prod.psi.redhat.com/job/scale-ci/job/e2e-benchmarking-multibranch-pipeline/job/write-scale-ci-results>write-scale-ci-results</a>)'
        )
        booleanParam(
            name: 'CLEANUP',
            defaultValue: false,
            description: 'Cleanup namespaces (and all sub-objects) created from workload (will run <a href=https://mastern-jenkins-csb-openshift-qe.apps.ocp-c1.prod.psi.redhat.com/job/scale-ci/job/e2e-benchmarking-multibranch-pipeline/job/benchmark-cleaner/>benchmark-cleaner</a>)'
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
        string(
            name: "CERBERUS_WATCH_NAMESPACES", 
            defaultValue: "[^.*\$]",
            description: "Which specific namespaces you want to watch any failing components, use [^.*\$] if you want to watch all namespaces"
        )
        string(
            name: "CERBERUS_IGNORE_PODS",
            defaultValue: "[^installer*, ^kube-burner*, ^redhat-operators*, ^certified-operators*, ^collect-profiles*]", 
            description: "Which specific pod names regex patterns you want to ignore in the namespaces you defined above"
        )
        string(
            name: 'CERBERUS_ITERATIONS', 
            defaultValue: '', 
            description: 'Number of iterations to run of cerberus.'
        )
        string(
          name: "PAUSE_TIME",
          defaultValue: "5",
          description: 'Amount of time to pause before running chaos scenarios'
        )
        choice(
          choices: ["application-outages","container-scenarios","namespace-scenarios","network-scenarios","node-scenarios","pod-scenarios","node-cpu-hog","node-io-hog", "node-memory-hog", "power-outages","pvc-scenario","time-scenarios","zone-outages"], 
          name: 'KRAKEN_SCENARIO', 
          description: '''Type of kraken scenario to run'''
        )
        choice(
          choices: ["python","pod"], 
          name: 'KRAKEN_RUN_TYPE', 
          description: '''Type of way to run chaos scenario'''
        )
        string(
            name: 'ITERATIONS', 
            defaultValue: '', 
            description: 'Number of iterations to run of kraken scenario.'
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
               See https://github.com/redhat-chaos/krkn-hub/blob/main/docs/cerberus.md for list of variables to pass <br>
               e.g.<br>
               SOMEVAR1='env-test'<br>
               SOMEVAR2='env2-test'<br>
               ...<br>
               SOMEVARn='envn-test'<br>
               </p>'''
        )
        string(
            name: 'CERBERUS_REPO',
            defaultValue: 'https://github.com/redhat-chaos/cerberus',
            description: 'You can change this to point to your fork if needed.'
        )
        string(
            name: 'CERBERUS_REPO_BRANCH',
            defaultValue: 'main', 
            description: 'You can change this to point to a branch on your fork if needed.'
        )
       string(
        name: 'KRAKEN_REPO', 
        defaultValue:'https://github.com/redhat-chaos/krkn', 
        description:'You can change this to point to your fork if needed.'
       )
       string(
        name: 'KRAKN_REPO_BRANCH', 
        defaultValue:'main', 
        description:'You can change this to point to a branch on your fork if needed.'
       )
       string(
        name: 'KRAKEN_HUB_REPO', 
        defaultValue:'https://github.com/redhat-chaos/krkn-hub', 
        description:'You can change this to point to your fork if needed.'
        )
       string(
        name: 'KRAKN_HUB_REPO_BRANCH', 
        defaultValue:'main', 
        description:'You can change this to point to a branch on your fork if needed.'
      )
      string(
        name: 'SVT_REPO',
        defaultValue:'https://github.com/openshift/svt',
        description:'''<p>
          Repository to get regression test scripts and artifacts.<br>
          You can change this to point to your fork if needed.
          </p>'''
      )
      string(
        name: 'SVT_REPO_BRANCH',
        defaultValue:'master',
        description:'You can change this to point to a branch on your fork if needed.'
      )
      string(
        name: 'E2E_BENCHMARKING_REPO',
        defaultValue:'https://github.com/cloud-bulldozer/e2e-benchmarking',
        description:'You can change this to point to your fork if needed.'
      )
      string(
        name: 'E2E_BENCHMARKING_REPO_BRANCH',
        defaultValue:'master',
        description:'You can change this to point to a branch on your fork if needed.'
      )
     }

  stages {
    stage("Set base variables") { 
        agent { label params['JENKINS_AGENT_LABEL'] }
            steps {
                script {

                  if ( UPGRADE_VERSION == "" ) {
                    currentBuild.description = """
                      Running kraken and cerberus in parallel<br>
                    """
                  } else {
                    currentBuild.description = """
                      Running kraken during an upgrade and cerberus all in parallel <br>
                    """
                  }
                }
      }
    }
    stage("Scale Up Cluster") {
        agent { label params['JENKINS_AGENT_LABEL'] }
        when {
            expression { params.SCALE_UP.toInteger() > 0 || params.INFRA_WORKLOAD_INSTALL == true }
        }
        steps {
            script{

                scale_up = build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cluster-workers-scaling/', parameters: [
                    string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), text(name: "ENV_VARS", value: ENV_VARS),
                    booleanParam(name: 'INFRA_WORKLOAD_INSTALL', value: INFRA_WORKLOAD_INSTALL),
                    string(name: 'WORKER_COUNT', value: SCALE_UP), string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL)
                ]
                currentBuild.description += """
                    <b>Scaled Up:</b>  <a href="${scale_up.absoluteUrl}"> ${global_scale_num} </a><br/>
                """
                if( scale_up != null && scale_up.result.toString() != "SUCCESS") {
                    status = "Scale Up Failed"
                    currentBuild.result = "FAILURE"
                }
            }
        }
    }
    stage("Run parallel tests") {
        parallel {
            stage("Check cluster health") {
                agent { label params['JENKINS_AGENT_LABEL'] }
                steps {
                    script {
                        cerberus_job = build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cerberus',
                            parameters: [
                                string(name: 'BUILD_NUMBER', value: BUILD_NUMBER),text(name: "ENV_VARS", value: ENV_VARS),
                                string(name: "CERBERUS_WATCH_NAMESPACES", value: CERBERUS_WATCH_NAMESPACES),
                                string(name: 'CERBERUS_IGNORE_PODS', value: CERBERUS_IGNORE_PODS),string(name: 'CERBERUS_ITERATIONS', value: CERBERUS_ITERATIONS),
                                string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL),booleanParam(name: "INSPECT_COMPONENTS", value: false),
                                string(name: "ENV_VARS", value: ENV_VARS)
                            ],
                            propagate: false
                        currentBuild.description += """
                            <b>Cerberus Job: </b> <a href="${cerberus_job.absoluteUrl}"> ${params.CERBERUS_ITERATIONS} iterations were ran</a> <br/>
                        """
                    }
                }
            }
            stage("Start Kraken run") {
                agent { label params['JENKINS_AGENT_LABEL'] }
                steps {
                    script {
                            kraken_job = build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/kraken',
                            parameters: [
                                string(name: 'BUILD_NUMBER', value: BUILD_NUMBER),text(name: "ENV_VARS", value: ENV_VARS),
                                string(name: "KRAKEN_REPO", value: KRAKEN_REPO),string(name: "KRAKN_REPO_BRANCH", value: KRAKN_REPO_BRANCH),
                                string(name: "KRAKEN_HUB_REPO", value: KRAKEN_HUB_REPO),string(name: "KRAKN_HUB_REPO_BRANCH", value: KRAKN_HUB_REPO_BRANCH),
                                string(name: 'KRAKEN_SCENARIO', value: KRAKEN_SCENARIO),string(name: "KRAKEN_RUN_TYPE", value: KRAKEN_RUN_TYPE),
                                string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL),string(name: "PAUSE_TIME", value: PAUSE_TIME),
                                string(name: "ITERATIONS", value: ITERATIONS),string(name: "ENV_VARS", value: ENV_VARS)
                            ],
                            propagate: false
                            currentBuild.description += """
                            <b>Kraken Job: </b> <a href="${kraken_job.absoluteUrl}"> ${KRAKEN_SCENARIO} </a> <br/>
                        """
                    }
                }
            }
            stage('Upgrade'){
                agent { label params['JENKINS_AGENT_LABEL'] }
                when {
                    expression { UPGRADE_VERSION != "" }
                }
                steps{
                    script{
                        currentBuild.description += """
                            <b>Upgrade to: </b> ${UPGRADE_VERSION} <br/>
                        """
                        scale_upgrade_ci = build job: "scale-ci/e2e-benchmarking-multibranch-pipeline/upgrade", propagate: false,parameters:[
                            string( name: "BUILD_NUMBER", value: BUILD_NUMBER),string(name: "MAX_UNAVAILABLE", value: MAX_UNAVAILABLE),
                            string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL),string(name: "UPGRADE_VERSION", value: UPGRADE_VERSION),
                            booleanParam(name: "ENABLE_FORCE", value: ENABLE_FORCE),booleanParam(name: "WRITE_TO_FILE", value: false),
                            text(name: "ENV_VARS", value: ENV_VARS)
                        ]
                        currentBuild.description += """
                            <b>Upgrade Job: </b> <a href="${scale_upgrade_ci.absoluteUrl}"> ${UPGRADE_VERSION} </a> <br/>
                        """
                        
                    }
                }
            }
            stage("Perf Testing"){
                agent { label params['JENKINS_AGENT_LABEL'] }
                when {
                    expression { CI_TYPE != "" }
                }
                steps{
                    script {
                        if (params.CI_TYPE == "etcd-perf") {
                            scale_upgrade_ci = build job: "scale-ci/e2e-benchmarking-multibranch-pipeline/etcd-perf", propagate: false, parameters:[
                                    string(name: "BUILD_NUMBER", value: BUILD_NUMBER),string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL),
                                    text(name: "ENV_VARS", value: ENV_VARS),string(name: "E2E_BENCHMARKING_REPO", value: E2E_BENCHMARKING_REPO),
                                    booleanParam(name: "CERBERUS_CHECK", value: false),
                                    string(name: "E2E_BENCHMARKING_REPO_BRANCH", value: E2E_BENCHMARKING_REPO_BRANCH),
                                    booleanParam(name: "WRITE_TO_FILE", value: WRITE_TO_FILE)
                            ]
                            currentBuild.description += """
                                    <b>Scale-Ci: </b> etcd-perf <br/>
                                    <b>Scale-CI Job: </b> <a href="${scale_upgrade_ci.absoluteUrl}"> ${scale_upgrade_ci.getNumber()} </a> <br/>
                                """
                        } else if (params.CI_TYPE == "router-perf") {
                            scale_upgrade_ci = build job: "scale-ci/e2e-benchmarking-multibranch-pipeline/router-perf",propagate: false, parameters:[
                                    string(name: "BUILD_NUMBER", value: BUILD_NUMBER),string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL),
                                    text(name: "ENV_VARS", value: ENV_VARS),string(name: "E2E_BENCHMARKING_REPO", value: E2E_BENCHMARKING_REPO),
                                    booleanParam(name: "CERBERUS_CHECK", value: false),
                                    string(name: "E2E_BENCHMARKING_REPO_BRANCH", value: E2E_BENCHMARKING_REPO_BRANCH),
                                    booleanParam(name: "WRITE_TO_FILE", value: WRITE_TO_FILE)
                            ]
                                currentBuild.description += """
                                    <b>Scale-Ci: </b> router-perf <br/>
                                    <b>Scale-CI Job: </b> <a href="${scale_upgrade_ci.absoluteUrl}"> ${scale_upgrade_ci.getNumber()} </a> <br/>
                                """
                        } else if ( ["network-perf-pod-network-test","network-perf-serviceip-network-test","network-perf-hostnetwork-network-test"].contains(params.CI_TYPE) ) {
                            scale_upgrade_ci = build job: "scale-ci/e2e-benchmarking-multibranch-pipeline/network-perf", propagate: false, parameters:[
                                    string(name: "BUILD_NUMBER", value: BUILD_NUMBER),string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL),
                                    string(name: "WORKLOAD_TYPE", value: WORKLOAD_TYPE),booleanParam(name: "NETWORK_POLICY", value: NETWORK_POLICY),
                                    booleanParam(name: "CERBERUS_CHECK", value: false),
                                    text(name: "ENV_VARS", value: ENV_VARS),string(name: "E2E_BENCHMARKING_REPO", value: E2E_BENCHMARKING_REPO),
                                    string(name: "E2E_BENCHMARKING_REPO_BRANCH", value: E2E_BENCHMARKING_REPO_BRANCH),
                                    booleanParam(name: "WRITE_TO_FILE", value: WRITE_TO_FILE)
                                ]
                            currentBuild.description += """
                                    <b>Scale-Ci: Network Perf </b> ${WORKLOAD_TYPE} ${NETWORK_POLICY} <br/>
                                    <b>Scale-CI Job: </b> <a href="${scale_upgrade_ci.absoluteUrl}"> ${scale_upgrade_ci.getNumber()} </a> <br/>
                            """
                            } else if (params.CI_TYPE == "regression-test") {
                            scale_upgrade_ci = build job: "scale-ci/e2e-benchmarking-multibranch-pipeline/regression-test",propagate: false, parameters:[
                                    string(name: "BUILD_NUMBER", value: BUILD_NUMBER),string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL),
                                    text(name: "ENV_VARS", value: ENV_VARS),string(name: "SVT_REPO", value: SVT_REPO),
                                    string(name: "SVT_REPO_BRANCH", value: SVT_REPO_BRANCH),string(name: "PARAMETERS", value: VARIABLE),
                                    string(name: "SCRIPT", value: SCRIPT),string(name: "TEST_CASE", value: TEST_CASE),
                                    booleanParam(name: "CLEANUP", value: CLEANUP),booleanParam(name: "CERBERUS_CHECK", value: false),
                            ]
                                currentBuild.description += """
                                    <b>Scale-Ci: </b> regression-test <br/>
                                    <b>Scale-CI Job: </b> <a href="${scale_upgrade_ci.absoluteUrl}"> ${scale_upgrade_ci.getNumber()} </a> <br/>
                                """
                            } else {
                                scale_upgrade_ci = build job: "scale-ci/e2e-benchmarking-multibranch-pipeline/kube-burner", propagate: false, parameters:[
                                    string(name: "BUILD_NUMBER", value: BUILD_NUMBER),string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL),
                                    string(name: "WORKLOAD", value: CI_TYPE),string(name: "VARIABLE", value: VARIABLE),string(name: 'NODE_COUNT', value: NODE_COUNT),
                                    string(name: "BUILD_LIST", value: BUILD_LIST),string(name: 'APP_LIST', value: APP_LIST),text(name: "ENV_VARS", value: ENV_VARS),booleanParam( name: "WRITE_TO_FILE", value: WRITE_TO_FILE),
                                    booleanParam(name: "CERBERUS_CHECK", value: false),booleanParam(name: "CLEANUP", value: CLEANUP),
                                    string(name: "E2E_BENCHMARKING_REPO", value: E2E_BENCHMARKING_REPO),
                                    string(name: "E2E_BENCHMARKING_REPO_BRANCH", value: E2E_BENCHMARKING_REPO_BRANCH)
                                ]
                                currentBuild.description += """
                                    <b>Scale-Ci: Kube-burner </b> ${CI_TYPE}- ${VARIABLE} <br/>
                                    <b>Scale-CI Job: </b> <a href="${scale_upgrade_ci.absoluteUrl}"> ${scale_upgrade_ci.getNumber()} </a> <br/>
                                """
                            }  

                    }
                }
            }
        }
    }
    stage("Scale down workers") {
        agent { label params['JENKINS_AGENT_LABEL'] }
        when {
            expression { params.SCALE_DOWN.toInteger() > 0 }
        }
            steps {
            script {
                build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cluster-workers-scaling',
                    parameters: [
                        string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), string(name: 'WORKER_COUNT', value: SCALE_DOWN),
                        text(name: "ENV_VARS", value: ENV_VARS), string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL)
                    ]
            }
        }
        }
    stage('Set status') {
        agent { label params['JENKINS_AGENT_LABEL'] }
        steps {
            script{
                def status = ""
                if ( scale_upgrade_ci != "" ) {
                    if ( scale_upgrade_ci.result.toString() != "SUCCESS" ) { 
                        status += "Scale-ci Failed"
                        currentBuild.result = "FAILURE"
                    } else { 
                        status += "Scale-ci Passed"
                    }
                }
                if ( kraken_job != "" ) {
                    if (status != "" ) {
                        status += ","
                    }
                    if ( kraken_job.result.toString() != "SUCCESS" ){
                        status += "Kraken Failed"
                        currentBuild.result = "FAILURE"
                    } else { 
                        status += "Kraken Passed"
                    }
                }
                if ( cerberus_job != "" ) {
                    if (status != "" ) {
                        status += ","
                    }
                    if ( cerberus_job.result.toString() != "SUCCESS" ) {
                        if (status != "" ) {
                        status += ","
                        }
                        status += "Cerberus Failed"
                        currentBuild.result = "FAILURE"
                    } else { 
                        status += "Cerberus Passed"
                    }
                }
                currentBuild.description += """
                    <b>Final Status: </b> ${status} <br/>
                """
            }
        }
    }
  }
}

