# -*- coding:utf-8 -*-
import asyncio
from pyppeteer import launch
import time
import requests
import imaplib
import email as mailParser
import re
requests.packages.urllib3.disable_warnings()


class Register:
    def __init__(self, req_params):
        self.req_params = req_params
        self.params_dict = {}
        self.params_dict['username'] = self.req_params['username']
        self.params_dict['password'] = self.req_params['password']
        self.params_dict['proxy'] = self.req_params['proxy']
        self.params_dict['email'] = self.req_params['email']
        self.params_dict['email_pwd'] = self.req_params['email_pwd']
        self.params_dict['email_server'] = self.req_params['email_server']
        print(self.params_dict)

    async def register_func(self):
        self.m = imaplib.IMAP4_SSL(self.params_dict['email_server'])
        try:
            msg, info = self.m.login(self.params_dict['email'], self.params_dict['email_pwd'])
            print("邮箱登录成功。")
        except Exception as e:
            return {
                'error': '邮箱登陆失败,请检查邮箱账号密码是否正确。%s' % e.args,
                'code': 1103001,
                'data': ""
            }
        try:
            msg_dict = dict(
                username='',
                password='',
            )
            browser = await launch(executablePath="/usr/bin/google-chrome-stable", headless=True, args=["--proxy-server=" + self.params_dict['proxy'], "--no-sandbox"])
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
                '''
            )
            await page.evaluateOnNewDocument("window.confirm=(e)=>true")
        except Exception as e:
            return {
                'error': '浏览器启动失败，请重试。%s' % e.args,
                'code': 1103002,
                'data': ""
            }
        try:
            await page.goto('https://www.discuss.com.hk/register.php', timeout=3000000)
            await page.waitFor(5000)
            await page.click('.cc-btn')
            await page.type('#username', self.params_dict['username'])
            await page.type('#password', self.params_dict['password'])
            await page.type('#password2', self.params_dict['password'])
            await page.type('#email', self.params_dict['email'])
        except Exception as e:
            return {
                'error': '请求网页响应失败，请重试。%s' % e.args,
                'code': 1103003,
                'data': ""
            }
        try:
            print("正在处理验证码...")
            page_url = "https://www.discuss.com.hk/register.php"
            API_KEY = "XXX"
            data_sitekey = "6LdLK0EUAAAAAOW4sWFiUm0FspjiEjX0pfhojEBt"
            u1 = f"https://2captcha.com/in.php?key={API_KEY}&method=userrecaptcha&googlekey={data_sitekey}&pageurl={page_url}&json=1"
            r1 = requests.get(u1)
            rid = r1.json().get("request")
            u2 = f"https://2captcha.com/res.php?key={API_KEY}&action=get&id={int(rid)}&json=1"
            time.sleep(25)
            for i in range(30):
                r2 = requests.get(u2)
                if r2.json().get("request") == 'CAPCHA_NOT_READY':
                    print("验证码尚未返回，请等待。")
                    time.sleep(5)
                elif r2.json().get("request") == 'ERROR_CAPTCHA_UNSOLVABLE':
                    print("验证码获取失败，请重启。")
                    await browser.close()
                    break
                elif r2.json().get("status") == 1:
                    print("验证码获取成功，正在提交。")
                    form_tokon = r2.json().get("request")
                    wirte_tokon_js = f'document.getElementById("g-recaptcha-response").innerHTML="{form_tokon}";'
                    submit_js = 'recapCallback()'
                    await page.evaluate(wirte_tokon_js)
                    await page.evaluate(submit_js)
                    await page.waitFor(3000)
                    await page.click('input[name="agree_tc"]')
                    await page.waitFor(5000)
                    await page.click('.submit')
                    await page.waitFor(10000)
                    await browser.close()
                    msg_dict['username'] = self.params_dict['username']
                    msg_dict['password'] = self.params_dict['password']
                    return msg_dict
        except Exception as e:
            return {
                'error': '谷歌验证码处理失败，请重试。%s' % e.args,
                'code': 1103004,
                'data': ""
            }

    def req_captcha(self):
        try:
            self.m.select('INBOX')
            msg, dataid = self.m.search(None, 'FROM no-reply@discuss.com.hk')
            if msg != 'OK':
                raise Exception("搜索邮件失败")
            id_list = dataid[0].split()
            if (id_list):
                _id = id_list[-1]
            else:
                raise Exception("暂未收到邮件")
            msg, data = self.m.fetch(_id, 'RFC822')
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
            try:
                activate_url = re.findall('<a href="(.*?)"', content, re.S)[0]
                activate_url = re.sub('amp;', '', activate_url)
                print(activate_url)
                self.m.close()
                self.m.logout()
                print("此次注册邮箱验证码为：" + activate_url)
                self.req_activate_code(activate_url)
            except Exception as e:
                raise Exception("解析邮件失败." % e.args)
        except Exception as e:
            raise Exception("获取注册邮箱链接失败，请重试。")

    def req_activate_code(self, activate_url):
        try:
            headers = {
                'authority': 'www.discuss.com.hk',
                'cache-control': 'max-age=0',
                'upgrade-insecure-requests': '1',
                'user-agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.116 Safari/537.36',
                'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'sec-fetch-site': 'none',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-user': '?1',
                'sec-fetch-dest': 'document',
                'accept-language': 'zh-CN,zh;q=0.9',
            }
            proxies = {
                'http': f'{self.params_dict["proxy"]}',
                'https': f'{self.params_dict["proxy"]}'
            }
            sess = requests.Session()
            response = sess.get(activate_url, headers=headers, proxies=proxies, verify=False)
            print(response.status_code)
            print("注册激活邮箱成功激活")
        except Exception as e:
            raise Exception("邮箱激活失败，请重试。")

    def crawling_reg(self):
        loop = asyncio.get_event_loop()
        msg_dict = loop.run_until_complete(self.register_func())
        time.sleep(300)
        try:
            self.req_captcha()
            return msg_dict
        except Exception as e:
            return {
                'error': '注册邮箱激活失败-%s' % e.args,
                'code': 1103004,
                'data': ''
            }