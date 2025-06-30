
def aws = null
def install = null
def build_string = "DEFAULT"
def status = "PASS"
def VERSION = ""
def FLEXY_BUILD_NUMBER = ""
def install_type_desc = ""
def bushslicer_config = ""

def userId = currentBuild.rawBuild.getCause(hudson.model.Cause$UserIdCause)?.userId
if (userId) {
  currentBuild.displayName = "${userId}-${currentBuild.displayName}"
}

pipeline{
    agent any

    parameters {
        separator(name: "BUILD_FLEXY_COMMON_PARAMS", sectionHeader: "Build Flexy Parameters Common", sectionHeaderStyle: """
				font-size: 18px;
				font-weight: bold;
				font-family: 'Orienta', sans-serif;
			  """)
        string(name: 'OCP_PREFIX', defaultValue: '', description: 'Name of ocp cluster you want to build')
        string(name: 'OCP_VERSION', defaultValue: '', description: 'Build version to install the cluster.')
        choice(choices: ['x86_64','aarch64', 's390x', 'ppc64le', 'multi', 'multi-aarch64','multi-x86_64','multi-ppc64le', 'multi-s390x'], name: 'ARCH_TYPE', description: '''Type of installation''')
        separator(name: "BUILD_FLEXY_FROM_PROFILE", sectionHeader: "Build Flexy From Profile", sectionHeaderStyle: """
				font-size: 18px;
				font-weight: bold;
				font-family: 'Orienta', sans-serif;
			  """)
        string(name: 'CI_PROFILE', defaultValue: '', description: 'Name of ci profile to build for the cluster you want to build')
        choice(choices: ['extra-small','small','medium','large'], name: 'PROFILE_SCALE_SIZE', description: 'Size of cluster to scale to; will be ignored if SCALE_UP is set')
        separator(name: "BUILD_FLEXY", sectionHeader: "Build Flexy Parameters", sectionHeaderStyle: """
				font-size: 18px;
				font-weight: bold;
				font-family: 'Orienta', sans-serif;
			""")
        choice(choices: ['','aws', 'azure', 'gcp', 'osp', 'alicloud', 'ibmcloud', 'vsphere', 'ash'], name: 'CLOUD_TYPE', description: '''Cloud type (As seen on https://gitlab.cee.redhat.com/aosqe/flexy-templates/-/tree/master/functionality-testing/aos-4_9, after ""-on-") <br/>
        Will be ignored if BUILD_NUMBER is set''')
        choice(choices: ['','ovn', 'sdn'], name: 'NETWORK_TYPE', description: 'Network type, will be ignored if BUILD_NUMBER is set')
        choice(choices: ['','ipi', 'upi', 'sno'], name: 'INSTALL_TYPE', description: '''Type of installation (set to SNO for sno cluster type),  <br/>
        will be ignored if BUILD_NUMBER is set''')
        string(name: 'MASTER_COUNT', defaultValue: '3', description: 'Number of master nodes in your cluster to create.')
        string(name: "WORKER_COUNT", defaultValue: '3', description: 'Number of worker nodes in your cluster to create.')
        string(name:'JENKINS_AGENT_LABEL',defaultValue:'oc420',description:
        '''
        scale-ci-static: for static agent that is specific to scale-ci, useful when the jenkins dynamic agent isn't stable<br>
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
        choice(choices: ['openshift-qe','openshift-qe-lrc'], name: 'ACCOUNT', description: ''' This is ONLY for AWS cluster install. For longrun cluster on AWS use 'openshift-qe-lrc'.<br>
            The is not applicable if CI_PROFILE is used.''')
        string(name: "CI_PROFILES_URL",defaultValue: "https://gitlab.cee.redhat.com/aosqe/ci-profiles.git/",description:"Owner of ci-profiles repo to checkout, will look at folder 'scale-ci/\${major_v}.\${minor_v}'")
        string(name: "CI_PROFILES_REPO_BRANCH", defaultValue: "master", description: "Branch of ci-profiles repo to checkout" )
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
                    def install_type_custom = params.INSTALL_TYPE
                    def custom_cloud_type = params.CLOUD_TYPE
                    def custom_jenkins_label = JENKINS_AGENT_LABEL
                    VERSION = params.OCP_VERSION
                    println "${VERSION}"
                    def version_list = VERSION.tokenize(".")
                    println "version ${version_list}"
                    def major_v = version_list[0]
                    def minor_v = version_list[1]
                    def extra_launcher_vars = ''
                    println "major ${major_v} minor ${minor_v}"
                    def var_loc = ""
                    if(params.CI_PROFILE != "") {
                        installData = readYaml(file: "local-ci-profiles/scale-ci/${major_v}.${minor_v}/${params.CI_PROFILE}.install.yaml")
                        installData.install.flexy.each { env.setProperty(it.key, it.value) }

                        for (data in installData) {
                            println "in ${data.key}"
                            if (data.key == "scale" ) {
                                println "in ${data.value}"
                                data.value.get(params.PROFILE_SCALE_SIZE).each { env.setProperty(it.key, it.value) }
                                break
                            }
                        }
                        var_loc = env.VARIABLES_LOCATION
                        if (env.EXTRA_LAUNCHER_VARS != null ) {
                            extra_launcher_vars = env.EXTRA_LAUNCHER_VARS + '\n'
                        }
                        println "extra lanch vars ${extra_launcher_vars}"
                        println "env scale ${env.SCALE_UP}"

                        if (env.BUSHSLICER_CONFIG != null ) {
                            bushslicer_config = env.BUSHSLICER_CONFIG
                        }

                        install_type_desc = "${params.CI_PROFILE}"
                    }
                    else {
                        def network_ending = ""

                        if (params.CLOUD_TYPE == "vsphere") {
                             network_ending = "-vmc7"
                        }
                        if (params.NETWORK_TYPE != "sdn") {
                         if (params.CLOUD_TYPE == "alicloud") {
                             network_ending = "-fips-${params.NETWORK_TYPE}-ci"
                         } else if (params.CLOUD_TYPE != "ash" ) {
                            network_ending += "-${params.NETWORK_TYPE}"
                         }
                        }
                        def worker_type = ""
                        if (params.CLOUD_TYPE == "aws") {
                            if (params.INSTALL_TYPE == "sno") {
                                extra_launcher_vars = "master_worker_AllInOne: 'true'\nnum_masters: 1\nnum_workers: 0\nvm_type: 'm5.4xlarge'\n"
                                install_type_custom = "ipi"
                            } else {
                            extra_launcher_vars = "vm_type_workers: 'm5.xlarge'\nnum_workers: " + WORKER_COUNT + "\nnum_masters: " + MASTER_COUNT + "\n"
                            }
                            if (params.ACCOUNT == "openshift-qe-lrc") {
                                bushslicer_config ='''
services:
  AWS-CI:
    install_base_domain: qe-lrc.devcluster.openshift.com
    awscred: config/credentials/lrc/.awscred
    host_opts:
      ssh_private_key: config/keys/openshift-qe.pem
    config_opts:
      region: us-east-2
                            '''
                            }
                        }
                        else if (params.CLOUD_TYPE == "azure") {
                            extra_launcher_vars = "vm_type_workers: 'Standard_D8s_v3'\nregion: centralus\nnum_workers: " + WORKER_COUNT + "\nnum_masters: " + MASTER_COUNT + "\n"
                        }
                        else if (params.CLOUD_TYPE == "gcp") {
                            extra_launcher_vars = "vm_type_workers: 'n1-standard-4'\nnum_workers: " + WORKER_COUNT + "\nnum_masters: " + MASTER_COUNT + "\n"
                            if (params.NETWORK_TYPE != "sdn") {
                             network_ending = network_ending + "-ci"
                            }
                        }
                        else if (params.CLOUD_TYPE == "osp") {
                            extra_launcher_vars = "vm_type_workers: 'ci.m1.xlarge'\nnum_workers: " + WORKER_COUNT + "\nnum_masters: " + MASTER_COUNT + "\n"
                        }
                        else if (params.CLOUD_TYPE == "alicloud") {

                            extra_launcher_vars = "vm_type_workers: 'ecs.g6.xlarge'\nnum_workers: " + WORKER_COUNT + "\nnum_masters: " + MASTER_COUNT + "\n"
                        }
                        else if (params.CLOUD_TYPE == "ibmcloud") {
                            extra_launcher_vars = "vm_type_workers: 'bx2d-4x16'\nregion: 'jp-tok'\nnum_workers: " + WORKER_COUNT + "\nnum_masters: " + MASTER_COUNT + "\n"
                        }
                        else if (params.CLOUD_TYPE == "vsphere") {
                            extra_launcher_vars = " num_workers: " + WORKER_COUNT + "\nnum_masters: " + MASTER_COUNT + "\n"
                        } else if (params.CLOUD_TYPE == "ash") {
                            custom_cloud_type = "azure"
                            extra_launcher_vars = " num_workers: " + WORKER_COUNT + "\nnum_masters: " + MASTER_COUNT + "\n"
                            if (params.NETWORK_TYPE != "sdn") {
                            extra_launcher_vars += 'networkType: "OVNKubernetes"\n'
                            }
                            network_ending = "-ash_wwt"
                            custom_jenkins_label = "fedora-installer-wwt"
                        }
                        var_loc = "private-templates/functionality-testing/aos-${major_v}_${minor_v}/${install_type_custom}-on-${custom_cloud_type}/versioned-installer${network_ending}"

                        install_type_desc = "${install_type_custom} ${custom_cloud_type} ${params.NETWORK_TYPE}"
                    }
                    def version_string=""
                    // z stream and ec builds are on quay
                    def registry = "quay.io/openshift-release-dev/ocp-release"
                    // nightly build is on registery.ci.openshift.org
                    if (VERSION.contains('nightly'))
                    {
                        if (params.CI_PROFILE.contains('ARM'))
                        {
                            registry = "registry.ci.openshift.org/ocp-arm64/release-arm64"
                        }
                        else
                        {
                            registry =  "registry.ci.openshift.org/ocp/release"
                        }
                        
                    }

                    if (registry.contains('quay')) {
                      version_string = "${registry}:${VERSION}-${ARCH_TYPE}"
                    } else {
                      version_string = "${registry}:${VERSION}"
                    }
                    

                    install = build job:"ocp-common/Flexy-install", propagate: false, parameters:[
                        string(name: "INSTANCE_NAME_PREFIX", value: OCP_PREFIX),
                        string(name: "VARIABLES_LOCATION", value: "${var_loc}"),
                        string(name: "JENKINS_AGENT_LABEL", value: custom_jenkins_label),
                        text(name: "LAUNCHER_VARS", value: "${extra_launcher_vars}installer_payload_image: '${version_string}'"),
                        text(name: "BUSHSLICER_CONFIG", value: "${bushslicer_config}")
                    ]
                    currentBuild.result =  install.result
                    FLEXY_BUILD_NUMBER = install.number.toString()
                    if( install.result.toString()  != "SUCCESS") {
                        println "installation failed"
                        status = "Install failed"

                    }
                }
            }
        }
    }
    post {
        always {
            script {
                currentBuild.description = """
                {
                    "INSTALLER_TYPE": "$install_type_desc",
                    "FLEXY_BUILD_NUMBER": "$FLEXY_BUILD_NUMBER"
                }
                """
            }
        }
    }
}
