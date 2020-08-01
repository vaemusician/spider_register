# -*- coding:utf-8 -*-
from yam_core import register_func
from faker import Faker
import asyncio


f = Faker('zh_TW')


def register(**kw):
    task_msg = kw.get("task_msg")
    email = kw.get("email")
    email_pwd = kw.get("email_pwd")
    email_server = kw.get("email_server")
    password = kw.get("password", f'{f.password(16)}')
    proxy = kw.get('proxy', '')
    if email != None and proxy != None:
        loop = asyncio.get_event_loop()
        data = loop.run_until_complete(register_func(email, email_pwd, email_server, password, proxy))
    else:
        data = {
            'error': "必要参数不能为空！",
            'data': '',
            'code': 1102001
        }
    return data