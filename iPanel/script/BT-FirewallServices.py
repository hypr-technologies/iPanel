# coding: utf-8
# -------------------------------------------------------------------
# iPanel
# -------------------------------------------------------------------
# Copyright (c) 2014-2099 iPanel(http://www.iPanel.com) All rights reserved.
# -------------------------------------------------------------------

import os
import subprocess
import sys
import threading



def run_cmd(cmd):
    try:
        subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True
    except:
        return False


def load_iptables():
    """
    恢复 iptables 规则
    """
    if run_cmd("iptables -C INPUT -j IN_BT"):
        print("iptables existed")
    else:
        if run_cmd("iptables-restore --noflush < /www/server/panel/data/iptablesdata"):
            print("iptables restored")


def load_ipset():
    """
    恢复 ipset 规则
    """
    if run_cmd("ipset restore < /www/server/panel/data/ipsetdata"):
        print("ipset restored")
    else:
        print("ipset existed")


def save_iptables():
    """
    保存 iptables 规则
    """
    if run_cmd("iptables -C INPUT -j IN_BT"):
        if run_cmd(
                "iptables-save  | grep -E 'IN_BT|OUT_BT|FORWARD_BT|^\*|^COMMIT' | sed 's/^-A INPUT/-I INPUT/; s/^-A OUTPUT/-I OUTPUT/; s/^-A PREROUTING/-I PREROUTING/' > /www/server/panel/data/iptablesdata"):
            print("iptables saved")


def save_ipset():
    """
    保存 ipset 规则
    """
    if run_cmd("ipset save | grep -E '_bt_' > /www/server/panel/data/ipsetdata"):
        print("ipset saved")


def dbus_listener():
    if not os.path.exists("/sbin/firewalld"):
        print("is not Firewalld")
        return

    cmd = [
        "dbus-monitor",
        "--system",
        "type='signal',path='/org/fedoraproject/FirewallD1',interface='org.fedoraproject.FirewallD1',member='Reloaded'",
        "type='signal',interface='org.freedesktop.DBus',member='NameOwnerChanged',arg0='org.fedoraproject.FirewallD1',arg1=''"
    ]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    while True:
        line = process.stdout.readline().strip()

        if not line:
            break
        if "signal" in line:
            if "member=Reloaded" in line:
                print("firewalld reload...")
                load_iptables()
            elif "member=NameOwnerChanged" in line:
                print("firewalld restart...")
                threading.Timer(3, load_iptables).start()


def main():
    import time
    if len(sys.argv) < 2:
        print("command：start|reload|stop|save")
        sys.exit(1)

    command = sys.argv[1]
    if command == "start":
        load_ipset()
        load_iptables()
        listener_thread = threading.Thread(target=dbus_listener)
        listener_thread.daemon = True
        listener_thread.start()
        while True:
            time.sleep(1)
    elif command == "reload":
        save_ipset()
        save_iptables()
        load_ipset()
        load_iptables()
    elif command == "stop":
        save_ipset()
        save_iptables()
    elif command == "save":
        save_ipset()
        save_iptables()
    elif command == "saveiptables":
        save_iptables()
    elif command == "saveipset":
        save_ipset()
    elif command == "loadiptables":
        load_iptables()
    elif command == "loadipset":
        load_ipset()
    elif command == "reloadiptables":
        save_iptables()
        load_iptables()
    elif command == "reloadipset":
        save_ipset()
        load_ipset()
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
