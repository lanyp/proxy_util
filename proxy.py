import requests
from pyquery import PyQuery
import time
import random
from pymongo import MongoClient
import json
import threading


# 公共类
class Common:
    def __init__(self):
        # 定义一个User-Agent的List
        self.ua_list = [
            'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.94 Safari/537.36',
            'Mozilla/5.0 (compatible; Baiduspider/2.0; +http://www.baidu.com/search/spider.html)',
            'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)',
            'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            'Mozilla/5.0 (compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm)',
        ]
        self.headers = {
            'User-Agent': random.choice(self.ua_list),
        }
        # 验证代理的url
        self.url = 'http://www.baidu.com/'

    # 打开链接获取响应信息
    def get_response(self, url):
        response = requests.get(url, headers=self.headers, timeout=5)
        text = response.text
        return text

    # 验证代理是否可用
    def _alive(self, proxy):
        try:
            response_status_code = requests.get(url=self.url, headers=self.headers, proxies={"http": proxy},
                                                timeout=5).status_code
            if response_status_code == 200:
                print("可用代理:", proxy)
                return True
            else:
                print("不可用代理:", proxy)
                return False
        except Exception:
            print("无效代理:", proxy)
            return False

    # 开启多线程验证
    def thread_alive(self, proxy):
        thread = threading.Thread(target=self._alive, args=(proxy,))
        thread.start()


# 代理池
class ProxyPool:
    def __init__(self, proxys):
        self.pool = []
        self.proxys = proxys
        self.common = Common()

    # 获取可用的代理池
    def get_alive_pool(self, total_page):
        self.pool = self.proxys.get_pool(total_page)
        for i in self.pool:
            if self.common.thread_alive(i['ip_port']):
                continue
            else:
                self.pool.remove(i)

    # 写进文件
    def save_txt(self, path):
        try:
            file = open(path, 'w', encoding='utf-8')
            for i in self.pool:
                json.dump(i, file, ensure_ascii=False)
                file.write('\n')
            file.close()
        except FileNotFoundError:
            print("找不到文件路径")

    # 存在mongoDB中
    def save_mongo(self):
        try:
            client = MongoClient()
            db = client.Proxy  # 连接数据库(无则创建)
            db.xici.drop()  # 先删除数据库
            xici_proxy = db.xici  # 连接集合(无则创建)
            for i in self.pool:
                # 插入文档
                xici_proxy.insert(i)
        except ConnectionError:
            print("连接数据库失败")


# 基类
class IProxyBase:
    def __init__(self):
        self.pool = []

    def get_pool(self, total_page):
        return


# 子类继承基类
class XiciProxy(IProxyBase):
    def __init__(self, url):
        super(XiciProxy, self).__init__()
        self.url = url
        self.common = Common()

    # 获取代理池
    def get_pool(self, total_page):
        for i in range(1, int(total_page)):
            text = self.common.get_response(self.url + str(i))
            jpy = PyQuery(text)
            ips = jpy("#ip_list > tr").items()
            for ip in ips:
                tds = ip("td")
                if tds == []:
                    continue
                # 定义一个字典
                pool_dict = {}
                # ip加端口
                pool_dict["ip_port"] = tds[1].text + ":" + tds[2].text
                # 服务器地址
                pool_dict["address"] = tds("a").text()
                # 是否匿名
                pool_dict["anonymity"] = tds[4].text
                # 存货时间
                pool_dict["alive"] = tds[8].text
                self.pool.append(pool_dict)
        time.sleep(1)
        return self.pool


# 代理类
class Proxy_util:
    def __init__(self):
        # 西祠代理
        self.url = "http://www.xicidaili.com/wn/"

    # 获取代理
    def get(self, save_mongo=False, save_txt=False, path="d:/proxy.json", total_page=20):
        if int(total_page) < 2:
            total_page = 2
        proxys = XiciProxy(self.url)
        proxy_pool = ProxyPool(proxys)
        proxy_pool.get_alive_pool(int(total_page))
        if save_txt:
            proxy_pool.save_txt(path)
        if save_mongo:
            proxy_pool.save_mongo()
        return proxy_pool.pool


if __name__ == '__main__':
    proxys = Proxy_util().get(save_txt=True)
    print(random.choice(proxys))
