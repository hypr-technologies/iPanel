#!/bin/bash
action=$1
panel_path="/www/server/panel" # 面板路径
webserver_bin="$panel_path/webserver/sbin/webserver"  # nginx二进制文件
webserver_conf="$panel_path/webserver/conf/webserver.conf" # nginx配置文件
webserver_pid="$panel_path/webserver/logs/webserver.pid" # nginx pid文件


PID=0



get_pid() {
    if [ ! -f "$webserver_pid" ]; then
        PID=0
    else
        PID=$(cat $webserver_pid)
        if [ "$PID" == "" ]; then
            PID=0
        else
            PID=$(ps aux | grep "$PID" | grep -v grep | awk '{print $2}')
            PID_11=$(ps aux | grep "$webserver_bin" | grep -v grep | awk '{print $2}')
            if [ "$PID" != "$PID_11" ]; then
                PID=0
            fi
        fi
    fi

    PID=$(ps aux | grep "$webserver_bin" | grep -v grep | awk '{print $2}')
    if [ -z "$PID" ]; then
          PID=0
    else
      PID="$PID"
    fi

    if [ -z "$PID" ]; then
        PID=0
    fi
}

validate_server_files() {
    if [ ! -f "$webserver_conf" ]; then
        echo "aaPanel web server configuration not found: $webserver_conf"
        exit 1
    fi

    if [ ! -f "$webserver_bin" ]; then
        echo "aaPanel web server binary not found: $webserver_bin"
        exit 1
    fi
}

start() {
    validate_server_files
    get_pid
    
    if [ $PID -gt 0 ]; then
        echo "aaPanel web server is already running with PID ($PID)"
        exit 1
    fi

    echo -n "Starting aaPanel web server..."
    if [ -f "$webserver_pid" ]; then
        rm -f $webserver_pid
    fi
    chmod 700 $webserver_bin
    $webserver_bin -c $webserver_conf
    if [ $? -ne 0 ]; then
        echo "Failed to start aaPanel web server"
        exit 1
    fi

    echo " Started"
}

stop() {
    validate_server_files
    get_pid
    if [ $PID -eq 0 ]; then
        echo "aaPanel web server is not running"
        exit 1
    fi

    echo -n "Stopping aaPanel web server..."
    $webserver_bin -c $webserver_conf -s stop
    
    pids=$(lsof -c webserver|grep LISTEN|awk '{print $2}'|sort -u)
    for pid in $pids; do
        kill -9 $pid
    done

    pids=$(ps aux | grep "$webserver_bin" | grep -v grep | awk '{print $2}')
    for pid in $pids; do
        kill -9 $pid
        child_process=1
    done
    if [ "$child_process" = 1 ]; then
        if [ -f /www/server/panel/data/port.pl ]; then
            kill -9 $(lsof -t -i:$(cat /www/server/panel/data/port.pl) -sTCP:LISTEN)
        fi
    fi

    echo " Stopped"
}

restart() {
    validate_server_files
    get_pid
    echo -n "Restarting aaPanel web server..."
    if [ $PID -eq 0 ]; then
        $webserver_bin -c $webserver_conf
    else
        $webserver_bin -c $webserver_conf -s reopen
    fi

    if [ $? -ne 0 ]; then
        echo "Failed to restart aaPanel web server"
        exit 1
    fi

    echo " Restarted"
}

status() {
    validate_server_files
    get_pid
    if [ $PID -eq 0 ]; then
        echo "aaPanel web server is not running"
    else
        cmdline=/proc/$PID/cmdline
        if [ ! -f $cmdline ]; then
            echo "aaPanel web server is not running"
            rm -f $webserver_pid
            exit 1
        fi
        echo "aaPanel web server is running with PID ($PID)"
    fi
}

reload() {
    validate_server_files
    get_pid
    if [ $PID -eq 0 ]; then
        echo "aaPanel web server is not running"
        exit 1
    fi

    echo -n "Reloading aaPanel web server..."
    $webserver_bin -c $webserver_conf -s reload
    if [ $? -ne 0 ]; then
        echo "Failed to reload aaPanel web server"
        exit 1
    fi
    echo " Reloaded"
}

configtest() {
    validate_server_files
    # 检查配置文件正确性，检查程序自动输出检查结果
    $webserver_bin -c $webserver_conf -t

}

download() {
    tip_file=$panel_path/data/download.pl
    if [ -f $tip_file ]; then
        echo "aaPanel web server binary has been downloaded"
        exit 1
    fi

    # 标记已下载
    echo "1" > $tip_file

    # 获取machine
    machine=$(uname -m)
    zip_file=$panel_path/data/webserver-$machine.zip
    wget -O $zip_file https://github.com/hypr-technologies/iPanel/releases/latest/download/webserver/webserver-$machine.zip
    if [ $? -ne 0 ]; then
        echo "Failed to download aaPanel web server binary"
        rm -f $zip_file
        exit 1
    fi

    # 验证文件hash
    hash256=$(sha256sum $zip_file | awk '{print $1}')
    cloud_hash256=$(wget -q -O - https://github.com/hypr-technologies/iPanel/releases/latest/download/webserver/webserver-$machine.txt)
    if [ "$hash256" != "$cloud_hash256" ]; then
        echo "Failed to verify aaPanel web server binary"
        rm -f $zip_file
        exit 1
    fi

    # 解压文件
    unzip -o $zip_file -d $panel_path/
    if [ ! -f $webserver_bin ]; then
        echo "Failed to extract aaPanel web server binary"
        rm -f $zip_file
        exit 1
    fi

    # 删除临时文件
    rm -f $zip_file
    # 设置权限
    chmod 700 $webserver_bin
    echo "aaPanel web server binary has been downloaded"
    bash /www/server/panel/init.sh reload
}


case "$action" in
    start)
        start
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    reload)
        reload
        ;;
    configtest)
        configtest
        ;;
    test)
        configtest
        ;;
    download)
        download
        ;;
    *)
        echo "Usage: $0 {start|stop|restart|status|reload|configtest|test|download}"
        exit 1
        ;;
esac


