#!/bin/bash

# alias chrome
chrome="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
# start headless chrome from the cli
PORT=9222
SLEEP_TIME=10

echo "==============================================="
echo "Starting Chrome in headless mode on port $PORT and as background job"

"$chrome" --headless --remote-debugging-port=$PORT &
CHROME_PID=$!

echo "sleeping script for $SLEEP_TIME to let chrome initialize"
echo "==============================================="

sleep $SLEEP_TIME

echo "==============================================="
echo "Starting the har file generation for sites listed in har-cli.inpu"
echo "Output file is 50-site-2-accesses.har"
echo "==============================================="

let grace=30*1000
let timeout=60*1000

xargs npx chrome-har-capturer --cache --port $PORT --retry 3 --grace $grace --timeout $timeout -o test.har < har-cli.input

kill $CHROME_PID
