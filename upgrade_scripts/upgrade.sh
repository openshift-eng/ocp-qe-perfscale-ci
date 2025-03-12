#!/bin/bash
source ./common.sh
upgrade_pass=True

if [ "$#" -lt 1 ]; then
  echo "syntax: $0 <target_build_version> "
  echo "example:"
  echo "./upgrade.sh 4.8.1"
  exit 1
fi

taget_build_arr=(${1//,/ })  #target_build maybe a list "4.1.22,4.1.0-0.nightly-2019-11-04-224442,4.2.2"

enable_force=true
scale=false
eus=false
eus_channel="fast"
maxUnavail=1
#optional parameters
while [[ $# -gt 1 ]]
do
key="$1"
echo "key $key"

case $key in
    -f|--force)
    enable_force=$2
    shift # past argument
    shift # past value
    ;;
    -s|--scale)
    scale=$2
    shift # past argument
    shift # past value
    ;;
    -e|--eus)
    eus=$2
    shift # past argument
    shift # past value
    ;;
   -c|--chn)
    eus_channel=$2
    shift # past argument
    shift # past value
    ;;
    -u|--maxunavil)
    maxUnavail=$2
    shift # past argument
    shift # past value
    ;;
    *)    # unknown option
    #need to get past file
    shift # past arg
    ;;
esac
done

echo "force $enable_force"
echo "scale $scale"
echo "target version $taget_build_arr"
echo "eus $eus"
#wait 120s for all pod get ready
sleep 120
#capture_failed_pods_before_upgrade
python3 -c "import check_upgrade; check_upgrade.set_max_unavailable($maxUnavail)"

#Get the node architecture type
image_stream_tag=$(oc get istag cli-artifacts:latest -n openshift -o yaml)
if echo "$image_stream_tag" | grep -q "architecture: amd64" && echo "$image_stream_tag" | grep -q "architecture: arm64"; then
    node_arch="multi"
else
    node_name=$(oc get node | grep master| head -1| awk '{print $1}')
    node_arch=$(oc get node $node_name -ojsonpath='{.status.nodeInfo.architecture}')
fi


if [[ "X$node_arch" == "Xarm64" ]];then
   arch_prefix=aarch64
   release_path=ocp-arm64/release-arm64
elif [[ "X$node_arch" == "Xmulti" ]];then
   arch_prefix=multi
   release_path=ocp/release
else
   arch_prefix=x86_64
   release_path=ocp/release
fi


for target_build in "${taget_build_arr[@]}"
do
  check_upgrade_version $target_build
  echo ${target_build} |grep nightly >/dev/null 2>&1
 
  if [ $? -eq 0 ]
  then
      echo "target version nightly "
      target_version_prefix=${target_build}   #night build:4.2.0-0.nightly-2020-02-03-234322
      echo node_arch is $node_arch
      #Get target ocp image sha256 values
      #The node arch type is arm64 amd64 and multi
      if [[ "X$node_arch" == "Xmulti" ]]; then
	  image_path=$( echo $target_build | cut -d- -f1-3)
	  target_sha=$(curl -s https://multi.ocp.releases.ci.openshift.org/releasestream/${image_path}/release/${target_build} |grep PullSpec | awk -F'@' '{print $2}' | awk -F'<' '{print $1}')
      else
          target_sha=$(python3 -c "import check_upgrade; check_upgrade.get_sha_url('https://${node_arch}.ocp.releases.ci.openshift.org/graph','$target_version_prefix')")
      fi

      if [[ $target_sha == "" ]]; then
          echo "Could not find target version in 'https://${node_arch}.ocp.releases.ci.openshift.org/graph'"
          exit 1
      fi

      if [[ "X$eus" == "Xtrue" ]]; then
        python3 -c "import check_upgrade; check_upgrade.pause_machinepool_worker('true')"
        #Check if the worker node is arm64 or x86_64
        if [ "X$enable_force" == "Xtrue" ];then
           upgrade_line="oc adm upgrade --to-image $target_sha --force --allow-explicit-upgrade"
        else
           upgrade_line="oc adm upgrade --to-image $target_sha --allow-explicit-upgrade"
        fi
      elif [[ "X$node_arch" == "Xmulti" ]]; then
           upgrade_line="oc adm upgrade --to-image quay.io/openshift-release-dev/ocp-release-nightly@${target_sha} --force --allow-explicit-upgrade"
      else
        if [ "X$enable_force" == "Xtrue" ];then
           upgrade_line="oc adm upgrade --to-image registry.ci.openshift.org/$release_path:$target_version_prefix --force --allow-explicit-upgrade"
        else
           upgrade_line="oc adm upgrade --to-image registry.ci.openshift.org/$release_path:$target_version_prefix --allow-explicit-upgrade"
        fi
      fi
  else
    echo "target version quay "
    target_version_prefix=$(echo ${target_build}) #4.3.0-x86_64 ==> we got "Cluster version is 4.3.0"
    if [[ "X$eus" == "Xtrue" ]]; then
        python3 -c "import check_upgrade; check_upgrade.set_upstream_channel('$eus_channel','$target_version_prefix')"
        python3 -c "import check_upgrade; check_upgrade.pause_machinepool_worker('true')"
        found_version=$(python3 -c "import check_upgrade; check_upgrade.verify_version_in_channel_list('$target_version_prefix')")
        if [[ "X$found_version" == "XERROR" ]]; then
          echo "Could not find target version $target_version_prefix in 'oc adm upgrade' recommended paths"
          exit 1
        fi
        if [ "X$enable_force" == "Xtrue" ];then
          upgrade_line="oc adm upgrade --to $target_version_prefix --force"
        else
          upgrade_line="oc adm upgrade --to $target_version_prefix"
        fi
    else
      if [ "X$enable_force" == "Xtrue" ];then
        upgrade_line="oc adm upgrade --to-image quay.io/openshift-release-dev/ocp-release:${target_version_prefix}-${arch_prefix} --force --allow-explicit-upgrade"
      else
        upgrade_line="oc adm upgrade --to-image quay.io/openshift-release-dev/ocp-release:${target_version_prefix}-${arch_prefix} --allow-explicit-upgrade"
      fi
    fi
  fi

  echo "target version $target_version_prefix"
  echo "upgrade line $upgrade_line"
  echo $upgrade_line
  SECONDS=0
  CONSOLE_LAST_LINE="$($upgrade_line)"
  echo $CONSOLE_LAST_LINE
  export UPGRADE_WAIT_NUM=${UPGRADE_WAIT_NUM:-300}
  export PYTHONUNBUFFERED=1
  echo "Specify UPGRADE_WAIT_NUM is $UPGRADE_WAIT_NUM"
  python3 -c "import check_upgrade; check_upgrade.check_upgrade('$target_version_prefix',wait_num=$UPGRADE_WAIT_NUM)"
  duration=$SECONDS
  echo "$(($duration / 60)) minutes and $(($duration % 60)) seconds elapsed."
  sleep 30
  abnormal_co
  sleep 1
done

if [[ "X$eus" == "Xtrue" ]]; then
python3 -c "import check_upgrade; check_upgrade.pause_machinepool_worker('false')"
sleep 10
python3 -c "import check_upgrade; check_upgrade.wait_for_mcp_upgrade()"

fi

if [ "X$scale" == "Xtrue" ]; then
  #add machinesets
  machine_name=$(oc get machineset -n openshift-machine-api -o name --no-headers | grep "^.*$" -m1)
  #get first machine replica count
  #add 1 to replica count
  machine_replicas=$(oc get $machine_name -n openshift-machine-api -o jsonpath={.status.replicas})
  machine_replicas=$((machine_replicas + 1))
  oc scale --replicas=$machine_replicas -n openshift-machine-api $machine_name
  python3 -c "import check_upgrade; check_upgrade.wait_for_replicas('$machine_replicas','$machine_name')"
fi
#wait 120s for all pod get ready
sleep 120
#capture_failed_pods_after_upgrade
exit 0 #upgrade succ and post-check succ
