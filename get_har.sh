#!/bin/bash

SCRIPTDIR="`dirname $0`"

cd $SCRIPTDIR

if [ ! "$3" ]
then
  echo "Missing at least one of the arguments"
  echo "Usage: ./get_har.sh <Chrome Profile Name> <PORT> <TIMEINTERVAL>"
  exit 1
fi

# alias chrome
chrome="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# start headless chrome from the cli
SLEEP_TIME=10
PROFILE=$1
PORT=$2
TIMEINTERVAL=$3

echo "==============================================="
echo "Starting Chrome in headless mode on port $PORT and as background job"

"$chrome" --headless --remote-debugging-port=$PORT --profile-directory="$PROFILE" &
CHROME_PID=$!

echo "sleeping script for $SLEEP_TIME to let chrome initialize"
echo "==============================================="

sleep $SLEEP_TIME

now=$(date +"%Y-%m-%d_%H%M%S")
OUTPUT_HAR="data/50-site-metrics-${TIMEINTERVAL}-${now}.har"

echo "==============================================="
echo "Starting the har file generation for sites listed in inputs/new_sites.input"
echo "Output file is $OUTPUT_HAR"
echo "==============================================="

let grace=30*1000
let timeout=60*1000

export PATH="/usr/local/bin:${PATH}"

xargs /usr/local/bin/npx chrome-har-capturer --cache --port $PORT --retry 3 --grace $grace --timeout $timeout -o $OUTPUT_HAR < inputs/new_sites.input

kill $CHROME_PID
