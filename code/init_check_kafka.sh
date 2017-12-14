#!/bin/bash

start() {
  echo "Starting health check service..."
  python /opt/aws/bin/check_kafka.py &
}

stop() {
  echo "Stopping health check service..."
  kill $(ps aux | grep "python /opt/aws/bin/check_kafka.py" | grep -v grep | awk '{print $2}')
}

status() {
  echo "Health check service is running on pid:" $(ps aux | grep "python /opt/aws/bin/check_kafka.py" | grep -v grep | awk '{print $2}')
}

case "$1" in
  start)
    start
    ;;
  stop)
    stop
    ;;
  restart)
    stop
    start
    ;;
  status)
    status
    ;;
  *)
    echo "Usage: $0 {start|stop|restart|status}"
    exit 1
esac

exit 0