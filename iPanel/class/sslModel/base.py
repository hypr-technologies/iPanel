# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://hypr.local) All rights reserved.
# -------------------------------------------------------------------
# Author: cjxin <cjxin@hypr.local>
# -------------------------------------------------------------------
# 面板获取列表公共库
# ------------------------------

import os,sys,time,json,db,re
import uuid

os.chdir("/www/server/panel")
if 'class/' not in sys.path:
    sys.path.insert(0, 'class/')
import public



caa_value = '0 issue "letsencrypt.org"'
# godaddy接口访问不了，先注释
# 'GoDaddyDns':'godaddy'
dns_type = {'DNSPodDns': 'dnspod', 'AliyunDns': 'aliyun', 'HuaweiCloudDns': 'huaweicloud', 'TencentCloudDns': 'tencentcloud', 'CloudFlareDns': 'cloudflare', 'WestDns': 'west'}
# dns_name = {'DNSPodDns':'DNSPod','AliyunDns':'阿里云DNS','HuaweiCloudDns':'华为云DNS','TencentCloudDns':'腾讯云DNS','CloudflareDns':'CloudFlare',}
class sslBase(object):
    def __init__(self):
        self.dns_provider_name = self.__class__.__name__

        self.top_domain_list = [
            '.ac.cn', '.ah.cn', '.bj.cn', '.com.cn', '.cq.cn', '.fj.cn', '.gd.cn',
            '.gov.cn', '.gs.cn', '.gx.cn', '.gz.cn', '.ha.cn', '.hb.cn', '.he.cn',
            '.hi.cn', '.hk.cn', '.hl.cn', '.hn.cn', '.jl.cn', '.js.cn', '.jx.cn',
            '.ln.cn', '.mo.cn', '.net.cn', '.nm.cn', '.nx.cn', '.org.cn', '.us.kg']
        top_domain_list_data = public.readFile('{}/config/domain_root.txt'.format(public.get_panel_path()))
        if top_domain_list_data:
            self.top_domain_list = set(self.top_domain_list + top_domain_list_data.strip().split('\n'))

    def log_response(self, response):
        try:
            log_body = response.json()
        except ValueError:
            log_body = response.content
        return log_body

    def create_dns_record(self, domain_name, domain_dns_value):
        raise NotImplementedError("create_dns_record method must be implemented.")

    def delete_dns_record(self, domain_name, domain_dns_value):
        raise NotImplementedError("delete_dns_record method must be implemented.")

    @classmethod
    def new(cls, conf_data):
        raise NotImplementedError("new method must be implemented.")

    def remove_record(self, domain, host, s_type):
        raise NotImplementedError("remove_record method must be implemented.")

    def add_record_for_creat_site(self, domain, server_ip):
        raise NotImplementedError("remove_record method must be implemented.")


    def extract_zone(self,domain_name, is_let_txt=False):
        if is_let_txt:
            domain_name = domain_name.lstrip("*.")
        top_domain = "." + ".".join(domain_name.rsplit('.')[-2:])
        is_tow_top = False
        if top_domain in self.top_domain_list:
            is_tow_top = True
        if domain_name.count(".") <= 1:
            zone = ""
            root = domain_name
            acme_txt = "_acme-challenge"
        else:
            zone, middle, last = domain_name.rsplit(".", 2)
            acme_txt = "_acme-challenge.%s" % zone
            if is_tow_top:
                last = top_domain[1:]
                middle = zone.split(".")[-1]
            root = ".".join([middle, last])
        return root, zone, acme_txt

    def get_dns_data(self, get):
        """
        @name 获取dns的api数据
        """
        res = {}
        sfile = "{}/config/dns_mager.conf".format(public.get_panel_path())

        try:
            if not os.path.exists(sfile):
                return res
            data = json.loads(public.readFile(sfile))

            for key in data.keys():
                for val in data[key]:
                    if val['id'] in res:
                        continue
                    if not dns_type.get(key,''):
                        continue
                    # val['dns_name'] = dns_name.get(key)
                    val['dns_name'] = key
                    val['dns_type'] = dns_type.get(key,'')
                    res[val['id']] = val
        except:pass
        return res

    def get_record_data(self):
        path = '{}/data/record_data.json'.format(public.get_panel_path())
        try:
            data = json.loads(public.readFile(path))
        except:
            data = {}
        return data

    def set_record_data(self, data):
        path = '{}/data/record_data.json'.format(public.get_panel_path())
        record_data = self.get_record_data()
        record_data.update(data)
        try:
            public.writeFile(path, json.dumps(record_data))
        except:
            pass

def _dns_data():
    """
    将旧的dnsapi同步到dns_mager.conf
    """
    try:
        old_file = "{}/config/dns_api.json".format(public.get_panel_path())
        if not os.path.exists(old_file):
            return
        new_file = "{}/config/dns_mager.conf".format(public.get_panel_path())
        try:
            old_data = json.loads(public.readFile(old_file))
        except:
            return
        if not os.path.exists(new_file):
            new_data = {}
        else:
            new_data = json.loads(public.readFile(new_file))
        for i in old_data:
            if not i['data']:
                continue
            if i['name'] == "TencentCloudDns":
                for d in i['data']:
                    d['name'] = "secret_id" if d['name'] == "AccessKey" else "secret_key" if d['name'] == "SecretKey" else d['name']
            if new_data.get(i['name']) or i['name'] not in dns_type.keys():
                continue
            pl = True
            value = {'ps': "旧版本{}接口".format(i['name']), 'id': uuid.uuid4().hex}
            for val in i['data']:
                if not val['value']:
                    pl = False
                    break
                value.update({val['name']: val['value']})
            if not pl:
                continue
            new_data[i['name']] = [value]
        # print(new_data)
        public.writeFile(new_file, json.dumps(new_data))
    except:
        pass

_dns_data()
del _dns_data

