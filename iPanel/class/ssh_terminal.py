# coding: utf-8
# +-------------------------------------------------------------------
# | iPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2025 Hypr Technologies
# | Licensed under the MIT License
# | https://github.com/hyprtech/ipanel/blob/main/LICENSE
# +-------------------------------------------------------------------
# | Based on original work by iPanel (2015-2099)
# | Original Author: hwliang <hwl@hypr.local>
# +-------------------------------------------------------------------
import json
import time
import os
import sys
import socket
import threading
import re


if not 'class/' in sys.path:
    sys.path.insert(0,'class/')
from io import BytesIO, StringIO

def returnMsg(status,msg,value=None):
    if value:
        msg = public.get_msg_gettext(msg,value)
    return {'status':status,'msg':msg}

import public

class ssh_terminal:
    _panel_path = '/www/server/panel'
    _save_path = _panel_path + '/config/ssh_info/'
    _host = None
    _port = 22
    _user = None
    _pass = None
    _pkey = None
    _ws = None
    _ssh = None
    _last_cmd = ""
    _last_cmd_tip = 0
    _log_type = public.lang("iPanel terminal")
    _history_len = 0
    _client = ""
    _rep_ssh_config = False
    _sshd_config_backup = None
    _rep_ssh_service = False
    _tp = None
    _old_conf = None
    _debug_file = 'logs/terminal.log'
    _s_code = None
    _last_num = 0
    _key_passwd = None
    _video_addr = ""
    _host_row_id = ""

    def __init__(self):
        # 创建jp_login_record表记录ssh登录记录
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'ssh_login_record')).count():
            public.M('').execute('''CREATE TABLE ssh_login_record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                addr TEXT,
                server_ip TEXT,
                user_agent TEXT,
                ssh_user TEXT,
                login_time INTEGER DEFAULT 0,
                close_time INTEGER DEFAULT 0,
                video_addr TEXT);''')
            public.M('').execute('CREATE INDEX ssh_login_record ON ssh_login_record (addr);')
        self.time = time.time()

    def record(self, rtype, data):
        if os.path.exists(public.get_panel_path() + "/data/open_ssh_login.pl") and  self._video_addr:
            path=self._video_addr
            if rtype == 'header':
                with open(path, 'w') as fw:
                    fw.write(json.dumps(data) + '\n')
                    return True
            else:
                with open(path, 'r') as fr:
                    content = json.loads(fr.read())
                    stdout = content["stdout"]
                atime = time.time()
                iodata = [atime - self.time, data]
                stdout.append(iodata)
                content["stdout"] = stdout
                with open(path, 'w') as fw:
                    fw.write(json.dumps(content) + '\n')
                    self.time = atime
                    return True
        return False

    def connect(self):
        '''
            @name 连接服务器
            @author hwliang<2020-08-07>
            @return dict{
                status: bool 状态
                msg: string 详情
            }
        '''
        if not self._host: return public.return_msg_gettext(False, public.lang("Wrong connection address"))

        if not self._user: self._user = 'root'
        if not self._port: self._port = 22
        self.is_local()

        if self._host in ['127.0.0.1','localhost']:
            self._port = public.get_ssh_port()
            self.set_sshd_config(True)

        num = 0
        while num < 5:
            num +=1
            try:
                self.debug(public.lang('Reconnection attempts:{}',num))
                if self._rep_ssh_config: time.sleep(0.1)
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2 + num)
                sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8192)
                sock.connect((self._host, self._port))
                break
            except Exception as e:
                if num == 5:
                    self.set_sshd_config(True)
                    self.debug(public.lang('Retry connection failed, {}',e))
                    if self._host in ['127.0.0.1','localhost']:
                        return returnMsg(False,'Connection failure: {}',("Authentication failed ," + self._user + "@" + self._host + ":" +str(self._port),))
                    return returnMsg(False,'Connection failure: {}',(self._host,self._port))
                else:
                    time.sleep(0.2)


        import paramiko

        self._tp = paramiko.Transport(sock)

        try:
            self._tp.start_client()
            if not self._pass and not self._pkey:
                self.set_sshd_config(True)
                return public.return_msg_gettext(False,'Password or private key cannot both be empty: {}:{}',(self._host,str(self._port)))
            self._tp.banner_timeout=60
            if self._pkey:
                self.debug(public.lang("Authenticating private key"))
                if sys.version_info[0] == 2:
                    try:
                        self._pkey = self._pkey.encode('utf-8')
                    except:
                        pass
                    p_file = BytesIO(self._pkey)
                else:
                    p_file = StringIO(self._pkey)

                try:
                    if self._key_passwd:
                        pkey = paramiko.RSAKey.from_private_key(p_file,password=self._key_passwd)
                    else:
                        pkey = paramiko.RSAKey.from_private_key(p_file)
                    self.debug("尝试使用RSA私钥认证")
                except Exception as ex:
                    try:
                        p_file.seek(0) # 重置游标
                        if self._key_passwd:
                            pkey = paramiko.Ed25519Key.from_private_key(p_file,password=self._key_passwd)
                        else:
                            pkey = paramiko.Ed25519Key.from_private_key(p_file)
                        self.debug("尝试使用Ed25519私钥认证")
                    except:
                        try:
                            p_file.seek(0)
                            if self._key_passwd:
                                pkey = paramiko.ECDSAKey.from_private_key(p_file,password=self._key_passwd)
                            else:
                                pkey = paramiko.ECDSAKey.from_private_key(p_file)
                            self.debug("尝试使用ECDSA私钥认证")
                        except:
                            p_file.seek(0)
                            if self._key_passwd:
                                try:
                                    pkey = paramiko.DSSKey.from_private_key(p_file,password=self._key_passwd)
                                except Exception as ex:
                                    ex = str(ex)
                                    if ex.find('OpenSSH private key file checkints do not match') != -1:
                                        return public.returnMsg(False, public.lang("Incorrect private key password:{}", ex))
                                    elif ex.find('encountered RSA key, expected DSA key') != -1:
                                        pkey = paramiko.RSAKey.from_private_key(p_file,password=self._key_passwd)
                                    else:
                                        return public.returnMsg(False, public.lang("Private key error: {}", ex))
                            else:
                                pkey = paramiko.DSSKey.from_private_key(p_file)
                if not pkey: return public.returnMsg(False, public.lang("Private key error!"))
                self._tp.auth_publickey(username=self._user, key=pkey)
            else:
                try:
                    self._tp.auth_none(self._user)
                except Exception as e:
                    e = str(e)
                    if e.find('keyboard-interactive') >= 0:
                        self._auth_interactive()
                    else:
                        self.debug('Authenticating password')
                        self._tp.auth_password(username=self._user, password=self._pass)
                # self._tp.auth_password(username=self._user, password=self._pass)
        except Exception as e:
            if self._old_conf:
                s_file = '/www/server/panel/config/t_info.json'
                if os.path.exists(s_file): os.remove(s_file)
            self.set_sshd_config(True)
            self._tp.close()
            e = str(e)
            if e.find('websocket error!') != -1:
                return public.return_msg_gettext(True, public.lang("connection succeeded"))
            if e.find('Authentication timeout') != -1:
                self.debug("认证超时{}".format(e))
                return public.return_msg_gettext(False,'Authentication timed out, please press enter to try again!{}',(e,))
            if e.find('Authentication failed') != -1:
                self.debug('认证失败{}'.format(e))
                if self._key_passwd:
                    sshd_config = public.readFile('/etc/ssh/sshd_config')
                    if sshd_config and sshd_config.find('ssh-dss') == -1:
                        return returnMsg(False,'The private key verification fails, the private key may be incorrect, or the ssh-dss private key authentication type may not be enabled in the /etc/ssh/sshd_config configuration file')
                    return returnMsg(False,'Authentication failed, please check whether the private key is correct: {}'.format(e + "," + self._user + "@" + self._host + ":" +str(self._port)))
                return public.return_msg_gettext(False,'Account or Password incorrect: {}',(str(e + "," + self._user + "@" + self._host + ":" +str(self._port)),))
            if e.find('Bad authentication type; allowed types') != -1:
                self.debug(public.lang('Authentication failed {}',str(e)))
                if self._host in ['127.0.0.1','localhost'] and self._pass == 'none':
                    return public.return_msg_gettext(False,'Username or Password incorrect: {}',(str("Authentication failed ," + self._user + "@" + self._host + ":" +str(self._port)),))
                return public.return_msg_gettext(False,'Unsupported authentication type: {}',(str(e)))
            if e.find('Connection reset by peer') != -1:
                self.debug(public.lang("The target server actively refused the connection"))
                return public.return_msg_gettext(False,public.lang("The target server actively refused the connection"))
            if e.find('Error reading SSH protocol banner') != -1:
                self.debug('The protocol header response timed out')
                return public.return_msg_gettext(False,public.lang('The protocol header response timed out, and the network quality with the target server was too bad: {}',str(e)))
            if e.find('encountered RSA key, expected DSA key') != -1:
                self.debug('Private keys may require password access')
                return public.return_msg_gettext(False,public.lang('Private keys may require password access: {}',str(e)))
            if e.find('password and salt must not be empty') != -1:
                self.debug('Private keys may require password access')
                return public.return_msg_gettext(False,public.lang('Private keys may require password access: {}',str(e)))
            if not e:
                self.debug('The SSH protocol handshake timed out')
                return public.return_msg_gettext(False, public.lang("The SSH protocol handshake timed out, and the network quality with the target server is too bad"))
            err =  public.get_error_info()
            self.debug(err)
            return public.return_msg_gettext(False,public.lang('unknown error: {}',str(err)))

        self.debug(public.lang("The authentication is successful and the session channel is being constructed"))
        self._ssh = self._tp.open_session()
        self._ssh.get_pty(term='xterm', width=100, height=34)
        self._ssh.invoke_shell()
        self._connect_time = time.time()
        self._last_send = []
        from BTPanel import request
        self._client = public.GetClientIp() +':' + str(request.environ.get('REMOTE_PORT'))
        public.write_log_gettext(self._log_type,'Successfully logged in to the SSH server [{}:{}]',(self._host,str(self._port)))
        self.history_send(public.lang("Login success\n"))
        self.set_sshd_config(True)
        self.debug(public.lang("Login success"))
        from BTPanel import session
        self._video_addr = "/www/server/panel/plugin/jumpserver/static/video/%s.json" % str(int(self._connect_time))
        if not os.path.exists("/www/server/panel/plugin/jumpserver/static/video/"):
            os.makedirs("/www/server/panel/plugin/jumpserver/static/video/")
        # 如果开启了录像功能
        user_agent = str(request.headers.get('User-Agent'))
        if os.path.exists(public.get_panel_path() + "/data/open_ssh_login.pl"):
            self._host_row_id = public.M('ssh_login_record').add(
                'addr,server_ip,ssh_user,user_agent,login_time,video_addr',
                (self._client, self._host, self._user, user_agent
                 , int(self._connect_time),
                 self._video_addr))

            self.record('header', {
                "version": 1,
                "width": 100,
                "height": 29,
                "timestamp": int(self._connect_time),
                "env": {
                    "TERM": "xterm",
                    "SHELL": "/bin/bash",
                },
                "stdout": []
            })
        return public.return_msg_gettext(True, public.lang("connection succeeded"))

    def _auth_interactive(self):
        self.debug('Verification Code')

        self.brk = False

        def handler(title, instructions, prompt_list):
            if not self._ws:  raise public.PanelError('websocket error!')
            if instructions:
                self._ws.send(instructions)
            if title:
                self._ws.send(title)
            resp = []
            for pr in prompt_list:
                if str(pr[0]).strip() == "Password:":
                    resp.append(self._pass)
                elif str(pr[0]).strip() == "Verification code:":
                    # 获取前段传入的验证码
                    self._ws.send("Verification code# ")
                    self._s_code = True
                    code = ""
                    while True:
                        data = self._ws.receive()
                        if data.find('"resize":1') != -1:
                            self.resize(data)
                            continue
                        self._ws.send(data)
                        if data in ["\n", "\r"]: break
                        code += data
                    resp.append(code)
                    self._ws.send("\n")
            self._s_code = None
            return tuple(resp)

        self._tp.auth_interactive(self._user, handler)

    def get_login_user(self):
        '''
            @name 获取本地登录用户
            @author hwliang<2020-08-07>
            @return string
        '''

        if self._user != 'root': return self._user
        l_user = 'root'
        ssh_config_file = '/etc/ssh/sshd_config'
        ssh_config = public.readFile(ssh_config_file)
        if not ssh_config: return l_user

        if ssh_config.find('PermitRootLogin yes') != -1: return l_user


        user_list  = self.get_ulist()
        login_user = ''
        for u_info in user_list:
            if u_info['user'] == 'root': continue
            if u_info['login'] == '/bin/bash':
                login_user = u_info['user']
                break

        if not login_user:
            return l_user

        return login_user


    def get_ulist(self):
        '''
            @name 获取本地用户列表
            @author hwliang<2020-08-07>
            @return list
        '''
        u_data = public.readFile('/etc/passwd')
        u_list = []
        for i in u_data.split("\n"):
            u_tmp = i.split(':')
            if len(u_tmp) < 3: continue
            u_info = {}
            u_info['user'],u_info['pass'],u_info['uid'],u_info['gid'],u_info['user_msg'],u_info['home'],u_info['login'] = u_tmp
            u_list.append(u_info)
        return u_list

    def is_local(self):
        '''
            @name 处理本地连接
            @author hwliang<2020-08-07>
            @ps 如果host为127.0.0.1或localhost，则尝试自动使用publicKey登录
            @return void
        '''

        if self._pass: return
        if self._pkey: return
        if self._host in ['127.0.0.1','localhost']:
            try:
                self._port = public.get_ssh_port()
                self.set_sshd_config()
                s_file = '/www/server/panel/config/t_info.json'
                if os.path.exists(s_file):
                    ssh_info = json.loads(public.en_hexb(public.readFile(s_file)))
                    self._host = ssh_info['host'].strip()
                    if 'username' in ssh_info:
                        self._user = ssh_info['username']
                    if 'pkey' in ssh_info:
                        self._pkey = ssh_info['pkey']
                    if 'password' in ssh_info:
                        self._pass = ssh_info['password']
                    self._old_conf = True
                    return
                ssh_key_type_file = '{}/data/ssh_key_type.pl'.format(public.get_panel_path())
                ssh_key_type = ''
                if os.path.exists(ssh_key_type_file):
                    ssh_key_type_new = public.readFile(ssh_key_type_file)
                    if ssh_key_type_new: ssh_key_type = ssh_key_type_new.strip()
                login_user = self.get_login_user()
                if self._user == 'root' and login_user == 'root':
                    id_rsa_file = ['/root/.ssh/id_ed25519','/root/.ssh/id_ecdsa','/root/.ssh/id_rsa','/root/.ssh/id_rsa_bt']
                    if ssh_key_type: id_rsa_file.insert(0,'/root/.ssh/id_{}'.format(ssh_key_type))
                    for ifile in id_rsa_file:
                        if os.path.exists(ifile):
                            self._pkey = public.readFile(ifile)
                            host_path = self._save_path + self._host
                            if not os.path.exists(host_path):
                                os.makedirs(host_path,384)
                            return


                if not self._pass or not self._pkey or not self._user:
                    home_path = '/home/' + login_user
                    if login_user == 'root':
                        home_path = '/root'
                    self._user = login_user
                    id_rsa_file = [home_path + '/.ssh/id_ed25519',home_path + '/.ssh/id_ecdsa',home_path + '/.ssh/id_rsa',home_path + '/.ssh/id_rsa_bt']
                    if ssh_key_type: id_rsa_file.insert(0,home_path + '/.ssh/id_{}'.format(ssh_key_type))
                    for ifile in id_rsa_file:
                        if os.path.exists(ifile):
                            self._pkey = public.readFile(ifile)
                            return

                    self._pass = 'none'
                    return

            except:
                return

    def get_sys_version(self):
        '''
            @name 获取操作系统版本
            @author hwliang<2020-08-13>
            @return bool
        '''
        version = public.readFile('/etc/redhat-release')
        if not version:
            version = public.readFile('/etc/issue').strip().split("\n")[0].replace('\\n','').replace(r'\l','').strip()
        else:
            version = version.replace('release ','').replace('Linux','').replace('(Core)','').strip()
        return version

    def get_ssh_status(self):
        '''
            @name 获取SSH服务状态
            @author hwliang<2020-08-13>
            @return bool
        '''
        version = self.get_sys_version()
        if os.path.exists('/usr/bin/apt-get'):
            if os.path.exists('/etc/init.d/sshd'):
                status = public.ExecShell("service sshd status | grep -P '(dead|stop|not running)'|grep -v grep")
            else:
                status = public.ExecShell("service ssh status | grep -P '(dead|stop|not running)'|grep -v grep")
        else:
            if version.find(' 7.') != -1 or version.find(' 8.') != -1 or version.find('Fedora') != -1:
                status = public.ExecShell("systemctl status sshd.service | grep 'dead'|grep -v grep")
            else:
                status = public.ExecShell("/etc/init.d/sshd status | grep -e 'stopped' -e '已停'|grep -v grep")
        if len(status[0]) > 3:
            status = False
        else:
            status = True
        return status

    def is_running(self,rep = False):
        '''
            @name 处理SSH服务状态
            @author hwliang<2020-08-13>
            @param rep<bool> 是否恢复原来的SSH服务状态
            @return bool
        '''
        try:
            if rep and self._rep_ssh_service:
                self.restart_ssh('stop')
                return True

            ssh_status = self.get_ssh_status()
            if not ssh_status:
                self.restart_ssh('start')
                self._rep_ssh_service = True
                return True
            return False
        except:
            return False


    def set_sshd_config(self,rep = False):
        '''
            @name 设置本地SSH配置文件，以支持pubkey认证
            @author hwliang<2020-08-13>
            @param rep<bool> 是否恢复ssh配置文件
            @return bool
        '''
        self.is_running(rep)
        if rep and not self._rep_ssh_config:
            return False

        try:
            sshd_config_file = '/etc/ssh/sshd_config'
            if not os.path.exists(sshd_config_file):
                return False

            sshd_config = public.readFile(sshd_config_file)

            if not sshd_config:
                return False

            if rep:
                if self._sshd_config_backup:
                    public.writeFile(sshd_config_file,self._sshd_config_backup)
                    self.restart_ssh()
                return True

            pin = r'^\s*PubkeyAuthentication\s+(yes|no)'
            pubkey_status = re.findall(pin,sshd_config,re.I)
            if pubkey_status:
                if pubkey_status[0] == 'yes':
                    pubkey_status = True
                else:
                    pubkey_status = False

            pin = r'^\s*RSAAuthentication\s+(yes|no)'
            rsa_status = re.findall(pin,sshd_config,re.I)
            if rsa_status:
                if rsa_status[0] == 'yes':
                    rsa_status = True
                else:
                    rsa_status = False

            self._sshd_config_backup = sshd_config
            is_write = False
            if not pubkey_status:
                sshd_config = re.sub(r'\n#?PubkeyAuthentication\s\w+','\nPubkeyAuthentication yes',sshd_config)
                is_write = True
            if not rsa_status:
                sshd_config = re.sub(r'\n#?RSAAuthentication\s\w+','\nRSAAuthentication yes',sshd_config)
                is_write = True

            if is_write:
                public.writeFile(sshd_config_file,sshd_config)
                self._rep_ssh_config = True
                self.restart_ssh()
            else:
                self._sshd_config_backup = None

            return True
        except:
            return False

    def restart_ssh(self,act = 'reload'):
        '''
        重启ssh 无参数传递
        '''
        version = public.readFile('/etc/redhat-release')
        if not os.path.exists('/etc/redhat-release'):
            public.ExecShell('service ssh ' + act)
        elif version.find(' 7.') != -1 or version.find(' 8.') != -1:
            public.ExecShell("systemctl " + act + " sshd.service")
        else:
            public.ExecShell("/etc/init.d/sshd " + act)

    def resize(self, data):
        '''
            @name 调整终端大小
            @author hwliang<2020-08-07>
            @param data<dict> 终端尺寸数据
            {
                cols: int 列
                rows: int 行
            }
            @return bool
        '''
        try:
            data = json.loads(data)
            self._ssh.resize_pty(width=data['cols'], height=data['rows'])
            return True
        except:
            return False


    def recv(self):
        '''
            @name 读取tty缓冲区数据
            @author hwliang<2020-08-07>
            @return void
        '''
        n = 0
        try:
            while self._ws.connected:
                resp_line = self._ssh.recv(1024)
                if not resp_line:
                    if not self._tp.is_active():
                        self.debug(public.lang("Channel disconnected"))
                        self._ws.send(public.lang("The connection is disconnected, press enter to try to reconnect!"))
                        self.close()
                        return

                if not resp_line:
                    n+=1
                    if n > 5: break
                    continue
                n = 0
                if not self._ws.connected:
                    return
                try:
                    result = resp_line.decode('utf-8','ignore')
                except:
                    try:
                        result = resp_line.decode()
                    except:
                        result = str(resp_line)
                self.record('iodata', result)
                self._ws.send(result)

                # self.history_recv(result)
        except Exception as e:
            e = str(e)
            if e.find('closed') != -1:
                self.debug(public.getMsg('SSH_LOGIN_INFO'))
            elif self._ws.connected:
                self.debug(public.lang('Error reading tty buffer data, {}',str(e)))

        if not self._ws.connected:
            self.debug(public.lang("The client has actively disconnected"))
        self.close()

    def send(self):
        '''
            @name 写入数据到缓冲区
            @author hwliang<2020-08-07>
            @return void
        '''
        try:
            while self._ws.connected:
                if self._s_code:
                    time.sleep(0.1)
                    continue
                client_data = self._ws.receive()
                if not client_data: continue
                if client_data == '{}': continue
                if len(client_data) > 10:
                    if client_data.find('{"host":"') != -1:
                        continue
                    if client_data.find('"resize":1') != -1:
                        self.resize(client_data)
                        continue
                self._ssh.send(client_data)
                # self.history_send(client_data)
        except Exception as ex:
            ex = str(ex)

            if ex.find('_io.BufferedReader') != -1:
                self.debug(public.lang("An error occurred while reading data from websocket. Retrying"))
                self.send()
                return
            elif ex.find('closed') != -1:
                self.debug(public.lang("SSH_LOGIN_INFO"))
            else:
                self.debug(public.get_msg_gettext('An error occurred while writing data to the buffer: {}',(str(ex),)))

        if not self._ws.connected:
            self.debug(public.lang("The client has actively disconnected"))
        self.close()


    def history_recv(self,recv_data):
        '''
            @name 从接收实体保存命令
            @author hwliang<2020-08-12>
            @param recv_data<string> 数据实体
            @return void
        '''
        #处理TAB补登
        if self._last_cmd_tip == 1:
            if not recv_data.startswith('\r\n'):
                self._last_cmd += recv_data.replace('\u0007','').replace("\x07","").strip()
            self._last_cmd_tip = 0

        #上下切换命令
        if self._last_cmd_tip == 2:
            self._last_cmd = recv_data.strip().replace("\x08","").replace("\x07","").replace("\x1b[K","")
            self._last_cmd_tip = 0

    def history_send(self,send_data):
        '''
            @name 从发送实体保存命令
            @author hwliang<2020-08-12>
            @param send_data<string> 数据实体
            @return void
        '''
        if not send_data: return
        his_path = self._save_path + self._host
        if not os.path.exists(his_path): return
        his_file = his_path + '/history.pl'

        #上下切换命令
        if send_data in ["\x1b[A","\x1b[B"]:
            self._last_cmd_tip = 2
            return

        #左移光标
        if send_data in ["\x1b[C"]:
            self._last_num -= 1
            return

        # 右移光标
        if send_data in ["\x1b[D"]:
            self._last_num += 1
            return

        #退格
        if send_data == "\x7f":
            self._last_cmd = self._last_cmd[:-1]
            return

        #过滤特殊符号
        if send_data in ["\x1b[C","\x1b[D","\x1b[K","\x07","\x08","\x03","\x01","\x02","\x04","\x05","\x06","\x1bOB","\x1bOA","\x1b[8P","\x1b","\x1b[4P","\x1b[6P","\x1b[5P"]:
            return

        #Tab补全处理
        if send_data == "\t":
            self._last_cmd_tip = 1
            return

        if str(send_data).find("\x1b") != -1:
            return

        if send_data[-1] in ['\r','\n']:
            if not self._last_cmd: return
            his_shell = [int(time.time()),self._client,self._user,self._last_cmd]
            public.writeFile(his_file, json.dumps(his_shell) + "\n","a+")
            self._last_cmd = ""

            #超过50M则保留最新的20000行
            if os.stat(his_file).st_size > 52428800:
                his_tmp = public.GetNumLines(his_file,20000)
                public.writeFile(his_file, his_tmp)
        else:
            if self._last_num >= 0:
                self._last_cmd += send_data


    def close(self):
        '''
            @name 释放连接
            @author hwliang<2020-08-07>
            @return void
        '''
        try:
            if self._host_row_id:
                public.M('ssh_login_record').where('id=?', self._host_row_id).update(
                    {'close_time': int(time.time())})
            if self._ssh:
                self._ssh.close()
            if self._tp:  # 关闭宿主服务
                self._tp.close()
            if self._ws.connected:
                self._ws.close()
        except:
            pass


    def set_attr(self,ssh_info):
        '''
            @name 设置对象属性，并连接服务器
            @author hwliang<2020-08-07>
            @return void
        '''
        self._host = ssh_info['host'].strip()
        self._port = int(ssh_info['port'])
        if 'username' in ssh_info:
            self._user = ssh_info['username']
        if 'pkey' in ssh_info:
            self._pkey = ssh_info['pkey']
        if 'password' in ssh_info:
            self._pass = ssh_info['password']
        if 'pkey_passwd' in ssh_info:
            self._key_passwd = ssh_info['pkey_passwd']
        try:
            result = self.connect()
        except Exception as ex:
            if str(ex).find("NoneType") == -1:
                raise public.PanelError(ex)
        return result


    def heartbeat(self):
        '''
            @name 心跳包
            @author hwliang<2020-09-10>
            @return void
        '''
        while True:
            time.sleep(30)
            if self._tp.is_active():
                self._tp.send_ignore()
            else:
                break
            if self._ws.connected:
                self._ws.send("")
            else:
                break

    def debug(self,msg):
        '''
            @name 写debug日志
            @author hwliang<2020-09-10>
            @return void
        '''
        msg = "{} - {}:{} => {} \n".format(public.format_date(),self._host,self._port,msg)
        self.history_send(msg)
        public.writeFile(self._debug_file,msg,'a+')

    def run(self,web_socket, ssh_info=None):
        '''
            @name 启动SSH客户端对象
            @author hwliang<2020-08-07>
            @param web_socket<websocket> websocket句柄对像
            @param ssh_info<dict> SSH信息{
                host: 主机地址,
                port: 端口
                username: 用户名
                password: 密码
                pkey: 密钥(如果不为空，将使用密钥连接)
            }
            @return void
        '''
        self._ws = web_socket
        if not self._ssh:
            if not ssh_info:
                return
            result = self.set_attr(ssh_info)
        else:
            result = public.get_msg_gettext(True,'ALREADY_CONNECTED')
        if result['status']:
            sendt = threading.Thread(target=self.send)
            recvt = threading.Thread(target=self.recv)
            ht = threading.Thread(target=self.heartbeat)
            sendt.start()
            recvt.start()
            ht.start()
            sendt.join()
            recvt.join()
            ht.join()
            self.close()
        else:
            self._ws.send(result['msg'])
            self.close()

    def __del__(self):
        '''
            自动释放
        '''
        self.close()



class ssh_host_admin(ssh_terminal):
    _panel_path = '/www/server/panel'
    _save_path = _panel_path + '/config/ssh_info/'
    _pass_file = _panel_path + '/data/a_pass.pl'
    _user_command_file = _save_path + '/user_command.json'
    _sys_command_file = _save_path + '/sys_command.json'
    _pass_str = None

    def __init__(self):
        self.__create_aes_pass()

    def __create_aes_pass(self):
        '''
            @name 创建AES密码
            @author
            @return string
        '''
        if not os.path.exists(self._save_path):
            os.makedirs(self._save_path,384)
        if not os.path.exists(self._pass_file):
            public.writeFile(self._pass_file,public.GetRandomString(16))
            public.set_mode(self._pass_file,600)
        if not self._pass_str:
            self._pass_str = public.readFile(self._pass_file)
            if not self._pass_str:
                self._pass_str = public.GetRandomString(16)
                public.writeFile(self._pass_file,self._pass_str)
                public.set_mode(self._pass_file,600)

    def get_host_list(self,args = None):
        '''
            @name 获取本机保存的SSH信息列表
            @author hwliang<2020-08-07>
            @param args<dict_obj or None>
            @return list
        '''

        host_list = []
        for name in os.listdir(self._save_path):
            info_file = self._save_path + name +'/info.json'
            if not os.path.exists(info_file): continue
            try:
                info_tmp = self.get_ssh_info(name)
                host_info = {}
                host_info['host'] = name
                host_info['port'] = info_tmp['port']
                host_info['ps'] = info_tmp['ps']
                host_info['sort'] = int(info_tmp['sort'])
            except:
                if os.path.exists(info_file):
                    os.remove(info_file)
                continue

            host_list.append(host_info)

        host_list = sorted(host_list,key=lambda x: x['sort'],reverse=False)
        return host_list

    def get_host_find(self,args):
        '''
            @name 获取指定SSH信息
            @author hwliang<2020-08-07>
            @param args<dict_obj>{
                host: 主机地址
            }
            @return dict
        '''
        args.host = args.host.strip()
        info_file = self._save_path + args.host +'/info.json'
        if not os.path.exists(info_file):
            return public.return_msg_gettext(False, public.lang("The specified SSH information does not exist!"))
        info_tmp = self.get_ssh_info(args.host)
        host_info = {}
        host_info['host'] = args.host
        host_info['port'] = info_tmp['port']
        host_info['ps'] = info_tmp['ps']
        host_info['sort'] = info_tmp['sort']
        host_info['username'] = info_tmp['username']
        host_info['password'] = info_tmp['password']
        host_info['pkey'] = info_tmp['pkey']
        host_info['pkey_passwd'] = ''
        if 'pkey_passwd' in info_tmp:
            host_info['pkey_passwd'] = info_tmp['pkey_passwd']
        return host_info

    def modify_host(self,args):
        '''
            @name 修改SSH信息
            @author hwliang<2020-08-07>
            @param args<dict_obj>{
                host: 被修改的主机地址,
                new_host: 新的主机地址,
                port: 端口
                ps: 备注
                sort: 排序(可选)
                username: 用户名
                password: 密码
                pkey: 密钥(如果不为空，将使用密钥连接)
                pkey_passwd: 密钥的密码
            }
            @return dict
        '''
        args.new_host = args.new_host.strip()
        args.host = args.host.strip()
        if args.host != args.new_host:
            info_file = self._save_path + args.new_host +'/info.json'
            if os.path.exists(info_file):
                return public.return_msg_gettext(False, public.lang("The specified host address has been added to other SSH information!"))

        info_file = self._save_path + args.host +'/info.json'

        if not os.path.exists(info_file):
            return public.return_msg_gettext(False, public.lang("The specified SSH information does not exist!"))

        if not 'sort' in args:
            r_data = public.aes_decrypt(public.readFile(info_file),self._pass_str)
            info_tmp = json.loads(r_data)
            args.sort = info_tmp['sort']

        host_info = {}
        host_info['host'] = args.new_host
        host_info['port'] = int(args['port'])
        host_info['ps'] = args['ps']
        host_info['sort'] = args['sort']
        host_info['username'] = args['username']
        host_info['password'] = args['password']
        host_info['pkey'] = args['pkey']
        if 'pkey_passwd' in args:
            host_info['pkey_passwd'] = args['pkey_passwd']
        else:
            host_info['pkey_passwd'] = ''
        if not host_info['pkey']: host_info['pkey'] = ''
        result = self.set_attr(host_info)
        if not result['status']: return result
        self.save_ssh_info(args.host,host_info)
        if args.host != args.new_host:
            public.ExecShell('mv {} {}'.format(self._save_path + args.host,self._save_path + args.new_host))
        public.write_log_gettext(self._log_type,'Modify the SSH information of HOST: {}',(args.host,))
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))

    def create_host(self,args):
        '''
            @name 添加SSH信息
            @author hwliang<2020-08-07>
            @param args<dict_obj>{
                host: 主机地址,
                port: 端口
                ps: 备注
                sort: 排序(可选，默认0)
                username: 用户名
                password: 密码
                pkey: 密钥(如果不为空，将使用密钥连接)
                pkey_passwd： 密钥的密码
            }
            @return dict
        '''
        args.host = args.host.strip()
        host_path = self._save_path + args.host
        info_file = host_path +'/info.json'
        if os.path.exists(info_file):
            args.new_host = args.host
            return self.modify_host(args)
            #return public.returnMsg(False, public.lang("Specify that SSH information has been added!"))
        if not os.path.exists(host_path):
            os.makedirs(host_path,384)
        if not 'sort' in args: args.sort = 0
        if not 'ps' in args: args.ps = args.host
        host_info = {}
        host_info['host'] = args.host
        host_info['port'] = int(args['port'])
        host_info['ps'] = args['ps']
        host_info['sort'] = int(args['sort'])
        host_info['username'] = args['username']
        host_info['password'] = args['password']
        host_info['pkey'] = args['pkey']
        host_info['pkey_passwd'] = ''
        if 'pkey_passwd' in args:
            host_info['pkey_passwd'] = args['pkey_passwd']
        result = self.set_attr(host_info)
        if not result['status']: return result
        self.save_ssh_info(args.host,host_info)
        public.write_log_gettext(self._log_type,'Add the SSH information of HOST: {}',(str(args.host),))
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))


    def remove_host(self,args):
        '''
            @name 删除指定SSH信息
            @author hwliang<2020-08-07>
            @param args<dict_obj>{
                host: 主机地址
            }
            @return dict
        '''
        args.host = args.host.strip()
        if not args.host: return public.return_msg_gettext(False, public.lang("Parameter ERROR!"))
        host_path = self._save_path + args.host
        if not os.path.exists(host_path):
            return public.return_msg_gettext(False, public.lang("The specified SSH information does not exist!"))
        public.ExecShell("rm -rf {}".format(host_path))
        public.write_log_gettext(self._log_type,'Delete the SSH information of HOST: {}',(str(args.host),))
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))


    def get_ssh_info(self,host):
        '''
            @name 获取并解密指定SSH信息
            @author hwliang<2020-08-07>
            @param  host<string> 主机地址
            @return dict or False
        '''
        info_file = self._save_path + host + '/info.json'
        if not os.path.exists(info_file): return False
        try:
            r_data = public.aes_decrypt(public.readFile(info_file),self._pass_str)
        except ValueError as ex:
            if str(ex).find('Incorrect AES key length') != -1:
                if os.path.exists(self._pass_file):
                    os.remove(self._pass_file)
                self.__create_aes_pass()
                r_data = public.aes_decrypt(public.readFile(info_file),self._pass_str)

        return json.loads(r_data)

    def save_ssh_info(self,host,host_info):
        '''
            @name 获取并解密指定SSH信息
            @author hwliang<2020-08-07>
            @param  host<string> 主机地址
            @param  host_info<dict> ssh信息字典
            @return bool
        '''
        host_path = self._save_path + host
        if not os.path.exists(host_path):
            os.makedirs(host_path,384)
        info_file = host_path +'/info.json'
        r_data = public.aes_encrypt(json.dumps(host_info),self._pass_str)
        public.writeFile(info_file,r_data)
        return True

    def set_sort(self,args):
        '''
            @name 获取并解密指定SSH信息
            @author hwliang<2020-08-07>
            @param  args<dict_obj>{
                sort_list<json>{
                    主机host : 排序编号,
                    主机host : 排序编号,
                    ...
                }
            }
            @return bool
        '''
        if not 'sort_list' in args:
            return public.return_msg_gettext(False, public.lang("Please pass in the [sort_list] field"))
        sort_list = json.loads(args.sort_list)
        for name in sort_list.keys():
            info_file = self._save_path + name + '/info.json'
            if not os.path.exists(info_file): continue

            ssh_info = self.get_ssh_info(name)
            ssh_info['sort'] = int(sort_list[name])
            self.save_ssh_info(name,ssh_info)
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))

    def get_command_list(self,args = None, user_cmd = False , sys_cmd = False):
        '''
            @name 获取常用命令列表
            @author hwliang<2020-08-08>
            @param  args<dict_obj>
            @param  user_cmd<bool> 是否不获取用户配置
            @param  sys_cmd<bool>  是否不获取系统配置
            @return list
        '''

        sys_command = []
        if not sys_cmd:
            if os.path.exists(self._sys_command_file):
                sys_command = json.loads(public.readFile(self._sys_command_file))

        user_command = []
        if not user_cmd:
            if os.path.exists(self._user_command_file):
                user_command = json.loads(public.readFile(self._user_command_file))

        command = sys_command + user_command
        return command


    def command_exists(self,command,title):
        '''
            @name 判断命令是否存在
            @author hwliang<2020-08-08>
            @param  command<list> 常用命令列表
            @param  title<string> 命令标题
            @return bool
        '''
        for cmd in command:
            if cmd['title'] == title: return True
        return False

    def save_command(self,command,sys_cmd=False):
        '''
            @name 保存常用命令
            @author hwliang<2020-08-08>
            @param  command<list> 常用命令列表
            @param  sys_cmd<bool> 是否为系统配置
            @return void
        '''
        s_file = self._user_command_file
        if sys_cmd:
            s_file = self._sys_command_file
        public.writeFile(s_file,json.dumps(command))

    def create_command(self,args):
        '''
            @name 创建常用命令
            @author hwliang<2020-08-08>
            @param  args<dict_obj>{
                title<string> 标题
                shell<string> 命令文本
            }
            @return dict
        '''
        args.title = args.title.strip()
        command = self.get_command_list(sys_cmd=True)

        if self.command_exists(command,args.title):
            return public.return_msg_gettext(False, public.lang("The specified command name already exists"))

        cmd = {
            "title": args.title,
            "shell": args.shell.strip()
        }

        command.append(cmd)
        self.save_command(command)
        public.write_log_gettext(self._log_type,'Add common commands [{}]',(str(args.title),))
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))

    def get_command_find(self,args = None, title=None):
        '''
            @name 获取指定命令信息
            @author hwliang<2020-08-08>
            @param  args<dict_obj>{
                title<string> 标题
            } 可选
            @param title 标题 可选
            @return dict
        '''
        if args: title = args.title.strip()
        command = self.get_command_list()
        for cmd in command:
            if cmd['title'] == title or cmd['title'] == args.title:
                return cmd
        return public.return_msg_gettext(False, public.lang("The specified command does not exist"))

    def modify_command(self,args):
        '''
            @name 修改常用命令
            @author hwliang<2020-08-08>
            @param  args<dict_obj>{
                title<string> 标题
                new_title<string> 新标题
                shell<string> 命令文本
            }
            @return dict
        '''
        args.title = args.title.strip()
        command = self.get_command_list(sys_cmd=True)
        if not self.command_exists(command,args.title):
            return public.return_msg_gettext(False, public.lang("The specified command does not exist"))
        for i in range(len(command)):
            if command[i]['title'] == args.title or command[i]['title'] == title:
                command[i]['title'] = args.new_title.strip()
                command[i]['shell'] = args.shell.strip()
                break
        self.save_command(command)
        public.write_log_gettext(self._log_type,'Modify common commands [{}]',(str(args.title),))
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))

    def remove_command(self,args):
        '''
            @name 删除指定命令
            @author hwliang<2020-08-08>
            @param  args<dict_obj>{
                title<string> 标题
            }
            @return dict
        '''
        args.title = args.title.strip()
        command = self.get_command_list(sys_cmd=True)
        if not self.command_exists(command,args.title):
            return public.return_msg_gettext(False, public.lang("The specified command does not exist"))
        for i in range(len(command)):
            if command[i]['title'] == args.title:
                del(command[i])
                break

        self.save_command(command)
        public.write_log_gettext(self._log_type,'Delete common commands [{}]',(str(args.title),))
        return public.return_msg_gettext(True, public.lang("Setup successfully!"))

