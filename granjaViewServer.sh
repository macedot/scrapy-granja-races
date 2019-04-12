#!/bin/bash

declare PYTHON="python3"

runningPid=0
function finish {
	isRunning=$(kill -0 ${runningPid} 2>&1)
	if [ ! -z ${isRunning} ]; then
		kill ${runningPid} 2>/dev/null
		sleep 1
		isRunning=$(kill -0 ${runningPid} 2>&1)
		if [ ! -z ${isRunning} ]; then
			kill -9 ${runningPid} 2>/dev/null
		fi
	fi
}

#trap finish EXIT SIGINT SIGTERM

export PATH=".:$HOME:$PATH"

# Get ready to work
GRANJA_WORK_PATH="${HOME}/scrapyGranja"
if [ ! -d "${GRANJA_WORK_PATH}" ]; then
	echo "Invalid GRANJA_WORK_PATH : ${GRANJA_WORK_PATH}" 1>&2
fi

granjaView_py="${GRANJA_WORK_PATH}/granjaView.py"
if [ ! -f "${granjaView_py}" ]; then
	echo "Invalid granjaView_py : ${granjaView_py}" 1>&2
fi

while(true); do
	$PYTHON ${granjaView_py} 2>&1 | tee -a log.txt
	sleep 3
done

# Job is done!
exit 0
