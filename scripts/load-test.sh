#!/bin/bash
# Simple Load Test to trigger HPA
URL=$1
CONCURRENCY=${2:-10}
DURATION=${3:-60}

if [ -z "$URL" ]; then
    echo "Usage: ./load-test.sh <URL> [CONCURRENCY] [DURATION]"
    echo "Example: ./load-test.sh http://api.1.2.3.4.nip.io/api/v1/stores"
    exit 1
fi

echo "🔥 Bombarding $URL for $DURATION seconds with $CONCURRENCY parallel requests..."

# Use 'ab' (Apache Benchmark) if available, otherwise fallback to a loop
if command -v ab &> /dev/null; then
    ab -n 100000 -c $CONCURRENCY -t $DURATION $URL
else
    echo "Apache Benchmark (ab) not found. Falling back to bash loop..."
    for i in $(seq 1 $CONCURRENCY); do
        while true; do
            curl -s -o /dev/null $URL
        done &
    done
    sleep $DURATION
    kill $(jobs -p)
fi

echo "✅ Load test complete."
