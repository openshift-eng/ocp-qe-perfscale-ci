def aws = null
def install = null
def scale_up = null
def loaded_ci = null
def health_check = null
def upgrade_ci = null
def destroy_ci = null
def must_gather = null
def build_string = "DEFAULT"
def load_result = "SUCCESS"
def loaded_url = ""
def upgrade_url = ""
def must_gather_url = ""
def proxy_settings = ""
def status = "PASS"
def VERSION = ""
def global_scale_num = 0

def userId = currentBuild.rawBuild.getCause(hudson.model.Cause$UserIdCause)?.userId
if (userId) {
  currentBuild.displayName = "${userId}-${currentBuild.displayName}"
}

def JENKINS_JOB_NUMBER = currentBuild.number.toString()
println "JENKINS_JOB_NUMBER $JENKINS_JOB_NUMBER"

pipeline{
    agent any
    options { 
      timeout(time: 10, unit: 'HOURS')
    }
    parameters {
      separator(
        name: "PRE_BUILT_FLEXY_ENV", 
        sectionHeader: "Pre Built Flexy", 
        sectionHeaderStyle: """
          font-size: 18px;
          font-weight: bold;
          font-family: 'Orienta', sans-serif;
        """
      )
      string(
        name: 'BUILD_NUMBER', 
        defaultValue: '', 
        description: 'Build number of job that has installed the cluster.'
      )
      separator(
        name: "BUILD_FLEXY_COMMON_PARAMS", 
        sectionHeader: "Build Flexy Parameters Common", 
        sectionHeaderStyle: """
          font-size: 18px;
          font-weight: bold;
          font-family: 'Orienta', sans-serif;
        """
      )
      string(
        name: 'OCP_PREFIX', 
        defaultValue: '', 
        description: 'Name of ocp cluster you want to build'
      )
      string(
        name: 'OCP_VERSION',
        defaultValue: '', 
        description: 'Build version to install the cluster.'
      )
      choice(
        choices: ["",'x86_64','aarch64', 's390x', 'ppc64le', 'multi', 'multi-aarch64','multi-x86_64','multi-ppc64le', 'multi-s390x'], 
        name: 'ARCH_TYPE', 
        description: '''Type of architecture installation for quay image url; <b>
        set to x86_64 by default or if profile contains ARM will set to aarch64
        If this is not blank will use value you set here'''
      )
        
      separator(
        name: "BUILD_FLEXY_FROM_PROFILE", 
        sectionHeader: "Build Flexy From Profile", 
        sectionHeaderStyle: """
          font-size: 18px;
          font-weight: bold;
          font-family: 'Orienta', sans-serif;
        """
      )
      string(
        name: 'CI_PROFILE', 
        defaultValue: '', 
        description: """Name of ci profile to build for the cluster you want to build <br>
          You'll give the name of the file (under the specific version) without `.install.yaml`
        """
      )
      choice(
        choices: ['extra-small','small','medium',''], 
        name: 'PROFILE_SCALE_SIZE', 
        description: """Set scale size to set number of workers to add and define size of masters and workers. <br>
        For information about size definitions see <a href="https://gitlab.cee.redhat.com/aosqe/ci-profiles/-/blob/master/scale-ci/4.11/02_IPI-on-AWS.install.yaml#L10"> here </a> (will need ot look at your specific profile) <br>
        set Size of cluster to scale to; will be ignored if SCALE_UP is set"""
      )
      separator(
        name: "BUILD_FLEXY", 
        sectionHeader: "Build Flexy Parameters", 
        sectionHeaderStyle: """
          font-size: 18px;
          font-weight: bold;
          font-family: 'Orienta', sans-serif;
        """
      )
        separator(name: "SCALE_UP_JOB_INFO", sectionHeader: "Scale Up Job Options", sectionHeaderStyle: """
				font-size: 18px;
				font-weight: bold;
				font-family: 'Orienta', sans-serif;
			""")
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
      string(name: 'SCALE_DOWN', 
        defaultValue: '0', 
        description:
        '''If value is set to anything greater than 0, cluster will be scaled down after the execution of the workload is complete,<br>
        if the build fails, scale down may not happen, user should review and decide if cluster is ready for scale down or re-run the job on same cluster.'''
      )
      string(
        name: 'RHEL_SCALE_UP', 
        defaultValue: '0', 
        description: 'If value is set to anything greater than 0, cluster will be scaled up before executing the workload.'
      )
      string(
        name: 'RHEL_INSTANCE_SIZE', 
        defaultValue: 'm5.2xlarge', 
        description: 'If value is set to anything greater than 0, cluster will be scaled up before executing the workload.'
      )
      separator(
        name: "SCALE_CI_JOB_INFO", 
        sectionHeader: "Scale-CI Job Options", 
        sectionHeaderStyle: """
          font-size: 18px;
          font-weight: bold;
          font-family: 'Orienta', sans-serif;"""
      )
      booleanParam(
          name: 'CHURN',
          defaultValue: true,
          description: '''Run churn at end of original iterations. <a href=https://github.com/cloud-bulldozer/e2e-benchmarking/tree/master/workloads/kube-burner#churn>Churning</a> allows you to scale down and then up a percentage of JOB_ITERATIONS after the objects have been created <br>
          Use the following variables in ENV_VARS to set specifics of churn: <br>
          CHURN_DURATION=60m  <br>
          CHURN_PERCENT=20 <br>
          CHURN_DELAY=30s
          NOTE: this only applies to kube-burner workloads'''
      )
      choice(
        choices: ["","cluster-density-v2"], 
        name: 'CI_TYPE', 
        description: '''Type of scale-ci job to run. Can be left blank to not run ci job <br>
          Router-perf tests will use all defaults if selected, all parameters in this section below will be ignored '''
      )
      booleanParam(
        name: "KUBE_BURNER_OCP",
        defaultValue: false,
        description: "If enabled, the kube-burner-ocp versions of the selected CI_TYPE will be run"      
      )
      string(
        name: 'VARIABLE', 
        defaultValue: '1000', 
        description: '''
        This variable configures parameter needed for each type of workload. By default 1000. <br>
        - <b>cluster-density</b>: This will export JOB_ITERATIONS env variable; set to 9 * num_workers. This variable sets the number of iterations to perform (1 namespace per iteration). <br>
        '''
      )
      separator(
        name: " Network-Perf Job Options", 
        sectionHeader: " Network-Perf Job Options:", 
        sectionHeaderStyle: """
          font-size: 18px;
          font-weight: bold;
          font-family: 'Orienta', sans-serif;"""
      )
      separator(
        name: "KRAKEN SCENARIO", 
        sectionHeader: "Kraken Workloads:", 
        sectionHeaderStyle: """
          font-size: 18px;
          font-weight: bold;
          font-family: 'Orienta', sans-serif;"""
      )
      booleanParam(
        name: "MEMORY_HOG",
        defaultValue: true,
        description: "If enabled, the krkn versions of node_memory_hog will run"      
      )
      booleanParam(
        name: "CPU_HOG",
        defaultValue: true,
        description: "If enabled, the krkn versions of node_cpu_hog will run"      
      )
      choice(
          choices: ["python","pod"], 
          name: 'KRAKEN_RUN_TYPE', 
          description: '''Type of way to run chaos scenario'''
        )
      string(
        name: 'NODE_CPU_PERCENTAGE', 
        defaultValue: '', 
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
      separator(
        name: "NODE_DENSITY_JOB_INFO", 
        sectionHeader: "Node Density Job Options", 
        sectionHeaderStyle: """
          font-size: 14px;
          font-weight: bold;
          font-family: 'Orienta', sans-serif;"""
      )
      string(
        name: 'NODE_COUNT', 
        defaultValue: '3', 
        description: 'Number of worker nodes to be used in your cluster for this workload.'
      )
      separator(
        name: "CONCURRENT_BUILDS_JOB_INFO", 
        sectionHeader: "Concurrent Builds Job Options", 
        sectionHeaderStyle: """
          font-size: 14px;
          font-weight: bold;
          font-family: 'Orienta', sans-serif;"""
      )
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
        name: "INGRESS_PERF_INFO", 
        sectionHeader: "Ingress-Perf Job Config", 
        sectionHeaderStyle: """
          font-size: 14px;
          font-weight: bold;
          font-family: 'Orienta', sans-serif;"""
      )
      string(
        name: 'CONFIG',
        defaultValue: "config/standard.yml",
        description: 'Config type for ingress-perf'
      )
      separator(
        name: "NETWORK_PERF_INFO", 
        sectionHeader: "Network-Perf Job Options", 
        sectionHeaderStyle: """
          font-size: 14px;
          font-weight: bold;
          font-family: 'Orienta', sans-serif;"""
      )
      choice(
        choices: ['smoke', 'pod2pod', 'hostnet', 'pod2svc','full-run'],
        name: 'WORKLOAD_TYPE',
        description: 'Workload type'
      )
      booleanParam(
        name: "NETWORK_POLICY",
        defaultValue: false,
        description: "If enabled, benchmark-operator will create a network policy to allow ingress trafic in uperf server pods"
      )

      separator(
        name: "UPGRADE_INFO",
        sectionHeader: "Upgrade Options",
        sectionHeaderStyle: """
        font-size: 18px;
        font-weight: bold;
        font-family: 'Orienta', sans-serif;"""
      )
      string(
        name: 'UPGRADE_VERSION',
        description: 'This variable sets the version number you want to upgrade your OpenShift cluster to (can list multiple by separating with comma, no spaces).'
      )
      booleanParam(
        name: 'EUS_UPGRADE',
        defaultValue: false,
        description: '''This variable will perform an EUS type upgrade <br>
        See "https://docs.google.com/document/d/1396VAUFLmhj8ePt9NfJl0mfHD7pUT7ii30AO7jhDp0g/edit#heading=h.bv3v69eaalsw" for how to run'''
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

      separator(
        name: "GENERAL_BUILD_INFO",
        sectionHeader: "General Options",
        sectionHeaderStyle: """
        font-size: 18px;
        font-weight: bold;
        font-family: 'Orienta', sans-serif;"""
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
      booleanParam(
        name: 'CERBERUS_CHECK',
        defaultValue: false,
        description: 'Check cluster health status pass (will run <a href=https://mastern-jenkins-csb-openshift-qe.apps.ocp-c1.prod.psi.redhat.com/job/scale-ci/job/e2e-benchmarking-multibranch-pipeline/job/cerberus/>cerberus</a>)'
      )
      booleanParam(
        name: 'MUST_GATHER', 
        defaultValue: true, 
        description: 'This variable will run must-gather if any cerberus components fail'
      )
      string(
        name: 'IMAGE_STREAM', 
        defaultValue: 'openshift/must-gather', 
        description: 'Base image stream of data to gather for the must-gather.'
      )
      string(
        name: 'IMAGE', 
        defaultValue: '', 
        description: 'Optional image to help get must-gather information on non default areas. See <a href="https://docs.openshift.com/container-platform/4.12/support/gathering-cluster-data.html">docs</a> for more information and options.'
      )
      booleanParam(
        name: 'DESTROY_WHEN_DONE', 
        defaultValue: 'False', 
        description: 'If you want to destroy the cluster created at the end of your run '
      )
      booleanParam(
          name: "SEND_SLACK",
          defaultValue: false,
          description: "Check this box to send a Slack notification to #ocp-qe-scale-ci-results upon the job's completion"
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
          e.g.<br>
          SOMEVAR1='env-test'<br>
          SOMEVAR2='env2-test'<br>
          ...<br>
          SOMEVARn='envn-test'<br>
          </p>'''
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
    
    stages{
        stage("Build Flexy Clusters") {
           agent { label params['JENKINS_AGENT_LABEL'] }
           steps {
                // checkout CI profile repo from GitLab
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
                            [$class: 'RelativeTargetDirectory', relativeTargetDir: 'local-ci-profiles']
                        ],
                        submoduleCfg: [],
                        userRemoteConfigs: [[
                            name: 'origin',
                            refspec: "+refs/heads/${params.CI_PROFILES_REPO_BRANCH}:refs/remotes/origin/${params.CI_PROFILES_REPO_BRANCH}",
                            url: "${params.CI_PROFILES_URL}"
                        ]]
                    ]
                script{

                    def custom_jenkins_label = JENKINS_AGENT_LABEL
                    if (params.SCALE_UP.toInteger() > 0 ) {
                        global_scale_num = params.SCALE_UP.toInteger()
                    }
                    println "global num $global_scale_num"
                     if(params.BUILD_NUMBER == "") {

                        if(params.CI_PROFILE != "" ) {

                            // read data from CI profile install file
                            MAJOR_VERSION = params.OCP_VERSION.split("\\.")[0]
                            MINOR_VERSION = params.OCP_VERSION.split("\\.")[1]

                            installData = readYaml(file: "local-ci-profiles/scale-ci/$MAJOR_VERSION.$MINOR_VERSION/${CI_PROFILE}.install.yaml")
                            installData.install.flexy.each { env.setProperty(it.key, it.value) }
                            // loop through install data keys to make sure scale is one of them
                            def scale_profile_size = 0
                            for (data in installData) {
                                if (data.key == "scale" ) {
                                    scale_profile_size = data.value.get(PROFILE_SCALE_SIZE).SCALE_UP
                                    break
                                }
                            }
                            if (scale_profile_size != 0 && global_scale_num == 0 ) {
                                // get scale_up val from profile
                                global_scale_num = scale_profile_size
                                
                            }
                            println "scale up not null $global_scale_num"
                            currentBuild.description = """
                                <b>CI Profile:</b> ${params.CI_PROFILE} <br/>
                                <b>Profile Size:</b> ${params.PROFILE_SCALE_SIZE} <br/>
                            """

                        } 
                        def set_arch_type = "x86_64"
                        if (params.ARCH_TYPE != "") {
                          set_arch_type = params.ARCH_TYPE
                        }
                        else if (params.CI_PROFILE != "" && params.CI_PROFILE.contains('ARM')) {
                          set_arch_type = "aarch64"
                        }

                        install = build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cluster-builder/', parameters: [
                            text(name: "ENV_VARS", value: ENV_VARS),string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL),
                            string(name: 'CI_PROFILES_URL', value: CI_PROFILES_URL),string(name: 'CI_PROFILES_REPO_BRANCH', value: CI_PROFILES_REPO_BRANCH),
                            string(name: 'OCP_PREFIX', value: OCP_PREFIX),string(name: 'OCP_VERSION', value: OCP_VERSION),
                            string(name: 'CI_PROFILE', value: CI_PROFILE),string(name: 'PROFILE_SCALE_SIZE', value: PROFILE_SCALE_SIZE),
                            string(name: "ARCH_TYPE", value: set_arch_type)
                        ]
                        def build_num = ""
                        if (install.description?.trim()) {
                            def description = readYaml(text: install.description)
                            if (description["FLEXY_BUILD_NUMBER"] != null) {
                              build_num = description["FLEXY_BUILD_NUMBER"]
                            }
                        }

                        if( install.result.toString() == "SUCCESS") {
                           status = "PASS"
                        }
                        build_string = build_num
                    } else {
                     copyArtifacts(
                        filter: '',
                        fingerprintArtifacts: true,
                        projectName: 'ocp-common/Flexy-install',
                        selector: specific(params.BUILD_NUMBER),
                        target: 'flexy-artifacts'
                       )
                       sh "echo 'ls flexy-artifacts/workdir/install-dir'"
                       if (fileExists("flexy-artifacts/workdir/install-dir/cluster_info.yaml")) {
                         println('cluster_info.yaml')
                          installData = readYaml(file: "flexy-artifacts/workdir/install-dir/cluster_info.yaml")
                          VERSION = installData.INSTALLER.VERSION
                          currentBuild.description = """
                              <b>Using Pre-Built Flexy</b> <br/>
                          """
                       } else if (fileExists("flexy-artifacts/workdir/install-dir/cluster_info.json")) {
                          installData = readJSON file: "flexy-artifacts/workdir/install-dir/cluster_info.json"
                          println "json version $installData"
                          VERSION = installData.INSTALLER.VERSION
                          currentBuild.description = """
                              <b>Using Pre-Built Flexy</b> <br/>
                          """
                        
                       } else {
                         println "unknown version"
                          VERSION = "Unknown Version"
                       }

                        if (params.BUILD_NUMBER != "") {
                            build_string = params.BUILD_NUMBER
                        }
                     }

                    currentBuild.description += """
                        <b>Version:</b> ${VERSION}<br/>
                        <b>Flexy-install Build:</b> ${build_string}<br/>
                    """
                 if ( build_string != "DEFAULT") {
                     copyArtifacts(
                        fingerprintArtifacts: true,
                        projectName: 'ocp-common/Flexy-install',
                        selector: specific(build_string),
                        filter: "workdir/install-dir/",
                        target: 'flexy-artifacts'
                       )
                    if (fileExists("flexy-artifacts/workdir/install-dir/client_proxy_setting.sh")) {
                     println "client proxy set"
                     proxy_settings = sh returnStdout: true, script: 'cat flexy-artifacts/workdir/install-dir/client_proxy_setting.sh'
                     proxy_settings = proxy_settings.replace('export ', '')
                    }
                    
                    if ( !ENV_VARS.contains("http_proxy") ) {

                      ENV_VARS += '\n' + proxy_settings
                      println "$ENV_VARS $global_scale_num"
                    } else {
                      println "proxy settings already set"
                    }
                 }
               }
            }
        }

        stage("Rhel scale up nodes") {
          agent { label params['JENKINS_AGENT_LABEL'] }
          when {
                expression { build_string != "DEFAULT" && status == "PASS" && params.RHEL_SCALE_UP.toInteger() > 0 }
            }
          steps{
            copyArtifacts(
                filter: '',
                fingerprintArtifacts: true,
                projectName: 'ocp-common/Flexy-install',
                selector: specific(build_string),
                target: 'flexy-artifacts'
            )
            script {
                buildinfo = readYaml file: "flexy-artifacts/BUILDINFO.yml"
                currentBuild.displayName = "${currentBuild.displayName}-${build_string}"
                currentBuild.description = "Copying Artifact from Flexy-install build <a href=\"${buildinfo.buildUrl}\">Flexy-install#${build_string}</a>"
                buildinfo.params.each { env.setProperty(it.key, it.value) }
            }
            checkout changelog: false,
                  poll: false,
                  scm: [
                      $class: 'GitSCM',
                      branches: [[name: "master"]],
                      doGenerateSubmoduleConfigurations: false,
                      extensions: [
                          [$class: 'CloneOption', noTags: true, reference: '', shallow: true],
                          [$class: 'PruneStaleBranch'],
                          [$class: 'CleanCheckout'],
                          [$class: 'IgnoreNotifyCommit'],
                          [$class: 'RelativeTargetDirectory', relativeTargetDir: 'scaleup']
                      ],
                      submoduleCfg: [],
                      userRemoteConfigs: [[
                          name: 'origin',
                          refspec: "+refs/heads/master:refs/remotes/origin/master",
                          url: "https://gitlab.cee.redhat.com/aosqe/v4-scaleup.git"
                      ]]
                  ]
            script{
              if ( params.RHEL_SCALE_UP.toInteger() > 0 ) {
                
                RETURNSTDOUT = sh(returnStdout: true, script: '''
                mkdir -p ~/.kube
                cp $WORKSPACE/flexy-artifacts/workdir/install-dir/auth/kubeconfig ~/.kube/config
                oc get clusterversion -o jsonpath='{.items[*].status.desired.version}'
                ''')
                println("return status $RETURNSTDOUT")
                  RETURNSTDOUT = RETURNSTDOUT.toString().split('\n')[-1]
                  MAJOR_VERSION = RETURNSTDOUT.split("\\.")[0]
                  MINOR_VERSION = RETURNSTDOUT.split("\\.")[1]
                  scale_divide = params.RHEL_SCALE_UP.toInteger() / 30
                  println("scale divide $scale_divide")
                  for (int i=0; i < scale_divide; i ++) {
                  
                  if ( i % 30 > 0 ){
                    rhel_scale_num = params.RHEL_SCALE_UP.toInteger() - ( i * 30 )
                  }else {
                    rhel_scale_num = 30 
                  }
                  version="aos-$MAJOR_VERSION"
                  version += "_"
                  version += "$MINOR_VERSION"
                  scale_data = readYaml(file: "scaleup/ocp4-rhel-scaleup/$version/default_map.yaml")
                  scale_data.aws.each { env.setProperty(it.key, it.value) }


                  scale_config = '''
                    RHEL_WORKER_PREFIX: rhel''' + i + '''\n
                    cluster_domain: qe.devcluster.openshift.com
                    aws:
                      profile: default
                      instance_size: m5.2xlarge
                      root_volume_size: "120"
                      ssh_user: ec2-user
                    '''

                        
                    RHEL_MAJOR_OS = 8
                    scale_config += "  RHEL_INSTANCE_SIZE: " + params.RHEL_INSTANCE_SIZE + "\n  image_8: " + env.image_8
                    println("scale config $scale_config")
                    install = build job: 'ocp4-rhel-scaleup', parameters: [
                          text(name: "EXTRA_VARS", value: "${scale_config}"),string(name: 'JENKINS_AGENT_LABEL', value: "ansible-core"),
                          string(name: 'FLEXY_BUILD_NUMBER', value: "${build_string}"),string(name: 'RHEL_WORKER_COUNT', value: rhel_scale_num.toString()),
                          string(name: 'RHEL_MAJOR_OS', value: "8"),
                          string(name: "SCALEUP_REPO", value: "https://gitlab.cee.redhat.com/aosqe/v4-scaleup.git"),
                          string(name: "SCALEUP_BRANCH", value: "master")
                      ]
              }

          }
          }
          }
        }

        stage("Scale Up Cluster") {
           agent { label params['JENKINS_AGENT_LABEL'] }
            when {
                expression { build_string != "DEFAULT" && status == "PASS" && (global_scale_num.toInteger() > 0 || params.INFRA_WORKLOAD_INSTALL == true)}
            }
           steps {
            script{

                scale_up = build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/cluster-workers-scaling/', parameters: [
                    string(name: 'BUILD_NUMBER', value: "${build_string}"), text(name: "ENV_VARS", value: ENV_VARS),
                    booleanParam(name: 'INFRA_WORKLOAD_INSTALL', value: INFRA_WORKLOAD_INSTALL),
                    string(name: 'WORKER_COUNT', value: global_scale_num.toString()), string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL)
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

        stage("Perf Testing"){
            agent { label params['JENKINS_AGENT_LABEL'] }
            when {
                expression { build_string != "DEFAULT" && status == "PASS" }
            }
            stages{
              stage("cluster-density-v2"){
                 when {
                expression { params.KUBE_BURNER_OCP == true }
                 }
                 steps{
                  script{
                    loaded_ci = build job: "scale-ci/e2e-benchmarking-multibranch-pipeline/kube-burner-ocp", propagate: false, parameters:[
                            string(name: "BUILD_NUMBER", value: "${build_string}"),string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL),
                            string(name: "WORKLOAD", value: CI_TYPE),string(name: "VARIABLE", value: VARIABLE),
                            text(name: "ENV_VARS", value: ENV_VARS),booleanParam(name: "WRITE_TO_FILE", value: WRITE_TO_FILE),
                            booleanParam(name: "CERBERUS_CHECK", value: CERBERUS_CHECK),booleanParam(name: "CLEANUP", value: CLEANUP),
                            string(name: "E2E_BENCHMARKING_REPO", value: E2E_BENCHMARKING_REPO),
                            string(name: "E2E_BENCHMARKING_REPO_BRANCH", value: E2E_BENCHMARKING_REPO_BRANCH),booleanParam(name: "MUST_GATHER", value: MUST_GATHER),
                            booleanParam(name: "CHURN", value: CHURN),
                            string(name: 'IMAGE', value: IMAGE),string(name: 'IMAGE_STREAM', value: IMAGE_STREAM)
                        ]
                        currentBuild.description += """
                            <b>Scale-Ci: Kube-burner-ocp </b> ${CI_TYPE}- ${VARIABLE} <br/>
                            <b>Scale-CI Job: </b> <a href="${loaded_ci.absoluteUrl}"> ${loaded_ci.getNumber()} </a> <br/>
                        """
                  }
                 }
              }
            }
        }
               
        stage("Run parallel tests") {
          parallel {
            stage("krkn"){
              agent { label params['JENKINS_AGENT_LABEL'] }
              stages{
                  stage("Start Kraken run"){
                  when {
                        expression { params.CPU_HOG == true }
                      }
                      steps {
                          script {
                                  kraken_job = build job: 'scale-ci/shyadav-e2e-benchmarking-multibranch-pipeline/kraken',
                                  parameters: [
                                      string(name: 'BUILD_NUMBER', value: "${build_string}"),
                                      text(name: "ENV_VARS", value: ENV_VARS),
                                      string(name: 'KRAKEN_SCENARIO', value: "node-cpu-hog"),
                                      string(name: "KRAKEN_RUN_TYPE", value: KRAKEN_RUN_TYPE),
                                      string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL),
                                      string(name: "CPU_PERCENT", value:NODE_CPU_PERCENTAGE),
                                      string(name: "TOTAL_CHAOS_DURATION", value:TOTAL_CHAOS_DURATION),
                                      string(name: "NODE_CPU_CORE", value:NODE_CPU_CORE)    
                                  ],
                                  propagate: false
                                  currentBuild.description += """
                                  <b>Kraken Job: </b> <a href="${kraken_job.absoluteUrl}"> ${kraken_job.getNumber()} </a> <br/>
                                  """
                                  if( kraken_job.result.toString() != "SUCCESS") {
                                    status = "Kraken cpu hog Failed"
                                    currentBuild.result = "FAILURE"
                                  }
                          }
                      }
                  }
                  stage("Start Kraken run 2") {
                    when {
                        expression { params.MEMORY_HOG == true }
                      }
                      steps {
                          script {
                                  kraken_job1 = build job: 'scale-ci/shyadav-e2e-benchmarking-multibranch-pipeline/kraken',
                                  parameters: [
                                      string(name: 'BUILD_NUMBER', value: "${build_string}"),
                                      text(name: "ENV_VARS", value: ENV_VARS),
                                      string(name: 'KRAKEN_SCENARIO', value: "node-memory-hog"),
                                      string(name: "KRAKEN_RUN_TYPE", value: KRAKEN_RUN_TYPE),
                                      string(name: 'JENKINS_AGENT_LABEL', value: JENKINS_AGENT_LABEL),
                                      string(name: "TOTAL_CHAOS_DURATION", value:TOTAL_CHAOS_DURATION),
                                      string(name: "MEMORY_CONSUMPTION_PERCENTAGE", value: MEMORY_CONSUMPTION_PERCENTAGE),
                                      string(name: "NUMBER_OF_WORKERS", value: NUMBER_OF_WORKERS)
                                  ],
                                  propagate: false
                                  currentBuild.description += """
                                  <b>Kraken Job: </b> <a href="${kraken_job1.absoluteUrl}"> ${kraken_job1.getNumber()} </a> <br/>
                                  """
                                  if( kraken_job1.result.toString() != "SUCCESS") {
                                    status = "Kraken memory hog Failed"
                                    currentBuild.result = "FAILURE"
                                  }
                          }
                      }
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
                      def set_arch_type = "x86_64"
                      if (params.ARCH_TYPE != "") {
                        set_arch_type = params.ARCH_TYPE
                      }
                      else if (params.CI_PROFILE != "" && params.CI_PROFILE.contains('ARM')) {
                        set_arch_type = "aarch64"
                      }	
                      upgrade_ci = build job: "scale-ci/e2e-benchmarking-multibranch-pipeline/upgrade", propagate: false,parameters:[
                          string(name: "BUILD_NUMBER", value: build_string),string(name: "MAX_UNAVAILABLE", value: MAX_UNAVAILABLE),
                          string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL),string(name: "UPGRADE_VERSION", value: UPGRADE_VERSION),
                          string(name: "ARCH_TYPE", value: set_arch_type),
                          booleanParam(name: "EUS_UPGRADE", value: EUS_UPGRADE),string(name: "EUS_CHANNEL", value: EUS_CHANNEL),
                          booleanParam(name: "WRITE_TO_FILE", value: WRITE_TO_FILE),booleanParam(name: "ENABLE_FORCE", value: ENABLE_FORCE),
                          booleanParam(name: "SCALE", value: SCALE),text(name: "ENV_VARS", value: ENV_VARS)
                      ]
                      currentBuild.description += """
                          <b>Upgrade Job: </b> <a href="${upgrade_ci.absoluteUrl}"> ${upgrade_ci.getNumber()} </a> <br/>
                      """
                      if( upgrade_ci.result.toString() != "SUCCESS") {
                        status = "Upgrade Failed"
                        currentBuild.result = "FAILURE"
                      }
                    }
                }
            }
          }
        }
  
        stage("Write out results") {
            agent { label params['JENKINS_AGENT_LABEL'] }
            when {
                expression { params.WRITE_TO_FILE == true }
            }
            steps{
                script{
                    println "write to file $loaded_ci "

                    if(loaded_ci != null ) {
                        loaded_url = loaded_ci.absoluteUrl
                    }
                    if(upgrade_ci != null ) {
                        upgrade_url = upgrade_ci.absoluteUrl
                    }
                    if ( must_gather != null ) {
                        must_gather_url = must_gather.absoluteUrl
                    }
                    build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/write-scale-ci-results', parameters: [
                        string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL),string(name: "BUILD_NUMBER", value: build_string),
                        string(name: 'CI_STATUS', value: "${status}"), string(name: 'UPGRADE_JOB_URL', value: upgrade_url),
                        text(name: "ENV_VARS", value: ENV_VARS),booleanParam(name: 'SCALE', value: SCALE),
                        string(name: 'CI_JOB_URL', value: loaded_url), booleanParam(name: 'ENABLE_FORCE', value: ENABLE_FORCE),
                        string(name: 'LOADED_JOB_URL', value: BUILD_URL), string(name: 'JOB', value: "loaded-upgrade"), 
                        string(name: 'PROFILE', value: CI_PROFILE),string(name: 'PROFILE_SIZE', value: PROFILE_SCALE_SIZE),
                        string(name: "JENKINS_JOB_NUMBER", value: JENKINS_JOB_NUMBER), string(name: "JENKINS_JOB_PATH", value: JOB_NAME)
                    ], propagate: false

                }
              }
        }
        stage('Destroy Flexy Cluster'){
            agent { label params['JENKINS_AGENT_LABEL'] }
            steps{
                script{
                    if(install != null && (install.result.toString() != "SUCCESS" || params.DESTROY_WHEN_DONE == true)) {
                        destroy_ci = build job: 'ocp-common/Flexy-destroy', parameters: [
                            string(name: "BUILD_NUMBER", value: build_string),string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL)
                        ]
                    } else if(install == null && params.DESTROY_WHEN_DONE == true) {
                        destroy_ci = build job: 'ocp-common/Flexy-destroy', parameters: [
                            string(name: "BUILD_NUMBER", value: build_string),string(name: "JENKINS_AGENT_LABEL", value: JENKINS_AGENT_LABEL)
                        ]
                    }

                    if( destroy_ci != null) {
                        println "destroy not null"
                        if( destroy_ci.result.toString() != "SUCCESS") {
                            println "destroy failed"
                            currentBuild.result = "FAILURE"
                            status = "Destroy Failed"
                        }
                    }
                }
            }
        }
    }
    post {
        always {
            script {
                currentBuild.description += """
                    <b>Final Status:</b> ${status}<br/>
                """
              if (params.SEND_SLACK == true ) {
                        build job: 'scale-ci/e2e-benchmarking-multibranch-pipeline/post-to-slack',
                        parameters: [
                            string(name: 'BUILD_NUMBER', value: BUILD_NUMBER), string(name: 'WORKLOAD', value: "loaded-upgrade"),
                            text(name: "BUILD_URL", value: env.BUILD_URL), string(name: 'BUILD_ID', value: currentBuild.number.toString()),string(name: 'RESULT', value:currentBuild.currentResult)
                        ], propagate: false
                }
            }
        }
    }
}
