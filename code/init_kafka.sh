#!/bin/bash

start() {
  echo "Starting kafka service..."
  #let MEM_TOTAL=`free -m | grep 'Mem:' | awk '{print $2}'`
  #let MEM_KAFKA=MEM_TOTAL/2
  MEM_KAFKA=512
  MEM_UNIT='M'
  export KAFKA_HEAP_OPTS="-Xmx$MEM_KAFKA$MEM_UNIT -Xms$MEM_KAFKA$MEM_UNIT"
  export JAVA_HOME=/usr/lib/jvm/jre-1.8.0
  export JMX_PORT=9999
  cd /opt/{{KafkaDir}}
  bin/kafka-server-start.sh config/server.properties &
}

stop() {
  echo "Stopping kafka service..."
  kill $(ps aux | grep "server.properties" | grep -v grep | awk '{print $2}')
}

status() {
  echo "Kafka service is running on pid:" $(ps aux | grep "server.properties" | grep -v grep | awk '{print $2}')
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