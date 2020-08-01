# -*- coding:utf-8 -*-
import asyncio
from pyppeteer import launch
import time
import imaplib
import email as mailParser
import re
import logging


logger = logging.getLogger("yam_register")
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
formatter = logging.Formatter(fmt="%(asctime)s-%(name)s-%(levelname)s-%(message)s")
ch.setFormatter(formatter)
logger.addHandler(ch)


def req_captcha(m, email_server):
    logger.info("正在搜索邮件，请稍等。")
    if email_server == 'imap.mail.ru':
        m.select('/&BCEEPwQwBDw-')
        msg, dataid = m.search(None, 'since 10-Sep-2019')
    else:
        msg, inbox_list = m.list()
        for box in inbox_list:
            m.select(box.split()[-1])
            msg, dataid = m.search(None, 'FROM member@mserice.yam.com')
            data_list = dataid[0].split()
            if len(data_list) != 0:
                break
    if msg != 'OK':
        raise Exception("搜索邮件失败，请重试。")
    id_list = dataid[0].split()
    if (id_list):
        _id = id_list[-1]
    else:
        raise Exception("暂未收到邮件")
    logger.info("正在处理邮件，请稍等。")
    msg, data = m.fetch(_id, 'RFC822')
    if msg != 'OK':
        raise Exception("获取指定邮件失败")
    content_list = []
    mail = mailParser.message_from_bytes(data[0][1])
    for part in mail.walk():
        if not part.is_multipart():
            if not part.get_param("name"):
                content_list.append(part.get_payload(
                    decode=True).decode('utf-8'))
    content = ''.join(content_list)
    logger.info("正在解析邮件，请稍等。")
    try:
        activate_code = re.findall('break-all;"><b>(.*?)</b>', content, re.S)[0]
        m.close()
        m.logout()
        print("此次注册邮箱验证码为：" + activate_code)
        return activate_code
    except:
        raise Exception("解析邮件失败.")


async def register_func(email, email_pwd, email_server, password, proxy):
    m = imaplib.IMAP4_SSL(email_server)
    try:
        msg, info = m.login(email, email_pwd)
    except Exception as e:
        logger.error("邮箱登陆失败.%s" % e.args)
        return {
            'error': '邮箱登陆失败,请检查邮箱账号密码是否正确。%s' % e.args,
            'code': 1103001,
            'data': ""
        }
    logger.debug("邮箱登陆成功...")
    browser = await launch(executablePath="/usr/bin/google-chrome-stable", headless=True, args=["--proxy-server=" + proxy, "--no-sandbox"])
    context = await browser.createIncognitoBrowserContext()
    page = await context.newPage()
    await page.setUserAgent(
        'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36')
    await page.evaluateOnNewDocument(
        '''
        () => {
        const newProto = navigator.__proto__;
        delete newProto.webdriver;
        navigator.__proto__ = newProto;
        }
        ''')
    await page.setViewport(viewport={'width': 1280, 'height': 800})
    res = await page.goto('https://membercenter.yam.com/Reg?URL=https://www.yam.com', timeout=300000)
    await page.waitFor(5000)
    if res.status == 200:
        logger.info("正在输入账号及密码，请稍等。")
        await page.type('#MEMBER_ID', email, delay=.2 * 1000)
        await page.type('#MEMBER_PWD', password, delay=.2 * 1000)
        await page.type('#MEMBER_PWDR', password, delay=.2 * 1000)
        await page.click('.button')
        if await page.J("#main div p:nth-child(8)"):
            print("已触发谷歌人机验证")
            await page.type('#MEMBER_PWDR', password, delay=.2 * 1000)
            await page.click('.button')
            raise Exception("谷歌人机验证失败,请重试。")
        else:
            print("未触发谷歌人机验证")
        await asyncio.sleep(150)
        try:
            activate_code = req_captcha(m, email_server)
            print("正在输入验证码...")
        except:
            return {
                'error': '邮箱获取验证码失败',
                'code': 1103002,
                'data': ""
            }
        activate_code = list(str(activate_code))
        for i in range(0, len(activate_code)):
            await page.type(f'input[name="c{i+1}"]', activate_code[i], delay=.2 * 1000)
        await page.waitFor(3000)
        await page.click('button')
        await page.waitFor(10000)
        await browser.close()
        print(email, password)
        logger.info("注册成功!")
        return {
            'code': 0,
            'data': {
                'email': email,
                'password': password,
            },
            'error': ''
        }
    else:
        print("请求网页响应失败，请重试。")
        await browser.close()