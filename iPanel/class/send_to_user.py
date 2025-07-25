# coding: utf-8
# +-------------------------------------------------------------------
# | iPanel x3
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2017 iPanel(www.iPanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: lkq <1249648969@iPanel.com>
# +-------------------------------------------------------------------
# +--------------------------------------------------------------------
# |   告警消息队列
# +--------------------------------------------------------------------
import public,send_mail
import time,os,sys,json
class send_to_user:
    '''
    建立数据库
    '''
    def __init__(self):
        self.mail = send_mail.send_mail()
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'send_settings')).count():
            public.M('').execute('''CREATE TABLE "send_settings" (
                "id" INTEGER PRIMARY KEY AUTOINCREMENT,"name" TEXT,"type" TEXT,"path" TEXT,"send_type" TEXT,"last_time" TEXT ,"time_frame" TEXT,"inser_time" TEXT DEFAULT'');''')
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', 'send_msg')).count():
            public.M('').execute('''CREATE TABLE "send_msg" ("id" INTEGER PRIMARY KEY AUTOINCREMENT,"name" TEXT,"send_type" TEXT,"msg" TEXT,"is_send" TEXT,"type" TEXT,"inser_time" TEXT DEFAULT '');''')

    '''设置表插入数据'''
    def insert_settings(self,name,type,path,send_type,time_frame=180):
        inser_time = self.dtchg(int(time.time()))
        last_time=int(time.time())
        if public.M('send_settings').where('name=?',(name,)).count(): return False
        data={"name":name,"type":type,"path":path,"send_type":send_type,"time_frame":time_frame,"inser_time":inser_time,"last_time":last_time}
        return public.M('send_settings').insert(data)

    '''数据库插入'''
    def inser_send_msg(self,name,send_type,msg,type,inser_time):
        inser_time=self.dtchg(inser_time)
        if not inser_time:return False
        if public.M('send_msg').where('name=? and send_type=? and type=? and inser_time=?',(name,send_type,type,inser_time)).count():return False
        data={"name":name,"send_type":send_type,"msg":msg,"is_send":False,"type":type,"inser_time":inser_time}
        return  public.M('send_msg').insert(data)

    def insert_msg(self, name, send_type, msg, type, insert_time):
        return self.inser_send_msg(name, send_type, msg, type, insert_time)

    def dtchg(self,x):
        try:
            time_local = time.localtime(float(x))
            dt = time.strftime("%Y-%m-%d %H:%M:%S", time_local)
            return dt
        except:
            return False

    def get_ip(self):
        if os.path.exists('/www/server/panel/data/iplist.txt'):
            data=public.ReadFile('/www/server/panel/data/iplist.txt')
            return data.strip()
        else:return '127.0.0.1'

    def get_safe_logs(self, path,p=1,num=11):
        try:
            import cgi
            pythonV = sys.version_info[0]
            if not os.path.exists(path): return '111';
            start_line = (p - 1) * num
            count = start_line + num
            fp = open(path, 'rb')
            buf = ""
            try:
                fp.seek(-1, 2)
            except:
                return []
            if fp.read(1) == "\n": fp.seek(-1, 2)
            data = []
            b = True
            n = 0
            for i in range(count):
                while True:
                    newline_pos = str.rfind(buf, "\n")
                    pos = fp.tell()
                    if newline_pos != -1:
                        if n >= start_line:
                            line = buf[newline_pos + 1:]
                            try:
                                tmp_data = json.loads(cgi.escape(line))
                                data.append(tmp_data)
                            except:
                                pass
                        buf = buf[:newline_pos]
                        n += 1
                        break
                    else:
                        if pos == 0:
                            b = False
                            break
                        to_read = min(4096, pos)
                        fp.seek(-to_read, 1)
                        t_buf = fp.read(to_read)
                        if pythonV == 3: t_buf = t_buf.decode('utf-8')
                        buf = t_buf + buf
                        fp.seek(-to_read, 1)
                        if pos - to_read == 0:
                            buf = "\n" + buf
                if not b: break;
            fp.close()
        except:
            data = []
        return data

    '''
    读取数据库中的值、写入到数据库中
    '''
    def read_thread(self):
        if not public.M('send_settings').count():return False
        send_data=public.M('send_settings').field('id,name,type,path,send_type,inser_time,last_time,time_frame').select()
        for i in send_data:
            if (int(time.time())-int(i['last_time']))<int(i['time_frame']):continue
            if i['type']=='json':
                if os.path.exists(i['path']):
                    read_file=self.get_safe_logs(i['path'],p=1,num=100)
                    if not read_file:continue
                    if not read_file[0]:continue
                    for i2 in read_file:
                        self.inser_send_msg(i['name'],i['send_type'],self.get_ip()+"服务器触发告警信息为: "+i2[1]+',触发告警时间:'+self.dtchg(int(time.time())),'json',i2[0])
                    public.writeFile(i['path'], '')
                    public.M('send_settings').where("id=?", (i['id'],)).update({"last_time": int(time.time())})
            if i['type']=='file':
                if os.path.exists(i['path']):
                    try:
                        f=open(i['path'],'r')
                        for i2 in f:
                            i2 =i2.strip()
                            if i2:
                                self.inser_send_msg(i['name'], i['send_type'],self.get_ip()+"服务器触发告警信息为: "+i2+',触发告警时间:'+self.dtchg(int(time.time())), 'file', int(time.time()))
                        os.remove(i['path'])
                        public.M('send_settings').where("id=?", (i['id'],)).update({"last_time": int(time.time())})
                    except:
                        os.remove(i['path'])

    def __write_log(self,name, msg):
        public.WriteLog(name+'告警', msg)

    '''发送消息线程'''
    def send_msg(self):
        if not public.M('send_msg').count(): return False
        send_msg=public.M('send_msg').where("is_send=?",(False,)).field('id,name,send_type,msg,is_send,type,inser_time').select()
        count=1
        for i in send_msg:
            if count>=4:break
            if i['send_type']=='mail':
                if public.send_mail(i['name'], i['msg']):
                    self.__write_log(i['name'], i['msg'])
                    public.M('send_msg').where("id=?", (i['id'],)).update({"is_send":True})
            if i['send_type']=='dingding':
                if public.send_dingding(i['msg']):
                    self.__write_log(i['name'], i['msg'])
                    public.M('send_msg').where("id=?", (i['id'],)).update({"is_send": True})
            count += 1
        public.M('send_msg').where("is_send=?", (True,)).delete()

    def main(self):
        self.read_thread()
        self.send_msg()

