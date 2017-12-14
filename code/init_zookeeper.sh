#!/bin/bash

start() {
  echo "Starting zookeeper service..."
  cd /opt/{{ZookDir}}
  bin/zkServer.sh start
}

stop() {
  echo "Stopping zookeeper service..."
  cd /opt/{{ZookDir}}
  bin/zkServer.sh stop
}

status() {
  echo "Zookeeper service is running on pid:" $(ps aux | grep "zoo.cfg" | grep -v grep | awk '{print $2}')
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