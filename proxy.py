import requests
import random
import time
import multiprocessing

USE_REDIS = True
if USE_REDIS:
    import redis as red
    redis = red.Redis(decode_responses=True)
    redis.flushdb()

class Proxy_Pool:
    def __init__(self, proxy_url:str,test_url:str,failwords:list=None, worker=4):
        self.proxy_url = proxy_url
        self.test_url = test_url
        self.failwords = failwords
        if not self.failwords:
            self.failwords = []
        self.s = requests.Session()
        self.Headers= {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/77.0.3865.90 Safari/537.36'}
        self.proxy = None
        self.start_proxy_service(worker)

    @staticmethod
    def save_Exception_info(e:Exception):
        with open('./Exception.txt', 'a') as f:
            f.write(str(e))
            f.write('\n')

    # get url with proxy (http only)
    def get(self,url,headers=None,renew=False,timeout=2):
        if not self.proxy:
            while redis.llen("proxy_Pool") == 0:
                time.sleep(random.random())
            self.proxy = redis.lpop("proxy_Pool")
        if renew:
            while redis.llen("proxy_Pool") == 0:
                time.sleep(random.random())
            self.proxy = redis.lpop("proxy_Pool")
        try:
            resp = self.s.get(url,headers=headers,timeout=timeout,proxies={'http':self.proxy})
        except requests.RequestException as e:
            self.save_Exception_info(e)
            return 0
        except Exception as e:
            self.save_Exception_info(e)
            return self.get(url,headers,renew=True, timeout=timeout)
        try:
            content = resp.content.decode('utf-8')
        except  UnicodeEncodeError as e:
            self.save_Exception_info(e)
            return 0
        except Exception as e:
            self.save_Exception_info(e)
            return 0
        # check status ---->
        if resp.status_code != 200:
            print('Error status code', resp.status_code)
            return self.get(url,renew=True)
        for word in self.failwords:
            if word in content:
                return self.get(url,renew=True)
        # check end here ------
        return resp

    # start button of proxy service
    def start_proxy_service(self, worker):
        if not worker:
            raise ValueError('proxy worker not specified, expect int, got', type(worker) , worker)
        p = multiprocessing.Pool(worker)
        for _ in range(worker):
            print('start')
            p.apply_async(self.proxy_process)
        p.close()

    def proxy_process(self):
        while True:
            proxy = self.get_proxy(self.proxy_url,
                                   self.test_url,
            ['Bad gate']
            )
            redis.lpush("proxy_Pool",proxy)
            print('Add 1 proxy')
            time.sleep(1)

    # get a valid proxy
    def get_proxy(self,proxy_url:str, test_url:str, failwords=None):
        if not failwords:
            failwords = []
        proxy_count = 0
        while True:
            proxy_list = self.s.get(proxy_url,headers=self.Headers).content.decode('utf-8').split('\r\n') # windows form
            random.shuffle(proxy_list)  # optional
            for proxy in proxy_list:
                # test validity
                try:
                    response = self.s.get(test_url,headers=self.Headers,proxies={'http':proxy},timeout=3)
                except Exception as e:
                    proxy_count += 1
                    continue
                # check status
                if response.status_code != 200:
                    proxy_count += 1
                    continue
                # decode contents
                try:
                    content = response.content.decode('utf-8')
                except Exception as e:
                    self.save_Exception_info(e)
                    proxy_count += 1
                    continue
                # check key word
                for word in failwords:
                    if word in content:
                        proxy_count += 1
                        continue
                # refresh to try a new proxy list
                if proxy_count >= 7:
                    return self.get_proxy(proxy_url,test_url,failwords)
                return proxy


class MyRequests:
    def __init__(self):
        self.s = requests.Session()
        self.Headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}

    @staticmethod
    def save_Exception_info(e:Exception):
        with open('./Exception.txt', 'a') as f:
            f.write(str(e))
            f.write('\n')

    def get(self, url, timeout=5, retry=False, retryMax=0, retryCount=0):
        try:
            resp = self.s.get(url, timeout=timeout, headers=self.Headers)
        except Exception as e:
            print(e)
            self.save_Exception_info(e)
            if retry and retryCount < retryMax:
                retryCount += 1
                return self.get(url, timeout, retry, retryMax, retryCount)
            else:
                return False
        # check status code
        if resp.status_code != 200:
            print(resp.content.decode('utf-8'))
            if retry and retryCount < retryMax:
                retryCount += 1
                return self.get(url, timeout, retry, retryMax, retryCount)
            else:
                return False
        else:
            return resp


if __name__ == '__main__':
    e = Proxy_Pool('http://dev.energy67.top/api/?apikey=90c68bee2d04747b727310c1a810d9272a43cde8&num=15&type=text&line=win&proxy_type=putong&sort=rand&model=post&protocol=http&address=&kill_address=&port=&kill_port=&today=false&abroad=1&isp=&anonymity=2',
                   'http://search.ccgp.gov.cn/bxsearch?searchtype=1&page_index=1&start_time=&end_time=&timeType=2&searchparam=&searchchannel=0&dbselect=bidx&kw=&bidSort=0&pinMu=0&bidType=0&buyerName=&projectId=&displayZone=&zoneId=&agentName=',
                   ['Bad gate'])



