#!/bin/bash

# It will take about 15 mins If Kube-apiserver rolling out occurs after upgrade was fnished
kas_rollingout_wait(){
    timeout=60
    internal=5
    t=0
    PROGRESSING=$(oc get co/kube-apiserver --no-headers | awk '{print $4}')
    while [ $t -lt $timeout ] ;do
        if [ "X$PROGRESSING" == "XFalse" ];then
          echo "Kube-apiserver is done progressing"
          break
        fi
        [ "X$PROGRESSING" == "XTrue" ] && break
        sleep $internal
        t=$(( t + internal ))
        PROGRESSING=$(oc get co/kube-apiserver --no-headers | awk '{print $4}')
        echo "kube-apiserver still progressing $PROGRESSING"
    done
    if [ "X$PROGRESSING" == "XTrue" ];then
        echo -e "Kube-apiserver is rolling out ..."
        internal=20
        timeout=900
        while [ $t -lt $timeout ]; do
            [ "X$PROGRESSING" == "XFalse" ] && break
            sleep $internal
            t=$(( t + internal ))
            PROGRESSING=$(oc get co/kube-apiserver --no-headers | awk '{print $4}')
        done
        if [ "X$PROGRESSING" == "XFalse" ];then
            echo -e "#### Kube-apiserver rolling out was completed!"
        else
            echo -e "#### Warning: After waiting, co/kube-apiserver is still in Progressing!"
            echo -e "#### Warning: If this issue happened during 4.3->4.4 upgrade, then probably hit the bug 1931033, detailed in https://issues.redhat.com/browse/OCPQE-3342!"
            echo -e "#### Warning: otherwise, then probably hit the bug https://bugzilla.redhat.com/show_bug.cgi?id=1909600"
        fi
    fi
}


function abnormal_co() {
  echo -e "exit from upgrade loop\n"
  echo -e "**************Post Action after upgrade****************\n"

  post_check1=`oc get node -o wide`
  post_check2=`oc get co`
  echo -e "Post action: #oc get node: ${post_check1}\n\n"
  echo -e "Post action: #oc get co:${post_check2}\n\n"
  echo -e "print detail msg for node(SchedulingDisabled) if exist:\n"
  echo -e "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Abnormal node details~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n"
  if oc get node --no-headers | grep -E 'SchedulingDisabled|NotReady' ; then
                  oc get node --no-headers | grep -E 'SchedulingDisabled|NotReady'| awk '{print $1}'|while read line; do oc describe node $line;done
                  ret1="abnormal"
  fi
  echo -e "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n"
  echo -e "print detail msg for co(AVAILABLE != True or PROGRESSING!=False or DEGRADED!=False or version != target_version) if exist:\n"
  # Check if the kube-apiserver is rolling out after upgrade
  if [ -z "$ret1" ]; then # If master nodes are normal
      kas_rollingout_wait
  fi 

  echo -e "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~Abnormal co details~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n"
  abnormalCO=""
  abnormalCO=$(oc get co -o jsonpath='{range .items[*]}{.metadata.name} {range .status.conditions[*]} {.type}={.status}{end}{"\n"}{end}' | grep -v "openshift-samples" | grep -w -E 'Available=False|Progressing=True|Degraded=True' | awk '{print $1}')
  if [ "X$abnormalCO" != "X" ]; then
      upgrade_pass=False
      quick_diagnosis "$abnormalCO"
      for aco in $abnormalCO; do
          oc describe co $aco
          echo -e "\n~~~~~~~~~~~~~~~~~~~~~~~\n"
      done
  fi
  ret2=`oc get co |sed '1d'|grep -v "openshift-samples"|grep -v "service-catalog-apiserver"|grep -v "service-catalog-controller-manager"|grep -v "True        False         False"|awk '{print $1}'|while read line; do oc describe co $line;done`
  oc get co |sed '1d'|grep -v "openshift-samples"|grep -v ${target_version_prefix}|awk '{print $1}'|while read line; do oc describe co $line;echo -e "\n~~~~~~~~~~~~~~~~~~~~~~~\n";done
  ret3=`oc get co |sed '1d'|grep -v "openshift-samples"|grep -v "service-catalog-apiserver"|grep -v "service-catalog-controller-manager"|grep -v ${target_version_prefix}|awk '{print $1}'|while read line; do oc describe co $line;done`
  echo -e "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n\n"


  # The upgrade itself never finished, do not report this as a post-check failure
  if [ "X$upgrade_completed" == "Xfalse" ]; then
      echo -e "The cluster never reached ${target_version_prefix}, see the upgrade check output above.\n"
      exit 1 # upgrade itself fail
  fi

  if [ -z "$ret1" ] && [ -z "$ret2" ] && [ -z "$ret3" ]; then
      echo -e "post check passed without err.\n"

  else
      python3 -c "import check_upgrade; check_upgrade.pause_machinepool_worker('false')"
      sleep 10
      python3 -c "import check_upgrade; check_upgrade.wait_for_mcp_upgrade(wait_num=120)"
      exit 127 # upgrade itself succ and post-check fail
  fi

}

# Quick diagnosis for abnormal cluster operators
function quick_diagnosis() {
    local abnormal_cos="$1"

    echo -e "~~~~~~~~\n $abnormal_cos \n~~~~~~~~\n"
    abnormal_co_logs=".abnormal_co_logs"
    all_co_logs=".all_co_logs" > "$abnormal_co_logs"
    oc get -o json clusteroperators > "$all_co_logs"
    for co in $abnormal_cos; do
        jq -r --arg co "$co" '.items[] | .metadata.name as $name | select($name == $co).status.conditions[] | .lastTransitionTime + " [" + $name + "] " + .type + " " + .status + " " + (.reason // "-") + " " + (.message // "-")' "$all_co_logs" >> "$abnormal_co_logs"
    done
    echo "#### Quick diagnosis: The first abnormal cluster operator is often the culprit! ####"
    echo "=> Below status and logs for the different conditions of all abnormal cos are sorted by 'lastTransitionTime':"
    # Error-tagging in one single line log
    reg1="Available False"
    reg2="Progressing True"
    reg3="Degraded True"
    reg4="not available"
    sed -i "s/$reg1/-->>$reg1<<--/g;s/$reg2/-->>$reg2<<--/g;s/$reg3/-->>$reg3<<--/g;s/$reg4/-->>$reg4<<--/g;" "$abnormal_co_logs"
    cat "$abnormal_co_logs" | sort
    echo -e "\n--------------------------\n"
    [ -f "$all_co_logs" ] && rm -f "$all_co_logs"
    [ -f "$abnormal_co_logs" ] && rm -f "$abnormal_co_logs"
}


function check_upgrade_version() {

  cur_version=$(oc get clusterversion -o jsonpath='{.items[0].status.desired.version}')
  cur_version_list=(${cur_version//./ })
  target_version_list=(${1//./ })
  index=1
  counter_cur=0
  for cur_version in "${cur_version_list[@]}"
  do
    counter_target=0
    for target_build_v in "${target_version_list[@]}"
    do
      if [[ $counter_cur -eq 1 ]]; then
        if [[ $counter_target -eq 1 ]]; then
          if [[ $cur_version -lt $((target_build_v - 1)) ]]; then
             echo "target build is more than 1 version ahead of current build"
             echo "Please update target version to be increased by 1"
             exit 1
            fi
        fi
      fi
      counter_target=$((counter_target+1))
  done
    counter_cur=$((counter_cur+1))
  done

}

function capture_failed_pods_before_upgrade(){
  #Save the failed job before upgrade and make sure new failed job caused by upgrade,ignore installer, build error
  echo "Capture failed pods before upgrade OCP"
  echo "####################################################################################"
  oc get pods -A| grep -v -E 'Running|Completed|installer|build'| awk '(NF=NF-2) 1'>/tmp/upgrade-before-failed-pods.txt
}

function capture_failed_pods_after_upgrade(){
  #Save the failed job after upgrade and make sure new failed job caused by upgrade
  echo "Capture failed pods after upgrade OCP, No messages means no errors"
  echo "####################################################################################"
  #Adding re-try steps to avoid temp failed pod
  oc get pods -A| grep -v -E 'Running|Completed|installer|build'| awk '(NF=NF-2) 1'>/tmp/upgrade-after-failed-pods.txt
  cat /tmp/upgrade-before-failed-pods.txt /tmp/upgrade-after-failed-pods.txt | sort | uniq -u>/tmp/new-failed-pods.txt
  init_retry=1
  max_retry=30

  while [[ $init_retry -le $max_retry && -s /tmp/new-failed-pods.txt ]]
  do
     oc get pods -A| grep -v -E 'Running|Completed|installer|build'| awk '(NF=NF-2) 1'>/tmp/upgrade-after-failed-pods.txt
     cat /tmp/upgrade-before-failed-pods.txt /tmp/upgrade-after-failed-pods.txt | sort | uniq -u>/tmp/new-failed-pods.txt
     echo -n "."&&sleep 10
     init_retry=$(( $init_retry + 1 ))
  done

  if [ -s /tmp/new-failed-pods.txt ];then

          echo "There are some failed job after upgrade, please check"
          echo "####################################################################################"
          cat /tmp/new-failed-pods.txt
          echo "####################################################################################"
          cat /tmp/new-failed-pods.txt | awk '{print $1"\t"$2}' >/tmp/pods.lst
          total_lines=$(cat /tmp/pods.lst|wc -l)
          init_line=1
          while [ $init_line -le $total_lines ]
          do
                  namespace=$(cat /tmp/pods.lst | sed -n "${init_line}p" | awk '{print $1}')
                  podname=$(cat /tmp/pods.lst | sed -n "${init_line}p" | awk '{print $2}')
                  echo "The detailed failed pods $podname information in $namespace:"
                  echo "------------------------------------------------------------------------------------" 
                  oc describe pod $podname -n $namespace
                  init_line=$(( $init_line + 1 ))
          done
          exit 1
  fi
}
