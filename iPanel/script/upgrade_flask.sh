#!/bin/bash
PATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin
export PATH

is_flask1=$(/www/server/panel/pyenv/bin/pip3 list|grep 'Flask'|grep ' 1.')
if [ "${is_flask1}" = "" ];then
    exit;
fi

/www/server/panel/pyenv/bin/pip3 install flask -U
/www/server/panel/pyenv/bin/pip3 install flask-sock
/www/server/panel/pyenv/bin/pip3 install simple-websocket==0.10.0 -I

rm -f /www/server/panel/script/upgrade_flask.sh
bash /www/server/panel/init.sh reload

