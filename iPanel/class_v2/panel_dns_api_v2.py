#coding: utf-8
# +-------------------------------------------------------------------
# | iPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 iPanel(www.iPanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: 沐落 <cjx@iPanel.com>
# +-------------------------------------------------------------------
# TODO panel_dns_api_v2.py 废弃

import public,os,sys,json,time,random
import requests
from OpenSSL import crypto
import sys, os
import time
import copy
import json
import base64
import hashlib
import binascii
import urllib

if sys.version_info[0] == 2:  # python2
    import urlparse
    from urlparse import urljoin
    import urllib2
    import cryptography.hazmat
    import cryptography.hazmat.backends
    import cryptography.hazmat.primitives.serialization
else:  # python3
    from urllib.parse import urlparse
    from urllib.parse import urljoin
    import cryptography
import platform
import hmac
try:
    import requests
except:
    public.ExecShell('btpip install requests')
    import requests
try:
    import OpenSSL
except:
    public.ExecShell('btpip install pyOpenSSL')
    import OpenSSL
import random
import datetime
import logging
from hashlib import sha1

os.chdir("/www/server/panel")
if not 'class/' in sys.path:
    sys.path.insert(0,'class/')
import public
caa_value = '0 issue "letsencrypt.org"'


def extract_zone(domain_name):
    domain_name = domain_name.lstrip("*.")
    top_domain_list = ['.ac.cn', '.ah.cn', '.bj.cn', '.com.cn', '.cq.cn', '.fj.cn', '.gd.cn',
                        '.gov.cn', '.gs.cn', '.gx.cn', '.gz.cn', '.ha.cn', '.hb.cn', '.he.cn',
                        '.hi.cn', '.hk.cn', '.hl.cn', '.hn.cn', '.jl.cn', '.js.cn', '.jx.cn',
                        '.ln.cn', '.mo.cn', '.net.cn', '.nm.cn', '.nx.cn', '.org.cn','.my.id']
    old_domain_name = domain_name
    top_domain = "."+".".join(domain_name.rsplit('.')[-2:])
    new_top_domain = "." + top_domain.replace(".","")
    is_tow_top = False
    if top_domain in top_domain_list:
        is_tow_top = True
        domain_name = domain_name[:-len(top_domain)] + new_top_domain

    if domain_name.count(".") > 1:
        zone, middle, last = domain_name.rsplit(".", 2)
        acme_txt = "_acme-challenge.%s" % zone
        if is_tow_top: last = top_domain[1:]
        root = ".".join([middle, last])
    else:
        zone = ""
        root = old_domain_name
        acme_txt = "_acme-challenge"
    return root, zone, acme_txt

class BaseDns(object):
    def __init__(self):
        self.dns_provider_name = self.__class__.__name__

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

class DNSPodDns(BaseDns):
    dns_provider_name = "dnspod"
    _type = 0 # 0:lest 1：锐成
    def __init__(self, DNSPOD_ID, DNSPOD_API_KEY, DNSPOD_API_BASE_URL="https://dnsapi.cn/"):
        self.DNSPOD_ID = DNSPOD_ID
        self.DNSPOD_API_KEY = DNSPOD_API_KEY
        self.DNSPOD_API_BASE_URL = DNSPOD_API_BASE_URL
        self.HTTP_TIMEOUT = 65  # seconds
        self.DNSPOD_LOGIN = "{0},{1}".format(self.DNSPOD_ID, self.DNSPOD_API_KEY)

        if DNSPOD_API_BASE_URL[-1] != "/":
            self.DNSPOD_API_BASE_URL = DNSPOD_API_BASE_URL + "/"
        else:
            self.DNSPOD_API_BASE_URL = DNSPOD_API_BASE_URL
        super(DNSPodDns, self).__init__()

    def create_dns_record(self, domain_name, domain_dns_value):
        domain_name,_,subd = extract_zone(domain_name)
        if self._type == 1:
            self.add_record(domain_name,subd.replace('_acme-challenge.',''),domain_dns_value,'CNAME')
        else:
            self.add_record(domain_name,subd,domain_dns_value,'TXT')



    def add_record(self,domain_name,subd,domain_dns_value,s_type):
        url = urljoin(self.DNSPOD_API_BASE_URL, "Record.Create")
        body = {
            "record_type": s_type,
            "domain": domain_name,
            "sub_domain": subd,
            "value": domain_dns_value,
            "record_line_id": "0",
            "format": "json",
            "login_token": self.DNSPOD_LOGIN,
        }
        create_dnspod_dns_record_response = requests.post(
            url, data=body, timeout=self.HTTP_TIMEOUT
        ).json()
        if create_dnspod_dns_record_response["status"]["code"] != "1":
            raise ValueError(
                "Error creating dnspod dns record: status_code={status_code} response={response}".format(
                    status_code=create_dnspod_dns_record_response["status"]["code"],
                    response=create_dnspod_dns_record_response["status"]["message"],
                )
            )


    def remove_record(self,domain_name,subd,s_type):
        url = urljoin(self.DNSPOD_API_BASE_URL, "Record.List")
        rootdomain = domain_name
        body = {
            "login_token": self.DNSPOD_LOGIN,
            "format": "json",
            "domain": rootdomain,
            "subdomain": subd,
            "record_type": s_type,
        }
        list_dns_response = requests.post(url, data=body, timeout=self.HTTP_TIMEOUT).json()
        for i in range(0, len(list_dns_response["records"])):
            if list_dns_response["records"][i]['name'] != subd:
                continue
            rid = list_dns_response["records"][i]["id"]
            urlr = urljoin(self.DNSPOD_API_BASE_URL, "Record.Remove")
            bodyr = {
                "login_token": self.DNSPOD_LOGIN,
                "format": "json",
                "domain": rootdomain,
                "record_id": rid,
            }
            requests.post(
                urlr, data=bodyr, timeout=self.HTTP_TIMEOUT
            ).json()

    def delete_dns_record(self, domain_name, domain_dns_value):
        try:
            domain_name,_,subd = extract_zone(domain_name)
            self.remove_record(domain_name,subd,'TXT')
            self.remove_record(domain_name,'_acme-challenge','CNAME')
        except:
            pass



class CloudFlareDns(BaseDns):
    dns_provider_name = "cloudflare"
    _type = 0 # 0:lest 1：锐成
    def __init__(
        self,
        CLOUDFLARE_EMAIL,
        CLOUDFLARE_API_KEY,
        CLOUDFLARE_API_BASE_URL="https://api.cloudflare.com/client/v4/",
    ):
        self.CLOUDFLARE_DNS_ZONE_ID = None
        self.CLOUDFLARE_EMAIL = CLOUDFLARE_EMAIL
        self.CLOUDFLARE_API_KEY = CLOUDFLARE_API_KEY
        self.CLOUDFLARE_API_BASE_URL = CLOUDFLARE_API_BASE_URL
        self.HTTP_TIMEOUT = 65  # seconds

        try:
            import urllib.parse as urlparse
        except:
            import urlparse

        if CLOUDFLARE_API_BASE_URL[-1] != "/":
            self.CLOUDFLARE_API_BASE_URL = CLOUDFLARE_API_BASE_URL + "/"
        else:
            self.CLOUDFLARE_API_BASE_URL = CLOUDFLARE_API_BASE_URL
        super(CloudFlareDns, self).__init__()

    def get_headers(self):
        if os.path.exists('/www/server/panel/data/cf_limit_api.pl'):
            headers = {"Authorization": "Bearer "+self.CLOUDFLARE_API_KEY}
        else:
            headers = {"X-Auth-Email": self.CLOUDFLARE_EMAIL, "X-Auth-Key": self.CLOUDFLARE_API_KEY}
        return headers

    def find_dns_zone(self, domain_name):
        url = urljoin(self.CLOUDFLARE_API_BASE_URL, "zones?status=active&name={0}".format(domain_name))
        headers = self.get_headers()
        find_dns_zone_response = requests.get(url, headers=headers, timeout=self.HTTP_TIMEOUT)
        if find_dns_zone_response.status_code != 200:
            raise ValueError(
                "Error creating cloudflare dns record: status_code={status_code} response={response}".format(
                    status_code=find_dns_zone_response.status_code,
                    response=self.log_response(find_dns_zone_response),
                )
            )

        result = find_dns_zone_response.json()["result"]
        for i in result:
            if i["name"] in domain_name:
                setattr(self, "CLOUDFLARE_DNS_ZONE_ID", i["id"])
        if isinstance(self.CLOUDFLARE_DNS_ZONE_ID, type(None)):
            raise ValueError(
                "Error unable to get DNS zone for domain_name={domain_name}: status_code={status_code} response={response}".format(
                    domain_name=domain_name,
                    status_code=find_dns_zone_response.status_code,
                    response=self.log_response(find_dns_zone_response),
                )
            )

    def add_record(self,domain_name,value,s_type):
        url = urljoin(
            self.CLOUDFLARE_API_BASE_URL,
            "zones/{0}/dns_records".format(self.CLOUDFLARE_DNS_ZONE_ID),
        )
        # if '_' in self.CLOUDFLARE_API_KEY or '-' in self.CLOUDFLARE_API_KEY:
        #     headers = {"Authorization": "Bearer "+self.CLOUDFLARE_API_KEY}
        # else:
        #     headers = {"X-Auth-Email": self.CLOUDFLARE_EMAIL, "X-Auth-Key": self.CLOUDFLARE_API_KEY}
        headers = self.get_headers()
        body = {
            "type": s_type,
            "name": domain_name,
            "content": "{0}".format(value),
        }

        create_cloudflare_dns_record_response = requests.post(
            url, headers=headers, json=body, timeout=self.HTTP_TIMEOUT
        )
        if create_cloudflare_dns_record_response.status_code != 200:
            raise ValueError(
                "Error creating cloudflare dns record: status_code={status_code} response={response}".format(
                    status_code=create_cloudflare_dns_record_response.status_code,
                    response=self.log_response(create_cloudflare_dns_record_response),
                )
            )

    def create_dns_record(self, domain_name, domain_dns_value):
        domain_name = domain_name.lstrip("*.")
        self.find_dns_zone(domain_name)

        url = urljoin(
            self.CLOUDFLARE_API_BASE_URL,
            "zones/{0}/dns_records".format(self.CLOUDFLARE_DNS_ZONE_ID),
        )
        # if '_' in self.CLOUDFLARE_API_KEY or '-' in self.CLOUDFLARE_API_KEY:
        #     headers = {"Authorization": "Bearer "+self.CLOUDFLARE_API_KEY}
        # else:
        #     headers = {"X-Auth-Email": self.CLOUDFLARE_EMAIL, "X-Auth-Key": self.CLOUDFLARE_API_KEY}
        headers = self.get_headers()
        body = {
            "type": "TXT",
            "name": "_acme-challenge" + "." + domain_name + ".",
            "content": "{0}".format(domain_dns_value),
        }

        if self._type == 1:
            body['type'] = 'CNAME'
            root, _, acme_txt = extract_zone(domain_name)
            body['name'] = acme_txt.replace('_acme-challenge.','')

        create_cloudflare_dns_record_response = requests.post(
            url, headers=headers, json=body, timeout=self.HTTP_TIMEOUT
        )
        if create_cloudflare_dns_record_response.status_code != 200:
            # raise error so that we do not continue to make calls to ACME
            # server
            raise ValueError(
                "Error creating cloudflare dns record: status_code={status_code} response={response}".format(
                    status_code=create_cloudflare_dns_record_response.status_code,
                    response=self.log_response(create_cloudflare_dns_record_response),
                )
            )


    def remove_record(self,domain_name,dns_name,s_type):
        # if '_' in self.CLOUDFLARE_API_KEY or '-' in self.CLOUDFLARE_API_KEY:
        #     headers = {"Authorization": "Bearer "+self.CLOUDFLARE_API_KEY}
        # else:
        #     headers = {"X-Auth-Email": self.CLOUDFLARE_EMAIL, "X-Auth-Key": self.CLOUDFLARE_API_KEY}
        headers = self.get_headers()
        list_dns_payload = {"type": s_type, "name": dns_name}
        list_dns_url = urljoin(
            self.CLOUDFLARE_API_BASE_URL,
            "zones/{0}/dns_records".format(self.CLOUDFLARE_DNS_ZONE_ID),
        )

        list_dns_response = requests.get(
            list_dns_url, params=list_dns_payload, headers=headers, timeout=self.HTTP_TIMEOUT
        )

        for i in range(0, len(list_dns_response.json()["result"])):
            dns_record_id = list_dns_response.json()["result"][i]["id"]
            url = urljoin(
                self.CLOUDFLARE_API_BASE_URL,
                "zones/{0}/dns_records/{1}".format(self.CLOUDFLARE_DNS_ZONE_ID, dns_record_id),
            )
            headers = {"X-Auth-Email": self.CLOUDFLARE_EMAIL, "X-Auth-Key": self.CLOUDFLARE_API_KEY}
            requests.delete(
                url, headers=headers, timeout=self.HTTP_TIMEOUT
            )

    def delete_dns_record(self, domain_name, domain_dns_value):
        domain_name = domain_name.lstrip("*.")
        dns_name = "_acme-challenge" + "." + domain_name
        self.remove_record(domain_name,dns_name,'TXT')



class AliyunDns(object):
    _type = 0 # 0:lest 1：锐成
    def __init__(self, key, secret, ):
        self.key = str(key).strip()
        self.secret = str(secret).strip()
        self.url = "http://alidns.aliyuncs.com"

    def sign(self, accessKeySecret, parameters):  # '''签名方法
        def percent_encode(encodeStr):
            encodeStr = str(encodeStr)
            if sys.version_info[0] == 3:
                import urllib.request
                res = urllib.request.quote(encodeStr, '')
            else:
                res = urllib2.quote(encodeStr, '')
            res = res.replace('+', '%20')
            res = res.replace('*', '%2A')
            res = res.replace('%7E', '~')
            return res

        sortedParameters = sorted(parameters.items(), key=lambda parameters: parameters[0])
        canonicalizedQueryString = ''
        for (k, v) in sortedParameters:
            canonicalizedQueryString += '&' + percent_encode(k) + '=' + percent_encode(v)
        stringToSign = 'GET&%2F&' + percent_encode(canonicalizedQueryString[1:])
        if sys.version_info[0] == 2:
            h = hmac.new(accessKeySecret + "&", stringToSign, sha1)
        else:
            h = hmac.new(bytes(accessKeySecret + "&", encoding="utf8"), stringToSign.encode('utf8'), sha1)
        signature = base64.encodestring(h.digest()).strip()
        return signature


    def create_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        self.delete_dns_record(domain_name, domain_dns_value)
        if self._type == 1:
            acme_txt = acme_txt.replace('_acme-challenge.','')
            self.add_record(root,'CNAME',acme_txt,domain_dns_value)
        else:
            try:
                self.add_record(root,'CAA','@',caa_value)
            except: pass
            self.add_record(root,'TXT',acme_txt,domain_dns_value)

    def add_record(self,domain,s_type,host,value):
        randomint = random.randint(11111111111111, 99999999999999)
        now = datetime.datetime.utcnow()
        otherStyleTime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        paramsdata = {
            "Action": "AddDomainRecord", "Format": "json", "Version": "2015-01-09", "SignatureMethod": "HMAC-SHA1", "Timestamp": otherStyleTime,
            "SignatureVersion": "1.0", "SignatureNonce": str(randomint), "AccessKeyId": self.key,
            "DomainName": domain,
            "RR": host,
            "Type": s_type,
            "Value": value,
        }

        Signature = self.sign(self.secret, paramsdata)
        paramsdata['Signature'] = Signature
        req = requests.get(url=self.url, params=paramsdata)
        if req.status_code != 200:
            if req.json()['Code'] == 'IncorrectDomainUser' or req.json()['Code'] == 'InvalidDomainName.NoExist':
                raise ValueError("This domain name does not exist under this Ali cloud account. Adding parsing failed.")
            elif req.json()['Code'] == 'InvalidAccessKeyId.NotFound' or req.json()['Code'] == 'SignatureDoesNotMatch':
                raise ValueError("API key error, add parsing failed")
            else:
                raise ValueError(req.json()['Message'])

    def query_recored_items(self, host, zone=None, tipe=None, page=1, psize=200):
        randomint = random.randint(11111111111111, 99999999999999)
        now = datetime.datetime.utcnow()
        otherStyleTime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        paramsdata = {
            "Action": "DescribeDomainRecords", "Format": "json", "Version": "2015-01-09", "SignatureMethod": "HMAC-SHA1", "Timestamp": otherStyleTime,
            "SignatureVersion": "1.0", "SignatureNonce": str(randomint), "AccessKeyId": self.key,
            "DomainName": host,
        }
        if zone:
            paramsdata['RRKeyWord'] = zone
        if tipe:
            paramsdata['TypeKeyWord'] = tipe
        Signature = self.sign(self.secret, paramsdata)
        paramsdata['Signature'] = Signature
        req = requests.get(url=self.url, params=paramsdata)
        return req.json()

    def query_recored_id(self, root, zone, tipe="TXT"):
        record_id = None
        recoreds = self.query_recored_items(root, zone, tipe=tipe)
        recored_list = recoreds.get("DomainRecords", {}).get("Record", [])
        recored_item_list = [i for i in recored_list if i["RR"] == zone]
        if len(recored_item_list):
            record_id = recored_item_list[0]["RecordId"]
        return record_id

    def remove_record(self,domain,host,s_type = 'TXT'):
        record_id = self.query_recored_id(domain,host,s_type)
        if not record_id:
            msg = "Cannot find record_id for domain name: ", domain
            print(msg)
            return
        randomint = random.randint(11111111111111, 99999999999999)
        now = datetime.datetime.utcnow()
        otherStyleTime = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        paramsdata = {
            "Action": "DeleteDomainRecord", "Format": "json", "Version": "2015-01-09", "SignatureMethod": "HMAC-SHA1", "Timestamp": otherStyleTime,
            "SignatureVersion": "1.0", "SignatureNonce": str(randomint), "AccessKeyId": self.key,
            "RecordId": record_id,
        }
        Signature = self.sign(self.secret, paramsdata)
        paramsdata['Signature'] = Signature
        req = requests.get(url=self.url, params=paramsdata)
        if req.status_code != 200:
            raise ValueError("Deleting a parse record failed")

    def delete_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        self.remove_record(root,acme_txt,'TXT')
        self.remove_record(root,'@','CAA')
        self.remove_record(root,'_acme-challenge','CNAME')

class CloudxnsDns(object):
    def __init__(self, key, secret, ):
        self.key = key
        self.secret = secret
        self.APIREQUESTDATE = time.ctime()

    def get_headers(self, url, parameter=''):
        APIREQUESTDATE = self.APIREQUESTDATE
        APIHMAC = public.Md5(self.key + url + parameter + APIREQUESTDATE + self.secret)
        headers = {
            "API-KEY": self.key,
            "API-REQUEST-DATE": APIREQUESTDATE,
            "API-HMAC": APIHMAC,
            "API-FORMAT": "json"
        }
        return headers

    def get_domain_list(self):
        url = "https://www.cloudxns.net/api2/domain"
        headers = self.get_headers(url)
        req = requests.get(url=url, headers=headers,verify=False)
        req = req.json()

        return req

    def get_domain_id(self, domain_name):
        req = self.get_domain_list()
        for i in req["data"]:
            if domain_name.strip() == i['domain'][:-1]:
                return i['id']
        return False

    def create_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        domain = self.get_domain_id(root)
        if not domain:
            raise ValueError('The domain name does not exist under this cloudxns user, adding parsing failed.')

        url = "https://www.cloudxns.net/api2/record"
        data = {
            "domain_id": int(domain),
            "host": acme_txt,
            "value": domain_dns_value,
            "type": "TXT",
            "line_id": 1,
        }
        parameter = json.dumps(data)
        headers = self.get_headers(url, parameter)
        req = requests.post(url=url, headers=headers, data=parameter,verify=False)
        req = req.json()

        return req

    def delete_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        print("delete_dns_record start: ", acme_txt, domain_dns_value)
        url = "https://www.cloudxns.net/api2/record/{}/{}".format(self.get_record_id(root,'TXT'), self.get_domain_id(root))
        headers = self.get_headers(url, )
        req = requests.delete(url=url, headers=headers, verify=False)
        req = req.json()
        return req

    def get_record_id(self, domain_name,s_type = 'TXT'):
        url = "http://www.cloudxns.net/api2/record/{}?host_id=0&offset=0&row_num=2000".format(self.get_domain_id(domain_name))
        headers = self.get_headers(url, )
        req = requests.get(url=url, headers=headers,verify=False)
        req = req.json()
        for i in req['data']:
            if i['type'] == s_type:
                return i['record_id']
        return False

class Dns_com(object):
    _type = 0 # 0:lest 1：锐成
    def __init__(self, key, secret, ):
        pass

    def get_dns_obj(self):
        p_path = '/www/server/panel/plugin/dns'
        if not os.path.exists(p_path +'/dns_main.py'): return None
        sys.path.insert(0,p_path)
        import dns_main
        public.mod_reload(dns_main)
        return dns_main.dns_main()

    def create_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)

        if self._type == 1:
            acme_txt = acme_txt.replace('_acme-challenge.','')
            result = self.add_record(acme_txt + '.' + root,domain_dns_value)
        else:
            result = self.get_dns_obj().add_txt(acme_txt + '.' + root,domain_dns_value)

        if result == "False":
            raise ValueError('[DNS] This domain name does not exist in the currently bound Pagoda DNS cloud resolution account. Adding parsing failed!')
        time.sleep(5)

    def delete_dns_record(self, domain_name, domain_dns_value):
        root, _, acme_txt = extract_zone(domain_name)
        self.get_dns_obj().remove_txt(acme_txt + '.' + root)






