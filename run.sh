#!/bin/bash

export PATH=".:$HOME:$PATH"

declare baseName=$(basename $0)
declare currentTime=$(date +%Y%m%d_%H%M%S)
declare WORK_PATH="$(dirname $0)"
declare logFilePath="${WORK_PATH}/log/${baseName}-${currentTime}.log"
declare PYTHON="$(which python3)"
declare SCRAPY="$(which scrapy)"

function echoInfo {
	local msg=$1
	local DATETIME=$(date '+%Y-%m-%d %H:%M:%S')
	local logMsg="${DATETIME} INFO [${baseName}] ${msg}"
	echo $logMsg
	[ -f ${logFilePath} ] && echo $logMsg >> ${logFilePath}
	return 0
}

function echoError {
	local msg=$1
	DATETIME=$(date '+%Y-%m-%d %H:%M:%S')
	logMsg="${DATETIME} ERROR [${baseName}] ${msg}"
	echo $logMsg 1>&2
	[ -f ${logFilePath} ] && echo $logMsg >> ${logFilePath}
	return 0
}

# Get ready to work
if [ ! -d "${WORK_PATH}" ]; then
	echoError "Invalid WORK_PATH : ${WORK_PATH}" 1>&2
	exit 1
fi

cd ${WORK_PATH}
mkdir raceResults &>/dev/null
mkdir log &>/dev/null
mkdir backup &>/dev/null

touch ${logFilePath}
echoInfo "LOG: ${logFilePath}"

echoInfo "================================================================================"
echoInfo "7z a ${WORK_PATH}/backup/${currentTime}.7z ${WORK_PATH}/*.sqlite"
7z a ${WORK_PATH}/backup/${currentTime}.7z ${WORK_PATH}/*.sqlite 2>&1 | tee -a ${logFilePath}

PARAM="$*"
echoInfo "================================================================================"
echoInfo "${SCRAPY} crawl granjaRaces ${PARAM}"
$SCRAPY crawl granjaRaces ${PARAM} 2>&1 | tee -a ${logFilePath}

echoInfo "================================================================================"
echoInfo "$PYTHON granjaUpdateStatistics.py"
$PYTHON $WORK_PATH/granjaUpdateStatistics.py 2>&1 | tee -a ${logFilePath}

echoInfo "================================================================================"
dbFile=$(ls *.sqlite)
dbFileName=$(basename ${dbFile})
7z a ${WORK_PATH}/${dbFileName}.7z ${WORK_PATH}/*.sqlite 2>&1 | tee -a ${logFilePath}

msg="UPDATE `date --rfc-3339=seconds`"
echoInfo "================================================================================"
echoInfo "# GIT COMMIT: '${msg}'"
#git commit --amend --all --message="${msg}"
git commit --all --message="${msg}"

echoInfo "================================================================================"
echoInfo "# GIT PUSH"
killall ssh-agent ;eval "$(ssh-agent -s)" && ssh-add ~/.ssh/id_ed25519
git push

# Job is done!
echoInfo "================================================================================"
echoInfo "# Job is done!"
exit 0
