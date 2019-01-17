#!/bin/bash

export PATH=".:$HOME:$PATH"

declare baseName=$(basename $0)
declare currentTime=$(date +%Y%m%d_%H%M%S)
#declare WORK_PATH="${HOME}/scrapyGranja"
declare WORK_PATH="."
declare logFilePath="${WORK_PATH}/log/${baseName}-${currentTime}.log"
declare PYTHON="python3"

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

touch ${logFilePath}
echoInfo "LOG: ${logFilePath}"

BEGIN_RACE=$(cat ${WORK_PATH}/lastRaceId)
PARAM=""
if [ ! -z "${BEGIN_RACE}" ]; then
	PARAM="-a begin=$BEGIN_RACE"
fi
echoInfo "================================================================================"
echoInfo "scrapy crawl granjaRaces ${PARAM}"
/usr/local/bin/scrapy crawl granjaRaces ${PARAM} 2>&1 | tee -a ${logFilePath}

echoInfo "================================================================================"
echoInfo "$PYTHON granjaUpdateStatistics.py"
$PYTHON $WORK_PATH/granjaUpdateStatistics.py 2>&1 | tee -a ${logFilePath}

# Job is done!
echoInfo "================================================================================"
echoInfo "# Job is done!"
exit 0
