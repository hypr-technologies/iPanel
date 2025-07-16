#coding: utf-8
# +-------------------------------------------------------------------
# | iPanel
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 iPanel(www.iPanel.com) All rights reserved.
# +-------------------------------------------------------------------
# | Author: lotk
# | 登录处设置语言
# +-------------------------------------------------------------------

import public,os,sys,db,time,json,re
from BTPanel import session,cache,json_header
from flask import request,redirect,g

from Crypto import Random
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5 as PKCS1_cipher
import base64

try:
    from BTPanel import cache, session
except:
    pass

class userLang:

    # 获取语言选项
    def get_language(self, post):

        settings = '{}/BTPanel/languages/settings.json'.format(public.get_panel_path())
        custom = '{}/BTPanel/static/vite/lang/my-MY'.format(public.get_panel_path())
        if not os.path.exists(settings):
            data = {
                "default": "en",
                "languages": [
                    {
                        "name": "cht",
                        "google": "zh-tw",
                        "title": "繁體中文",
                        "cn": "繁體中文"
                    },
                    {
                        "name": "en",
                        "google": "en",
                        "title": "English",
                        "cn": "英语"
                    },
                    {
                        "name": "de",
                        "google": "de",
                        "title": "Deutsch",
                        "cn": "德语"
                    },
                    {
                        "name": "fra",
                        "google": "fr",
                        "title": "Français",
                        "cn": "法语"
                    },
                    {
                        "name": "spa",
                        "google": "es",
                        "title": "Español",
                        "cn": "西班牙语"
                    },
                    {
                        "name": "pt",
                        "google": "pt",
                        "title": "Português",
                        "cn": "葡萄牙语"
                    },
                    {
                        "name": "vie",
                        "google": "vi",
                        "title": "Tiếng Việt",
                        "cn": "越南语"
                    },
                    {
                        "name": "ind",
                        "google": "id",
                        "title": "Bahasa Indonesia",
                        "cn": "印尼语"
                    }, {
                        "name": "ru",
                        "google": "ru",
                        "title": "Русский",
                        "cn": "俄语"
                    }
                ]
            }
            public.writeFile(settings, json.dumps(data))

        settings_content = public.readFile(settings)
        try:
            if settings_content and settings_content.strip():
                data = json.loads(settings_content)
            else:
                data = {}
        except Exception as e:
            # public.print_log(f"settings.json 解析失败: {e}")
            data = {}

        #  保证default字段存在
        if 'default' not in data or not data['default']:
            data['default'] = 'en'
        #  保证languages字段存在
        if 'languages' not in data or not isinstance(data['languages'], list):
            data['languages'] = ['en']



        # data = json.loads(public.readFile(settings))
        if os.path.exists(custom):
            data['languages'].append({
                "name": "my",
                "google": "my",
                "title": "Custom",
                "cn": "自定义"
            })
        # 刚安装使用默认值
        if data['default']=="":
            data['default'] = 'en'

        return public.return_message(0, 0, data)

    # 设置语言偏好
    def set_language(self, post):

        if not hasattr(post, 'name'):
            return

        name = post.name
        if name == "":
            return

        # 登录阶段不设置 只记录
        path = "/www/server/panel/BTPanel/languages/language.pl"
        public.WriteFile(path, name)
        public.set_module_logs('language', 'login_set_language', 1)
        return public.return_message(0, 0, public.lang('The setup was successful'))

    # 获取当前设置的语言

