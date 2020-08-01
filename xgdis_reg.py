# -*- coding:utf-8 -*-
from discuss_core import Register


def register(**kw):
    task_msg = kw.get("task_msg")
    username = kw.get("username")
    password = kw.get("password")
    email = kw.get("email")
    email_server = kw.get("email_server")
    email_pwd = kw.get("email_pwd")
    proxy = kw.get('proxy', '')
    if email !=None and proxy != None:
        spider = Register(req_params=kw)
        data = spider.crawling_reg()
    else:
        data = {
            'error': "必要参数不能为空！",
            'data': '',
            'code': 1102001
        }
    return data