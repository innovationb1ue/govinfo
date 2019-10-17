import requests
import proxy
from bs4 import BeautifulSoup as bs
import logging
from multiprocessing import Pool
import os
import re
import csv


class govinfo:
    def __init__(self):
        self.s = proxy.my_requests()
        self.catalog2=0
        self.Headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36'}

    # start crawling
    def start(self):
        # self.multi_crawl_catalog(1, 23314, 363, worker=16, timeout=12)
        # self.get_article_info('http://govinfo.nlc.cn/gtfz/xxgk/gwyzcbm/jyb/201904/t20190404_22317377.shtml?classid=596;626#')
        self.multi_crawl_article()

    # subprocess generator for list page
    def multi_crawl_catalog(self, startpage, endpage, catalog2,  worker=4, timeout=8):
        self.catalog2 = catalog2
        p = Pool(worker)
        flag = (endpage-startpage+1) // worker
        # check wasted pages
        if os.path.exists('./wasted_%s.txt'%catalog2):
            with open('./wasted_%s.txt'%catalog2, 'r') as f:
                wastedPage = f.read().split('\n')
        else:
            wastedPage = []
        for i in range(worker):
            taskPages = [str(i) for i in range(startpage + i * flag, startpage + (i+1) * flag + 1) if str(i) not in wastedPage]
            p.apply_async(self.crawl_catalog, args=(taskPages,
                                                    catalog2,
                                                    timeout
                                                    )
                          )
        p.close()
        p.join()

    # crawl whole list page main function
    def crawl_catalog(self, pageindexlist, catalog2, timeout=8):
        for pageindex in pageindexlist:
            try:
                print('Getting %s'%pageindex)
                content = self.get_menu_page(pageindex, catalog2=catalog2, timeout=timeout)
                if content:
                    soup = bs(content, 'lxml')
                    tds = soup.find_all('a', attrs={'target':'_blank'})
                    urls = [i['href'] for i in tds[1:]]
                    with open('./urls.txt', 'a') as f:
                        for url in urls:
                            f.write(url)
                            f.write('\n')
                    with open('./wasted_%s.txt'%catalog2, 'a') as f:
                        f.write(str(pageindex))
                        f.write('\n')
            except Exception as e:
                print(e)
                with open('./error_page.txt', 'a') as f:
                    f.write(pageindex)
                    f.write('\n')
                with open('./Exception.txt', 'a') as f:
                    f.write(str(e))
                    f.write('\n')

                continue

    # get specific list page (component function)
    def get_menu_page(self, page=1, catalog2=363, timeout=2):
        url = 'http://govinfo.nlc.cn/search/pagezgb.jsp?catalog2=%s&tcfl=&page=%s'%(catalog2, page)
        resp = self.s.get(url, timeout=timeout, retry=True, retryMax=5)
        if resp:
            content = resp.content.decode('utf-8')
            return content
        else:
            return ''

    def multi_crawl_article(self, worker=4):
        p = Pool(worker)
        with open('./urls.txt', 'r') as f:
            urlList = f.read().split('\n')
        if os.path.exists('./wasted_urls_%s.txt'%self.catalog2):
            with open('./wasted_urls_%s.txt'%self.catalog2, 'r') as f:
                wasted = f.read().split('\n')
        else:
            wasted = set()
        urlList = list(set(urlList).symmetric_difference(set(wasted)))
        flag = len(urlList) // worker
        for i in range(worker):
            task = urlList[i*flag: (i+1)*flag]
            p.apply_async(self.crawl_article, args=(task,))
        p.close()
        p.join()

    # subprocess function crawl article (components function)
    def crawl_article(self, urlList):
        for url in urlList:
            title, body = self.get_article_info(url, timeout=8)
            with open('./articles_govinfo_%s.csv'%self.catalog2, 'a', encoding='utf-8',errors='ignore') as f:
                writer = csv.writer(f)
                writer.writerow([title, body])
            with open('./wasted_urls_%s.txt'%self.catalog2, 'a', encoding='utf-8', errors='ignore') as f:
                f.write(url)
                f.write('\n')

    # get specific page details(component function)
    def get_article_info(self, url, timeout=4):
        try:
            resp = self.s.get(url, timeout=timeout, retry=True, retryMax=5)
        except Exception as e:
            print(e)
            with open('Exception.txt', 'a') as f:
                f.write(str(e))
                f.write('\n')
            return ['', '']
        try:
            if resp:
                content = resp.content.decode('utf-8')
                infoTags = re.findall('OpenWindow.document.write\("(.*?)"\)', content)
                if infoTags:
                    title = infoTags[0]
                    body = infoTags[2]
                    print(title)
                    return[title, body]
                else:
                    return ['', '']
            else:
                return ['', '']
        except Exception as e:
            print(e)
            with open('Exception.txt', 'a') as f:
                f.write(str(e))
                f.write('\n')
            return ['', '']







if __name__ == '__main__':
    e = govinfo()
    e.start()