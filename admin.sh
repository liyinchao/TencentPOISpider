#!/bin/bash

if [ $# -lt 1 ];
then
    echo "USAGE: $0 [start | stop | restart]"
    exit 1
fi

NAME=run
PROGRAME=$NAME.py
SHELL=$NAME.sh
COMMAND=$1
PID=`ps -ef|grep $PROGRAME|grep -v $0|grep -v grep|awk '{print $2}'`
SHELLPID=`ps -ef|grep $SHELL|grep -v $0|grep -v grep|awk '{print $2}'`
start(){
        if [ -n "$PID" ];
        then
                echo "$PROGRAME is running, start service faild!"
                exit 1
        fi
        if [ -n "$SHELLPID" ];
        then
                echo "$SHELL is running, start service faild!"
                exit 1
        fi
        nohup python3 $PROGRAME > $NAME.o 2>&1 &
        nohup sh $SHELL > $NAME.s 2>&1 &
}

stop(){
        if [ -n "$SHELLPID" ];
        then
                kill -9 $SHELLPID
        fi
        if [ -n "$PID" ];
        then
                kill -9 $PID
        fi
}

case $COMMAND in
        start)
                start
                echo "$PROGRAME is start!"
                ;;
        stop)
                stop
                echo "$PROGRAME is stop!"
                exit 1
                ;;
        restart)
                stop
                sleep 5
                PID=`ps -ef|grep $PROGRAME|grep -v $0|grep -v grep|awk '{print $2}'`
                SHELLPID=`ps -ef|grep $SHELL|grep -v $0|grep -v grep|awk '{print $2}'`
                start
                echo "$PROGRAME is restart!"
                ;;
        *)
                echo "unknown command!"
                exit 1
esac